"""Tests for logslice.stats."""
import pytest
from logslice.stats import Stats


@pytest.fixture
def populated_stats():
    s = Stats()
    records = [
        {"level": "info", "service": "api"},
        {"level": "error", "service": "api"},
        {"level": "info", "service": "worker"},
        {"level": "info", "service": "api"},
    ]
    for r in records:
        s.record(r, matched=True)
    s.record({"level": "debug"}, matched=False)
    return s


def test_total_and_matched(populated_stats):
    assert populated_stats.total == 5
    assert populated_stats.matched == 4


def test_dropped_lines(populated_stats):
    summary = populated_stats.summary()
    assert summary["dropped_lines"] == 1


def test_top_values_level(populated_stats):
    top = populated_stats.top_values("level", n=2)
    values = dict(top)
    assert values["info"] == 3
    assert values["error"] == 1


def test_top_values_service(populated_stats):
    top = populated_stats.top_values("service", n=5)
    values = dict(top)
    assert values["api"] == 3
    assert values["worker"] == 1


def test_unique_values(populated_stats):
    assert populated_stats.unique_values("level") == 2
    assert populated_stats.unique_values("service") == 2


def test_fields_seen(populated_stats):
    summary = populated_stats.summary()
    assert "level" in summary["fields_seen"]
    assert "service" in summary["fields_seen"]


def test_empty_stats():
    s = Stats()
    summary = s.summary()
    assert summary["total_lines"] == 0
    assert summary["matched_lines"] == 0
    assert s.top_values("level") == []


def test_record_none_entry():
    s = Stats()
    s.record(None, matched=False)
    assert s.total == 1
    assert s.matched == 0
