"""Structured log line parser supporting JSON and logfmt formats."""

import json
from typing import Optional


def parse_line(line: str) -> Optional[dict]:
    """Parse a single log line into a dictionary.

    Tries JSON first, then logfmt. Returns None if parsing fails.
    """
    line = line.strip()
    if not line:
        return None

    # Try JSON
    if line.startswith("{"):
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            pass

    # Try logfmt
    return _parse_logfmt(line)


def _parse_logfmt(line: str) -> Optional[dict]:
    """Parse a logfmt-style line (key=value key="quoted value")."""
    result = {}
    i = 0
    while i < len(line):
        # Skip whitespace
        while i < len(line) and line[i] == " ":
            i += 1
        if i >= len(line):
            break

        # Read key
        eq = line.find("=", i)
        if eq == -1:
            break
        key = line[i:eq]
        i = eq + 1

        # Read value
        if i < len(line) and line[i] == '"':
            end = line.find('"', i + 1)
            if end == -1:
                return None
            value = line[i + 1:end]
            i = end + 1
        else:
            end = line.find(" ", i)
            if end == -1:
                end = len(line)
            value = line[i:end]
            i = end

        if not key:
            return None
        result[key] = value

    return result if result else None
