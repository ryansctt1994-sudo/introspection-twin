# Scheduled replay liveness

The 2026-11-04 14:45 UTC qualification trigger produced **no observed scheduled
run as of 15:18 UTC**. The workflow API reported `active`. This is a delivery
finding, not an indefinitely pending qualification and not proof of a cause.
The read-only API observation is recorded in `SCHEDULE_MISS_2026-11-04.json`.

The 20-minute arrival limit below was adopted **after** that missed trigger.
Its retrospective deadline was 15:05 UTC; this historical assessment is not
represented as a precommitted test. Subsequent deadlines are prospective.

**Later observation:** genuine scheduled run
[41857790032](https://github.com/ryansctt1994-sudo/introspection-twin/actions/runs/41857790032)
was created at **15:26:37 UTC** and completed successfully. Its actual job log
records merged main `3b811cd008495b51c75f9d942b04a440580c1d88`, tree
`172dc4e8e057ccbe63f9f1d3f2289c6d2ec42caf`, `FRESH=1`, both fresh flags true,
all checker/logger exits zero, real poison-refusal diagnostics, and a PASS replay
receipt. This satisfies the original scheduled FRESH execution requirement.
It does not erase the earlier absence. The old workflow had no trigger record,
so this event cannot be attributed to a particular one of its two cron entries.
The run appeared 41 minutes 37 seconds after 14:45; no specific cause is proved.

## Operational expectation

Daily FRESH replay moves to **15:47 UTC** (`47 15 * * *`), first expected on
2026-11-04 after this change reaches the default branch. The old 07:17 daily
entry and dated 14:45 entry are removed; no annual cleanup trigger remains.
The timing policy lives in `.github/replay-schedule.json` and CI checks that
it matches the workflow's single daily cron.

- A scheduled run must appear by **16:07 UTC** (trigger + 20 minutes).
- Successful completion metadata must be observed within **16:27 UTC**
  (trigger + 40 minutes). The replay job also has a 30-minute execution timeout.
- At **16:29 UTC**, a separate watchdog checks the event and completion and
  publishes its JSON receipt and job summary, including failures.
- At **16:57 UTC**, the configured ChatGPT task **Replay Schedule Watch** checks
  actual GitHub evidence and reports to the owner. It also checks the GitHub
  watchdog, whose arrival/completion deadlines are **16:49 / 16:54 UTC**.

These are chosen operational thresholds, not a GitHub delivery guarantee.
Changing them requires a new committed policy; late success does not erase the
original missed window. Check every expected slot; the default CLI checks only
the latest slot, so an external poller must retain its cursor and receipts.

`MISSED_SCHEDULE`, `LATE_RUN`, `COMPLETION_OVERDUE`, `RUN_FAILED`, and
`WORKFLOW_NOT_ACTIVE` fail the observation job. An API error, incomplete listing,
duplicate candidate, or rerun ambiguity returns `INCONCLUSIVE`. A completion
timestamp cannot be inferred precisely from `updated_at`; a bound after the
deadline returns `COMPLETION_NOT_VERIFIED_IN_WINDOW`, never on-time success.
Before a deadline the explicit `AWAITING_RUN`/`RUNNING` status exits 3, not 0.

## Outside-GitHub observation

The same dependency-free checker can be invoked by an external scheduler:

```sh
python3 scripts/check_schedule_liveness.py \
  --expected-at 2026-11-04T15:47:00Z \
  --output schedule-2026-11-04.json
```

For this public repository no token is required; an optional read-only
`GITHUB_TOKEN` raises API limits. Exit 0 means only on-time successful completion
metadata. Exit 1 is a finding, 2 an inconclusive observation, 3 not yet due or
within the waiting window. All output says `qualification: NOT_ASSESSED`.

The GitHub watchdog shares the platform and owner with the replay. It cannot
detect simultaneous scheduler failure by itself and is not an independent
witness. A separate ChatGPT task was accepted and enabled on 2026-11-04, with
its first check scheduled for 16:57 UTC and daily thereafter. It is instructed to
audit every elapsed slot, retain receipts/cursor where storage is available,
report API failures as inconclusive, inspect actual FRESH logs, and send the owner
a dated result. It cannot mutate the repository or substitute manual runs.

This is **configured external scheduling, with no completed task execution yet**
at this document's commit. The two schedulers remain under the same owner, and
neither is claimed to have guaranteed availability or independent witnessing.
An unavailable execution environment must be handled with connected read-only
GitHub tools or an explicit inconclusive result, never silence or inferred health.

## Evidence separation

PR #11 is merged at `3b811cd008495b51c75f9d942b04a440580c1d88`. Its hosted PR
FRESH run [41848268138](https://github.com/ryansctt1994-sudo/introspection-twin/actions/runs/41848268138)
and merged-main ordinary run [41849200680](https://github.com/ryansctt1994-sudo/introspection-twin/actions/runs/41849200680)
are evidence for those exact events. Neither substitutes for a scheduled run.

Scheduled qualification additionally requires the actual run's source SHA/tree,
`trigger-record.json` with `TRIGGER_EVENT=schedule` and the expected cron,
`fresh_requested=true`, `fresh_verified=true`, zero checker and logger exits,
actual checker diagnostics in the job log, and the final replay receipt.
The trigger-record requirement applies prospectively to this revised workflow;
the earlier run above is qualified to the original requirement using GitHub's
actual `event=schedule` metadata and its complete replay log. API
creation time alone cannot distinguish a very late prior trigger from the
intended slot; inspect the trigger record. A repeated daily cron string itself
cannot prove which intended date caused a severely delayed event; preserve that
attribution uncertainty. Owner-controlled CI remains evidence
under the same principal, not independent reproduction.

GitHub [documents](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)
delay or dropped jobs under load, particularly at the start of an hour, and
disabling after 60 days of inactivity in public repositories. Those facts make
off-boundary timing useful; they do not identify this incident's cause or imply
that every failed off-boundary attempt means a disabled workflow.
