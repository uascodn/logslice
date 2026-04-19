"""Statistics collection for sliced log output."""
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional


class Stats:
    """Accumulates statistics over processed log records."""

    def __init__(self) -> None:
        self.total: int = 0
        self.matched: int = 0
        self._field_counters: Dict[str, Counter] = defaultdict(Counter)

    def record(self, entry: Optional[Dict[str, Any]], matched: bool) -> None:
        """Update stats for a parsed log entry."""
        self.total += 1
        if not matched or entry is None:
            return
        self.matched += 1
        for key, value in entry.items():
            self._field_counters[key][str(value)] += 1

    def top_values(self, field: str, n: int = 5) -> List[tuple]:
        """Return top n values for a given field."""
        return self._field_counters[field].most_common(n)

    def unique_values(self, field: str) -> int:
        """Return number of unique values seen for a field."""
        return len(self._field_counters[field])

    def summary(self) -> Dict[str, Any]:
        """Return a summary dict."""
        return {
            "total_lines": self.total,
            "matched_lines": self.matched,
            "dropped_lines": self.total - self.matched,
            "fields_seen": list(self._field_counters.keys()),
        }
