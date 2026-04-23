"""Tests for logslice.limit."""
import pytest
from logslice.limit import parse_limit_expr, limit_records, apply_limit


@pytest.fixture
def records():
    return [{"i": i, "msg": f"line {i}"} for i in range(10)]


# --- parse_limit_expr ---

def test_parse_limit_expr_simple():
    assert parse_limit_expr("5") == {"offset": 0, "limit": 5}


def test_parse_limit_expr_with_offset():
    assert parse_limit_expr("3:5") == {"offset": 3, "limit": 5}


def test_parse_limit_expr_zero_limit():
    assert parse_limit_expr("0") == {"offset": 0, "limit": 0}


def test_parse_limit_expr_whitespace_stripped():
    assert parse_limit_expr("  10  ") == {"offset": 0, "limit": 10}


def test_parse_limit_expr_invalid_string():
    with pytest.raises(ValueError, match="Invalid limit expression"):
        parse_limit_expr("abc")


def test_parse_limit_expr_invalid_offset_string():
    with pytest.raises(ValueError, match="Invalid limit expression"):
        parse_limit_expr("abc:5")


def test_parse_limit_expr_negative_limit():
    with pytest.raises(ValueError, match="non-negative"):
        parse_limit_expr("-1")


def test_parse_limit_expr_negative_offset():
    with pytest.raises(ValueError, match="non-negative"):
        parse_limit_expr("-1:5")


# --- limit_records ---

def test_limit_records_fewer_than_limit(records):
    result = list(limit_records(records[:3], limit=10))
    assert result == records[:3]


def test_limit_records_exact(records):
    result = list(limit_records(records, limit=10))
    assert result == records


def test_limit_records_partial(records):
    result = list(limit_records(records, limit=4))
    assert result == records[:4]


def test_limit_records_zero_limit(records):
    result = list(limit_records(records, limit=0))
    assert result == []


def test_limit_records_with_offset(records):
    result = list(limit_records(records, limit=3, offset=2))
    assert result == records[2:5]


def test_limit_records_offset_beyond_length(records):
    result = list(limit_records(records, limit=5, offset=20))
    assert result == []


def test_limit_records_offset_exact_boundary(records):
    result = list(limit_records(records, limit=5, offset=5))
    assert result == records[5:10]


# --- apply_limit ---

def test_apply_limit_simple(records):
    result = list(apply_limit(records, "3"))
    assert result == records[:3]


def test_apply_limit_with_offset(records):
    result = list(apply_limit(records, "2:3"))
    assert result == records[2:5]


def test_apply_limit_invalid_expr(records):
    with pytest.raises(ValueError):
        list(apply_limit(records, "bad"))
