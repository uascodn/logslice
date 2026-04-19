"""Tests for logslice.parser module."""

import pytest
from logslice.parser import parse_line, _parse_logfmt


def test_parse_json_line():
    line = '{"level": "info", "msg": "started", "ts": "2024-01-01T00:00:00Z"}'
    result = parse_line(line)
    assert result == {"level": "info", "msg": "started", "ts": "2024-01-01T00:00:00Z"}


def test_parse_logfmt_simple():
    line = "level=info msg=started"
    result = parse_line(line)
    assert result == {"level": "info", "msg": "started"}


def test_parse_logfmt_quoted_value():
    line = 'level=error msg="something went wrong" code=500'
    result = _parse_logfmt(line)
    assert result["msg"] == "something went wrong"
    assert result["code"] == "500"


def test_parse_empty_line():
    assert parse_line("") is None
    assert parse_line("   ") is None


def test_parse_invalid_json_falls_back_to_logfmt():
    # Starts with { but is invalid JSON — should return None (logfmt also fails)
    line = "{not valid json"
    result = parse_line(line)
    assert result is None


def test_parse_logfmt_no_pairs():
    result = _parse_logfmt("no equals sign here")
    assert result is None


def test_parse_logfmt_empty_value():
    """A key with an empty value (key=) should be parsed with an empty string."""
    line = "level=info msg= code=200"
    result = _parse_logfmt(line)
    assert result is not None
    assert result["msg"] == ""
    assert result["level"] == "info"
    assert result["code"] == "200"
