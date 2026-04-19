"""Tests for logslice.slicer module."""

import json
import pytest
from logslice.slicer import slice_lines


def make_json_line(**kwargs):
    return json.dumps(kwargs)


LINES = [
    make_json_line(time="2024-03-01T09:00:00Z", level="info", msg="startup"),
    make_json_line(time="2024-03-01T10:00:00Z", level="error", msg="oops"),
    make_json_line(time="2024-03-01T11:00:00Z", level="info", msg="running"),
    make_json_line(time="2024-03-01T12:00:00Z", level="warn", msg="slow"),
]


def test_slice_no_filters():
    results = list(slice_lines(LINES))
    assert len(results) == 4


def test_slice_start_time():
    results = list(slice_lines(LINES, start_str="2024-03-01T10:00:00Z"))
    assert len(results) == 3
    assert results[0]["msg"] == "oops"


def test_slice_end_time():
    results = list(slice_lines(LINES, end_str="2024-03-01T10:00:00Z"))
    assert len(results) == 2


def test_slice_time_range():
    results = list(slice_lines(
        LINES,
        start_str="2024-03-01T10:00:00Z",
        end_str="2024-03-01T11:00:00Z",
    ))
    assert len(results) == 2


def test_slice_with_filter():
    results = list(slice_lines(LINES, filter_exprs=["level=error"]))
    assert len(results) == 1
    assert results[0]["msg"] == "oops"


def test_slice_time_and_filter():
    results = list(slice_lines(
        LINES,
        start_str="2024-03-01T10:00:00Z",
        filter_exprs=["level=info"],
    ))
    assert len(results) == 1
    assert results[0]["msg"] == "running"


def test_slice_skips_empty_lines():
    lines = ["", "  ", make_json_line(time="2024-03-01T10:00:00Z", msg="hi")]
    results = list(slice_lines(lines))
    assert len(results) == 1


def test_slice_invalid_start_raises():
    with pytest.raises(ValueError):
        list(slice_lines(LINES, start_str="not-a-date"))
