# Replay Schedule Watch — 20261113T225307Z

Status: FINDINGS. New slots: November 12–13; closed-window recheck: November 11.
Cumulative recorded coverage: 2026-11-04 through 2026-11-13, inclusive.

- intended_fire_time: **null / UNKNOWN**. Candidate cadence slots: November 7–13,
  16:57 UTC daily. Scheduler detailed run/delivery history is unavailable.
- actual_arrival_time: **2026-11-13T22:53:07Z**, first assistant audit clock reading.
- scheduler-reported last_run_time: **2026-11-13T22:53:00.101682+00:00**, a distinct field.
- Compared only with today's published cadence **2026-11-13T16:57:00Z**, arrival
  was 5h56m07s later. This does not identify the intended invocation slot.
- Next-run metadata reports 16:57 at -06:00 despite the UTC cadence/DTSTART.
  This inconsistency is recorded; the schedule was not changed.

Both workflows are active. Complete connected schedule/main pagination found 51
runs; jobs/artifacts pagination was also completed. Workflow state endpoints were
unavailable through the connector allowlist, so public read-only HTTPS supplied
those records. No GitHub API failure was treated as healthy.

| Creation-window date | Replay created / completed UTC | Watchdog created / completed UTC |
|---|---|---|
| 2026-11-11 | [22:18:48](https://github.com/ryansctt1994-sudo/introspection-twin/actions/runs/43110695731) / 22:22:10 | [22:54:20](https://github.com/ryansctt1994-sudo/introspection-twin/actions/runs/43115597567) / 22:54:30 |
| 2026-11-12 | [21:55:25](https://github.com/ryansctt1994-sudo/introspection-twin/actions/runs/43314981776) / 21:59:04 | [22:22:36](https://github.com/ryansctt1994-sudo/introspection-twin/actions/runs/43319304223) / 22:22:47 |
| 2026-11-13 | [21:40:09](https://github.com/ryansctt1994-sudo/introspection-twin/actions/runs/43512733146) / 21:44:18 | [22:04:23](https://github.com/ryansctt1994-sudo/introspection-twin/actions/runs/43516188219) / 22:04:33 |

All replay candidates qualify for scheduled FRESH execution: exact event/cron,
SHA/tree binding, fresh flags, real checker diagnostics, zero checker/logger
exits, and final PASS receipts. The actual step and digest-verified raw artifacts
were checked separately from mock controls. Their arrivals and completions still
miss the declared deadlines (16:07 / 16:27 UTC). The watchdogs also missed their
16:49 / 16:54 deadlines and failed correctly while reporting replay lateness.

Creation windows and a daily cron string do not prove an event's original
intended date. Runs are executed; timing/cause remains unexplained. API run start
and actual job completion timestamps are separate fields in each slot receipt.

First historically qualified scheduled FRESH run remains
[41857790032](https://github.com/ryansctt1994-sudo/introspection-twin/actions/runs/41857790032),
created 2026-11-04T15:26:37Z on merged #11. It is not counted for a later slot.
The old 14:45 miss remains preserved, with its explicitly retrospective 15:05
threshold. PR #12 is confirmed merged at 64b89a5dc73a42fd062370178ffb62bb4f028187.

Main audit/checker source: 74fb628459a98db44364b05d92539afd1efc8364.
Policy SHA-256: b6f945f91fba991517b948fdbc29d7e8feed590e6d558f788ae690f165680f70.
Checker SHA-256: 99a7c3c4e2613b4db1309e73b6179d83bb506bad9c4b9494dd5e8cf00941029b.

Canonical heartbeat SHA-256: 93ed38f7afe0ca12c13ffa3933ce720b28e4615731dd22760059cc18fc3674f3.
Audit receipt SHA-256: 03892480c52e56dcd72d7d3327938e5b18484c5244ded805db648dbdcc6384a3.
[Rekor entry](https://rekor.sigstore.dev/api/v1/log/entries/108e9186e8c5677aebfaa61a896e4c8167429802037b7bafe94ff971dc87787387e87b4f11bd337d) integrated at
2026-11-13T23:01:23+00:00. Inclusion, pinned log key, author-key match,
readback, and separately fetched service-owned signed checkpoint/consistency proof
were verified. Proofs are in publication-attempt-2/. The first network publication
failure remains in publication/ and its dated annotation; the heartbeat bytes were
not changed for retry. Publication is late; no missed daily deadline is erased.

Heartbeat payload and audit receipt are publicly retained here; a hash-only Rekor
entry alone would be missing payload coverage. Rekor witnesses publication time
only. It does not certify arrival, execution, the findings, independent observation
or guaranteed availability. This monitor remains under the same owner/principal.

No main/policy/workflow/PR edits, reruns, comments or messages were performed.
Only this monitor-heartbeats/ publication and Rekor entry are authorized remote writes.
