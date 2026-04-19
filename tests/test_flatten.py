import pytest
from logslice.flatten import flatten_record, unflatten_record, parse_flatten_expr


@pytest.fixture
def nested():
    return {
        "level": "info",
        "http": {"method": "GET", "status": 200},
        "user": {"id": 42, "meta": {"role": "admin"}},
    }


def test_flatten_simple(nested):
    flat = flatten_record(nested)
    assert flat["level"] == "info"
    assert flat["http.method"] == "GET"
    assert flat["http.status"] == 200
    assert flat["user.id"] == 42
    assert flat["user.meta.role"] == "admin"


def test_flatten_custom_separator(nested):
    flat = flatten_record(nested, separator="/")
    assert "http/method" in flat
    assert "user/meta/role" in flat


def test_flatten_max_depth(nested):
    flat = flatten_record(nested, max_depth=1)
    assert flat["http.method"] == "GET"
    # user.meta should NOT be further flattened
    assert flat["user.meta"] == {"role": "admin"}


def test_flatten_empty_record():
    assert flatten_record({}) == {}


def test_flatten_no_nesting():
    rec = {"a": 1, "b": "x"}
    assert flatten_record(rec) == rec


def test_unflatten_simple():
    flat = {"http.method": "GET", "http.status": 200, "level": "info"}
    nested = unflatten_record(flat)
    assert nested["http"]["method"] == "GET"
    assert nested["http"]["status"] == 200
    assert nested["level"] == "info"


def test_unflatten_deep():
    flat = {"a.b.c": 99}
    nested = unflatten_record(flat)
    assert nested["a"]["b"]["c"] == 99


def test_flatten_unflatten_roundtrip(nested):
    flat = flatten_record(nested)
    restored = unflatten_record(flat)
    assert restored == nested


def test_parse_flatten_expr_defaults():
    opts = parse_flatten_expr("")
    assert opts["separator"] == "."
    assert opts["max_depth"] is None


def test_parse_flatten_expr_sep():
    opts = parse_flatten_expr("sep=/")
    assert opts["separator"] == "/"


def test_parse_flatten_expr_depth():
    opts = parse_flatten_expr("depth=2")
    assert opts["max_depth"] == 2


def test_parse_flatten_expr_combined():
    opts = parse_flatten_expr("sep=_, depth=3")
    assert opts["separator"] == "_"
    assert opts["max_depth"] == 3
