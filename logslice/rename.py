"""Field renaming module for logslice."""

from typing import Dict, List


def rename_fields(record: dict, mapping: Dict[str, str]) -> dict:
    """Return a new record with fields renamed according to mapping.

    Keys in mapping are old names; values are new names.
    Fields not in mapping are preserved unchanged.
    If the old field is missing, the mapping entry is silently skipped.
    """
    result = {}
    for key, value in record.items():
        new_key = mapping.get(key, key)
        result[new_key] = value
    return result


def parse_rename_expr(expr: str) -> Dict[str, str]:
    """Parse a rename expression string into an old->new mapping.

    Format: ``old1=new1,old2=new2``

    Raises ValueError on malformed entries.
    """
    mapping: Dict[str, str] = {}
    for part in expr.split(","):
        part = part.strip()
        if not part:
            continue
        if "=" not in part:
            raise ValueError(
                f"Invalid rename expression {part!r}: expected 'old=new' format"
            )
        old, new = part.split("=", 1)
        old, new = old.strip(), new.strip()
        if not old:
            raise ValueError("Rename expression has empty source field name")
        if not new:
            raise ValueError("Rename expression has empty destination field name")
        mapping[old] = new
    if not mapping:
        raise ValueError("Rename expression produced no mappings")
    return mapping


def apply_renames(records, mapping: Dict[str, str]):
    """Yield records with fields renamed according to mapping."""
    for record in records:
        yield rename_fields(record, mapping)
