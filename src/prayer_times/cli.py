"""Command-line interface: `prayer-times صنعاء`."""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .core import PRAYERS, PrayerTimesError, fetch_times, format_delta, next_prayer


def render(times, upcoming: str, remaining) -> str:
    lines = [f"مواقيت الصلاة في {times.city}"]
    sub = " | ".join(x for x in (times.date, times.hijri) if x)
    if sub:
        lines.append(sub)
    lines.append("-" * 28)
    for key, ar in PRAYERS:
        marker = "  ◀ القادمة" if ar == upcoming and key != "Sunrise" else ""
        lines.append(f"{ar:<8} {times.timings[key]}{marker}")
    lines.append("-" * 28)
    lines.append(f"الصلاة القادمة: {upcoming} — بعد {format_delta(remaining)}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="prayer-times",
        description="عرض مواقيت الصلاة لأي مدينة (من aladhan.com)",
    )
    parser.add_argument("city", nargs="+", help="اسم المدينة، مثل: صنعاء أو Cairo")
    parser.add_argument(
        "-m", "--method", type=int, default=None,
        help="طريقة الحساب في aladhan.com (مثلاً 4 = أم القرى)",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args(argv)

    city = " ".join(args.city)
    try:
        times = fetch_times(city, args.method)
        upcoming, remaining = next_prayer(times)
    except PrayerTimesError as exc:
        print(f"خطأ: {exc}", file=sys.stderr)
        return 1
    print(render(times, upcoming, remaining))
    return 0


if __name__ == "__main__":
    sys.exit(main())
