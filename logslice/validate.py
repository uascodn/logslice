"""Field validation for log records."""
from __future__ import annotations
import re
from typing import Any, Callable, Dict, List, Optional, Tuple

ValidationResult = Tuple[bool, Optional[str]]


def validate_required(record: Dict[str, Any], fields: List[str]) -> ValidationResult:
    """Check that all required fields are present and non-empty."""
    for field in fields:
        if field not in record or record[field] is None or record[field] == "":
            return False, f"missing required field: {field!r}"
    return True, None


def validate_type(record: Dict[str, Any], field: str, expected_type: type) -> ValidationResult:
    """Check that a field value is of the expected type."""
    if field not in record:
        return False, f"field not found: {field!r}"
    if not isinstance(record[field], expected_type):
        actual = type(record[field]).__name__
        return False, f"field {field!r} expected {expected_type.__name__}, got {actual}"
    return True, None


def validate_pattern(record: Dict[str, Any], field: str, pattern: str) -> ValidationResult:
    """Check that a field value matches a regex pattern."""
    if field not in record:
        return False, f"field not found: {field!r}"
    value = str(record[field])
    if not re.search(pattern, value):
        return False, f"field {field!r} value {value!r} does not match pattern {pattern!r}"
    return True, None


def validate_one_of(record: Dict[str, Any], field: str, allowed: List[Any]) -> ValidationResult:
    """Check that a field value is one of the allowed values."""
    if field not in record:
        return False, f"field not found: {field!r}"
    if record[field] not in allowed:
        return False, f"field {field!r} value {record[field]!r} not in allowed {allowed}"
    return True, None


def parse_validation_expr(expr: str) -> Callable[[Dict[str, Any]], ValidationResult]:
    """Parse a validation expression string into a validator function.

    Supported forms:
      required:field1,field2
      type:field:str
      pattern:field:regex
      oneof:field:val1,val2
    """
    parts = expr.split(":", 2)
    kind = parts[0]
    if kind == "required":
        fields = parts[1].split(",")
        return lambda r: validate_required(r, fields)
    if kind == "type":
        field, type_name = parts[1], parts[2]
        type_map = {"str": str, "int": int, "float": float, "bool": bool}
        t = type_map.get(type_name)
        if t is None:
            raise ValueError(f"unknown type: {type_name!r}")
        return lambda r, f=field, tp=t: validate_type(r, f, tp)
    if kind == "pattern":
        field, pattern = parts[1], parts[2]
        return lambda r, f=field, p=pattern: validate_pattern(r, f, p)
    if kind == "oneof":
        field = parts[1]
        allowed = parts[2].split(",")
        return lambda r, f=field, a=allowed: validate_one_of(r, f, a)
    raise ValueError(f"unknown validation kind: {kind!r}")


def apply_validations(
    record: Dict[str, Any],
    validators: List[Callable[[Dict[str, Any]], ValidationResult]],
) -> List[str]:
    """Run all validators against a record and return list of error messages."""
    errors = []
    for v in validators:
        ok, msg = v(record)
        if not ok and msg:
            errors.append(msg)
    return errors
