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


@dataclass(frozen=True)
class ServiceSummary:
    outage_id: str
    service: str
    error_count: int
    first_error_at: datetime


def parse_timestamp(value: str) -> datetime:
    """Parse ISO-8601; naive timestamps are assumed UTC so all values compare safely."""
    ts = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)


def summarize(rows: Iterable[LogRow]) -> list[ServiceSummary]:
    # (outage_id, service) -> [count, earliest timestamp]
    groups: dict[tuple[str, str], list] = {}
    for row in rows:
        if row.level.strip().upper() not in COUNTED_LEVELS:
            continue
        key = (row.outage_id, row.service)
        entry = groups.get(key)
        if entry is None:
            groups[key] = [1, row.timestamp]
        else:
            entry[0] += 1
            if row.timestamp < entry[1]:
                entry[1] = row.timestamp

    summaries = [
        ServiceSummary(outage, service, count, first)
        for (outage, service), (count, first) in groups.items()
    ]
    summaries.sort(key=lambda s: (s.outage_id, s.first_error_at, s.service))
    return summaries
