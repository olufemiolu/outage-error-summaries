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
    assert (s.service, s.total_count, s.error_count, s.fatal_count) == ("svc", 3, 2, 1)
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
    assert [(s.outage_id, s.total_count) for s in summarize(rows)] == [("O1", 2), ("O2", 1)]


def test_timezone_offsets_compare_correctly():
    rows = [
        row("O1", "2026-01-01T10:00:00+02:00", "a", "ERROR"),  # 08:00Z
        row("O1", "2026-01-01T09:00:00Z", "b", "ERROR"),
    ]
    assert [s.service for s in summarize(rows)] == ["a", "b"]


def test_level_case_insensitive():
    assert summarize([row("O1", "2026-01-01T00:00:00", "a", " error ")])[0].error_count == 1


def test_cli_accepts_severity_column(capsys):
    import io
    from outage_summary.cli import read_rows

    data = "outage_id,timestamp,service,severity\nO1,2026-01-01T00:00:00,a,FATAL\n"
    assert summarize(read_rows(io.StringIO(data)))[0].fatal_count == 1


def test_write_per_outage(tmp_path):
    from outage_summary.cli import write_per_outage

    rows = [row("O2", "2026-01-01T00:00:00", "a", "ERROR"), row("O1", "2026-01-01T00:00:00", "b", "FATAL")]
    from outage_summary.core import counted_entries

    paths = write_per_outage(summarize(rows), counted_entries(rows), tmp_path)
    assert [p.name for p in paths] == ["O1.csv", "O1_entries.csv", "O2.csv", "O2_entries.csv"]
    assert (tmp_path / "O1.csv").read_text().splitlines()[1].startswith("O1,b,1,0,1,")


def test_fatal_only_service_and_earliest_from_either_level():
    rows = [
        row("O1", "2026-01-01T00:00:05", "a", "ERROR"),
        row("O1", "2026-01-01T00:00:02", "a", "FATAL"),
        row("O1", "2026-01-01T00:00:03", "b", "FATAL"),
    ]
    a, b = summarize(rows)
    assert (a.service, a.error_count, a.fatal_count) == ("a", 1, 1)
    assert a.first_error_at.second == 2  # earliest is the FATAL row
    assert (b.service, b.error_count, b.fatal_count) == ("b", 0, 1)


def test_counted_entries_keep_each_timestamp_and_match_summary():
    from outage_summary.core import counted_entries

    rows = [
        LogRow("O1", parse_timestamp("2026-01-01T00:00:09"), "a", "ERROR", "L3"),
        LogRow("O1", parse_timestamp("2026-01-01T00:00:01"), "a", "WARN", "L1"),
        LogRow("O1", parse_timestamp("2026-01-01T00:00:02"), "b", "FATAL", "L2"),
    ]
    entries = counted_entries(rows)
    assert [(e.log_id, e.timestamp.second) for e in entries] == [("L2", 2), ("L3", 9)]
    assert len(entries) == sum(s.total_count for s in summarize(rows))
