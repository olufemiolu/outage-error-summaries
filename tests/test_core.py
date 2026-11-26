from datetime import datetime, timezone

from outage_summary.core import LogRow, parse_timestamp, summarize


def row(outage, ts, service, level):
    return LogRow(outage, parse_timestamp(ts), service, level)


def test_counts_repeats_and_only_error_fatal():
    rows = [
        row("O1", "2026-01-01T00:00:01", "svc", "ERROR"),
        row("O1", "2026-01-01T00:00:02", "svc", "ERROR"),
        row("O1", "2026-01-01T00:00:03", "svc", "FATAL"),
        row("O1", "2026-01-01T00:00:00", "svc", "WARN"),
        row("O1", "2026-01-01T00:00:00", "quiet", "INFO"),
    ]
    [s] = summarize(rows)
    assert (s.service, s.error_count) == ("svc", 3)
    # earliest ERROR/FATAL, not the earlier WARN
    assert s.first_error_at == datetime(2026, 1, 1, 0, 0, 1, tzinfo=timezone.utc)


def test_order_by_earliest_then_name_and_unordered_input():
    rows = [
        row("O1", "2026-01-01T00:00:09", "zeta", "ERROR"),
        row("O1", "2026-01-01T00:00:05", "beta", "ERROR"),
        row("O1", "2026-01-01T00:00:05", "alpha", "FATAL"),
        row("O1", "2026-01-01T00:00:01", "zeta", "ERROR"),  # zeta's earliest arrives late
    ]
    assert [s.service for s in summarize(rows)] == ["zeta", "alpha", "beta"]


def test_outages_grouped_separately():
    rows = [
        row("O2", "2026-01-01T00:00:00", "a", "ERROR"),
        row("O1", "2026-01-02T00:00:00", "a", "ERROR"),
        row("O1", "2026-01-02T00:00:00", "a", "ERROR"),
    ]
    assert [(s.outage_id, s.error_count) for s in summarize(rows)] == [("O1", 2), ("O2", 1)]


def test_timezone_offsets_compare_correctly():
    rows = [
        row("O1", "2026-01-01T10:00:00+02:00", "a", "ERROR"),  # 08:00Z
        row("O1", "2026-01-01T09:00:00Z", "b", "ERROR"),
    ]
    assert [s.service for s in summarize(rows)] == ["a", "b"]


def test_level_case_insensitive():
    assert summarize([row("O1", "2026-01-01T00:00:00", "a", " error ")])[0].error_count == 1
