# logslice

A CLI tool to filter and slice structured log files by time range or field value.

---

## Installation

```bash
pip install logslice
```

Or install from source:

```bash
git clone https://github.com/youruser/logslice.git
cd logslice && pip install .
```

---

## Usage

```bash
# Filter logs by time range
logslice --input app.log --from "2024-01-15T10:00:00" --to "2024-01-15T11:00:00"

# Filter by field value
logslice --input app.log --field level=error

# Combine filters and write output to a file
logslice --input app.log --from "2024-01-15T10:00:00" --field service=api -o out.log
```

**Options:**

| Flag | Description |
|------|-------------|
| `--input`, `-i` | Path to the structured log file (JSON, NDJSON) |
| `--from` | Start of time range (ISO 8601) |
| `--to` | End of time range (ISO 8601) |
| `--field` | Filter by `key=value` pair |
| `--output`, `-o` | Write results to a file instead of stdout |

---

## Example Output

```
{"timestamp": "2024-01-15T10:23:11Z", "level": "error", "service": "api", "msg": "timeout"}
{"timestamp": "2024-01-15T10:45:02Z", "level": "error", "service": "api", "msg": "connection refused"}
```

---

## License

MIT © 2024 youruser