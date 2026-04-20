from logslice.pivot import render_pivot_table, pivot_records


def _pivot():
    records = [
        {"env": "prod", "level": "error"},
        {"env": "prod", "level": "info"},
        {"env": "prod", "level": "info"},
        {"env": "dev",  "level": "info"},
    ]
    return pivot_records(records, "env", "level")


def test_render_contains_row_values():
    table = render_pivot_table(_pivot())
    assert "prod" in table
    assert "dev" in table


def test_render_contains_col_headers():
    table = render_pivot_table(_pivot())
    assert "error" in table
    assert "info" in table


def test_render_correct_counts():
    table = render_pivot_table(_pivot())
    lines = table.splitlines()
    prod_line = next(l for l in lines if "prod" in l)
    # prod has error=1, info=2
    assert "2" in prod_line
    assert "1" in prod_line


def test_render_separator_line():
    table = render_pivot_table(_pivot())
    lines = table.splitlines()
    assert any(set(l.strip()) <= {"-"} for l in lines)


def test_render_single_row_col():
    pivot = {"only": {"x": 5}}
    table = render_pivot_table(pivot)
    assert "only" in table
    assert "x" in table
    assert "5" in table
