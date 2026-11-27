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

## OUT-01 per-service error summary (standalone script)

`scripts/summarize_outage.py` uses only the standard library (no install
needed). It keeps only `ERROR` and `FATAL` rows, ignoring `WARN` and `INFO`
even when they carry an error code. It adds ERROR and FATAL together into one
`error_count` per `(outage_id, service)` and writes
`outage_id, city, service, error_count, first_error_timestamp`, ordered by
first error time (oldest first, ties by service name). Timestamps are written
exactly as they appear in the source.

```bash
python scripts/summarize_outage.py "data/Uber_Replayed Outage Error Logs (Six Outages).csv" \
    --outage OUT-01 -o data/summaries/OUT-01_service_error_summary.csv
```

Output: `data/summaries/OUT-01_service_error_summary.csv`
(6 services, 131 ERROR/FATAL rows; 48 WARN/INFO rows with error codes ignored).

**Why this order:** Ordering by first failure lists services in the order they
started failing, so the top rows point toward where the outage began and how it
spread.
