"""Tests for logslice.normalize."""

import pytest

from logslice.normalize import (
    normalize_value,
    normalize_field,
    normalize_fields,
    parse_normalize_expr,
    apply_normalizations,
)


# ---------------------------------------------------------------------------
# normalize_value
# ---------------------------------------------------------------------------

def test_normalize_value_lower():
    assert normalize_value("Hello World", "lower") == "hello world"


def test_normalize_value_upper():
    assert normalize_value("hello", "upper") == "HELLO"


def test_normalize_value_title():
    assert normalize_value("hello world", "title") == "Hello World"


def test_normalize_value_strip():
    assert normalize_value("  padded  ", "strip") == "padded"


def test_normalize_value_non_string_passthrough():
    assert normalize_value(42, "lower") == 42
    assert normalize_value(None, "upper") is None
    assert normalize_value(3.14, "strip") == 3.14


def test_normalize_value_unknown_mode_raises():
    with pytest.raises(ValueError, match="Unknown normalization mode"):
        normalize_value("x", "camel")


# ---------------------------------------------------------------------------
# normalize_field
# ---------------------------------------------------------------------------

def test_normalize_field_present():
    record = {"level": "ERROR", "msg": "boom"}
    result = normalize_field(record, "level", "lower")
    assert result["level"] == "error"
    assert result["msg"] == "boom"


def test_normalize_field_missing_returns_unchanged():
    record = {"msg": "ok"}
    result = normalize_field(record, "level", "lower")
    assert result == record


def test_normalize_field_does_not_mutate_original():
    record = {"level": "WARN"}
    normalize_field(record, "level", "lower")
    assert record["level"] == "WARN"


# ---------------------------------------------------------------------------
# normalize_fields
# ---------------------------------------------------------------------------

def test_normalize_fields_multiple_steps():
    record = {"level": "  ERROR  ", "service": "MyService"}
    steps = [{"field": "level", "mode": "strip"}, {"field": "level", "mode": "lower"}]
    result = normalize_fields(record, steps)
    assert result["level"] == "error"
    assert result["service"] == "MyService"


# ---------------------------------------------------------------------------
# parse_normalize_expr
# ---------------------------------------------------------------------------

def test_parse_normalize_expr_basic():
    assert parse_normalize_expr("level:lower") == {"field": "level", "mode": "lower"}


def test_parse_normalize_expr_strips_whitespace():
    assert parse_normalize_expr(" msg : strip ") == {"field": "msg", "mode": "strip"}


def test_parse_normalize_expr_missing_colon_raises():
    with pytest.raises(ValueError, match="Expected 'field:mode'"):
        parse_normalize_expr("levelupper")


def test_parse_normalize_expr_empty_field_raises():
    with pytest.raises(ValueError, match="Field name must not be empty"):
        parse_normalize_expr(":lower")


def test_parse_normalize_expr_invalid_mode_raises():
    with pytest.raises(ValueError, match="Unknown mode"):
        parse_normalize_expr("level:camel")


# ---------------------------------------------------------------------------
# apply_normalizations
# ---------------------------------------------------------------------------

def test_apply_normalizations_single_expr():
    record = {"level": "ERROR"}
    result = apply_normalizations(record, ["level:lower"])
    assert result["level"] == "error"


def test_apply_normalizations_multiple_exprs():
    record = {"level": "  WARN  ", "service": "api"}
    result = apply_normalizations(record, ["level:strip", "level:lower", "service:upper"])
    assert result["level"] == "warn"
    assert result["service"] == "API"


def test_apply_normalizations_empty_list_unchanged():
    record = {"level": "INFO"}
    result = apply_normalizations(record, [])
    assert result == record
