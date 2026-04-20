"""Template-based output formatting for log records."""
import re
from typing import Any, Dict

_FIELD_RE = re.compile(r"\{(\w+)(?::([^}]*))?\}")


def render_template(template: str, record: Dict[str, Any], missing: str = "") -> str:
    """Render a template string using fields from a log record.

    Supports {field} and {field:default} syntax.
    """
    def replacer(m: re.Match) -> str:
        key = m.group(1)
        default = m.group(2) if m.group(2) is not None else missing
        val = record.get(key)
        if val is None:
            return default
        return str(val)

    return _FIELD_RE.sub(replacer, template)


def parse_template_expr(expr: str) -> str:
    """Validate and return a template expression.

    Raises ValueError if the template contains no field references.
    """
    if not _FIELD_RE.search(expr):
        raise ValueError(f"Template contains no field references: {expr!r}")
    return expr


def apply_template(records, template: str, dest_field: str = "_line"):
    """Generator that adds a rendered template string to each record."""
    for record in records:
        out = dict(record)
        out[dest_field] = render_template(template, record)
        yield out
