# Schedule liveness window recalibration — 2026-11-11

Supersedes the timing windows in `SCHEDULE_LIVENESS_2026-11-04.md`; that record
is kept unchanged as history.

## Finding

All seven `replay schedule liveness` runs since the check landed (2026-11-04 to
2026-11-10) failed. Each time, the underlying scheduled `ci` run executed and
succeeded, but GitHub started it hours after the `47 15 * * *` slot:

| Slot (UTC)  | Scheduled `ci` created | Delay  | Conclusion |
|-------------|------------------------|--------|------------|
| 11-04 15:47 | 21:32:44               | 5h46m  | success    |
| 11-05 15:47 | 21:35:50               | 5h49m  | success    |
| 11-06 15:47 | 21:06:02               | 5h19m  | success    |
| 11-07 15:47 | 19:39:47               | 3h53m  | success    |
| 11-08 15:47 | 19:58:56               | 4h12m  | success    |
| 11-09 15:47 | 23:51:39               | 8h04m  | success    |
| 11-10 15:47 | 21:26:41               | 5h40m  | success    |

GitHub documents that scheduled workflows can be delayed under load and does not
guarantee a start time. A 20-minute arrival window could not pass on hosted
scheduling, so the check was permanently red and carried no signal.

## Change

- `arrival_grace_seconds`: 1200 → 43200 (run must be created within 12h of the slot).
- `completion_grace_seconds`: 2400 → 46800 (completion bound within 13h, i.e. 04:47 UTC next day).
- `schedule-liveness.yml` cron: `29 16 * * *` → `53 4 * * *`, after the new deadline and
  before the next slot, so the audit always targets a slot that should have finished.
- Fixtures now derive deadlines from the policy, and a test asserts the audit cron sits
  between the completion deadline and the next slot.

Unchanged: a missed slot, failed/cancelled/skipped run, stuck run, rerun or duplicate,
disabled workflow, non-schedule event, or incomplete API listing is still a finding or
INCONCLUSIVE. This measures delivery timeliness only; it does not qualify the replay.

## Verification

- `python3 scripts/test_schedule_liveness.py`: 19/19 pass; the new 8h04m-delay fixture
  fails against the old policy.
- Live re-evaluation of slot `2026-11-10T15:47:00Z` (run 42905100906) with the new
  policy: `COMPLETED_ON_TIME` (previously `LATE_RUN`).

If an on-time guarantee tighter than ~12h is required, hosted `schedule` cannot provide
it; an external trigger (e.g. `workflow_dispatch` from a reliable scheduler) would be needed.
