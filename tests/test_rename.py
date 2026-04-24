"""Tests for logslice.rename."""

import pytest

from logslice.rename import apply_renames, parse_rename_expr, rename_fields


@pytest.fixture()
def record():
    return {"level": "info", "msg": "hello", "svc": "api"}


# ---------------------------------------------------------------------------
# rename_fields
# ---------------------------------------------------------------------------

def test_rename_fields_renames_present_key(record):
    result = rename_fields(record, {"svc": "service"})
    assert "service" in result
    assert "svc" not in result
    assert result["service"] == "api"


def test_rename_fields_preserves_other_keys(record):
    result = rename_fields(record, {"svc": "service"})
    assert result["level"] == "info"
    assert result["msg"] == "hello"


def test_rename_fields_missing_key_silently_skipped(record):
    result = rename_fields(record, {"nonexistent": "other"})
    assert result == record


def test_rename_fields_multiple_renames(record):
    result = rename_fields(record, {"level": "severity", "msg": "message"})
    assert "severity" in result
    assert "message" in result
    assert "level" not in result
    assert "msg" not in result


def test_rename_fields_does_not_mutate_original(record):
    original_keys = set(record.keys())
    rename_fields(record, {"level": "severity"})
    assert set(record.keys()) == original_keys


# ---------------------------------------------------------------------------
# parse_rename_expr
# ---------------------------------------------------------------------------

def test_parse_rename_expr_single():
    mapping = parse_rename_expr("svc=service")
    assert mapping == {"svc": "service"}


def test_parse_rename_expr_multiple():
    mapping = parse_rename_expr("svc=service,msg=message")
    assert mapping == {"svc": "service", "msg": "message"}


def test_parse_rename_expr_strips_whitespace():
    mapping = parse_rename_expr(" svc = service ")
    assert mapping == {"svc": "service"}


def test_parse_rename_expr_missing_equals_raises():
    with pytest.raises(ValueError, match="expected 'old=new' format"):
        parse_rename_expr("svcservice")


def test_parse_rename_expr_empty_source_raises():
    with pytest.raises(ValueError, match="empty source"):
        parse_rename_expr("=service")


def test_parse_rename_expr_empty_destination_raises():
    with pytest.raises(ValueError, match="empty destination"):
        parse_rename_expr("svc=")


def test_parse_rename_expr_empty_string_raises():
    with pytest.raises(ValueError, match="no mappings"):
        parse_rename_expr("")


# ---------------------------------------------------------------------------
# apply_renames
# ---------------------------------------------------------------------------

def test_apply_renames_yields_all_records():
    records = [{"a": 1}, {"a": 2}]
    result = list(apply_renames(records, {"a": "b"}))
    assert len(result) == 2
    assert all("b" in r for r in result)


def test_apply_renames_empty_input():
    result = list(apply_renames([], {"a": "b"}))
    assert result == []
