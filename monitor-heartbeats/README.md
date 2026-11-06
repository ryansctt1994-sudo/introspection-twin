# Replay monitor public heartbeats

This branch contains public monitor reports, timestamp inventories, cadence and
Rekor publication proofs. GitHub main, Actions workflows and replay policies are
read-only. Report commits use `[skip ci]`; they do not rerun Actions.

Raw fields `intended_fire_time` and `actual_arrival_time` appear separately for
every recorded execution. The inventory preserves earlier receipts via hashes;
an unknown intended time remains null. For GitHub runs, arrival is API `created_at`.
For the external monitor, arrival is the first observed assistant audit clock
reading. Scheduler-reported last-run time is a separate field: it is not proof
of queue arrival, on-time execution or delivery. Detailed scheduler history is
unavailable. Earlier receipts and misses have not been overwritten.

For the November 6 audit:

- Intended fire: `2026-11-06T16:57:00Z`
- First observed audit execution: `2026-11-06T23:22:24Z`
- Difference: **23124 seconds / 6h25m24s**
- Scheduler reported last-run field: `2026-11-06T23:22:17.793410+00:00`

The first heartbeat is **retrospective bootstrap**, not an on-time observation or
a retroactively precommitted publication deadline. From **November 7**, the public
cadence is daily 16:57 UTC and publication by **17:17 UTC**. A missing heartbeat
past that deadline, or a later Rekor integration time, is a finding even if the
audit eventually succeeds. No scheduled configuration is evidence of execution.
An outsider can list the date folder and compare signed Rekor publication times
against the frozen cadence without asking the author. This does not automatically
notify anyone or provide an independent always-available observer.

The cadence is pinned by SHA-256
`6f9932dab0e6e165f40c9109ea8d0304b8443702ff8a5c17281b37262aef517f`.
The author key's DER SHA-256 is
`584ac012126b547a436d2fe27aff86a67ead99f56f66384d2498cd09c7b63c7f`.
Changing either needs a visible transition; no new key silently replaces a lost
one. The key is controlled by the same principal as the monitor. No private key
is in this branch.

Rekor stores a digest, so the full canonical heartbeat JSON is published here.
For each heartbeat, fetch that JSON, `rekor-entry.json` and `rekor-public-key.pem`
from its publication folder and run from `monitor-heartbeats`:

```sh
python -m publisher.external_anchor PATH/heartbeat.json PATH/rekor-entry.json PATH/rekor-public-key.pem
```

Install `cryptography==50.0.0` in a virtual environment first. Pin the public
publisher/cadence values from the bootstrap reference, compare the heartbeat
SHA-256 to the Rekor digest, verify signatures/inclusion, and calculate the
UTC difference from the two raw fields. A new checker may also fetch Rekor's own
checkpoint and verify consistency; full TUF-chain verification is not claimed.

The log externally witnesses publication at its signed integration time.
Reported arrival times, execution, findings and cadence remain author statements;
Rekor does not prove the monitor ran at its claimed time or that any result is
true. A stall becomes an externally checkable publication gap under this cadence.
This same-principal publication mechanism is not independent witnessing, guaranteed
availability, or protection against all log split views. A deleted/unavailable
public payload is missing coverage, never a healthy heartbeat.

The bootstrap heartbeat was additionally checked against Rekor's own signed live
checkpoint, fetched directly at 23:45:15 UTC. Its consistency proof connects tree
size 3604542209 to 3604572416. Raw responses are in the run's publication/live-log
folder. To make a fresh independent data-route check, use the included
`python -m publisher.live_log --manifest PATH/heartbeat.json --entry PATH/rekor-entry.json --checkpoint-sha256 EXPECTED_HEARTBEAT_DIGEST --output NEW_DIRECTORY`.
This is the same-principal verifier/data route, not another human witness.
