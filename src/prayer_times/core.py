"""Core logic: fetch prayer times from aladhan.com and compute the next prayer."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

API_BASE = "https://api.aladhan.com/v1"

# (API key, Arabic name)
PRAYERS: list[tuple[str, str]] = [
    ("Fajr", "الفجر"),
    ("Sunrise", "الشروق"),
    ("Dhuhr", "الظهر"),
    ("Asr", "العصر"),
    ("Maghrib", "المغرب"),
    ("Isha", "العشاء"),
]

# Common Arabic city names -> (city, country) in English for reliable lookups.
CITIES: dict[str, tuple[str, str]] = {
    "صنعاء": ("Sanaa", "Yemen"),
    "عدن": ("Aden", "Yemen"),
    "تعز": ("Taiz", "Yemen"),
    "الحديدة": ("Al Hudaydah", "Yemen"),
    "إب": ("Ibb", "Yemen"),
    "المكلا": ("Mukalla", "Yemen"),
    "مكة": ("Makkah", "Saudi Arabia"),
    "مكة المكرمة": ("Makkah", "Saudi Arabia"),
    "المدينة": ("Madinah", "Saudi Arabia"),
    "المدينة المنورة": ("Madinah", "Saudi Arabia"),
    "الرياض": ("Riyadh", "Saudi Arabia"),
    "جدة": ("Jeddah", "Saudi Arabia"),
    "الدمام": ("Dammam", "Saudi Arabia"),
    "القاهرة": ("Cairo", "Egypt"),
    "الإسكندرية": ("Alexandria", "Egypt"),
    "دبي": ("Dubai", "United Arab Emirates"),
    "أبوظبي": ("Abu Dhabi", "United Arab Emirates"),
    "الدوحة": ("Doha", "Qatar"),
    "الكويت": ("Kuwait City", "Kuwait"),
    "المنامة": ("Manama", "Bahrain"),
    "مسقط": ("Muscat", "Oman"),
    "عمّان": ("Amman", "Jordan"),
    "عمان": ("Amman", "Jordan"),
    "القدس": ("Jerusalem", "Palestine"),
    "غزة": ("Gaza", "Palestine"),
    "دمشق": ("Damascus", "Syria"),
    "بيروت": ("Beirut", "Lebanon"),
    "بغداد": ("Baghdad", "Iraq"),
    "الخرطوم": ("Khartoum", "Sudan"),
    "طرابلس": ("Tripoli", "Libya"),
    "تونس": ("Tunis", "Tunisia"),
    "الجزائر": ("Algiers", "Algeria"),
    "الرباط": ("Rabat", "Morocco"),
    "الدار البيضاء": ("Casablanca", "Morocco"),
    "إسطنبول": ("Istanbul", "Turkey"),
}


class PrayerTimesError(Exception):
    """Raised when prayer times cannot be fetched or parsed."""


@dataclass
class DayTimes:
    city: str
    timezone: str
    date: str  # DD-MM-YYYY as returned by the API
    hijri: str
    timings: dict[str, str]  # API key -> "HH:MM"


def build_url(city: str, method: int | None = None) -> str:
    """Build the aladhan.com request URL for a city (Arabic or English)."""
    name = city.strip()
    params: dict[str, str] = {}
    if name in CITIES:
        en_city, country = CITIES[name]
        endpoint = "timingsByCity"
        params = {"city": en_city, "country": country}
    else:
        endpoint = "timingsByAddress"
        params = {"address": name}
    if method is not None:
        params["method"] = str(method)
    return f"{API_BASE}/{endpoint}?{urllib.parse.urlencode(params)}"


def _clean_time(value: str) -> str:
    # The API may append a timezone abbreviation, e.g. "04:31 (+03)".
    return value.strip().split(" ")[0]


def parse_response(payload: dict, city: str) -> DayTimes:
    """Turn an aladhan.com JSON payload into a DayTimes."""
    if payload.get("code") != 200 or not isinstance(payload.get("data"), dict):
        raise PrayerTimesError(f"تعذّر العثور على مواقيت لمدينة: {city}")
    data = payload["data"]
    raw = data.get("timings", {})
    try:
        timings = {key: _clean_time(raw[key]) for key, _ in PRAYERS}
    except KeyError as exc:
        raise PrayerTimesError(f"استجابة غير مكتملة من الخادم: {exc}") from exc
    date = data.get("date", {})
    hijri = date.get("hijri", {})
    hijri_text = ""
    if hijri:
        month = hijri.get("month", {}).get("ar", "")
        hijri_text = f"{hijri.get('day', '')} {month} {hijri.get('year', '')} هـ".strip()
    return DayTimes(
        city=city,
        timezone=data.get("meta", {}).get("timezone", "UTC"),
        date=date.get("gregorian", {}).get("date", ""),
        hijri=hijri_text,
        timings=timings,
    )


def fetch_times(city: str, method: int | None = None, timeout: float = 15) -> DayTimes:
    """Fetch today's prayer times for a city from aladhan.com."""
    url = build_url(city, method)
    req = urllib.request.Request(url, headers={"User-Agent": "prayer-times-cli"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.load(resp)
    except urllib.error.HTTPError as exc:
        try:
            payload = json.load(exc)
        except Exception:
            raise PrayerTimesError(f"خطأ من الخادم ({exc.code}) لمدينة: {city}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise PrayerTimesError(f"تعذّر الاتصال بالخادم: {exc}") from exc
    return parse_response(payload, city)


def next_prayer(times: DayTimes, now: datetime | None = None) -> tuple[str, timedelta]:
    """Return (Arabic name, time remaining) of the next prayer.

    `now` defaults to the current time in the city's timezone. Sunrise is
    shown in the table but is not counted as a prayer here. After Isha the
    next prayer is tomorrow's Fajr (approximated by today's Fajr time).
    """
    tz = ZoneInfo(times.timezone)
    if now is None:
        now = datetime.now(tz)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=tz)
    else:
        now = now.astimezone(tz)

    for key, ar in PRAYERS:
        if key == "Sunrise":
            continue
        h, m = map(int, times.timings[key].split(":"))
        at = now.replace(hour=h, minute=m, second=0, microsecond=0)
        if at > now:
            return ar, at - now

    h, m = map(int, times.timings["Fajr"].split(":"))
    at = now.replace(hour=h, minute=m, second=0, microsecond=0) + timedelta(days=1)
    return "الفجر", at - now


def format_delta(delta: timedelta) -> str:
    """Format a timedelta as Arabic text, e.g. '2 ساعة و 5 دقيقة'."""
    total_min = int(delta.total_seconds() // 60)
    hours, minutes = divmod(total_min, 60)
    if hours and minutes:
        return f"{hours} ساعة و {minutes} دقيقة"
    if hours:
        return f"{hours} ساعة"
    return f"{minutes} دقيقة"
