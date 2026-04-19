"""Terminal color highlighting for log output."""

import re

ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"

LEVEL_COLORS = {
    "error": "\033[31m",    # red
    "fatal": "\033[35m",    # magenta
    "warn": "\033[33m",     # yellow
    "warning": "\033[33m",  # yellow
    "info": "\033[32m",     # green
    "debug": "\033[36m",    # cyan
    "trace": "\033[34m",    # blue
}


def colorize_level(level: str) -> str:
    """Return ANSI-colored version of a log level string."""
    key = level.lower()
    color = LEVEL_COLORS.get(key, "")
    if color:
        return f"{color}{ANSI_BOLD}{level}{ANSI_RESET}"
    return level


def highlight_field(key: str, value: str) -> str:
    """Return highlighted key=value pair."""
    return f"{ANSI_BOLD}{key}{ANSI_RESET}={value}"


def highlight_pattern(text: str, pattern: str) -> str:
    """Wrap all occurrences of pattern in text with highlight color."""
    if not pattern:
        return text
    highlight_color = "\033[43m\033[30m"  # yellow bg, black fg
    try:
        highlighted = re.sub(
            f"({re.escape(pattern)})",
            f"{highlight_color}\\1{ANSI_RESET}",
            text,
            flags=re.IGNORECASE,
        )
    except re.error:
        return text
    return highlighted


def highlight_record(record: dict, search: str = "") -> str:
    """Format a log record with color highlights for level and optional search term."""
    parts = []
    for key, value in record.items():
        str_val = str(value)
        if key in ("level", "severity"):
            str_val = colorize_level(str_val)
        if search:
            str_val = highlight_pattern(str_val, search)
        parts.append(f"{ANSI_BOLD}{key}{ANSI_RESET}={str_val}")
    return "  ".join(parts)
