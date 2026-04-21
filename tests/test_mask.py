"""Tests for logslice.mask."""

import pytest
from logslice.mask import (
    mask_value,
    mask_field,
    mask_fields,
    redact_patterns,
    parse_mask_expr,
)


def test_mask_value_full():
    assert mask_value("secret") == "******"


def test_mask_value_keep_last():
    assert mask_value("secret", keep=2) == "****et"


def test_mask_value_keep_exceeds_length():
    assert mask_value("hi", keep=5) == "hi"


def test_mask_value_custom_char():
    assert mask_value("abc", char="X") == "XXX"


def test_mask_value_non_string_passthrough():
    assert mask_value(42) == 42


def test_mask_value_empty_string():
    assert mask_value("") == ""


def test_mask_field_present():
    rec = {"password": "hunter2", "user": "alice"}
    result = mask_field(rec, "password")
    assert result["password"] == "*******"
    assert result["user"] == "alice"


def test_mask_field_missing_no_error():
    rec = {"user": "alice"}
    result = mask_field(rec, "password")
    assert result == {"user": "alice"}


def test_mask_field_does_not_mutate():
    rec = {"token": "abc"}
    mask_field(rec, "token")
    assert rec["token"] == "abc"


def test_mask_fields_multiple():
    rec = {"a": "foo", "b": "bar", "c": "baz"}
    result = mask_fields(rec, ["a", "b"])
    assert result["a"] == "***"
    assert result["b"] == "***"
    assert result["c"] == "baz"


def test_mask_fields_empty_list():
    rec = {"a": "foo", "b": "bar"}
    result = mask_fields(rec, [])
    assert result == {"a": "foo", "b": "bar"}


def test_mask_fields_does_not_mutate():
    rec = {"a": "foo", "b": "bar"}
    mask_fields(rec, ["a", "b"])
    assert rec["a"] == "foo"
    assert rec["b"] == "bar"


def test_redact_patterns_email():
    rec = {"msg": "contact user@example.com for help"}
    result = redact_patterns(rec, ["email"])
    assert "[REDACTED]" in result["msg"]
    assert "user@example.com" not in result["msg"]


def test_redact_patterns_ipv4():
    rec = {"msg": "request from 192.168.1.1"}
    result = redact_patterns(rec, ["ipv4"])
    assert "[REDACTED]" in result["msg"]


def test_redact_patterns_all_by_default():
    rec = {"msg": "token abcdefghijklmnopqrstuvwxyz123456 used"}
    result = redact_patterns(rec)
    assert "[REDACTED]" in result["msg"]


def test_redact_patterns_non_string_field_skipped():
    rec = {"count": 5, "msg": "hello"}
    result = redact_patterns(rec)
    assert result["count"] == 5


def test_redact_patterns_does_not_mutate():
    rec = {"msg": "contact user@example.com for help"}
    redact_patterns(rec, ["email"])
    assert "user@example.com" in rec["msg"]


def test_parse_mask_expr_simple():
    result = parse_mask_expr("password")
    assert result == {"field": "password", "keep": 0, "char": "*"}


def test_parse_mask_expr_with_keep():
    result = parse_mask_expr("token:keep=4")
    assert result["field"] == "token"
    assert result["keep"] == 4


def test_parse_mask_expr_with_char():
    result = parse_mask_expr("secret:char=X")
    assert result["char"] == "X"


def test_parse_mask_expr_with_keep_and_char():
    """Ensure both keep and char options can be parsed together."""
    result = parse_mask_expr("apikey:keep=2:char=#")
    assert result["field"] == "apikey"
    assert result["keep"] == 2
    assert result["char"] == "#"
