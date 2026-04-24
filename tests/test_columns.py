"""Tests for logslice.columns."""
import pytest

from logslice.columns import (
    apply_columns,
    parse_columns_expr,
    reorder_columns,
    select_columns,
)


# ---------------------------------------------------------------------------
# parse_columns_expr
# ---------------------------------------------------------------------------

def test_parse_columns_expr_single():
    assert parse_columns_expr("level") == ["level"]


def test_parse_columns_expr_multiple():
    assert parse_columns_expr("level,msg,service") == ["level", "msg", "service"]


def test_parse_columns_expr_strips_whitespace():
    assert parse_columns_expr(" level , msg ") == ["level", "msg"]


def test_parse_columns_expr_empty_raises():
    with pytest.raises(ValueError):
        parse_columns_expr("")


def test_parse_columns_expr_blank_raises():
    with pytest.raises(ValueError):
        parse_columns_expr("   ")


def test_parse_columns_expr_trailing_comma_raises():
    with pytest.raises(ValueError):
        parse_columns_expr("level,msg,")


# ---------------------------------------------------------------------------
# select_columns
# ---------------------------------------------------------------------------

def test_select_columns_keeps_only_named():
    rec = {"level": "info", "msg": "hello", "service": "api"}
    result = select_columns(rec, ["level", "msg"])
    assert result == {"level": "info", "msg": "hello"}


def test_select_columns_preserves_order():
    rec = {"a": 1, "b": 2, "c": 3}
    result = select_columns(rec, ["c", "a"])
    assert list(result.keys()) == ["c", "a"]


def test_select_columns_missing_field_fill_none():
    rec = {"level": "info"}
    result = select_columns(rec, ["level", "msg"])
    assert result["msg"] is None


def test_select_columns_missing_field_custom_fill():
    rec = {"level": "info"}
    result = select_columns(rec, ["level", "msg"], fill="")
    assert result["msg"] == ""


# ---------------------------------------------------------------------------
# reorder_columns
# ---------------------------------------------------------------------------

def test_reorder_columns_moves_named_first():
    rec = {"a": 1, "b": 2, "c": 3}
    result = reorder_columns(rec, ["c", "b"])
    keys = list(result.keys())
    assert keys[0] == "c"
    assert keys[1] == "b"
    assert "a" in keys


def test_reorder_columns_skips_missing():
    rec = {"a": 1, "b": 2}
    result = reorder_columns(rec, ["z", "a"])
    assert list(result.keys()) == ["a", "b"]


def test_reorder_columns_preserves_all_values():
    rec = {"x": 10, "y": 20, "z": 30}
    result = reorder_columns(rec, ["z"])
    assert result == {"z": 30, "x": 10, "y": 20}


# ---------------------------------------------------------------------------
# apply_columns
# ---------------------------------------------------------------------------

def test_apply_columns_filters_all_records():
    recs = [
        {"level": "info", "msg": "a", "ts": "t1"},
        {"level": "error", "msg": "b", "ts": "t2"},
    ]
    result = list(apply_columns(recs, ["level", "msg"]))
    assert all(set(r.keys()) == {"level", "msg"} for r in result)


def test_apply_columns_strict_raises_on_missing():
    recs = [{"level": "info"}]
    with pytest.raises(KeyError):
        list(apply_columns(recs, ["level", "msg"], strict=True))


def test_apply_columns_non_strict_fills_none():
    recs = [{"level": "info"}]
    result = list(apply_columns(recs, ["level", "msg"], strict=False))
    assert result[0]["msg"] is None
