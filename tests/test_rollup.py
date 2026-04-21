"""Tests for logslice.rollup."""

import pytest

from logslice.rollup import (
    parse_rollup_expr,
    rollup_records,
    render_rollup_table,
    SUPPORTED_FUNCS,
)


@pytest.fixture
def records():
    return [
        {"service": "api", "latency": "120", "level": "info"},
        {"service": "api", "latency": "80", "level": "error"},
        {"service": "worker", "latency": "200", "level": "info"},
        {"service": "worker", "latency": "50", "level": "info"},
        {"service": "api", "latency": "100", "level": "info"},
    ]


def test_parse_rollup_expr_basic():
    group, metrics = parse_rollup_expr("service:count")
    assert group == "service"
    assert metrics == [("count", "count")]


def test_parse_rollup_expr_multiple_metrics():
    group, metrics = parse_rollup_expr("service:count,latency:avg,latency:max")
    assert group == "service"
    assert ("latency", "avg") in metrics
    assert ("latency", "max") in metrics


def test_parse_rollup_expr_invalid():
    with pytest.raises(ValueError, match="Invalid rollup expression"):
        parse_rollup_expr("no-colon-here")


def test_rollup_count(records):
    results = rollup_records(records, group_by="service", metrics=[("count", "count")])
    by_service = {r["service"]: r for r in results}
    assert by_service["api"]["count_count"] == 3
    assert by_service["worker"]["count_count"] == 2


def test_rollup_sum(records):
    results = rollup_records(records, group_by="service", metrics=[("latency", "sum")])
    by_service = {r["service"]: r for r in results}
    assert by_service["api"]["latency_sum"] == pytest.approx(300.0)
    assert by_service["worker"]["latency_sum"] == pytest.approx(250.0)


def test_rollup_avg(records):
    results = rollup_records(records, group_by="service", metrics=[("latency", "avg")])
    by_service = {r["service"]: r for r in results}
    assert by_service["api"]["latency_avg"] == pytest.approx(100.0)
    assert by_service["worker"]["latency_avg"] == pytest.approx(125.0)


def test_rollup_min_max(records):
    results = rollup_records(
        records,
        group_by="service",
        metrics=[("latency", "min"), ("latency", "max")],
    )
    by_service = {r["service"]: r for r in results}
    assert by_service["api"]["latency_min"] == pytest.approx(80.0)
    assert by_service["api"]["latency_max"] == pytest.approx(120.0)


def test_rollup_missing_field_returns_none(records):
    results = rollup_records(records, group_by="service", metrics=[("nonexistent", "sum")])
    for row in results:
        assert row["nonexistent_sum"] is None


def test_rollup_unsupported_func(records):
    with pytest.raises(ValueError, match="Unsupported aggregation function"):
        rollup_records(records, group_by="service", metrics=[("latency", "median")])


def test_rollup_missing_group_key():
    recs = [{"service": "api"}, {"level": "info"}]  # second has no 'service'
    results = rollup_records(recs, group_by="service", metrics=[("count", "count")])
    groups = {r["service"] for r in results}
    assert "__missing__" in groups


def test_render_rollup_table_contains_headers(records):
    results = rollup_records(records, group_by="service", metrics=[("latency", "avg")])
    table = render_rollup_table(results)
    assert "service" in table
    assert "latency_avg" in table


def test_render_rollup_table_contains_values(records):
    results = rollup_records(records, group_by="service", metrics=[("latency", "sum")])
    table = render_rollup_table(results)
    assert "api" in table
    assert "worker" in table


def test_render_rollup_table_empty():
    assert render_rollup_table([]) == "(no data)"
