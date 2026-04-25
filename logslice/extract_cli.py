"""CLI entry point for the extract sub-command."""

import argparse
import json
import sys
from typing import List, Optional

from logslice.extract import apply_extracts, parse_extract_expr
from logslice.parser import parse_line
from logslice.output import format_record


def build_extract_parser(parent: Optional[argparse.ArgumentParser] = None) -> argparse.ArgumentParser:
    p = parent or argparse.ArgumentParser(
        prog="logslice extract",
        description="Extract sub-values from fields via regex or split.",
    )
    p.add_argument(
        "expr",
        nargs="+",
        help=(
            "Extract expression(s). "
            "regex:<src>/<pattern>/<dest>[/<group>] or "
            "split:<src>/<delim>/<index>/<dest>"
        ),
    )
    p.add_argument(
        "file",
        nargs="?",
        default="-",
        help="Input file (default: stdin).",
    )
    p.add_argument(
        "--fmt",
        default="json",
        choices=["json", "logfmt", "pretty"],
        help="Output format (default: json).",
    )
    return p


def run_extract(args: argparse.Namespace, out=None) -> int:
    if out is None:
        out = sys.stdout

    try:
        parsed_exprs = [parse_extract_expr(e) for e in args.expr]
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    source = sys.stdin if args.file == "-" else open(args.file)
    try:
        for raw in source:
            raw = raw.rstrip("\n")
            if not raw:
                continue
            record = parse_line(raw)
            if record is None:
                continue
            record = apply_extracts(record, parsed_exprs)
            out.write(format_record(record, args.fmt) + "\n")
    finally:
        if args.file != "-":
            source.close()
    return 0


def main(argv: Optional[List[str]] = None) -> None:
    parser = build_extract_parser()
    args = parser.parse_args(argv)
    sys.exit(run_extract(args))


if __name__ == "__main__":
    main()
