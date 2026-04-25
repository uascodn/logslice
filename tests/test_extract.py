"""Tests for logslice.extract."""

import pytest
from logslice.extract import (
    extract_regex,
    extract_split,
    parse_extract_expr,
    apply_extracts,
)


@pytest.fixture
def record():
    return {"msg": "error code=404 not found", "path": "/api/v2/users", "level": "error"}


# --- extract_regex ---

def test_extract_regex_basic(record):
    result = extract_regex(record, "msg", r"code=(\d+)", "status_code")
    assert result["status_code"] == "404"


def test_extract_regex_no_match_returns_unchanged(record):
    result = extract_regex(record, "msg", r"latency=(\d+)", "latency")
    assert "latency" not in result
    assert result["msg"] == record["msg"]


def test_extract_regex_missing_source_field(record):
    result = extract_regex(record, "nonexistent", r"(\d+)", "num")
    assert "num" not in result


def test_extract_regex_group_zero_fallback(record):
    # group=0 means whole match
    result = extract_regex(record, "msg", r"code=\d+", "match", group=0)
    assert result["match"] == "code=404"


def test_extract_regex_does_not_mutate_original(record):
    original = dict(record)
    extract_regex(record, "msg", r"(\d+)", "num")
    assert record == original


# --- extract_split ---

def test_extract_split_basic(record):
    result = extract_split(record, "path", "/", 3, "resource")
    assert result["resource"] == "users"


def test_extract_split_index_out_of_range(record):
    result = extract_split(record, "path", "/", 99, "resource")
    assert "resource" not in result


def test_extract_split_missing_source_field(record):
    result = extract_split(record, "missing", "/", 0, "part")
    assert "part" not in result


def test_extract_split_does_not_mutate_original(record):
    original = dict(record)
    extract_split(record, "path", "/", 1, "part")
    assert record == original


# --- parse_extract_expr ---

def test_parse_extract_expr_regex_basic():
    e = parse_extract_expr("regex:msg/code=(\\d+)/code/1")
    assert e["mode"] == "regex"
    assert e["source"] == "msg"
    assert e["dest"] == "code"
    assert e["group"] == 1


def test_parse_extract_expr_regex_default_group():
    e = parse_extract_expr("regex:msg/(\\d+)/num")
    assert e["group"] == 1


def test_parse_extract_expr_split_basic():
    e = parse_extract_expr("split:path/./2/ext")
    assert e["mode"] == "split"
    assert e["source"] == "path"
    assert e["delimiter"] == "."
    assert e["index"] == 2
    assert e["dest"] == "ext"


def test_parse_extract_expr_invalid_mode():
    with pytest.raises(ValueError, match="Unknown extract mode"):
        parse_extract_expr("unknown:foo/bar/baz")


def test_parse_extract_expr_regex_too_few_parts():
    with pytest.raises(ValueError, match="Invalid regex"):
        parse_extract_expr("regex:msg/onlyone")


def test_parse_extract_expr_split_wrong_parts():
    with pytest.raises(ValueError, match="Invalid split"):
        parse_extract_expr("split:path/./2")


# --- apply_extracts ---

def test_apply_extracts_multiple(record):
    exprs = [
        parse_extract_expr("regex:msg/code=(\\d+)/status"),
        parse_extract_expr("split:path///3/resource"),
    ]
    result = apply_extracts(record, exprs)
    assert result["status"] == "404"
    assert result["resource"] == "users"


def test_apply_extracts_empty_list(record):
    result = apply_extracts(record, [])
    assert result == record
