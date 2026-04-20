"""Focused tests for render_diff formatting details."""

import pytest
from logslice.diff import diff_records, render_diff, ADDED, REMOVED, CHANGED


def test_render_added_uses_plus_prefix():
    a = {}
    b = {"new_field": "value"}
    diff = diff_records(a, b)
    rendered = render_diff(diff)
    assert "+" in rendered
    assert "new_field" in rendered


def test_render_removed_uses_minus_prefix():
    a = {"old_field": "value"}
    b = {}
    diff = diff_records(a, b)
    rendered = render_diff(diff)
    assert "-" in rendered
    assert "old_field" in rendered


def test_render_changed_uses_tilde_prefix():
    a = {"x": 1}
    b = {"x": 2}
    diff = diff_records(a, b)
    rendered = render_diff(diff)
    assert "~" in rendered


def test_render_unchanged_not_shown():
    a = {"keep": "same", "change": "old"}
    b = {"keep": "same", "change": "new"}
    diff = diff_records(a, b)
    rendered = render_diff(diff)
    lines = rendered.splitlines()
    # unchanged fields should not appear in output
    assert not any("keep" in line for line in lines)


def test_render_multiple_changes_all_present():
    a = {"a": 1, "b": 2, "c": 3}
    b = {"a": 9, "b": 2, "d": 4}
    diff = diff_records(a, b)
    rendered = render_diff(diff)
    assert "a" in rendered   # changed
    assert "c" in rendered   # removed
    assert "d" in rendered   # added
    assert "b" not in rendered  # unchanged — not shown


def test_render_color_disabled_no_escape():
    a = {"x": 1}
    b = {"x": 2}
    diff = diff_records(a, b)
    rendered = render_diff(diff, color=False)
    assert "\033[" not in rendered


def test_render_values_shown_as_repr():
    a = {"msg": "hello world"}
    b = {"msg": "goodbye"}
    diff = diff_records(a, b)
    rendered = render_diff(diff)
    assert "'hello world'" in rendered
    assert "'goodbye'" in rendered
