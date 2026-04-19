"""Command-line interface for logslice."""

import sys
import json
import argparse
from typing import List, Optional

from logslice.slicer import slice_lines


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice",
        description="Filter and slice structured log files by time range or field value.",
    )
    p.add_argument(
        "file",
        nargs="?",
        help="Log file to read (default: stdin)",
    )
    p.add_argument(
        "--start",
        metavar="DATETIME",
        help="Include records at or after this time (ISO 8601)",
    )
    p.add_argument(
        "--end",
        metavar="DATETIME",
        help="Include records at or before this time (ISO 8601)",
    )
    p.add_argument(
        "-f", "--filter",
        metavar="EXPR",
        action="append",
        dest="filters",
        help="Filter expression, e.g. level=error (repeatable)",
    )
    p.add_argument(
        "--output",
        choices=["json", "logfmt"],
        default="json",
        help="Output format (default: json)",
    )
    return p


def format_record(record: dict, fmt: str) -> str:
    if fmt == "json":
        return json.dumps(record)
    # logfmt output
    parts = []
    for k, v in record.items():
        v_str = str(v)
        if " " in v_str or "=" in v_str:
            v_str = f'"{v_str}"'
        parts.append(f"{k}={v_str}")
    return " ".join(parts)


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.file:
        try:
            source = open(args.file, "r", encoding="utf-8")
        except OSError as e:
            print(f"logslice: error: {e}", file=sys.stderr)
            return 1
    else:
        source = sys.stdin

    try:
        for record in slice_lines(source, args.start, args.end, args.filters):
            print(format_record(record, args.output))
    except ValueError as e:
        print(f"logslice: error: {e}", file=sys.stderr)
        return 2
    finally:
        if args.file:
            source.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
