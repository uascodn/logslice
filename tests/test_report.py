import pytest
from logslice.stats import Stats
from logslice.report import render_report


@pytest.fixture
def stats():
    s = Stats(track_fields=["level", "service"])
    for _ in range(10):
        s.record({"level": "info", "service": "api"}, matched=True)
    for _ in range(3):
        s.record({"level": "error", "service": "db"}, matched=True)
    for _ in range(2):
        s.record({"level": "warn", "service": "api"}, matched=False)
    return s


def test_render_report_totals(stats):
    report = render_report(stats)
    assert "total lines   : 15" in report
    assert "matched lines : 13" in report
    assert "dropped lines : 2" in report


def test_render_report_top_values(stats):
    report = render_report(stats)
    assert "top level" in report
    assert "info" in report
    assert "error" in report


def test_render_report_no_agg(stats):
    report = render_report(stats)
    assert "aggregations" not in report


def test_render_report_with_agg(stats):
    agg_results = {
        "avg:latency by service": {"api": 12.5, "db": 7.333},
        "count": {"_all": 100},
    }
    report = render_report(stats, agg_results=agg_results)
    assert "aggregations" in report
    assert "avg:latency by service" in report
    assert "api" in report
    assert "12.5" in report


def test_render_report_header_footer(stats):
    report = render_report(stats)
    assert report.startswith("=== logslice report ===")
    assert report.endswith("=" * 23)
