"""Tests for logslice.cast."""

import pytest

from logslice.cast import (
    apply_casts,
    cast_field,
    cast_fields,
    cast_value,
    parse_cast_expr,
)


# ---------------------------------------------------------------------------
# cast_value
# ---------------------------------------------------------------------------

def test_cast_value_to_int():
    assert cast_value("42", "int") == 42
    assert isinstance(cast_value("42", "int"), int)


def test_cast_value_to_float():
    assert cast_value("3.14", "float") == pytest.approx(3.14)


def test_cast_value_to_bool_true_variants():
    for v in ("true", "True", "1", "yes", "on"):
        assert cast_value(v, "bool") is True


def test_cast_value_to_bool_false_variants():
    for v in ("false", "False", "0", "no", "off"):
        assert cast_value(v, "bool") is False


def test_cast_value_bool_passthrough():
    assert cast_value(True, "bool") is True
    assert cast_value(False, "bool") is False


def test_cast_value_to_str():
    assert cast_value(123, "str") == "123"


def test_cast_value_invalid_int_raises():
    with pytest.raises((ValueError, TypeError)):
        cast_value("not_a_number", "int")


def test_cast_value_invalid_bool_raises():
    with pytest.raises(ValueError):
        cast_value("maybe", "bool")


def test_cast_value_unknown_type_raises():
    with pytest.raises(ValueError, match="Unknown target type"):
        cast_value("x", "bytes")


# ---------------------------------------------------------------------------
# cast_field
# ---------------------------------------------------------------------------

def test_cast_field_converts_string_to_int():
    rec = {"latency": "120", "msg": "ok"}
    result = cast_field(rec, "latency", "int")
    assert result["latency"] == 120
    assert result["msg"] == "ok"


def test_cast_field_missing_field_unchanged():
    rec = {"msg": "ok"}
    result = cast_field(rec, "latency", "int")
    assert "latency" not in result


def test_cast_field_does_not_mutate_original():
    rec = {"n": "5"}
    cast_field(rec, "n", "int")
    assert rec["n"] == "5"


def test_cast_field_failure_leaves_value_unchanged_when_no_default():
    rec = {"n": "abc"}
    result = cast_field(rec, "n", "int")
    assert result["n"] == "abc"


def test_cast_field_failure_uses_default():
    rec = {"n": "abc"}
    result = cast_field(rec, "n", "int", default=0)
    assert result["n"] == 0


# ---------------------------------------------------------------------------
# cast_fields
# ---------------------------------------------------------------------------

def test_cast_fields_multiple():
    rec = {"a": "1", "b": "2.5", "c": "true"}
    result = cast_fields(rec, [("a", "int"), ("b", "float"), ("c", "bool")])
    assert result == {"a": 1, "b": pytest.approx(2.5), "c": True}


# ---------------------------------------------------------------------------
# parse_cast_expr
# ---------------------------------------------------------------------------

def test_parse_cast_expr_valid():
    assert parse_cast_expr("latency:float") == ("latency", "float")
    assert parse_cast_expr("retries:int") == ("retries", "int")
    assert parse_cast_expr("active:bool") == ("active", "bool")
    assert parse_cast_expr("name:str") == ("name", "str")


def test_parse_cast_expr_no_colon_raises():
    with pytest.raises(ValueError, match="field:type"):
        parse_cast_expr("latencyfloat")


def test_parse_cast_expr_empty_field_raises():
    with pytest.raises(ValueError, match="empty"):
        parse_cast_expr(":int")


def test_parse_cast_expr_unknown_type_raises():
    with pytest.raises(ValueError, match="Unknown type"):
        parse_cast_expr("field:bytes")


# ---------------------------------------------------------------------------
# apply_casts
# ---------------------------------------------------------------------------

def test_apply_casts_multiple_exprs():
    rec = {"x": "10", "y": "3.0", "flag": "yes"}
    result = apply_casts(rec, ["x:int", "y:float", "flag:bool"])
    assert result["x"] == 10
    assert result["y"] == pytest.approx(3.0)
    assert result["flag"] is True
