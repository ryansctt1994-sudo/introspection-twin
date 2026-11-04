# EARR independence / controlling-principal lineage — proposed amendment v0.1
**DRAFT PROPOSAL. Not the official EARR v0.2 schema or a merged governance rule.**

## Origin of amendment
[EARR-IT-075](EARR_IT_075_SEVEN_FIELD_CANDIDATE_2026-11-03.md) documents the exact source and CI log of [run #75](https://github.com/ryansctt1994-sudo/introspection-twin/actions/runs/41660708557). Its seven provisional fields are factually populated but it was prepared by an AI assistant under the source repository owner's direction. **A different producing agent does not create an independent reviewing principal.**

**Disposition:** This is a first *worked example*, not a seven-field official-schema-conformant record, not a verified independent review, and not a completed EARR independent-witness milestone. No EARR acceptance is asserted.

## Proposed addition within the existing reviewer/independence field
Do **not** add an eighth top-level field unless the actual schema custodian explicitly approves a version change. Embed the following identity and lineage attributes into EARR's designated reviewer/independence field when its actual schema becomes available:

| Proposed attribute | Meaning | Run #75 provisional value |
|---|---|---|
| `claimant_agent` | Actor producing the original claim | Repository CI workflow / GitHub Actions |
| `claimant_principal` | Party whose interests/control the claim represents | Repository owner/controller |
| `preparer_agent` | Actor assembling the record | ChatGPT (GPT-6), owner-directed |
| `preparer_principal` | Party directing or controlling the preparer | **Same repository owner/controller** |
| `agent_relation` | Identity of agents relative to one another | `DIFFERENT_AGENT` |
| `principal_relation` | Independence of ultimate directing parties | `SAME_PRINCIPAL` |
| `evidence_custody_relation` | Who controls original source, retrieval and preserved bytes | `ORIGIN_PLATFORM_AND_CLAIMANT_CONTEXT`; no separately held reviewer copy |
| `conflict_disclosure` | Funding, commissioning, employment, control, conflicts | Owner-directed AI assistance |
| `review_class` | Decision after reviewing lineage and primary-source access | `DELEGATED_NON_INDEPENDENT` |
| `reviewer_independence_status` | Whether independence has been established | `NOT_MET` |
| `reviewer_attestation` | External reviewer signature/source/date, if any | `ABSENT` |

These are **proposed subfields**, not assertions about unknown official seven-field names.

## Decision rules (proposed and falsifiable)
1. `DIFFERENT_AGENT` alone cannot yield `INDEPENDENT`; an AI assistant acting for the same controlling principal remains `DELEGATED_NON_INDEPENDENT`.
2. `SAME_PRINCIPAL` gives `NOT_MET` for independent-review acceptance, irrespective of number of agents or LLM providers.
3. `DIFFERENT_PRINCIPAL` is **necessary but not sufficient**. Examine independence of appointment, control, material incentives/conflicts, unfiltered primary-evidence access, and preservation/custody.
4. If identity, appointment or custody is unknown, classify `UNVERIFIED`; do not claim independent witnessing.
5. Even an independent, primary-source reader establishes only what they personally inspected. **W0 remains** until any separate custody/witness qualification is performed; no unreviewed status promotion.
6. A missing evidence path, exit code or replay marker is `UNKNOWN` / `NOT_OBSERVED` for that field, not an invented zero or a PASS. Distinguish `requested` from `observed`.

## Negative and positive acceptance fixtures
| Fixture | Observed relationship | Expected classification |
|---|---|---|
| A | Same agent and same principal | `SELF_REVIEW`; independent = no |
| B — run #75 preparer | Distinct AI agent, same controlling principal | `DELEGATED_NON_INDEPENDENT`; independent = no |
| C | Different agent/principal, reviewer merely copies owner's proposed verdict | `UNVERIFIED`; no independent raw observation |
| D | Different principal, identified reviewer, direct source read, conflict assessment, signed dated notes, separate evidence custody | `ELIGIBLE_FOR_INDEPENDENT_ASSESSMENT`, subject to review; not automatic W1 |
| E | Principal relationship unknown or controlled reviewer cannot be excluded | `UNVERIFIED`; no promotion |

A validator or reviewer protocol conforming to this *proposed* amendment must reject any case where Fixture B is marked `INDEPENDENT` and must not infer independent witness status from Fixture D without actual custody verification.

## Source/claim separation
**Observed:** In all thirty retrieved scheduled-run logs (October 5–November 3, 2026), direct `scripts/check_kernel_replay.sh` invocation returned `Permission denied`, no final `KERNEL REPLAY: PASS` appeared, the result field was blank, and GitHub reported success. See [Annex A](EARR_IT_075_SEVEN_FIELD_CANDIDATE_2026-11-03.md#annex-a--complete-scheduled-run-log-census).

**Bounded inference:** the scheduled verification step did not successfully execute in any of those thirty runs. Does **not** establish anything beyond the retrieved scheduled history; does not disprove the Lean build or theorems.

**Governance gap:** a correct externally sourced case prepared under the same principal is a useful worked example but does not satisfy a requirement for independent preparation.

## Required independent closure
Give an external reviewer [the conclusion-blind source packet](REVIEWER_FIRST_RUN_075.md), not the claimant's case verdict first. Record reviewer name/affiliation, actual principal, conflict disclosure, direct access method, UTC inspection time, original excerpts and source hashes. Compare their report against EARR-IT-075 **after** their independent record is fixed. An external reader is not automatically a W1 qualified independent witness.

**Authority unchanged:** E2 / W0 / O0 — HOLD. No official EARR contract amendment is accepted until approved by its actual custodian.
