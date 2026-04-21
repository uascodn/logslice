"""CLI entry point for record-level diff between two log files."""

import argparse
import sys
from typing import List

from logslice.parser import parse_line
from logslice.diff import diff_records, has_changes, render_diff


def build_diff_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-diff",
        description="Diff two structured log files record by record.",
    )
    p.add_argument("file_a", help="First log file")
    p.add_argument("file_b", help="Second log file")
    p.add_argument(
        "--key",
        dest="key_field",
        default=None,
        help="Field to use as record key for alignment (default: positional)",
    )
    p.add_argument(
        "--ignore",
        dest="ignore_fields",
        nargs="*",
        default=[],
        metavar="FIELD",
        help="Fields to ignore during comparison",
    )
    p.add_argument(
        "--changed-only",
        action="store_true",
        help="Only print records that differ",
    )
    p.add_argument(
        "--color",
        action="store_true",
        help="Colorize output",
    )
    return p


def _read_records(path: str) -> List[dict]:
    """Read and parse all valid log records from *path*.

    Raises:
        SystemExit: if the file cannot be opened, with a user-friendly message.
    """
    records = []
    try:
        with open(path) as fh:
            for line in fh:
                rec = parse_line(line)
                if rec is not None:
                    records.append(rec)
    except OSError as exc:
        sys.exit(f"logslice-diff: error reading '{path}': {exc.strerror}")
    return records


def run_diff(args: argparse.Namespace, out=None) -> int:
    if out is None:
        out = sys.stdout

    records_a = _read_records(args.file_a)
    records_b = _read_records(args.file_b)

    pairs = list(zip(records_a, records_b))
    exit_code = 0

    for idx, (a, b) in enumerate(pairs):
        diff = diff_records(a, b, ignore_fields=args.ignore_fields)
        if args.changed_only and not has_changes(diff):
            continue
        out.write(f"--- record {idx + 1}\n")
        out.write(render_diff(diff, color=args.color) + "\n")
        if has_changes(diff):
            exit_code = 1

    extra_a = len(records_a) - len(records_b)
    if extra_a > 0:
        out.write(f"--- {extra_a} extra record(s) only in {args.file_a}\n")
        exit_code = 1
    elif extra_a < 0:
        out.write(f"--- {-extra_a} extra record(s) only in {args.file_b}\n")
        exit_code = 1

    return exit_code


def main() -> None:
    parser = build_diff_parser()
    args = parser.parse_args()
    sys.exit(run_diff(args))
