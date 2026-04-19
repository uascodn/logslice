"""Tests for logslice.timerange module."""

import pytest
from datetime import datetime, timezone
from logslice.timerange import (
    parse_datetime,
    extract_timestamp,
    in_time_range,
    parse_time_range,
)


def dt(s):
    return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)


def test_parse_datetime_iso_z():
    result = parse_datetime("2024-03-01T12:00:00Z")
    assert result == datetime(2024, 3, 1, 12, 0, 0, tzinfo=timezone.utc)


def test_parse_datetime_with_microseconds():
    result = parse_datetime("2024-03-01T12:00:00.123456Z")
    assert result is not None
    assert result.microsecond == 123456


def test_parse_datetime_date_only():
    result = parse_datetime("2024-03-01")
    assert result == datetime(2024, 3, 1, tzinfo=timezone.utc)


def test_parse_datetime_invalid():
    assert parse_datetime("not-a-date") is None


def test_extract_timestamp_from_time_field():
    record = {"time": "2024-03-01T10:00:00Z", "msg": "hello"}
    ts = extract_timestamp(record)
    assert ts == datetime(2024, 3, 1, 10, 0, 0, tzinfo=timezone.utc)


def test_extract_timestamp_from_ts_field():
    record = {"ts": "2024-03-01T10:00:00Z"}
    ts = extract_timestamp(record)
    assert ts is not None


def test_extract_timestamp_missing():
    assert extract_timestamp({"msg": "no time here"}) is None


def test_in_time_range_within():
    record = {"time": "2024-03-01T12:00:00Z"}
    assert in_time_range(record, dt("2024-03-01T11:00:00"), dt("2024-03-01T13:00:00"))


def test_in_time_range_before_start():
    record = {"time": "2024-03-01T10:00:00Z"}
    assert not in_time_range(record, dt("2024-03-01T11:00:00"), None)


def test_in_time_range_after_end():
    record = {"time": "2024-03-01T14:00:00Z"}
    assert not in_time_range(record, None, dt("2024-03-01T13:00:00"))


def test_in_time_range_no_bounds():
    record = {"time": "2024-03-01T14:00:00Z"}
    assert in_time_range(record, None, None)


def test_in_time_range_no_timestamp_in_record():
    assert not in_time_range({"msg": "hi"}, dt("2024-03-01T00:00:00"), None)


def test_parse_time_range_valid():
    start, end = parse_time_range("2024-03-01T00:00:00Z", "2024-03-02T00:00:00Z")
    assert start < end


def test_parse_time_range_invalid_raises():
    with pytest.raises(ValueError, match="start time"):
        parse_time_range("bad-date", None)
