# outage-summary

Groups outage log rows into one summary row per service.

**Rule:** for each outage, count every `ERROR` and `FATAL` row per service
(repeats included), then output one row per service ordered by its earliest
`ERROR`/`FATAL` timestamp (oldest first), with ties broken alphabetically by
service name. Services with no `ERROR`/`FATAL` rows are omitted; outages are
emitted in `outage_id` order.

Output columns: `outage_id, service, total_count, error_count, fatal_count,
first_error_at` — `error_count` is ERROR rows only, `fatal_count` is FATAL rows
only, and `total_count` is their sum.

With `--out-dir DIR`, each outage also gets `DIR/<outage_id>.csv` (the summary)
and `DIR/<outage_id>_entries.csv`: every counted ERROR/FATAL row
(`outage_id, log_id, service, severity, timestamp`), oldest first, so you can
filter by time.

## Input

CSV with a header containing `outage_id,timestamp,service` plus a `level` or
`severity` column (extra columns ignored). Timestamps are ISO-8601; ones without an offset are treated as UTC.

## Usage

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e '.[dev]'
outage-summary examples/logs.csv      # or: python -m outage_summary < file.csv
pytest
```
