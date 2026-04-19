"""Tests for logslice.truncate module."""

import pytest
from logslice.truncate import (
    truncate_value,
    truncate_field,
    truncate_fields,
    truncate_all_fields,
    parse_truncate_expr,
)


def test_truncate_value_short_string_unchanged():
    assert truncate_value("hello", max_length=10) == "hello"


def test_truncate_value_exact_length_unchanged():
    assert truncate_value("hello", max_length=5) == "hello"


def test_truncate_value_long_string_truncated():
    result = truncate_value("abcdefghij", max_length=6)
    assert result == "abc..."
    assert len(result) == 6


def test_truncate_value_custom_suffix():
    result = truncate_value("abcdefghij", max_length=7, suffix="--")
    assert result.endswith("--")
    assert len(result) == 7


def test_truncate_field_modifies_target_field():
    record = {"msg": "a" * 300, "level": "info"}
    result = truncate_field(record, "msg", max_length=50)
    assert len(result["msg"]) == 50
    assert result["level"] == "info"


def test_truncate_field_missing_field_unchanged():
    record = {"level": "info"}
    result = truncate_field(record, "msg", max_length=50)
    assert result == {"level": "info"}


def test_truncate_field_non_string_unchanged():
    record = {"count": 12345}
    result = truncate_field(record, "count", max_length=3)
    assert result["count"] == 12345


def test_truncate_field_does_not_mutate_original():
    record = {"msg": "x" * 300}
    truncate_field(record, "msg", max_length=10)
    assert len(record["msg"]) == 300


def test_truncate_fields_multiple():
    record = {"a": "x" * 100, "b": "y" * 100, "c": "z"}
    result = truncate_fields(record, ["a", "b"], max_length=20)
    assert len(result["a"]) == 20
    assert len(result["b"]) == 20
    assert result["c"] == "z"


def test_truncate_all_fields():
    record = {"a": "x" * 50, "b": "y" * 50, "n": 42}
    result = truncate_all_fields(record, max_length=10)
    assert len(result["a"]) == 10
    assert len(result["b"]) == 10
    assert result["n"] == 42


def test_parse_truncate_expr_length_only():
    field, length = parse_truncate_expr("100")
    assert field is None
    assert length == 100


def test_parse_truncate_expr_field_and_length():
    field, length = parse_truncate_expr("message:80")
    assert field == "message"
    assert length == 80


def test_parse_truncate_expr_invalid_raises():
    with pytest.raises(ValueError):
        parse_truncate_expr("message:abc")


def test_parse_truncate_expr_no_colon_invalid_raises():
    with pytest.raises(ValueError):
        parse_truncate_expr("notanumber")
