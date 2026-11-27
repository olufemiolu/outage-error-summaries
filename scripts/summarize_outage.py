#!/usr/bin/env python3
"""Summarize ERROR/FATAL log rows per service for one outage.

Rules:
  * keep only rows whose severity is ERROR or FATAL; WARN and INFO rows are
    ignored even when they carry an error_code;
  * group by (outage_id, service); ERROR and FATAL rows are added together
    into a single error_count, repeats included;
  * write one row per service: outage_id, city, service, error_count,
    first_error_timestamp;
  * order rows by first error time, oldest first (ties: service name A-Z).

Timestamps are written exactly as they appear in the source file.

Usage:
  python scripts/summarize_outage.py INPUT.csv [--outage OUT-01] [-o OUTPUT.csv]
"""

from __future__ import annotations

import argparse
import csv
import sys
from datetime import datetime
from pathlib import Path

COUNTED_SEVERITIES = {"ERROR", "FATAL"}
REQUIRED = ("outage_id", "city", "service", "severity", "timestamp")
OUT_COLUMNS = ["outage_id", "city", "service", "error_count", "first_error_timestamp"]


def summarize(rows, outage_id: str) -> list[dict]:
    groups: dict[tuple[str, str], dict] = {}
    for line_no, row in rows:
        if row["outage_id"].strip() != outage_id:
            continue
        if row["severity"].strip().upper() not in COUNTED_SEVERITIES:
            continue
        raw_ts = row["timestamp"].strip()
        try:
            ts = datetime.fromisoformat(raw_ts)
        except ValueError:
            sys.exit(f"error: line {line_no}: bad timestamp {raw_ts!r}")
        key = (outage_id, row["service"].strip())
        city = row["city"].strip()
        g = groups.setdefault(key, {"city": city, "count": 0, "first": ts, "first_raw": raw_ts})
        if g["city"] != city:
            sys.exit(f"error: line {line_no}: {key} has more than one city "
                     f"({g['city']!r}, {city!r})")
        g["count"] += 1
        if ts < g["first"]:
            g["first"], g["first_raw"] = ts, raw_ts

    ordered = sorted(groups.items(), key=lambda kv: (kv[1]["first"], kv[0][1]))
    return [
        {"outage_id": o, "city": g["city"], "service": s,
         "error_count": g["count"], "first_error_timestamp": g["first_raw"]}
        for (o, s), g in ordered
    ]


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Per-service ERROR/FATAL summary for one outage.")
    p.add_argument("input", type=Path, help="log CSV")
    p.add_argument("--outage", default="OUT-01", help="outage_id to summarize (default: OUT-01)")
    p.add_argument("-o", "--output", type=Path, help="output CSV (default: stdout only)")
    args = p.parse_args(argv)

    with open(args.input, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        missing = [c for c in REQUIRED if c not in (reader.fieldnames or [])]
        if missing:
            sys.exit(f"error: missing column(s): {', '.join(missing)}")
        summary = summarize(enumerate(reader, start=2), args.outage)

    if not summary:
        sys.exit(f"error: no ERROR/FATAL rows found for outage {args.outage!r}")

    writer = csv.DictWriter(sys.stdout, fieldnames=OUT_COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(summary)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=OUT_COLUMNS)
            w.writeheader()
            w.writerows(summary)
        print(f"\nwrote {args.output} ({len(summary)} services, "
              f"{sum(r['error_count'] for r in summary)} errors)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
