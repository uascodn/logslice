"""CLI sub-command: logslice grep — search log records by pattern."""

import argparse
import sys
from typing import List, Optional

from logslice.parser import parse_line
from logslice.grep import grep_records, parse_grep_expr
from logslice.output import format_record


def build_grep_parser(subparsers=None) -> argparse.ArgumentParser:
    description = "Search log records matching a pattern."
    if subparsers is not None:
        parser = subparsers.add_parser("grep", description=description, help=description)
    else:
        parser = argparse.ArgumentParser(prog="logslice grep", description=description)

    parser.add_argument(
        "pattern",
        help=(
            "Pattern to search. Formats: 'text', '/regex/', '/regex/i', "
            "'field:/regex/'"
        ),
    )
    parser.add_argument(
        "file",
        nargs="?",
        default="-",
        help="Input file (default: stdin).",
    )
    parser.add_argument(
        "-v", "--invert",
        action="store_true",
        default=False,
        help="Invert match: print non-matching records.",
    )
    parser.add_argument(
        "-f", "--format",
        choices=["json", "logfmt", "pretty"],
        default="json",
        help="Output format (default: json).",
    )
    parser.add_argument(
        "-c", "--count",
        action="store_true",
        default=False,
        help="Print only the count of matching records.",
    )
    return parser


def run_grep(args: argparse.Namespace, out=None) -> int:
    """Execute the grep sub-command.  Returns exit code."""
    if out is None:
        out = sys.stdout

    try:
        grep_opts = parse_grep_expr(args.pattern)
    except Exception as exc:
        print(f"logslice grep: invalid pattern — {exc}", file=sys.stderr)
        return 2

    source = sys.stdin if args.file == "-" else open(args.file)

    try:
        raw_records = []
        for line in source:
            line = line.rstrip("\n")
            if not line:
                continue
            record = parse_line(line)
            if record is not None:
                raw_records.append(record)

        matched = list(
            grep_records(
                raw_records,
                pattern=grep_opts["pattern"],
                fields=grep_opts["fields"],
                invert=args.invert,
            )
        )
    finally:
        if args.file != "-":
            source.close()

    if args.count:
        print(len(matched), file=out)
    else:
        for record in matched:
            print(format_record(record, fmt=args.format), file=out)

    return 0


def main(argv: Optional[List[str]] = None) -> None:
    parser = build_grep_parser()
    args = parser.parse_args(argv)
    sys.exit(run_grep(args))


if __name__ == "__main__":
    main()
