"""Tests for logslice.join — inner/left join of two record streams."""

import pytest
from logslice.join import index_right, _merge, inner_join, left_join, parse_join_expr


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def left_records():
    return [
        {"id": "1", "service": "api", "latency": 120},
        {"id": "2", "service": "worker", "latency": 340},
        {"id": "3", "service": "api", "latency": 80},
    ]


@pytest.fixture()
def right_records():
    return [
        {"id": "1", "region": "us-east", "tier": "free"},
        {"id": "2", "region": "eu-west", "tier": "pro"},
        {"id": "4", "region": "ap-south", "tier": "free"},
    ]


# ---------------------------------------------------------------------------
# index_right
# ---------------------------------------------------------------------------

def test_index_records_keys(right_records):
    idx = index_right(right_records, key="id")
    assert set(idx.keys()) == {"1", "2", "4"}


def test_index_records_values(right_records):
    idx = index_right(right_records, key="id")
    assert idx["1"]["region"] == "us-east"
    assert idx["2"]["tier"] == "pro"


def test_index_records_missing_key_skipped():
    records = [
        {"id": "1", "val": "a"},
        {"val": "b"},          # no 'id' field — should be skipped
        {"id": "3", "val": "c"},
    ]
    idx = index_right(records, key="id")
    assert set(idx.keys()) == {"1", "3"}


# ---------------------------------------------------------------------------
# _merge
# ---------------------------------------------------------------------------

def test_merge_combines_fields():
    left = {"id": "1", "latency": 100}
    right = {"id": "1", "region": "us-east"}
    merged = _merge(left, right)
    assert merged["latency"] == 100
    assert merged["region"] == "us-east"


def test_merge_right_prefix_avoids_collision():
    left = {"id": "1", "name": "alpha"}
    right = {"id": "1", "name": "beta"}
    merged = _merge(left, right, prefix="right_")
    assert merged["name"] == "alpha"
    assert merged["right_name"] == "beta"


def test_merge_does_not_mutate_left():
    left = {"id": "1", "x": 1}
    right = {"id": "1", "y": 2}
    _merge(left, right)
    assert "y" not in left


# ---------------------------------------------------------------------------
# inner_join
# ---------------------------------------------------------------------------

def test_inner_join_matching_rows(left_records, right_records):
    result = list(inner_join(left_records, right_records, key="id"))
    ids = [r["id"] for r in result]
    assert sorted(ids) == ["1", "2"]


def test_inner_join_excludes_unmatched_left(left_records, right_records):
    result = list(inner_join(left_records, right_records, key="id"))
    ids = [r["id"] for r in result]
    assert "3" not in ids


def test_inner_join_excludes_unmatched_right(left_records, right_records):
    result = list(inner_join(left_records, right_records, key="id"))
    ids = [r["id"] for r in result]
    assert "4" not in ids


def test_inner_join_merged_fields(left_records, right_records):
    result = {r["id"]: r for r in inner_join(left_records, right_records, key="id")}
    assert result["1"]["region"] == "us-east"
    assert result["1"]["latency"] == 120
    assert result["2"]["tier"] == "pro"


# ---------------------------------------------------------------------------
# left_join
# ---------------------------------------------------------------------------

def test_left_join_keeps_all_left(left_records, right_records):
    result = list(left_join(left_records, right_records, key="id"))
    ids = [r["id"] for r in result]
    assert sorted(ids) == ["1", "2", "3"]


def test_left_join_unmatched_row_has_no_right_fields(left_records, right_records):
    result = {r["id"]: r for r in left_join(left_records, right_records, key="id")}
    assert "region" not in result["3"]
    assert result["3"]["service"] == "api"


def test_left_join_matched_row_has_right_fields(left_records, right_records):
    result = {r["id"]: r for r in left_join(left_records, right_records, key="id")}
    assert result["1"]["region"] == "us-east"


def test_left_join_excludes_right_only_rows(left_records, right_records):
    result = list(left_join(left_records, right_records, key="id"))
    ids = [r["id"] for r in result]
    assert "4" not in ids


# ---------------------------------------------------------------------------
# parse_join_expr
# ---------------------------------------------------------------------------

def test_parse_join_expr_inner():
    expr = parse_join_expr("inner:id")
    assert expr["type"] == "inner"
    assert expr["key"] == "id"


def test_parse_join_expr_left():
    expr = parse_join_expr("left:user_id")
    assert expr["type"] == "left"
    assert expr["key"] == "user_id"


def test_parse_join_expr_invalid_type():
    with pytest.raises(ValueError, match="join type"):
        parse_join_expr("outer:id")


def test_parse_join_expr_missing_key():
    with pytest.raises(ValueError):
        parse_join_expr("inner")


def test_parse_join_expr_empty_key():
    with pytest.raises(ValueError):
        parse_join_expr("left:")
