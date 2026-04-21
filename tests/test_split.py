"""Tests for logslice.split and logslice.split_cli."""

from __future__ import annotations

import json
import os
import textwrap
from pathlib import Path

import pytest

from logslice.split import (
    group_records,
    iter_split_groups,
    parse_split_expr,
    split_to_files,
)


# ---------------------------------------------------------------------------
# parse_split_expr
# ---------------------------------------------------------------------------

def test_parse_split_expr_field_only():
    field, prefix = parse_split_expr("level")
    assert field == "level"
    assert prefix is None


def test_parse_split_expr_with_prefix():
    field, prefix = parse_split_expr("service:app")
    assert field == "service"
    assert prefix == "app"


def test_parse_split_expr_empty_prefix_returns_none():
    field, prefix = parse_split_expr("level:")
    assert field == "level"
    assert prefix is None


# ---------------------------------------------------------------------------
# group_records
# ---------------------------------------------------------------------------

@pytest.fixture()
def records():
    return [
        {"level": "info", "msg": "a"},
        {"level": "error", "msg": "b"},
        {"level": "info", "msg": "c"},
        {"msg": "d"},  # missing 'level'
    ]


def test_group_records_basic(records):
    groups = group_records(records, "level")
    assert len(groups["info"]) == 2
    assert len(groups["error"]) == 1


def test_group_records_missing_field_uses_default(records):
    groups = group_records(records, "level")
    assert "__unknown__" in groups
    assert groups["__unknown__"][0]["msg"] == "d"


def test_group_records_custom_default(records):
    groups = group_records(records, "level", default="other")
    assert "other" in groups


# ---------------------------------------------------------------------------
# split_to_files
# ---------------------------------------------------------------------------

def test_split_to_files_creates_files(tmp_path, records):
    counts = split_to_files(records, "level", output_dir=str(tmp_path))
    assert counts["info"] == 2
    assert counts["error"] == 1
    assert (tmp_path / "info.jsonl").exists()
    assert (tmp_path / "error.jsonl").exists()


def test_split_to_files_with_prefix(tmp_path, records):
    split_to_files(records, "level", output_dir=str(tmp_path), prefix="run1")
    assert (tmp_path / "run1_info.jsonl").exists()


def test_split_to_files_content_is_valid_json(tmp_path, records):
    split_to_files(records, "level", output_dir=str(tmp_path))
    lines = (tmp_path / "info.jsonl").read_text().splitlines()
    parsed = [json.loads(l) for l in lines]
    assert all(r["level"] == "info" for r in parsed)


def test_split_to_files_creates_output_dir(tmp_path):
    out = tmp_path / "nested" / "dir"
    split_to_files([{"x": "1"}], "x", output_dir=str(out))
    assert out.is_dir()


# ---------------------------------------------------------------------------
# iter_split_groups
# ---------------------------------------------------------------------------

def test_iter_split_groups_yields_key_and_record():
    lines = [
        json.dumps({"level": "info", "msg": "hello"}),
        json.dumps({"level": "error", "msg": "oops"}),
    ]
    results = list(iter_split_groups(lines, "level"))
    assert results[0][0] == "info"
    assert results[1][0] == "error"


def test_iter_split_groups_skips_empty_lines():
    lines = ["", "   ", json.dumps({"level": "warn"})]
    results = list(iter_split_groups(lines, "level"))
    assert len(results) == 1


def test_iter_split_groups_missing_field_uses_default():
    lines = [json.dumps({"msg": "no level here"})]
    results = list(iter_split_groups(lines, "level"))
    assert results[0][0] == "__unknown__"
