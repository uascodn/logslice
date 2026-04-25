"""CLI entry point for the coalesce subcommand."""

import argparse
import json
import sys
from typing import List, Optional

from logslice.coalesce import apply_coalesces
from logslice.parser import parse_line
from logslice.output import format_record


def build_coalesce_parser(subparsers=None) -> argparse.ArgumentParser:
    description = (
        "Coalesce fields: write the first non-null value from a list of fields "
        "into a target field.  Expression format: field1,field2->target[:default]"
    )
    if subparsers is not None:
        parser = subparsers.add_parser("coalesce", help=description)
    else:
        parser = argparse.ArgumentParser(prog="logslice-coalesce", description=description)

    parser.add_argument(
        "expr",
        nargs="+",
        help="coalesce expression(s), e.g. 'host,hostname->host:unknown'",
    )
    parser.add_argument(
        "file",
        nargs="?",
        default="-",
        help="input file (default: stdin)",
    )
    parser.add_argument(
        "--fmt",
        choices=["json", "logfmt", "pretty"],
        default="json",
        help="output format (default: json)",
    )
    return parser


def run_coalesce(args: argparse.Namespace, out=None) -> None:
    if out is None:
        out = sys.stdout

    src = sys.stdin if args.file == "-" else open(args.file)
    try:
        for raw in src:
            raw = raw.rstrip("\n")
            if not raw:
                continue
            record = parse_line(raw)
            if record is None:
                continue
            record = apply_coalesces(record, args.expr)
            out.write(format_record(record, fmt=args.fmt) + "\n")
    finally:
        if src is not sys.stdin:
            src.close()


def main(argv: Optional[List[str]] = None) -> None:
    parser = build_coalesce_parser()
    args = parser.parse_args(argv)
    run_coalesce(args)


if __name__ == "__main__":
    main()
