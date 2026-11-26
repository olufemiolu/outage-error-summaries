"""CLI: read a CSV of log rows, write the per-service summary as CSV.

Input columns (header required): outage_id, timestamp, service, level
Extra columns are ignored.
"""

from __future__ import annotations

import argparse
import csv
import sys
from typing import Iterator, TextIO

from .core import LogRow, parse_timestamp, summarize

REQUIRED_COLUMNS = ("outage_id", "timestamp", "service", "level")


def read_rows(stream: TextIO) -> Iterator[LogRow]:
    reader = csv.DictReader(stream)
    missing = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
    if missing:
        raise SystemExit(f"error: input is missing column(s): {', '.join(missing)}")
    for line_no, rec in enumerate(reader, start=2):
        try:
            ts = parse_timestamp(rec["timestamp"])
        except ValueError:
            raise SystemExit(f"error: line {line_no}: bad timestamp {rec['timestamp']!r}")
        yield LogRow(rec["outage_id"].strip(), ts, rec["service"].strip(), rec["level"])


def write_summaries(summaries, stream: TextIO) -> None:
    writer = csv.writer(stream)
    writer.writerow(["outage_id", "service", "error_count", "first_error_at"])
    for s in summaries:
        writer.writerow([s.outage_id, s.service, s.error_count, s.first_error_at.isoformat()])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("input", nargs="?", default="-", help="CSV file (default: stdin)")
    args = parser.parse_args(argv)

    if args.input == "-":
        summaries = summarize(read_rows(sys.stdin))
    else:
        with open(args.input, newline="", encoding="utf-8") as fh:
            summaries = summarize(read_rows(fh))
    write_summaries(summaries, sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
