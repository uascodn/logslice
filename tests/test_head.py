"""Tests for logslice/head.py."""

import pytest

from logslice.head import first_n_records, head_records, parse_head_expr


@pytest.fixture
def records():
    return [
        {"level": "info", "msg": "one"},
        {"level": "warn", "msg": "two"},
        {"level": "error", "msg": "three"},
        {"level": "info", "msg": "four"},
        {"level": "debug", "msg": "five"},
    ]


# --- first_n_records ---

def test_first_n_records_fewer_than_n(records):
    result = first_n_records(records, 10)
    assert result == records


def test_first_n_records_exact(records):
    result = first_n_records(records, 5)
    assert len(result) == 5
    assert result == records


def test_first_n_records_partial(records):
    result = first_n_records(records, 3)
    assert len(result) == 3
    assert result[0]["msg"] == "one"
    assert result[2]["msg"] == "three"


def test_first_n_records_zero(records):
    result = first_n_records(records, 0)
    assert result == []


def test_first_n_records_negative_raises(records):
    with pytest.raises(ValueError, match=">= 0"):
        first_n_records(records, -1)


# --- head_records (iterator) ---

def test_head_records_yields_correct_count(records):
    result = list(head_records(records, 2))
    assert len(result) == 2
    assert result[0]["msg"] == "one"
    assert result[1]["msg"] == "two"


def test_head_records_zero_yields_nothing(records):
    result = list(head_records(records, 0))
    assert result == []


def test_head_records_more_than_available(records):
    result = list(head_records(records, 100))
    assert result == records


def test_head_records_negative_raises(records):
    with pytest.raises(ValueError, match=">= 0"):
        list(head_records(records, -5))


# --- parse_head_expr ---

def test_parse_head_expr_plain_integer():
    assert parse_head_expr("10") == 10


def test_parse_head_expr_n_equals_syntax():
    assert parse_head_expr("n=25") == 25


def test_parse_head_expr_whitespace_stripped():
    assert parse_head_expr("  7  ") == 7


def test_parse_head_expr_zero():
    assert parse_head_expr("0") == 0


def test_parse_head_expr_invalid_string():
    with pytest.raises(ValueError, match="Invalid head expression"):
        parse_head_expr("abc")


def test_parse_head_expr_negative_raises():
    with pytest.raises(ValueError, match=">= 0"):
        parse_head_expr("-3")
