"""Tests for logslice.bucket."""
import pytest
from logslice.bucket import (
    bucket_records,
    parse_bucket_field_expr,
    render_bucket_summary,
)


# ---------------------------------------------------------------------------
# parse_bucket_field_expr
# ---------------------------------------------------------------------------

def test_parse_field_only():
    field, buckets = parse_bucket_field_expr("level")
    assert field == "level"
    assert buckets is None


def test_parse_field_with_buckets():
    field, buckets = parse_bucket_field_expr("level:info,warn,error")
    assert field == "level"
    assert buckets == ["info", "warn", "error"]


def test_parse_strips_whitespace():
    field, buckets = parse_bucket_field_expr(" level : info , error ")
    assert field == "level"
    assert buckets == ["info", "error"]


def test_parse_empty_raises():
    with pytest.raises(ValueError):
        parse_bucket_field_expr("")


def test_parse_blank_field_raises():
    with pytest.raises(ValueError):
        parse_bucket_field_expr("  ")


def test_parse_colon_no_values_returns_none_buckets():
    field, buckets = parse_bucket_field_expr("level:")
    assert field == "level"
    assert buckets is None


# ---------------------------------------------------------------------------
# bucket_records
# ---------------------------------------------------------------------------

@pytest.fixture()
def records():
    return [
        {"level": "info", "msg": "a"},
        {"level": "error", "msg": "b"},
        {"level": "info", "msg": "c"},
        {"level": "warn", "msg": "d"},
        {"msg": "e"},  # missing field
    ]


def test_bucket_no_filter(records):
    groups = bucket_records(records, "level")
    assert set(groups.keys()) == {"info", "error", "warn", "__missing__"}
    assert len(groups["info"]) == 2
    assert len(groups["__missing__"]) == 1


def test_bucket_with_allowed_buckets(records):
    groups = bucket_records(records, "level", ["info", "error"])
    assert "warn" not in groups
    assert "__other__" in groups
    assert len(groups["__other__"]) == 1


def test_bucket_missing_field_key(records):
    groups = bucket_records(records, "level")
    assert "__missing__" in groups
    assert groups["__missing__"][0]["msg"] == "e"


def test_bucket_empty_input():
    groups = bucket_records([], "level")
    assert groups == {}


# ---------------------------------------------------------------------------
# render_bucket_summary
# ---------------------------------------------------------------------------

def test_render_contains_field_name(records):
    groups = bucket_records(records, "level")
    summary = render_bucket_summary(groups, "level")
    assert "level" in summary


def test_render_contains_bucket_keys(records):
    groups = bucket_records(records, "level")
    summary = render_bucket_summary(groups, "level")
    assert "info" in summary
    assert "error" in summary


def test_render_contains_total(records):
    groups = bucket_records(records, "level")
    summary = render_bucket_summary(groups, "level")
    assert "TOTAL" in summary
    assert "5" in summary
