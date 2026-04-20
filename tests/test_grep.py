"""Tests for logslice.grep."""

import re
import pytest
from logslice.grep import grep_record, grep_records, parse_grep_expr


@pytest.fixture()
def records():
    return [
        {"level": "info",  "msg": "server started",  "service": "api"},
        {"level": "error", "msg": "connection refused", "service": "db"},
        {"level": "warn",  "msg": "slow query detected", "service": "db"},
        {"level": "info",  "msg": "user login",         "service": "auth"},
    ]


# --- grep_record ---

def test_grep_record_matches_any_field():
    rec = {"level": "error", "msg": "disk full"}
    assert grep_record(rec, re.compile(r"disk")) is True


def test_grep_record_no_match():
    rec = {"level": "info", "msg": "all good"}
    assert grep_record(rec, re.compile(r"error")) is False


def test_grep_record_specific_field_match():
    rec = {"level": "error", "msg": "disk full"}
    assert grep_record(rec, re.compile(r"error"), fields=["level"]) is True


def test_grep_record_specific_field_no_match():
    rec = {"level": "error", "msg": "disk full"}
    assert grep_record(rec, re.compile(r"error"), fields=["msg"]) is False


def test_grep_record_missing_field_skipped():
    rec = {"level": "info"}
    # 'msg' doesn't exist — should not raise, just skip
    assert grep_record(rec, re.compile(r"anything"), fields=["msg"]) is False


def test_grep_record_numeric_value_converted():
    rec = {"code": 404, "msg": "not found"}
    assert grep_record(rec, re.compile(r"404")) is True


# --- grep_records ---

def test_grep_records_filters_correctly(records):
    result = list(grep_records(records, re.compile(r"db"), fields=["service"]))
    assert len(result) == 2
    assert all(r["service"] == "db" for r in result)


def test_grep_records_invert(records):
    result = list(grep_records(records, re.compile(r"db"), fields=["service"], invert=True))
    assert len(result) == 2
    assert all(r["service"] != "db" for r in result)


def test_grep_records_empty_input():
    result = list(grep_records([], re.compile(r"anything")))
    assert result == []


# --- parse_grep_expr ---

def test_parse_grep_expr_plain_pattern():
    opts = parse_grep_expr("error")
    assert opts["pattern"].search("error message")
    assert opts["fields"] is None


def test_parse_grep_expr_regex_literal():
    opts = parse_grep_expr("/conn(ection)?/")
    assert opts["pattern"].search("connection refused")
    assert opts["pattern"].search("conn reset")


def test_parse_grep_expr_case_insensitive_flag():
    opts = parse_grep_expr("/ERROR/i")
    assert opts["pattern"].search("error")
    assert opts["pattern"].search("ERROR")


def test_parse_grep_expr_field_scoped():
    opts = parse_grep_expr("service:/api/")
    assert opts["fields"] == ["service"]
    assert opts["pattern"].search("api")


def test_parse_grep_expr_field_scoped_case_insensitive():
    opts = parse_grep_expr("level:/ERROR/i")
    assert opts["fields"] == ["level"]
    assert opts["pattern"].search("error")
