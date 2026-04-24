"""Tests for logslice.numeric."""

import pytest

from logslice.numeric import (
    _to_float,
    apply_numeric_filter,
    numeric_in_range,
    numeric_threshold,
    parse_numeric_expr,
)


# ---------------------------------------------------------------------------
# _to_float
# ---------------------------------------------------------------------------

def test_to_float_int_string():
    assert _to_float("42") == 42.0


def test_to_float_float_string():
    assert _to_float("3.14") == pytest.approx(3.14)


def test_to_float_numeric_value():
    assert _to_float(99) == 99.0


def test_to_float_invalid_returns_none():
    assert _to_float("abc") is None


def test_to_float_none_returns_none():
    assert _to_float(None) is None


# ---------------------------------------------------------------------------
# numeric_in_range
# ---------------------------------------------------------------------------

def test_in_range_within_bounds():
    assert numeric_in_range({"latency": "150"}, "latency", 100.0, 200.0) is True


def test_in_range_below_low():
    assert numeric_in_range({"latency": "50"}, "latency", 100.0, 200.0) is False


def test_in_range_above_high():
    assert numeric_in_range({"latency": "250"}, "latency", 100.0, 200.0) is False


def test_in_range_no_low():
    assert numeric_in_range({"latency": "10"}, "latency", None, 200.0) is True


def test_in_range_no_high():
    assert numeric_in_range({"latency": "999"}, "latency", 100.0, None) is True


def test_in_range_missing_field():
    assert numeric_in_range({}, "latency", 0.0, 100.0) is False


def test_in_range_non_numeric_field():
    assert numeric_in_range({"latency": "fast"}, "latency", 0.0, 100.0) is False


# ---------------------------------------------------------------------------
# numeric_threshold
# ---------------------------------------------------------------------------

def test_threshold_gt_true():
    assert numeric_threshold({"code": 200}, "code", ">", 100.0) is True


def test_threshold_gt_false():
    assert numeric_threshold({"code": 50}, "code", ">", 100.0) is False


def test_threshold_gte():
    assert numeric_threshold({"code": 200}, "code", ">=", 200.0) is True


def test_threshold_lt():
    assert numeric_threshold({"code": 99}, "code", "<", 100.0) is True


def test_threshold_lte():
    assert numeric_threshold({"code": 100}, "code", "<=", 100.0) is True


def test_threshold_eq():
    assert numeric_threshold({"code": 200}, "code", "==", 200.0) is True


def test_threshold_neq():
    assert numeric_threshold({"code": 404}, "code", "!=", 200.0) is True


def test_threshold_invalid_op_raises():
    with pytest.raises(ValueError, match="Unsupported numeric operator"):
        numeric_threshold({"code": 200}, "code", "~", 200.0)


def test_threshold_missing_field():
    assert numeric_threshold({}, "code", ">", 0.0) is False


# ---------------------------------------------------------------------------
# parse_numeric_expr
# ---------------------------------------------------------------------------

def test_parse_gt():
    assert parse_numeric_expr("latency>100") == ("latency", ">", 100.0)


def test_parse_gte():
    assert parse_numeric_expr("score>=9.5") == ("score", ">=", 9.5)


def test_parse_eq():
    assert parse_numeric_expr("status_code==200") == ("status_code", "==", 200.0)


def test_parse_spaces_stripped():
    field, op, val = parse_numeric_expr(" retries >= 3 ")
    assert field == "retries"
    assert op == ">="
    assert val == 3.0


def test_parse_no_operator_raises():
    with pytest.raises(ValueError, match="No valid operator"):
        parse_numeric_expr("latency100")


def test_parse_missing_field_raises():
    with pytest.raises(ValueError, match="Missing field name"):
        parse_numeric_expr(">100")


def test_parse_invalid_threshold_raises():
    with pytest.raises(ValueError, match="Invalid numeric threshold"):
        parse_numeric_expr("latency>abc")


# ---------------------------------------------------------------------------
# apply_numeric_filter
# ---------------------------------------------------------------------------

def test_apply_numeric_filter_keeps_matching():
    records = [{"latency": 50}, {"latency": 150}, {"latency": 250}]
    result = list(apply_numeric_filter(iter(records), "latency", ">", 100.0))
    assert result == [{"latency": 150}, {"latency": 250}]


def test_apply_numeric_filter_empty_input():
    result = list(apply_numeric_filter(iter([]), "latency", ">", 0.0))
    assert result == []
