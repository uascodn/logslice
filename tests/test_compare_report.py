import pytest
from logslice.compare_report import render_compare_report


SAMPLE_DIFFS = [
    {"status": "only_in_a", "key": {"id": "3"}},
    {"status": "only_in_b", "key": {"id": "4"}},
    {
        "status": "changed",
        "key": {"id": "2"},
        "diffs": {"level": {"a": "warn", "b": "error"}},
    },
]


def test_report_contains_header():
    out = render_compare_report(SAMPLE_DIFFS)
    assert "logslice compare report" in out


def test_report_counts():
    out = render_compare_report(SAMPLE_DIFFS)
    assert "only in A : 1" in out
    assert "only in B : 1" in out
    assert "changed   : 1" in out


def test_report_only_a_label():
    out = render_compare_report(SAMPLE_DIFFS)
    assert "[only_in_a]" in out
    assert "id=3" in out


def test_report_only_b_label():
    out = render_compare_report(SAMPLE_DIFFS)
    assert "[only_in_b]" in out
    assert "id=4" in out


def test_report_changed_diff_detail():
    out = render_compare_report(SAMPLE_DIFFS)
    assert "level" in out
    assert "warn" in out
    assert "error" in out


def test_report_empty():
    out = render_compare_report([])
    assert "only in A : 0" in out
    assert "changed   : 0" in out
