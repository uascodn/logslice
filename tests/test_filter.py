"""Tests for logslice.filter module."""

import pytest
from logslice.filter import field_matches, field_contains, apply_filters, parse_filter_expr


RECORD = {"level": "error", "msg": "connection refused", "code": "500"}


def test_field_matches_true():
    assert field_matches(RECORD, "level", "error") is True


def test_field_matches_false():
    assert field_matches(RECORD, "level", "info") is False


def test_field_matches_missing_field():
    assert field_matches(RECORD, "service", "api") is False


def test_field_contains_true():
    assert field_contains(RECORD, "msg", "refused") is True


def test_field_contains_false():
    assert field_contains(RECORD, "msg", "timeout") is False


def test_apply_filters_all_match():
    filters = [("level", "=", "error"), ("code", "=", "500")]
    assert apply_filters(RECORD, filters) is True


def test_apply_filters_one_fails():
    filters = [("level", "=", "error"), ("code", "=", "200")]
    assert apply_filters(RECORD, filters) is False


def test_apply_filters_not_equal():
    filters = [("level", "!=", "info")]
    assert apply_filters(RECORD, filters) is True


def test_apply_filters_contains():
    filters = [("msg", "contains", "connection")]
    assert apply_filters(RECORD, filters) is True


def test_apply_filters_unsupported_op():
    with pytest.raises(ValueError, match="Unsupported filter operator"):
        apply_filters(RECORD, [("level", "~=", "error")])


def test_parse_filter_expr_equals():
    assert parse_filter_expr("level=error") == ("level", "=", "error")


def test_parse_filter_expr_not_equals():
    assert parse_filter_expr("code!=200") == ("code", "!=", "200")


def test_parse_filter_expr_contains():
    assert parse_filter_expr("msg contains timeout") == ("msg", "contains", "timeout")


def test_parse_filter_expr_invalid():
    with pytest.raises(ValueError):
        parse_filter_expr("no operator here")
