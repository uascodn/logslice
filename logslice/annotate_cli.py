"""CLI entry-point for the `logslice annotate` sub-command."""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from logslice.annotate import apply_annotation, annotate_index, parse_annotate_expr
from logslice.output import format_record
from logslice.parser import parse_line


def build_annotate_parser(parent: Optional[argparse._SubParsersAction] = None) -> argparse.ArgumentParser:
    description = "Annotate structured log records with new fields."
    if parent is not None:
        p = parent.add_parser("annotate", help=description, description=description)
    else:
        p = argparse.ArgumentParser(prog="logslice annotate", description=description)

    p.add_argument("file", nargs="?", default="-", help="Input log file (default: stdin)")
    p.add_argument(
        "-a", "--annotate",
        dest="annotations",
        metavar="EXPR",
        action="append",
        default=[],
        help=(
            "Annotation expression. Formats: "
            "field=value (static), "
            "field={src} (derived template), "
            "field=?cond:yes:no (conditional). "
            "May be repeated."
        ),
    )
    p.add_argument(
        "--index",
        metavar="FIELD",
        default=None,
        help="Add a sequential index under FIELD (default: no index).",
    )
    p.add_argument(
        "--index-start",
        type=int,
        default=0,
        metavar="N",
        help="Starting value for --index (default: 0).",
    )
    p.add_argument(
        "-f", "--format",
        choices=["json", "logfmt", "pretty"],
        default="json",
        help="Output format (default: json).",
    )
    return p


def run_annotate(args: argparse.Namespace, out=None) -> None:
    if out is None:
        out = sys.stdout

    specs = []
    for expr in args.annotations:
        try:
            specs.append(parse_annotate_expr(expr))
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            sys.exit(1)

    src = sys.stdin if args.file == "-" else open(args.file)
    try:
        records = (parse_line(line) for line in src if line.strip())
        # Filter out unparseable lines
        records = (r for r in records if r is not None)

        # Apply index annotation first if requested
        if args.index:
            records = annotate_index(records, field=args.index, start=args.index_start)

        # Apply each annotation expression in order
        for spec in specs:
            records = apply_annotation(records, spec)

        for rec in records:
            out.write(format_record(rec, args.format) + "\n")
    finally:
        if args.file != "-":
            src.close()


def main() -> None:  # pragma: no cover
    parser = build_annotate_parser()
    args = parser.parse_args()
    run_annotate(args)


if __name__ == "__main__":  # pragma: no cover
    main()
