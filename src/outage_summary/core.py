"""Grouping rule.

For each outage:
  * count every ERROR and FATAL row per service, repeats included;
  * emit one row per service that had at least one ERROR/FATAL row;
  * order rows by the service's earliest ERROR/FATAL timestamp (oldest first),
    breaking ties alphabetically by service name.

Outages themselves are emitted in ascending outage_id order.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

COUNTED_LEVELS = frozenset({"ERROR", "FATAL"})


@dataclass(frozen=True)
class LogRow:
    outage_id: str
    timestamp: datetime
    service: str
    level: str
    log_id: str = ""


@dataclass(frozen=True)
class ServiceSummary:
    outage_id: str
    service: str
    error_count: int  # ERROR rows only
    fatal_count: int  # FATAL rows only
    first_error_at: datetime  # earliest ERROR or FATAL row

    @property
    def total_count(self) -> int:
        return self.error_count + self.fatal_count


def parse_timestamp(value: str) -> datetime:
    """Parse ISO-8601; naive timestamps are assumed UTC so all values compare safely."""
    ts = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)


def is_counted(row: LogRow) -> bool:
    return row.level.strip().upper() in COUNTED_LEVELS


def counted_entries(rows: Iterable[LogRow]) -> list[LogRow]:
    """Every ERROR/FATAL row that summarize() counts, oldest first within each outage."""
    entries = [r for r in rows if is_counted(r)]
    entries.sort(key=lambda r: (r.outage_id, r.timestamp, r.service, r.log_id))
    return entries


def summarize(rows: Iterable[LogRow]) -> list[ServiceSummary]:
    # (outage_id, service) -> [error count, fatal count, earliest timestamp]
    groups: dict[tuple[str, str], list] = {}
    for row in rows:
        if not is_counted(row):
            continue
        level = row.level.strip().upper()
        entry = groups.setdefault((row.outage_id, row.service), [0, 0, row.timestamp])
        entry[0 if level == "ERROR" else 1] += 1
        if row.timestamp < entry[2]:
            entry[2] = row.timestamp

    summaries = [
        ServiceSummary(outage, service, errors, fatals, first)
        for (outage, service), (errors, fatals, first) in groups.items()
    ]
    summaries.sort(key=lambda s: (s.outage_id, s.first_error_at, s.service))
    return summaries
