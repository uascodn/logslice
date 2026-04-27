"""Unit tests for logslice.label."""

import pytest

from logslice.label import (
    apply_labels,
    label_field,
    parse_label_expr,
)


@pytest.fixture()
def rules():
    return [("error", "critical"), ("warn", "warning"), ("info", "info")]


def test_label_field_matches_first_rule(rules):
    rec = {"level": "error", "msg": "boom"}
    result = label_field(rec, "level", "severity", rules)
    assert result["severity"] == "critical"


def test_label_field_matches_second_rule(rules):
    rec = {"level": "warn", "msg": "heads up"}
    result = label_field(rec, "level", "severity", rules)
    assert result["severity"] == "warning"


def test_label_field_case_insensitive(rules):
    rec = {"level": "ERROR"}
    result = label_field(rec, "level", "severity", rules)
    assert result["severity"] == "critical"


def test_label_field_no_match_no_default(rules):
    rec = {"level": "debug"}
    result = label_field(rec, "level", "severity", rules)
    assert "severity" not in result


def test_label_field_no_match_with_default(rules):
    rec = {"level": "debug"}
    result = label_field(rec, "level", "severity", rules, default="unknown")
    assert result["severity"] == "unknown"


def test_label_field_missing_source_no_default(rules):
    rec = {"msg": "no level"}
    result = label_field(rec, "level", "severity", rules)
    assert "severity" not in result


def test_label_field_missing_source_with_default(rules):
    rec = {"msg": "no level"}
    result = label_field(rec, "level", "severity", rules, default="unknown")
    assert result["severity"] == "unknown"


def test_label_field_does_not_mutate_original(rules):
    rec = {"level": "info"}
    original = dict(rec)
    label_field(rec, "level", "severity", rules)
    assert rec == original


def test_apply_labels_multiple_records(rules):
    records = [
        {"level": "error"},
        {"level": "info"},
        {"level": "debug"},
    ]
    results = apply_labels(records, "level", "severity", rules, default="other")
    assert results[0]["severity"] == "critical"
    assert results[1]["severity"] == "info"
    assert results[2]["severity"] == "other"


def test_parse_label_expr_basic():
    src, dst, rules, default = parse_label_expr(
        "level->severity:error=critical,warn=warning,*=other"
    )
    assert src == "level"
    assert dst == "severity"
    assert ("error", "critical") in rules
    assert ("warn", "warning") in rules
    assert default == "other"


def test_parse_label_expr_no_default():
    src, dst, rules, default = parse_label_expr("status->label:200=ok,500=error")
    assert default is None
    assert len(rules) == 2


def test_parse_label_expr_missing_arrow_raises():
    with pytest.raises(ValueError, match="label expr"):
        parse_label_expr("level:error=critical")


def test_parse_label_expr_missing_colon_raises():
    with pytest.raises(ValueError, match="label expr"):
        parse_label_expr("level->severity")


def test_parse_label_expr_bad_rule_token_raises():
    with pytest.raises(ValueError, match="invalid rule token"):
        parse_label_expr("level->severity:erroronly")
