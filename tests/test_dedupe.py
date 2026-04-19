"""Tests for logslice.dedupe module."""

import pytest
from logslice.dedupe import dedupe_records, dedupe_consecutive, _record_key


def r(msg, level="info", service="svc"):
    return {"msg": msg, "level": level, "service": service}


# --- _record_key ---

def test_record_key_default_fields():
    rec = r("hello")
    assert _record_key(rec, ["msg"]) == ("hello",)


def test_record_key_multiple_fields():
    rec = r("hello", level="error")
    assert _record_key(rec, ["msg", "level"]) == ("hello", "error")


def test_record_key_missing_field():
    rec = {"msg": "hi"}
    assert _record_key(rec, ["msg", "service"]) == ("hi", "")


# --- dedupe_records ---

def test_dedupe_records_removes_duplicates():
    records = [r("a"), r("b"), r("a"), r("c"), r("b")]
    result = list(dedupe_records(iter(records)))
    assert [x["msg"] for x in result] == ["a", "b", "c"]


def test_dedupe_records_all_unique():
    records = [r("a"), r("b"), r("c")]
    result = list(dedupe_records(iter(records)))
    assert len(result) == 3


def test_dedupe_records_custom_fields():
    records = [
        {"msg": "x", "level": "info"},
        {"msg": "y", "level": "info"},
        {"msg": "x", "level": "error"},
    ]
    result = list(dedupe_records(iter(records), fields=["msg", "level"]))
    assert len(result) == 3


def test_dedupe_records_custom_fields_collapses():
    records = [
        {"msg": "x", "level": "info"},
        {"msg": "x", "level": "info"},
    ]
    result = list(dedupe_records(iter(records), fields=["msg", "level"]))
    assert len(result) == 1


def test_dedupe_records_max_seen_eviction():
    # With max_seen=2, old keys can be re-admitted
    records = [r("a"), r("b"), r("c"), r("a")]
    result = list(dedupe_records(iter(records), max_seen=2))
    msgs = [x["msg"] for x in result]
    assert msgs == ["a", "b", "c", "a"]


# --- dedupe_consecutive ---

def test_dedupe_consecutive_removes_runs():
    records = [r("a"), r("a"), r("b"), r("b"), r("a")]
    result = list(dedupe_consecutive(iter(records)))
    assert [x["msg"] for x in result] == ["a", "b", "a"]


def test_dedupe_consecutive_keeps_non_adjacent():
    records = [r("a"), r("b"), r("a")]
    result = list(dedupe_consecutive(iter(records)))
    assert len(result) == 3


def test_dedupe_consecutive_empty():
    result = list(dedupe_consecutive(iter([])))
    assert result == []


def test_dedupe_consecutive_custom_fields():
    records = [
        {"msg": "x", "level": "info"},
        {"msg": "x", "level": "error"},
    ]
    result = list(dedupe_consecutive(iter(records), fields=["msg"]))
    assert len(result) == 1
