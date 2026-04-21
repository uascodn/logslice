"""Tests for logslice.count."""
import pytest
from collections import Counter

from logslice.count import (
    parse_count_expr,
    count_field_values,
    top_counts,
    render_count_table,
)


# ---------------------------------------------------------------------------
# parse_count_expr
# ---------------------------------------------------------------------------

def test_parse_count_expr_field_only():
    result = parse_count_expr("level")
    assert result["field"] == "level"
    assert result["top"] == 10


def test_parse_count_expr_with_top():
    result = parse_count_expr("service:top=5")
    assert result["field"] == "service"
    assert result["top"] == 5


def test_parse_count_expr_empty_field_raises():
    with pytest.raises(ValueError, match="must specify a field"):
        parse_count_expr("")


def test_parse_count_expr_invalid_top_raises():
    with pytest.raises(ValueError, match="invalid top value"):
        parse_count_expr("level:top=abc")


# ---------------------------------------------------------------------------
# count_field_values
# ---------------------------------------------------------------------------

@pytest.fixture()
def records():
    return [
        {"level": "info", "service": "api"},
        {"level": "error", "service": "api"},
        {"level": "info", "service": "worker"},
        {"level": "warn", "service": "api"},
        {"level": "info"},  # no service field
    ]


def test_count_field_values_basic(records):
    counter = count_field_values(records, "level")
    assert counter["info"] == 3
    assert counter["error"] == 1
    assert counter["warn"] == 1


def test_count_field_values_missing_field_skipped(records):
    counter = count_field_values(records, "service")
    assert counter["api"] == 3
    assert counter["worker"] == 1
    assert sum(counter.values()) == 4  # record without service is skipped


def test_count_field_values_no_records():
    counter = count_field_values([], "level")
    assert len(counter) == 0


# ---------------------------------------------------------------------------
# top_counts
# ---------------------------------------------------------------------------

def test_top_counts_returns_most_common():
    c = Counter({"a": 5, "b": 3, "c": 1})
    result = top_counts(c, top=2)
    assert result == [("a", 5), ("b", 3)]


def test_top_counts_all_when_top_exceeds_size():
    c = Counter({"x": 2, "y": 1})
    result = top_counts(c, top=100)
    assert len(result) == 2


# ---------------------------------------------------------------------------
# render_count_table
# ---------------------------------------------------------------------------

def test_render_count_table_contains_field_header():
    counts = [("info", 10), ("error", 2)]
    table = render_count_table(counts, "level", total=12)
    assert "level" in table
    assert "info" in table
    assert "10" in table


def test_render_count_table_shows_percentage():
    counts = [("info", 1)]
    table = render_count_table(counts, "level", total=2)
    assert "50.0%" in table


def test_render_count_table_empty_returns_message():
    table = render_count_table([], "level")
    assert "No values found" in table


def test_render_count_table_no_total_no_pct():
    counts = [("info", 5)]
    table = render_count_table(counts, "level", total=0)
    assert "%" not in table
