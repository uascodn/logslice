"""CLI entry-point for format-convert: re-emit log records in a chosen format."""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from logslice.format_convert import (
    SUPPORTED_FORMATS,
    convert_record,
    parse_format_expr,
    records_to_csv,
)
from logslice.parser import parse_line


def build_format_convert_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-convert",
        description="Convert structured log records between formats.",
    )
    p.add_argument(
        "expr",
        help=(
            "Output format expression, e.g. 'json', 'logfmt', "
            "'csv:field1,field2', 'tsv:field1,field2'"
        ),
    )
    p.add_argument(
        "file",
        nargs="?",
        default="-",
        help="Input file (default: stdin)",
    )
    return p


def run_format_convert(
    args: argparse.Namespace,
    out=None,
    err=None,
) -> int:
    if out is None:
        out = sys.stdout
    if err is None:
        err = sys.stderr

    try:
        spec = parse_format_expr(args.expr)
    except ValueError as exc:
        err.write(f"error: {exc}\n")
        return 1

    fmt: str = spec["format"]
    columns: Optional[List[str]] = spec["columns"]

    src = sys.stdin if args.file == "-" else open(args.file)
    try:
        records = (parse_line(line) for line in src if line.strip())
        records = (r for r in records if r is not None)

        if fmt in ("csv", "tsv"):
            delimiter = "\t" if fmt == "tsv" else ","
            for row in records_to_csv(records, columns=columns, delimiter=delimiter):
                out.write(row)
        else:
            for record in records:
                out.write(convert_record(record, fmt, columns) + "\n")
    finally:
        if src is not sys.stdin:
            src.close()

    return 0


def main() -> None:
    parser = build_format_convert_parser()
    args = parser.parse_args()
    sys.exit(run_format_convert(args))


if __name__ == "__main__":
    main()
