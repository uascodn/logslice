"""Tests for logslice.annotate."""
from __future__ import annotations

import pytest
from logslice.annotate import (
    annotate_static,
    annotate_index,
    annotate_derived,
    annotate_conditional,
    parse_annotate_expr,
    apply_annotation,
)


@pytest.fixture
def records():
    return [
        {"level": "info", "service": "api", "msg": "started"},
        {"level": "error", "service": "worker", "msg": "failed"},
        {"level": "info", "service": "api", "msg": "done"},
    ]


def test_annotate_static_adds_field(records):
    result = list(annotate_static(records, "env", "prod"))
    assert all(r["env"] == "prod" for r in result)


def test_annotate_static_does_not_mutate_original(records):
    _ = list(annotate_static(records, "env", "prod"))
    assert "env" not in records[0]


def test_annotate_index_default_start(records):
    result = list(annotate_index(records))
    assert [r["_index"] for r in result] == [0, 1, 2]


def test_annotate_index_custom_start(records):
    result = list(annotate_index(records, field="seq", start=10))
    assert [r["seq"] for r in result] == [10, 11, 12]


def test_annotate_derived_simple(records):
    result = list(annotate_derived(records, "tag", "{service}-{level}"))
    assert result[0]["tag"] == "api-info"
    assert result[1]["tag"] == "worker-error"


def test_annotate_derived_missing_field(records):
    result = list(annotate_derived(records, "tag", "{missing}-x"))
    assert result[0]["tag"] == "-x"


def test_annotate_conditional_true_branch(records):
    result = list(annotate_conditional(records, "is_error", "level", "error", "yes", "no"))
    assert result[0]["is_error"] == "no"
    assert result[1]["is_error"] == "yes"


def test_annotate_conditional_false_default_none(records):
    result = list(annotate_conditional(records, "flag", "level", "error", True))
    assert result[0]["flag"] is None
    assert result[1]["flag"] is True


def test_parse_annotate_expr_static():
    spec = parse_annotate_expr("env=production")
    assert spec == {"type": "static", "field": "env", "value": "production"}


def test_parse_annotate_expr_derived():
    spec = parse_annotate_expr("tag={service}-{level}")
    assert spec["type"] == "derived"
    assert spec["field"] == "tag"
    assert spec["expr"] == "{service}-{level}"


def test_parse_annotate_expr_conditional_full():
    spec = parse_annotate_expr("flag=?level:error:yes:no")
    assert spec["type"] == "conditional"
    assert spec["condition_field"] == "level"
    assert spec["true_value"] == "yes"
    assert spec["false_value"] == "no"


def test_parse_annotate_expr_missing_equals():
    with pytest.raises(ValueError, match="missing '='"):
        parse_annotate_expr("nodequals")


def test_apply_annotation_static(records):
    spec = {"type": "static", "field": "env", "value": "staging"}
    result = list(apply_annotation(records, spec))
    assert all(r["env"] == "staging" for r in result)


def test_apply_annotation_unknown_type(records):
    with pytest.raises(ValueError, match="Unknown annotation type"):
        list(apply_annotation(records, {"type": "bogus", "field": "x"}))
