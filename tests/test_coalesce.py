"""Tests for logslice.coalesce."""

import pytest
from logslice.coalesce import (
    _is_present,
    coalesce_fields,
    parse_coalesce_expr,
    apply_coalesces,
)


# ---------------------------------------------------------------------------
# _is_present
# ---------------------------------------------------------------------------

def test_is_present_none_false():
    assert _is_present(None) is False


def test_is_present_empty_string_false():
    assert _is_present("") is False


def test_is_present_whitespace_false():
    assert _is_present("   ") is False


def test_is_present_zero_true():
    assert _is_present(0) is True


def test_is_present_nonempty_string_true():
    assert _is_present("hello") is True


# ---------------------------------------------------------------------------
# coalesce_fields
# ---------------------------------------------------------------------------

def test_coalesce_first_field_wins():
    rec = {"a": "alpha", "b": "beta"}
    result = coalesce_fields(rec, ["a", "b"], "out")
    assert result["out"] == "alpha"


def test_coalesce_skips_none_picks_second():
    rec = {"a": None, "b": "beta"}
    result = coalesce_fields(rec, ["a", "b"], "out")
    assert result["out"] == "beta"


def test_coalesce_skips_empty_string():
    rec = {"a": "", "b": "beta"}
    result = coalesce_fields(rec, ["a", "b"], "out")
    assert result["out"] == "beta"


def test_coalesce_all_missing_returns_default():
    rec = {"x": 1}
    result = coalesce_fields(rec, ["a", "b"], "out", default="fallback")
    assert result["out"] == "fallback"


def test_coalesce_does_not_mutate_original():
    rec = {"a": None}
    result = coalesce_fields(rec, ["a"], "out", default="d")
    assert "out" not in rec
    assert result["out"] == "d"


# ---------------------------------------------------------------------------
# parse_coalesce_expr
# ---------------------------------------------------------------------------

def test_parse_expr_basic():
    sources, target, default = parse_coalesce_expr("host,hostname->host")
    assert sources == ["host", "hostname"]
    assert target == "host"
    assert default is None


def test_parse_expr_with_default():
    sources, target, default = parse_coalesce_expr("host,hostname->host:unknown")
    assert sources == ["host", "hostname"]
    assert target == "host"
    assert default == "unknown"


def test_parse_expr_missing_arrow_raises():
    with pytest.raises(ValueError, match="->"):
        parse_coalesce_expr("host,hostname")


def test_parse_expr_empty_target_raises():
    with pytest.raises(ValueError, match="target field is empty"):
        parse_coalesce_expr("a,b->")


def test_parse_expr_no_sources_raises():
    with pytest.raises(ValueError, match="no source fields"):
        parse_coalesce_expr("->target")


# ---------------------------------------------------------------------------
# apply_coalesces
# ---------------------------------------------------------------------------

def test_apply_coalesces_multiple_exprs():
    rec = {"a": None, "b": "B", "c": None, "d": "D"}
    result = apply_coalesces(rec, ["a,b->out1", "c,d->out2"])
    assert result["out1"] == "B"
    assert result["out2"] == "D"


def test_apply_coalesces_empty_list_unchanged():
    rec = {"a": 1}
    result = apply_coalesces(rec, [])
    assert result == rec
