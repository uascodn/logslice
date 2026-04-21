"""Integration tests: annotate module used end-to-end via parse → annotate → format."""
from __future__ import annotations

import json
from logslice.annotate import (
    annotate_static,
    annotate_index,
    annotate_derived,
    annotate_conditional,
    parse_annotate_expr,
    apply_annotation,
)
from logslice.parser import parse_line
from logslice.output import format_record


def _make_records(raw_lines):
    return [parse_line(l) for l in raw_lines if l.strip()]


RAW = [
    '{"ts": "2024-01-01T00:00:00Z", "level": "info",  "service": "api",    "msg": "req"}',
    '{"ts": "2024-01-01T00:00:01Z", "level": "error", "service": "worker", "msg": "fail"}',
    '{"ts": "2024-01-01T00:00:02Z", "level": "warn",  "service": "api",    "msg": "slow"}',
]


def test_pipeline_static_then_index():
    records = _make_records(RAW)
    records = list(annotate_static(records, "env", "prod"))
    records = list(annotate_index(records, "n", start=1))
    assert records[0]["env"] == "prod"
    assert records[2]["n"] == 3


def test_pipeline_derived_label():
    records = _make_records(RAW)
    records = list(annotate_derived(records, "id", "{service}#{level}"))
    assert records[0]["id"] == "api#info"
    assert records[1]["id"] == "worker#error"


def test_pipeline_conditional_alert_flag():
    records = _make_records(RAW)
    records = list(
        annotate_conditional(records, "alert", "level", "error", "true", "false")
    )
    assert records[0]["alert"] == "false"
    assert records[1]["alert"] == "true"


def test_apply_annotation_roundtrip_json():
    records = _make_records(RAW)
    spec = parse_annotate_expr("region=us-east-1")
    annotated = list(apply_annotation(records, spec))
    for rec in annotated:
        line = format_record(rec, "json")
        parsed = json.loads(line)
        assert parsed["region"] == "us-east-1"


def test_chained_annotations_preserve_all_fields():
    records = _make_records(RAW)
    spec1 = parse_annotate_expr("env=staging")
    spec2 = parse_annotate_expr("label={service}-{env}")
    gen = apply_annotation(records, spec1)
    gen = apply_annotation(gen, spec2)
    result = list(gen)
    assert result[0]["env"] == "staging"
    assert result[0]["label"] == "api-staging"
    # Original fields intact
    assert result[0]["level"] == "info"
    assert result[0]["msg"] == "req"
