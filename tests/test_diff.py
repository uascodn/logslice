"""Tests for logslice.diff field-level diff utilities."""

import pytest
from logslice.diff import (
    diff_records,
    has_changes,
    diff_summary,
    render_diff,
    ADDED,
    REMOVED,
    CHANGED,
    UNCHANGED,
)


@pytest.fixture
def rec_a():
    return {"level": "info", "msg": "hello", "service": "api", "code": 200}


@pytest.fixture
def rec_b():
    return {"level": "warn", "msg": "hello", "service": "api", "latency": 42}


def test_diff_unchanged_fields(rec_a, rec_b):
    diff = diff_records(rec_a, rec_b)
    unchanged = [e for e in diff if e["status"] == UNCHANGED]
    fields = {e["field"] for e in unchanged}
    assert {"msg", "service"} == fields


def test_diff_changed_field(rec_a, rec_b):
    diff = diff_records(rec_a, rec_b)
    changed = [e for e in diff if e["status"] == CHANGED]
    assert len(changed) == 1
    assert changed[0]["field"] == "level"
    assert changed[0]["old"] == "info"
    assert changed[0]["new"] == "warn"


def test_diff_removed_field(rec_a, rec_b):
    diff = diff_records(rec_a, rec_b)
    removed = [e for e in diff if e["status"] == REMOVED]
    assert len(removed) == 1
    assert removed[0]["field"] == "code"


def test_diff_added_field(rec_a, rec_b):
    diff = diff_records(rec_a, rec_b)
    added = [e for e in diff if e["status"] == ADDED]
    assert len(added) == 1
    assert added[0]["field"] == "latency"


def test_diff_ignore_fields(rec_a, rec_b):
    diff = diff_records(rec_a, rec_b, ignore_fields=["level", "code", "latency"])
    statuses = {e["status"] for e in diff}
    assert statuses == {UNCHANGED}


def test_has_changes_true(rec_a, rec_b):
    diff = diff_records(rec_a, rec_b)
    assert has_changes(diff) is True


def test_has_changes_false():
    r = {"a": 1, "b": 2}
    diff = diff_records(r, r)
    assert has_changes(diff) is False


def test_diff_summary(rec_a, rec_b):
    diff = diff_records(rec_a, rec_b)
    summary = diff_summary(diff)
    assert summary[CHANGED] == 1
    assert summary[REMOVED] == 1
    assert summary[ADDED] == 1
    assert summary[UNCHANGED] == 2


def test_render_diff_no_changes():
    r = {"x": 1}
    diff = diff_records(r, r)
    rendered = render_diff(diff)
    assert "(no changes)" in rendered


def test_render_diff_shows_changed(rec_a, rec_b):
    diff = diff_records(rec_a, rec_b)
    rendered = render_diff(diff)
    assert "level" in rendered
    assert "->" in rendered


def test_render_diff_shows_added(rec_a, rec_b):
    diff = diff_records(rec_a, rec_b)
    rendered = render_diff(diff)
    assert "+" in rendered
    assert "latency" in rendered


def test_render_diff_shows_removed(rec_a, rec_b):
    diff = diff_records(rec_a, rec_b)
    rendered = render_diff(diff)
    assert "-" in rendered
    assert "code" in rendered


def test_render_diff_color_contains_escape(rec_a, rec_b):
    diff = diff_records(rec_a, rec_b)
    rendered = render_diff(diff, color=True)
    assert "\033[" in rendered
