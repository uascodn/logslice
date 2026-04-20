import pytest
from logslice.template import render_template, parse_template_expr, apply_template


@pytest.fixture
def record():
    return {"level": "info", "msg": "hello", "service": "api", "code": 200}


def test_render_simple(record):
    assert render_template("{level} {msg}", record) == "info hello"


def test_render_missing_field_empty_default(record):
    assert render_template("{missing}", record) == ""


def test_render_missing_field_explicit_default(record):
    assert render_template("{missing:n/a}", record) == "n/a"


def test_render_numeric_field(record):
    assert render_template("code={code}", record) == "code=200"


def test_render_no_placeholders(record):
    assert render_template("static text", record) == "static text"


def test_render_multiple_same_field(record):
    result = render_template("{level} and {level}", record)
    assert result == "info and info"


def test_parse_template_expr_valid():
    assert parse_template_expr("{level}: {msg}") == "{level}: {msg}"


def test_parse_template_expr_no_fields():
    with pytest.raises(ValueError, match="no field references"):
        parse_template_expr("no fields here")


def test_apply_template_adds_dest_field():
    records = [{"level": "warn", "msg": "oops"}]
    result = list(apply_template(records, "{level}: {msg}"))
    assert result[0]["_line"] == "warn: oops"
    assert result[0]["level"] == "warn"


def test_apply_template_custom_dest():
    records = [{"service": "db", "msg": "slow"}]
    result = list(apply_template(records, "[{service}] {msg}", dest_field="rendered"))
    assert result[0]["rendered"] == "[db] slow"


def test_apply_template_does_not_mutate_original():
    original = {"level": "info", "msg": "hi"}
    records = [original]
    list(apply_template(records, "{level}"))
    assert "_line" not in original
