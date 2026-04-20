"""Tests for logslice.validate."""
import pytest
from logslice.validate import (
    validate_required,
    validate_type,
    validate_pattern,
    validate_one_of,
    parse_validation_expr,
    apply_validations,
)


@pytest.fixture
def record():
    return {"level": "error", "msg": "boom", "code": 500, "service": "api"}


def test_validate_required_present(record):
    ok, err = validate_required(record, ["level", "msg"])
    assert ok and err is None


def test_validate_required_missing(record):
    ok, err = validate_required(record, ["level", "trace_id"])
    assert not ok
    assert "trace_id" in err


def test_validate_required_empty_string():
    ok, err = validate_required({"field": ""}, ["field"])
    assert not ok


def test_validate_type_correct(record):
    ok, err = validate_type(record, "code", int)
    assert ok and err is None


def test_validate_type_wrong(record):
    ok, err = validate_type(record, "level", int)
    assert not ok
    assert "str" in err


def test_validate_type_missing_field(record):
    ok, err = validate_type(record, "nonexistent", str)
    assert not ok
    assert "nonexistent" in err


def test_validate_pattern_matches(record):
    ok, err = validate_pattern(record, "level", r"^(error|warn|info)$")
    assert ok


def test_validate_pattern_no_match(record):
    ok, err = validate_pattern(record, "level", r"^\d+$")
    assert not ok
    assert "level" in err


def test_validate_one_of_allowed(record):
    ok, err = validate_one_of(record, "level", ["error", "warn", "info"])
    assert ok


def test_validate_one_of_disallowed(record):
    ok, err = validate_one_of(record, "level", ["warn", "info"])
    assert not ok


def test_parse_required_expr(record):
    v = parse_validation_expr("required:level,msg")
    ok, err = v(record)
    assert ok


def test_parse_type_expr(record):
    v = parse_validation_expr("type:code:int")
    ok, _ = v(record)
    assert ok


def test_parse_pattern_expr(record):
    v = parse_validation_expr("pattern:level:^error$")
    ok, _ = v(record)
    assert ok


def test_parse_oneof_expr(record):
    v = parse_validation_expr("oneof:level:error,warn,info")
    ok, _ = v(record)
    assert ok


def test_parse_unknown_expr():
    with pytest.raises(ValueError, match="unknown validation kind"):
        parse_validation_expr("bogus:field")


def test_apply_validations_no_errors(record):
    validators = [
        parse_validation_expr("required:level,msg"),
        parse_validation_expr("oneof:level:error,warn,info"),
    ]
    errors = apply_validations(record, validators)
    assert errors == []


def test_apply_validations_collects_errors():
    r = {"level": "debug"}
    validators = [
        parse_validation_expr("required:level,msg"),
        parse_validation_expr("oneof:level:error,warn"),
    ]
    errors = apply_validations(r, validators)
    assert len(errors) == 2
