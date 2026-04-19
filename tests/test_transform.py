"""Tests for logslice.transform."""

import pytest
from logslice.transform import (
    rename_field,
    drop_fields,
    keep_fields,
    add_field,
    parse_transform_expr,
    build_transform,
    apply_transforms,
)


@pytest.fixture
def record():
    return {"level": "info", "msg": "hello", "service": "api", "ts": "2024-01-01"}


def test_rename_field_present(record):
    result = rename_field(record, "msg", "message")
    assert "message" in result
    assert "msg" not in result
    assert result["message"] == "hello"


def test_rename_field_missing(record):
    result = rename_field(record, "nonexistent", "other")
    assert result == record


def test_drop_fields(record):
    result = drop_fields(record, ["level", "ts"])
    assert "level" not in result
    assert "ts" not in result
    assert "msg" in result


def test_drop_fields_missing_ignored(record):
    result = drop_fields(record, ["nonexistent"])
    assert result == record


def test_keep_fields(record):
    result = keep_fields(record, ["level", "msg"])
    assert set(result.keys()) == {"level", "msg"}


def test_keep_fields_missing_skipped(record):
    result = keep_fields(record, ["level", "missing"])
    assert set(result.keys()) == {"level"}


def test_add_field(record):
    result = add_field(record, "env", "prod")
    assert result["env"] == "prod"


def test_add_field_overwrites(record):
    result = add_field(record, "level", "debug")
    assert result["level"] == "debug"


def test_parse_transform_expr_rename():
    assert parse_transform_expr("rename:msg=message") == ("rename", "msg", "message")


def test_parse_transform_expr_drop():
    assert parse_transform_expr("drop:level,ts") == ("drop", ["level", "ts"])


def test_parse_transform_expr_keep():
    assert parse_transform_expr("keep:msg,service") == ("keep", ["msg", "service"])


def test_parse_transform_expr_add():
    assert parse_transform_expr("add:env=staging") == ("add", "env", "staging")


def test_parse_transform_expr_invalid_no_colon():
    with pytest.raises(ValueError, match="Invalid transform"):
        parse_transform_expr("renamemsg")


def test_parse_transform_expr_unknown_op():
    with pytest.raises(ValueError, match="Unknown transform op"):
        parse_transform_expr("uppercase:msg")


def test_build_and_apply_transform(record):
    fn = build_transform("rename:msg=message")
    result = fn(record)
    assert "message" in result


def test_apply_transforms_chain(record):
    fns = [
        build_transform("rename:msg=message"),
        build_transform("drop:ts"),
        build_transform("add:env=prod"),
    ]
    result = apply_transforms(record, fns)
    assert "message" in result
    assert "msg" not in result
    assert "ts" not in result
    assert result["env"] == "prod"
