import io
import json
from datetime import datetime, timedelta
from urllib.parse import parse_qs, urlparse
from zoneinfo import ZoneInfo

import pytest

from prayer_times import cli, core
from prayer_times.core import (
    DayTimes,
    PrayerTimesError,
    build_url,
    format_delta,
    next_prayer,
    parse_response,
)

SAMPLE = {
    "code": 200,
    "status": "OK",
    "data": {
        "timings": {
            "Fajr": "04:30",
            "Sunrise": "05:50",
            "Dhuhr": "11:55",
            "Asr": "15:15",
            "Sunset": "17:58",
            "Maghrib": "18:00",
            "Isha": "19:15 (+03)",
            "Imsak": "04:20",
            "Midnight": "23:55",
        },
        "date": {
            "gregorian": {"date": "01-11-2026"},
            "hijri": {"day": "20", "month": {"ar": "جُمادى الأولى"}, "year": "1448"},
        },
        "meta": {"timezone": "Asia/Aden"},
    },
}

TZ = ZoneInfo("Asia/Aden")


@pytest.fixture
def times():
    return parse_response(SAMPLE, "صنعاء")


def test_build_url_known_arabic_city():
    url = urlparse(build_url("صنعاء"))
    assert url.path.endswith("/timingsByCity")
    assert parse_qs(url.query) == {"city": ["Sanaa"], "country": ["Yemen"]}


def test_build_url_unknown_city_uses_address_and_method():
    url = urlparse(build_url(" London ", method=3))
    assert url.path.endswith("/timingsByAddress")
    assert parse_qs(url.query) == {"address": ["London"], "method": ["3"]}


def test_parse_response(times):
    assert times.timezone == "Asia/Aden"
    assert times.date == "01-11-2026"
    assert "1448" in times.hijri
    assert list(times.timings) == ["Fajr", "Sunrise", "Dhuhr", "Asr", "Maghrib", "Isha"]
    assert times.timings["Isha"] == "19:15"  # timezone suffix stripped


def test_parse_response_error():
    with pytest.raises(PrayerTimesError):
        parse_response({"code": 400, "data": "Unable to geocode"}, "xyz")


def test_parse_response_missing_key():
    bad = json.loads(json.dumps(SAMPLE))
    del bad["data"]["timings"]["Asr"]
    with pytest.raises(PrayerTimesError):
        parse_response(bad, "صنعاء")


@pytest.mark.parametrize(
    "hour, minute, expected, remaining",
    [
        (3, 0, "الفجر", timedelta(hours=1, minutes=30)),
        (5, 0, "الظهر", timedelta(hours=6, minutes=55)),  # sunrise is skipped
        (12, 0, "العصر", timedelta(hours=3, minutes=15)),
        (17, 59, "المغرب", timedelta(minutes=1)),
        (18, 30, "العشاء", timedelta(minutes=45)),
        (22, 0, "الفجر", timedelta(hours=6, minutes=30)),  # tomorrow
    ],
)
def test_next_prayer(times, hour, minute, expected, remaining):
    now = datetime(2026, 11, 1, hour, minute, tzinfo=TZ)
    name, delta = next_prayer(times, now)
    assert name == expected
    assert delta == remaining


def test_next_prayer_converts_other_timezones(times):
    now_utc = datetime(2026, 11, 1, 9, 0, tzinfo=ZoneInfo("UTC"))  # 12:00 in Aden
    assert next_prayer(times, now_utc)[0] == "العصر"


def test_next_prayer_exactly_at_prayer_time_moves_on(times):
    now = datetime(2026, 11, 1, 11, 55, tzinfo=TZ)
    assert next_prayer(times, now)[0] == "العصر"


@pytest.mark.parametrize(
    "delta, text",
    [
        (timedelta(minutes=5), "5 دقيقة"),
        (timedelta(hours=2), "2 ساعة"),
        (timedelta(hours=2, minutes=5, seconds=40), "2 ساعة و 5 دقيقة"),
    ],
)
def test_format_delta(delta, text):
    assert format_delta(delta) == text


def test_fetch_times_uses_api(monkeypatch):
    seen = {}

    def fake_urlopen(req, timeout):
        seen["url"] = req.full_url
        return io.BytesIO(json.dumps(SAMPLE).encode())

    monkeypatch.setattr(core.urllib.request, "urlopen", fake_urlopen)
    result = core.fetch_times("صنعاء")
    assert "api.aladhan.com" in seen["url"]
    assert result.timings["Fajr"] == "04:30"


def test_cli_prints_arabic_times(monkeypatch, capsys, times):
    monkeypatch.setattr(cli, "fetch_times", lambda city, method: times)
    monkeypatch.setattr(cli, "next_prayer", lambda t: ("العصر", timedelta(hours=1, minutes=10)))
    assert cli.main(["صنعاء"]) == 0
    out = capsys.readouterr().out
    for name in ("الفجر", "الشروق", "الظهر", "العصر", "المغرب", "العشاء"):
        assert name in out
    assert "مواقيت الصلاة في صنعاء" in out
    assert "الصلاة القادمة: العصر — بعد 1 ساعة و 10 دقيقة" in out


def test_cli_error(monkeypatch, capsys):
    def boom(city, method):
        raise PrayerTimesError("لا توجد مدينة")

    monkeypatch.setattr(cli, "fetch_times", boom)
    assert cli.main(["xyz"]) == 1
    assert "لا توجد مدينة" in capsys.readouterr().err
