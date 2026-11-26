# outage-summary

Groups outage log rows into one summary row per service.

**Rule:** for each outage, count every `ERROR` and `FATAL` row per service
(repeats included), then output one row per service ordered by its earliest
`ERROR`/`FATAL` timestamp (oldest first), with ties broken alphabetically by
service name. Services with no `ERROR`/`FATAL` rows are omitted; outages are
emitted in `outage_id` order.

## Input

CSV with a header containing `outage_id,timestamp,service,level` (extra columns
ignored). Timestamps are ISO-8601; ones without an offset are treated as UTC.

## Usage

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e '.[dev]'
outage-summary examples/logs.csv      # or: python -m outage_summary < file.csv
pytest
```
