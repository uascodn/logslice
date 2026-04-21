"""CLI entry-point for the split sub-command."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from logslice.split import parse_split_expr, split_to_files
from logslice.parser import parse_line


def build_split_parser(parent: Optional[argparse._SubParsersAction] = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    """Build (and optionally register) the argument parser for *split*."""
    kwargs = dict(
        description="Split structured log records into per-value output files.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    if parent is not None:
        parser = parent.add_parser("split", **kwargs)
    else:
        parser = argparse.ArgumentParser(prog="logslice split", **kwargs)

    parser.add_argument(
        "input",
        nargs="?",
        default="-",
        help="Input file (default: stdin).",
    )
    parser.add_argument(
        "--by",
        required=True,
        metavar="FIELD[:PREFIX]",
        help="Field to split on.  Optionally supply an output filename prefix after ':'.",
    )
    parser.add_argument(
        "--out-dir",
        default=".",
        metavar="DIR",
        help="Directory to write output files into (default: current directory).",
    )
    parser.add_argument(
        "--suffix",
        default=".jsonl",
        metavar="EXT",
        help="File extension for output files (default: .jsonl).",
    )
    parser.add_argument(
        "--default",
        default="__unknown__",
        metavar="VALUE",
        help="Group name used when the field is absent (default: __unknown__).",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print a summary of records written per group.",
    )
    return parser


def run_split(args: argparse.Namespace) -> int:
    """Execute the split command.  Returns an exit code."""
    field, prefix = parse_split_expr(args.by)

    if args.input == "-":
        lines = sys.stdin
    else:
        try:
            lines = open(args.input, encoding="utf-8")  # noqa: WPS515
        except OSError as exc:
            print(f"logslice split: error opening input: {exc}", file=sys.stderr)
            return 1

    def _iter_records():
        for line in lines:
            line = line.rstrip("\n")
            if not line:
                continue
            record = parse_line(line)
            if record is not None:
                yield record

    counts = split_to_files(
        _iter_records(),
        field=field,
        output_dir=args.out_dir,
        prefix=prefix,
        suffix=args.suffix,
        default=args.default,
    )

    if args.input != "-":
        lines.close()

    if args.summary:
        for group, n in sorted(counts.items()):
            print(f"{group}\t{n}")

    return 0


def main(argv: Optional[List[str]] = None) -> None:
    parser = build_split_parser()
    args = parser.parse_args(argv)
    sys.exit(run_split(args))


if __name__ == "__main__":
    main()
