# EARR-IT-075 — seven-field evidence record candidate (NON-CONFORMANT UNTIL SCHEMA IS PROVIDED)

**Status: FIRST WORKED EXAMPLE / DELEGATED NON-CLAIMANT AGENT UNDER THE SAME PRINCIPAL / INDEPENDENCE CONDITION NOT MET / NOT FORMALLY EARR-ACCEPTED.**

The authoritative EARR v0.2 seven-field schema, required field names and submission endpoint were **not present in the accessible source records**. The **seven fields below are a provisional working mapping, NOT a representation of Richard's official EARR contract**. They are completed factual entries for exactly one run. A human reviewer must independently inspect the GitHub records and map them to the actual form before claiming EARR milestone acceptance.

## Field 1 — Case identifier and bounded question
**Record:** EARR-IT-075; repository [introspection-twin](https://github.com/ryansctt1994-sudo/introspection-twin); GitHub Actions [scheduled run #75 / 41660708557](https://github.com/ryansctt1994-sudo/introspection-twin/actions/runs/41660708557), job 126002819397 (build-and-replay), 2026-11-03. **Question:** Did the green run execute and complete its scheduled fresh independent Lean kernel replay?

## Field 2 — Claimant, preparer and independence disclosure
**Claim source:** GitHub Actions status and the repository's replay workflow/record; underlying CI configuration maintained in the repository controlled by ryansctt1994-sudo. **Evidence preparer:** ChatGPT (GPT-6), inspecting source GitHub job data on 2026-11-03, distinct from the claimant **as an agent** but operating at the repository owner's direction **under the same controlling principal**. **Proposed independence classification:** `agent_relation=DIFFERENT_AGENT`, `principal_relation=SAME_PRINCIPAL`, `review_class=DELEGATED_NON_INDEPENDENT`, `independent_witness=false`. **The independence condition is NOT MET**, not merely unverified. The preparer has no independent authority, separate commissioning principal, or independently controlled evidence custody. Richard did not author or sign this entry. No external adjudication is claimed. See [EARR independence amendment proposal](EARR_INDEPENDENCE_AMENDMENT_PROPOSAL_2026-11-03.md).

## Field 3 — Immutable object and custody references
- GitHub workflow run ID: **41660708557**; run number **75**; event **schedule**; started **2026-11-03T15:08:14Z**; concluded **success**.
- Actual source commit: **fc952ad8c4d282813436bbce24d8d4ec0ee5f4e2**.
- Source Git tree: **f88f10a6bc69ca73c78225d3120b4eb6986c991f**.
- Toolchain claimed in record: **leanprover/lean4:v4.22.0**.
- Job log source: https://github.com/ryansctt1994-sudo/introspection-twin/actions/runs/41660708557 ; job 126002819397.
- Evidence custody: GitHub-hosted job log and workflow metadata. This entry includes quotes and links, not a separately signed, immutable third-party evidence bundle. The stored artifact file in the run was not cryptographically authenticated by the preparer.

## Field 4 — Reported result / claimed outcome
GitHub reported workflow and replay step **success**. The workflow configured FRESH=1 (scheduled event) and wrote a record field **fresh: true**. The record's **result:** field had **no value**. **fresh: true denotes requested mode, NOT independently observed replay completion.**

## Field 5 — Direct primary observations (verbatim log excerpts)
Job log:
- 2026-11-03T15:08:41.7164629Z ##[group]Run scripts/check_kernel_replay.sh | tee replay.log
- 2026-11-03T15:08:41.7254407Z /home/runner/work/_temp/4647a7b2-a052-4bd5-ad96-d365b838cae7.sh: line 1: scripts/check_kernel_replay.sh: Permission denied
- 2026-11-03T15:08:41.7523156Z fresh:     true
- 2026-11-03T15:08:41.7523416Z result:

No kernel-replay PASS sentinel appears in the inspected log. The raw record does **not** expose the numeric replay-process exit status. Do not infer one from the successful final GitHub job conclusion.

## Field 6 — Discrepancy and narrow verdict
**Verdict: FALSE-GREEN REPLAY ATTESTATION / SCHEDULED REPLAY DID NOT EXECUTE SUCCESSFULLY IN THIS RUN.** The script invocation was blocked by permissions, and the pipeline (without pipefail) allowed the successful tee command to mask that failure. A record of intent and an empty result were presented under a green workflow outcome. Separate Lean compilation and checker build steps were reported successful; this verdict does not disprove those builds or any Lean theorem. The incident is an evidence-reporting/failure-propagation defect, not an observed malicious modification.

## Field 7 — Corrective work, reproduction requirements and acceptance
- Existing fail-closed candidate: [PR #7](https://github.com/ryansctt1994-sudo/introspection-twin/pull/7), which invokes through Bash, enables pipefail, checks exact final marker, and tests negative controls. Its successful candidate CI is NOT a replay of this scheduled source commit and did not validate scheduled fresh mode.
- Proposed independent, observed-status receipt upgrade: stacked review branch **repair/replay-observed-receipt-20261103**; the gate records actual replay and tee exit statuses, source commit/tree and separate fresh-requested/fresh-observed fields **only after evaluation**.
- Review gate: independent operator inspects exact GitHub records without first adopting this verdict; compares output, recorded exit, and actual replay evidence; reruns a scheduled FRESH=1 workflow on an authorized merged source commit. Keep EARR acceptance, witness status and production authority withheld until the official schema and independent review are met.
- **Milestone disposition:** First worked EARR example = YES (provisional seven-field mapping, grounded in primary logs). Required independent preparer/witness = NO (different agent, same principal). Official seven-field schema conformance = UNVERIFIED. External independent review = NOT PERFORMED. **E2 / W0 / O0 — HOLD; no promotion.**

---

## Annex A — complete scheduled-run log census

**Across every scheduled run in the available 30-run history (October 5–November 3), the replay invocation failed; all thirty jobs reported green.** From all 30 scheduled runs returned by GitHub for this repository on 2026-11-03, raw job logs were individually inspected. Every one showed a permission-denied replay invocation, an empty record result, and no kernel PASS sentinel, despite GitHub job success. These are **30 failed replay-verification attestations**, not necessarily failed Lean builds.

| Date UTC | Scheduled run ID | GitHub conclusion | Raw replay findings |
|---|---|---|---|
| 2026-10-05 | [37337500569](https://github.com/ryansctt1994-sudo/introspection-twin/actions/runs/37337500569) | success | Permission denied; empty result; no replay PASS |
| 2026-10-06 | [37476969367](https://github.com/ryansctt1994-sudo/introspection-twin/actions/runs/37476969367) | success | Permission denied; empty result; no replay PASS |
| 2026-10-07 | [37637311633](https://github.com/ryansctt1994-sudo/introspection-twin/actions/runs/37637311633) | success | Permission denied; empty result; no replay PASS |
| 2026-10-08 | [37793701710](https://github.com/ryansctt1994-sudo/introspection-twin/actions/runs/37793701710) | success | Permission denied; empty result; no replay PASS |
| 2026-10-09 | [37943690332](https://github.com/ryansctt1994-sudo/introspection-twin/actions/runs/37943690332) | success | Permission denied; empty result; no replay PASS |
| 2026-10-10 | [38056777607](https://github.com/ryansctt1994-sudo/introspection-twin/actions/runs/38056777607) | success | Permission denied; empty result; no replay PASS |
| 2026-10-11 | [38145619947](https://github.com/ryansctt1994-sudo/introspection-twin/actions/runs/38145619947) | success | Permission denied; empty result; no replay PASS |
| 2026-10-12 | [38279484625](https://github.com/ryansctt1994-sudo/introspection-twin/actions/runs/38279484625) | success | Permission denied; empty result; no replay PASS |
| 2026-10-13 | [38418791818](https://github.com/ryansctt1994-sudo/introspection-twin/actions/runs/38418791818) | success | Permission denied; empty result; no replay PASS |
| 2026-10-14 | [38567213233](https://github.com/ryansctt1994-sudo/introspection-twin/actions/runs/38567213233) | success | Permission denied; empty result; no replay PASS |
| 2026-10-15 | [38736363027](https://github.com/ryansctt1994-sudo/introspection-twin/actions/runs/38736363027) | success | Permission denied; empty result; no replay PASS |
| 2026-10-16 | [38900457509](https://github.com/ryansctt1994-sudo/introspection-twin/actions/runs/38900457509) | success | Permission denied; empty result; no replay PASS |
| 2026-10-17 | [39029421407](https://github.com/ryansctt1994-sudo/introspection-twin/actions/runs/39029421407) | success | Permission denied; empty result; no replay PASS |
| 2026-10-18 | [39125746704](https://github.com/ryansctt1994-sudo/introspection-twin/actions/runs/39125746704) | success | Permission denied; empty result; no replay PASS |
| 2026-10-19 | [39271184650](https://github.com/ryansctt1994-sudo/introspection-twin/actions/runs/39271184650) | success | Permission denied; empty result; no replay PASS |
| 2026-10-20 | [39424526947](https://github.com/ryansctt1994-sudo/introspection-twin/actions/runs/39424526947) | success | Permission denied; empty result; no replay PASS |
| 2026-10-21 | [39603664628](https://github.com/ryansctt1994-sudo/introspection-twin/actions/runs/39603664628) | success | Permission denied; empty result; no replay PASS |
| 2026-10-22 | [39782830478](https://github.com/ryansctt1994-sudo/introspection-twin/actions/runs/39782830478) | success | Permission denied; empty result; no replay PASS |
| 2026-10-23 | [39954780361](https://github.com/ryansctt1994-sudo/introspection-twin/actions/runs/39954780361) | success | Permission denied; empty result; no replay PASS |
| 2026-10-24 | [40092170173](https://github.com/ryansctt1994-sudo/introspection-twin/actions/runs/40092170173) | success | Permission denied; empty result; no replay PASS |
| 2026-10-25 | [40193705109](https://github.com/ryansctt1994-sudo/introspection-twin/actions/runs/40193705109) | success | Permission denied; empty result; no replay PASS |
| 2026-10-26 | [40338072668](https://github.com/ryansctt1994-sudo/introspection-twin/actions/runs/40338072668) | success | Permission denied; empty result; no replay PASS |
| 2026-10-27 | [40510062411](https://github.com/ryansctt1994-sudo/introspection-twin/actions/runs/40510062411) | success | Permission denied; empty result; no replay PASS |
| 2026-10-28 | [40701890903](https://github.com/ryansctt1994-sudo/introspection-twin/actions/runs/40701890903) | success | Permission denied; empty result; no replay PASS |
| 2026-10-29 | [40890505069](https://github.com/ryansctt1994-sudo/introspection-twin/actions/runs/40890505069) | success | Permission denied; empty result; no replay PASS |
| 2026-10-30 | [41069327725](https://github.com/ryansctt1994-sudo/introspection-twin/actions/runs/41069327725) | success | Permission denied; empty result; no replay PASS |
| 2026-10-31 | [41206548509](https://github.com/ryansctt1994-sudo/introspection-twin/actions/runs/41206548509) | success | Permission denied; empty result; no replay PASS |
| 2026-11-01 | [41315366519](https://github.com/ryansctt1994-sudo/introspection-twin/actions/runs/41315366519) | success | Permission denied; empty result; no replay PASS |
| 2026-11-02 | [41487633318](https://github.com/ryansctt1994-sudo/introspection-twin/actions/runs/41487633318) | success | Permission denied; empty result; no replay PASS |
| 2026-11-03 | [41660708557](https://github.com/ryansctt1994-sudo/introspection-twin/actions/runs/41660708557) | success | Permission denied; empty result; no replay PASS |

Two older runs (October 5–6) used source commit fcc63c085497a26bf1468294a3df53fdd6a56c9f; October 7 through November 3 used fc952ad8c4d282813436bbce24d8d4ec0ee5f4e2. Counts refer to returned scheduled runs, not push/PR-triggered jobs. No claim is made about runs outside this returned set.

**Exact EARR compliance: NOT VERIFIED. Independent witness: NONE.**