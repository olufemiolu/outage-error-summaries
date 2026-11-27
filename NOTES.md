# Notes

## Key prompt

> Set up a basic python project for a long-grouping script, using the rule: For
> each outage, count every ERROR and FATAL row per service, including repeats,
> then output one row per service ordered by its earliest ERROR or FATAL
> timestamp, oldest first and arrange alphabetically by service name for ties

## Ordering choice and why

Within each outage, services are ordered by their **earliest ERROR or FATAL
timestamp, oldest first**, with **ties broken alphabetically by service name**.

Why _(rationale drafted by Claude; edit if yours differs)_: ordering by first
failure lists services in the order they started failing, so the top rows point
toward where the outage began and how it spread (in OUT-01, `eta-routing` fails
first at 18:02:11, and `dispatch-matching`'s first error at 18:05:31 is a timeout
calling `eta-routing`). The alphabetical tie-break makes the output deterministic
when two services first fail at the same second. Counting repeats keeps the
count proportional to how noisy each service was.

## What I checked or changed

- **Input column:** the data uses `severity`, not `level`; the script now
  accepts either.
- **Six outages vs. one:** `data/Replayed Outage Error Logs (Six Outages).csv`
  contains 179 rows, all `OUT-01` (Chicago, 2026-08-17 17:52:04–18:11:55, no
  gaps). Only one summary could be produced; the other five outages are not in
  the file.
- **Spot-checked eta-routing:** listed all 28 counted log_ids with severity and
  timestamp, and confirmed the count and first timestamp against the summary.
- **Checked file path and row count** used for OUT-01.
- **Questioned LOG-000034:** this caught a wrong claim (it had been guessed to
  be an uncounted eta-routing row). It is a `dispatch-matching` ERROR whose
  `upstream_service` is `eta-routing`; rows are grouped by `service`, so it
  counts for dispatch-matching. The real uncounted eta-routing rows are 6
  WARN/INFO rows (22, 28, 32, 56, 98, 159).
- **Changed:** one summary file per outage plus saved terminal output
  (`--out-dir`).
- **Changed:** summary splits ERROR vs. FATAL (`total_count`, `error_count`,
  `fatal_count`); `error_count` now means ERROR only.
- **Changed:** added `<outage_id>_entries.csv` listing every counted row with
  its own timestamp so results can be filtered by time.
