"""CLI: read a CSV of log rows, write the per-service summary as CSV.

Input columns (header required): outage_id, timestamp, service, and a level
column named either "level" or "severity". An optional "log_id" column is
carried into the per-entry files. Other columns are ignored.
"""

from __future__ import annotations

import argparse
import csv
import sys
from itertools import groupby
from pathlib import Path
from typing import Iterator, TextIO

from .core import LogRow, counted_entries, parse_timestamp, summarize

REQUIRED_COLUMNS = ("outage_id", "timestamp", "service")
LEVEL_COLUMNS = ("level", "severity")


def read_rows(stream: TextIO) -> Iterator[LogRow]:
    reader = csv.DictReader(stream)
    fields = reader.fieldnames or []
    missing = [c for c in REQUIRED_COLUMNS if c not in fields]
    level_col = next((c for c in LEVEL_COLUMNS if c in fields), None)
    if level_col is None:
        missing.append(" or ".join(LEVEL_COLUMNS))
    if missing:
        raise SystemExit(f"error: input is missing column(s): {', '.join(missing)}")
    for line_no, rec in enumerate(reader, start=2):
        try:
            ts = parse_timestamp(rec["timestamp"])
        except ValueError:
            raise SystemExit(f"error: line {line_no}: bad timestamp {rec['timestamp']!r}")
        yield LogRow(
            rec["outage_id"].strip(), ts, rec["service"].strip(), rec[level_col],
            (rec.get("log_id") or "").strip(),
        )


def write_summaries(summaries, stream: TextIO) -> None:
    writer = csv.writer(stream)
    writer.writerow(
        ["outage_id", "service", "total_count", "error_count", "fatal_count", "first_error_at"]
    )
    for s in summaries:
        writer.writerow(
            [s.outage_id, s.service, s.total_count, s.error_count, s.fatal_count,
             s.first_error_at.isoformat()]
        )


def write_entries(entries, stream: TextIO) -> None:
    writer = csv.writer(stream)
    writer.writerow(["outage_id", "log_id", "service", "severity", "timestamp"])
    for e in entries:
        writer.writerow(
            [e.outage_id, e.log_id, e.service, e.level.strip().upper(), e.timestamp.isoformat()]
        )


def write_per_outage(summaries, entries, out_dir: Path) -> list[Path]:
    """Per outage, write <id>.csv (summary) and <id>_entries.csv (every counted row).

    Returns the paths written.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    entries_by_outage = {k: list(g) for k, g in groupby(entries, key=lambda e: e.outage_id)}
    paths = []
    for outage_id, group in groupby(summaries, key=lambda s: s.outage_id):
        summary_path = out_dir / f"{outage_id}.csv"
        with open(summary_path, "w", newline="", encoding="utf-8") as fh:
            write_summaries(group, fh)
        entries_path = out_dir / f"{outage_id}_entries.csv"
        with open(entries_path, "w", newline="", encoding="utf-8") as fh:
            write_entries(entries_by_outage[outage_id], fh)
        paths += [summary_path, entries_path]
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("input", nargs="?", default="-", help="CSV file (default: stdin)")
    parser.add_argument(
        "--out-dir", type=Path,
        help="also write <outage_id>.csv and <outage_id>_entries.csv per outage here",
    )
    args = parser.parse_args(argv)

    if args.input == "-":
        rows = list(read_rows(sys.stdin))
    else:
        with open(args.input, newline="", encoding="utf-8") as fh:
            rows = list(read_rows(fh))
    summaries = summarize(rows)
    write_summaries(summaries, sys.stdout)
    sys.stdout.flush()
    if args.out_dir:
        paths = write_per_outage(summaries, counted_entries(rows), args.out_dir)
        print(f"\n{len(paths) // 2} outage(s) found; wrote:", file=sys.stderr)
        for path in paths:
            print(f"  {path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
