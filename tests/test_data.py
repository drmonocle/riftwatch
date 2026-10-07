"""
Unit tests for data normalization and date/time formatting.
"""

import datetime
from riftscout.data import format_relative_time, format_local_match_time, parse_iso_datetime


def test_parse_iso_datetime():
    dt = parse_iso_datetime("2026-10-07T12:00:00Z")
    assert dt is not None
    assert dt.year == 2026
    assert dt.month == 10
    assert dt.day == 7
    assert dt.hour == 12

    assert parse_iso_datetime("") is None
    assert parse_iso_datetime("invalid-date") is None


def test_format_relative_time():
    now = datetime.datetime.now(datetime.timezone.utc)

    # 30 minutes in the future
    future_30m = (now + datetime.timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    rel_30m = format_relative_time(future_30m)
    assert "in" in rel_30m and "m" in rel_30m

    # 2 hours in the future
    future_2h = (now + datetime.timedelta(hours=2, minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
    rel_2h = format_relative_time(future_2h)
    assert "in 2h" in rel_2h

    # 15 minutes ago
    past_15m = (now - datetime.timedelta(minutes=15)).strftime("%Y-%m-%dT%H:%M:%SZ")
    rel_past = format_relative_time(past_15m)
    assert "15m ago" in rel_past


def test_format_local_match_time():
    formatted = format_local_match_time("2026-10-07T18:00:00Z")
    assert len(formatted) > 5
    assert "Oct 07" in formatted
