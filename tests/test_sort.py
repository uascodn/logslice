import pytest
from logslice.sort import sort_records, parse_sort_expr


@pytest.fixture
def records():
    return [
        {"level": "info", "ts": "2024-01-03", "msg": "c"},
        {"level": "error", "ts": "2024-01-01", "msg": "a"},
        {"level": "warn", "ts": "2024-01-02", "msg": "b"},
    ]


def test_sort_ascending(records):
    result = sort_records(records, "ts")
    assert [r["ts"] for r in result] == ["2024-01-01", "2024-01-02", "2024-01-03"]


def test_sort_descending(records):
    result = sort_records(records, "ts", reverse=True)
    assert [r["ts"] for r in result] == ["2024-01-03", "2024-01-02", "2024-01-01"]


def test_sort_by_level(records):
    result = sort_records(records, "level")
    levels = [r["level"] for r in result]
    assert levels == sorted(levels)


def test_sort_missing_field_last():
    recs = [
        {"a": "z"},
        {"a": "a"},
        {"other": "x"},
    ]
    result = sort_records(recs, "a", missing_last=True)
    assert result[0]["a"] == "a"
    assert result[1]["a"] == "z"
    assert "a" not in result[2]


def test_sort_missing_field_first():
    recs = [
        {"a": "z"},
        {"other": "x"},
        {"a": "a"},
    ]
    result = sort_records(recs, "a", missing_last=False)
    assert "a" not in result[0]


def test_sort_stable_order():
    recs = [{"v": "b"}, {"v": "a"}, {"v": "b"}]
    result = sort_records(recs, "v")
    assert result[0]["v"] == "a"


def test_parse_sort_expr_default():
    field, reverse = parse_sort_expr("timestamp")
    assert field == "timestamp"
    assert reverse is False


def test_parse_sort_expr_asc():
    field, reverse = parse_sort_expr("level:asc")
    assert field == "level"
    assert reverse is False


def test_parse_sort_expr_desc():
    field, reverse = parse_sort_expr("ts:desc")
    assert field == "ts"
    assert reverse is True


def test_parse_sort_expr_invalid_direction():
    with pytest.raises(ValueError, match="asc"):
        parse_sort_expr("ts:random")


def test_parse_sort_expr_empty_field():
    with pytest.raises(ValueError):
        parse_sort_expr(":desc")
