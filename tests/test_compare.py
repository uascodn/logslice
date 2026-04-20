import pytest
from logslice.compare import index_records, compare_streams


def jline(d: dict) -> str:
    import json
    return json.dumps(d)


A = [
    jline({"id": "1", "level": "info", "msg": "hello"}),
    jline({"id": "2", "level": "warn", "msg": "world"}),
    jline({"id": "3", "level": "error", "msg": "boom"}),
]

B = [
    jline({"id": "1", "level": "info", "msg": "hello"}),
    jline({"id": "2", "level": "error", "msg": "world"}),
    jline({"id": "4", "level": "debug", "msg": "new"}),
]


def test_index_records_keys():
    idx = index_records(A, ["id"])
    assert set(idx.keys()) == {("1",), ("2",), ("3",)}


def test_index_records_values():
    idx = index_records(A, ["id"])
    assert idx[("1",)]["msg"] == "hello"


def test_compare_only_in_a():
    diffs = list(compare_streams(A, B, ["id"]))
    only_a = [d for d in diffs if d["status"] == "only_in_a"]
    assert len(only_a) == 1
    assert only_a[0]["key"] == {"id": "3"}


def test_compare_only_in_b():
    diffs = list(compare_streams(A, B, ["id"]))
    only_b = [d for d in diffs if d["status"] == "only_in_b"]
    assert len(only_b) == 1
    assert only_b[0]["key"] == {"id": "4"}


def test_compare_changed():
    diffs = list(compare_streams(A, B, ["id"]))
    changed = [d for d in diffs if d["status"] == "changed"]
    assert len(changed) == 1
    assert changed[0]["key"] == {"id": "2"}
    assert "level" in changed[0]["diffs"]
    assert changed[0]["diffs"]["level"] == {"a": "warn", "b": "error"}


def test_compare_no_diff():
    diffs = list(compare_streams(A, A, ["id"]))
    assert diffs == []


def test_compare_specific_fields():
    diffs = list(compare_streams(A, B, ["id"], compare_fields=["msg"]))
    changed = [d for d in diffs if d["status"] == "changed"]
    assert changed == []  # msg is same for id=2
