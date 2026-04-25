"""Tests for logslice.compute."""

import pytest
from logslice.compute import (
    compute_expr,
    parse_compute_expr,
    apply_computes,
    _to_number,
)


@pytest.fixture
def record():
    return {"latency_ms": 250, "bytes_in": 1024, "bytes_out": 512, "label": "ok"}


# --- _to_number ---

def test_to_number_int():
    assert _to_number(42) == 42.0

def test_to_number_float():
    assert _to_number(3.14) == 3.14

def test_to_number_string_int():
    assert _to_number("7") == 7.0

def test_to_number_string_float():
    assert _to_number("1.5") == 1.5

def test_to_number_invalid_returns_none():
    assert _to_number("abc") is None

def test_to_number_none_returns_none():
    assert _to_number(None) is None


# --- compute_expr ---

def test_compute_division(record):
    result = compute_expr(record, "latency_ms / 1000")
    assert result == pytest.approx(0.25)

def test_compute_addition(record):
    result = compute_expr(record, "bytes_in + bytes_out")
    assert result == pytest.approx(1536.0)

def test_compute_subtraction(record):
    result = compute_expr(record, "bytes_in - bytes_out")
    assert result == pytest.approx(512.0)

def test_compute_multiplication(record):
    result = compute_expr(record, "latency_ms * 2")
    assert result == pytest.approx(500.0)

def test_compute_missing_field_returns_none(record):
    assert compute_expr(record, "nonexistent / 10") is None

def test_compute_division_by_zero_returns_none(record):
    rec = {"x": 5, "y": 0}
    assert compute_expr(rec, "x / y") is None

def test_compute_non_numeric_field_returns_none(record):
    assert compute_expr(record, "label + 1") is None

def test_compute_literal_only(record):
    assert compute_expr(record, "42") == pytest.approx(42.0)

def test_compute_empty_expr_returns_none(record):
    assert compute_expr(record, "   ") is None


# --- parse_compute_expr ---

def test_parse_compute_expr_basic():
    field, expr = parse_compute_expr("latency_s=latency_ms/1000")
    assert field == "latency_s"
    assert expr == "latency_ms/1000"

def test_parse_compute_expr_strips_whitespace():
    field, expr = parse_compute_expr("  total  =  bytes_in + bytes_out  ")
    assert field == "total"
    assert expr == "bytes_in + bytes_out"

def test_parse_compute_expr_no_equals_raises():
    with pytest.raises(ValueError, match="field=expr"):
        parse_compute_expr("latency_ms 1000")

def test_parse_compute_expr_empty_field_raises():
    with pytest.raises(ValueError, match="field name"):
        parse_compute_expr("=latency_ms/1000")

def test_parse_compute_expr_empty_body_raises():
    with pytest.raises(ValueError, match="body"):
        parse_compute_expr("total=")


# --- apply_computes ---

def test_apply_computes_adds_field(record):
    result = apply_computes(record, [("latency_s", "latency_ms / 1000")])
    assert result["latency_s"] == pytest.approx(0.25)

def test_apply_computes_preserves_original_fields(record):
    result = apply_computes(record, [("total", "bytes_in + bytes_out")])
    assert result["bytes_in"] == 1024
    assert result["bytes_out"] == 512

def test_apply_computes_does_not_mutate_input(record):
    original = dict(record)
    apply_computes(record, [("x", "latency_ms * 2")])
    assert record == original

def test_apply_computes_whole_number_stored_as_int(record):
    result = apply_computes(record, [("double", "latency_ms * 2")])
    assert result["double"] == 500
    assert isinstance(result["double"], int)

def test_apply_computes_fractional_stored_as_float(record):
    result = apply_computes(record, [("latency_s", "latency_ms / 1000")])
    assert isinstance(result["latency_s"], float)

def test_apply_computes_failed_expr_skips_field(record):
    result = apply_computes(record, [("bad", "missing_field / 10")])
    assert "bad" not in result

def test_apply_computes_multiple_exprs(record):
    exprs = [("total", "bytes_in + bytes_out"), ("latency_s", "latency_ms / 1000")]
    result = apply_computes(record, exprs)
    assert result["total"] == 1536
    assert result["latency_s"] == pytest.approx(0.25)

def test_apply_computes_chained_uses_previous_result(record):
    exprs = [("total", "bytes_in + bytes_out"), ("total_kb", "total / 1024")]
    result = apply_computes(record, exprs)
    assert result["total_kb"] == pytest.approx(1.5)
