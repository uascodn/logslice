"""Tests for logslice.output module."""

import json
import pytest
from logslice.output import format_json, format_logfmt, format_pretty, format_record


SAMPLE = {"timestamp": "2024-01-01T00:00:00Z", "level": "info", "msg": "hello world", "code": 200}


def test_format_json_roundtrip():
    result = format_json(SAMPLE)
    parsed = json.loads(result)
    assert parsed == SAMPLE


def test_format_logfmt_simple():
    record = {"level": "info", "msg": "ok"}
    result = format_logfmt(record)
    assert "level=info" in result
    assert "msg=ok" in result


def test_format_logfmt_quotes_spaces():
    record = {"msg": "hello world"}
    result = format_logfmt(record)
    assert 'msg="hello world"' in result


def test_format_logfmt_quotes_equals():
    record = {"expr": "a=b"}
    result = format_logfmt(record)
    assert 'expr="a=b"' in result


def test_format_pretty_contains_keys():
    result = format_pretty(SAMPLE)
    assert "timestamp" in result
    assert "level" in result
    assert "msg" in result
    assert result.startswith("---")


def test_format_pretty_priority_order():
    result = format_pretty(SAMPLE)
    ts_pos = result.index("timestamp")
    level_pos = result.index("level")
    msg_pos = result.index("msg")
    assert ts_pos < level_pos < msg_pos


def test_format_record_json():
    result = format_record(SAMPLE, fmt="json")
    assert json.loads(result) == SAMPLE


def test_format_record_logfmt():
    result = format_record({"k": "v"}, fmt="logfmt")
    assert result == "k=v"


def test_format_record_pretty():
    result = format_record(SAMPLE, fmt="pretty")
    assert "---" in result


def test_format_record_invalid_format():
    with pytest.raises(ValueError, match="Unsupported format"):
        format_record(SAMPLE, fmt="xml")
