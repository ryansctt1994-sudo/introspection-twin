# IntrospectionTwin v0.1.1

> [!NOTE]
> **Portfolio evidence status (2026-10-06): E2 / W0 / O0.** Local builds, hostile tests, kernel replay, or externally reported reruns remain bounded evidence. No run is admitted as portfolio-independent reproduction unless its operator/environment/receipt satisfy the portfolio witness criteria.

Lean 4 receipt lattice and authority gate. v0.1 is an evolution of the MIT IntrospectionTwin v0,
which is itself an independent reimplementation of the kernel-receipt pattern from the
meta-introspector repositories. No code is imported from `lean-worker`, `aok`,
`introspector-llc` (AGPL-3.0) or `time` (GPL-3.0). MIT. Copyright Ryan Scott 2026.

**Toolchain:** `leanprover/lean4:v4.22.0` · **Build:** 0 errors, 0 warnings · **Library:** 31
hand-written theorems, no `sorry` (none of the 84 theorem constants depend on `sorryAx`)

## Claim, at the strength of its evidence

> Internally consistent along the verified promotion path. Receipts and witnesses cannot be
> constructed outside their defining files by ordinary code. The spine's entry point (`admit`)
> synthesizes its own witness and ignores any status a receipt arrives with. Soundness is
> conditional on honest kernel replay (lean4checker, outside the building process) and on
> in-memory evaluation: a serialized receipt is a claim, not evidence, until signed.

v0's "non-gameable" is withdrawn. The hostile suite below shows which attacks are now closed and
which one is closed **only** by kernel replay.

## Run it

```bash
lake build                                   # builds the library AND runs the hostile tests
LEAN4CHECKER=/path/to/lean4checker scripts/check_kernel_replay.sh       # ~10 s
FRESH=1 LEAN4CHECKER=... scripts/check_kernel_replay.sh                 # + all dependencies, ~5 min
```

`lake build` is the test run: every expectation is a command that fails the build on a wrong
verdict. lean4checker must be built at tag `v4.22.0` (instructions in the script).

## What changed from v0

| v0 | v0.1 | Why |
| --- | --- | --- |
| The **pasted draft** did not build on v4.22.0 (4 errors in `Receipt.lean`, 1 in `State.lean`). The actual `weaver/introspection-twin` tree had already been rewritten past these and did build (externally reported replay, 2026-10-04; not admitted as portfolio-independent evidence without a qualifying receipt) | Builds clean from zero | `rfl` can't see through `match r.status`; `<;> [a; b]` doesn't parse; `injection` fails on `do`-blocks |
| Public constructors: `{ status := .kernel_checked, .. }` was a valid receipt | `private mk` on `Receipt` and `ReplayWitness`; public `Receipt.sketch` / `.foreign` open receipts only | Forgery (proved by the test file failing to compile 5 ways) |
| Witness dropped on promotion | Retained (`witness : Option ReplayWitness`) | End-to-end theorem was unprovable |
| Gate checked the receipt's *declared* allowance | Gate checks the retained witness against the *condition's* allowance | `evaluateGate_sound` now needs no hypotheses |
| Spine consumed receipts | `admit`: claim named by the spine's own condition, witness synthesized in-process, receipt reopened | A checked receipt for a trivial lemma can't carry a different claim |
| `kernelAccepted` was the only witness flag | `+ isTheorem` | A Prop-valued `def` is not a proof claim |
| Axiom names compared as strings throughout | `sorryAx` detected as a `Name` | First step toward Name-typed axioms (open item 1) |
| Shape of `step`'s result only | `step_ok_iff`: success **iff** all six guards hold | Safety inversion is now a corollary |
| "Strictly monotonic" gas | Weakly monotone; strict iff `cost > 0`; budget never exceeded | The v0 summary overstated it |

## Theorems that matter

| Theorem | Says |
| --- | --- |
| `evaluateGate_sound` | Gate passes ⇒ kernel_checked, subject and claim match, and the witness shows: declaration exists, is a theorem, no sorry, every used axiom ∈ the **condition's** allowance |
| `admitCore_sound` | Admission depends only on the fresh witness, whatever status/witness the receipt arrived with |
| `checked_has_clean_witness` | Every receipt reachable through the public API that is kernel_checked carries a clean witness |
| `promote_open_iff` | An open receipt is promoted **iff** its witness is clean |
| `gate_rejects_disallowed_axiom` | One axiom outside the condition's allowance fails the gate, whatever the receipt declared |
| `step_ok_iff` / `step_safety_inversion` | `step` succeeds iff identity, sequence, tool, command, size, gas guards all hold |
| `step_within_budget` | Gas never exceeds the budget after a successful step |

Axioms used: gate/receipt/admit theorems are constructive (`propext`, `Quot.sound`); the step
theorems use `Classical.choice` (from `by_cases`/`omega`). Pinned in `Test/Hostile.lean`, and the
library's own theorems are run through its own gate there.

## Hostile suite (all pass)

| # | Attack | Result | Caught by |
| --- | --- | --- | --- |
| — | Positive controls: rfl / propext / Classical.em | Admitted exactly by the profiles that should admit them | — |
| 1 | `sorry` three dependencies deep | Rejected, every profile | gate (`sorryAx`) |
| 2 | `native_decide` over a lying `@[implemented_by]` | **Builds a proof of `False` in v4.22.0.** Rejected, every profile | gate (`Lean.ofReduceBool`) **and** kernel replay (refuses native code) |
| 3 | Custom `axiom hostile_bad : False` | Rejected (and the axiom itself, claimed as a theorem) | gate |
| 4 | `axiom «Quot.sound» : False` (spoofs an allowed name) | Rejected | gate, via `Name.toString` escaping — fragile, open item 1 |
| 5 | Prop-valued `def` | Rejected | `isTheorem` |
| 6 | Missing declaration | Rejected | `kernelAccepted` |
| 7 | Checked receipt for `ctl_rfl` presented for `hostile_s3`, or for another subject | Rejected; admitted for its own claim | `admit` reopens and re-checks |
| 8 | Forge receipt (struct instance, ⟨⟩, `with` update, `Receipt.mk`) or witness (⟨⟩) | Does not compile | private constructors |
| 9 | Harness given a wrong expectation | Build fails | harness non-vacuity |
| 10 | **Declaration added without kernel checking** (`debug.skipKernelTC`) | **In-process gate ADMITS it** (asserted). lean4checker refuses: *"'bypass_false' has type True but it is expected to have type False"* | **kernel replay only** |

Case 10 is the point: `collectAxioms` cannot see what the kernel never checked. Without
`check_kernel_replay.sh` in CI, the gate can be handed a proof of `False`.

## Kernel replay (author-reported until replayed on your side)

Run on the author's machine; the externally reported replay of 2026-10-04 confirmed `lake build` and
the hostile suite; it is not admitted as portfolio-independent evidence without a qualifying witness receipt but did not have lean4checker installed. `.github/workflows/ci.yml` runs the
same replay on your runner and uploads a record naming the commit and toolchain.

```
Honest modules (must replay):     10 / 10 replay ok   (discovered from the source tree)
Poisoned modules (must be refused): Bypass.KernelBypass  refused ('bypass_false' has type)
                                    Test.NativeDecide    refused (_nativeDecide_)
FRESH replay of IntrospectionTwin + Init + Lean: ok, 277 s
```

Modules are discovered from the tree, not listed by hand: a module missing from a list is a
module nobody checked.

## Integration rule for the spine

1. Call `admit c r` (in `CoreM`), never `evaluateGate` on a receipt from elsewhere.
2. Build `c.expectedClaim` from the spine's own policy, never from the receipt.
3. Run `check_kernel_replay.sh` in CI (`.github/workflows/ci.yml`) on the commit named in
   `c.expectedSubject`; a receipt from a build that didn't pass replay is not evidence.
4. Across a process or network boundary, receipts must be signed by a builder key, or the
   consumer re-runs `admit` against a replayed environment.

## Open items, in priority order

1. **Name-typed axioms.** `usedAxioms` and profiles are `List String`. Spoofing is caught today
   only because `Name.toString` escapes single-component names. Make them `List Name`.
2. **Commit binding.** Nothing proves the environment `admit` inspects was built from
   `subject.commitHash`. CI must rebuild at that commit with the pinned toolchain before replay.
3. **Signatures** for receipts that leave the process (Ed25519, builder key in the spine's trust root).
4. **Tamper-evident history.** `observationHistory` is ordered, not chained. Add `prevDigest`
   (SHA-256) per observation and prove `step` extends the chain.
5. **Reconstructed files.** `Twin/Bounds.lean` and `Twin/Observation.lean` are placeholders. The
   independent replay found one mismatch: the original observation field is `agentId`, not
   `agentIdentity`. v0.1.1 uses `agentId`. The original also carries `timestamp`, `binaryUri`,
   `exitCode`, `inputDigest`, `outputDigest`, which `step` does not read; a scratch build with
   those five fields added (stand-in types, `DecidableEq` dropped) kept every proof intact.
   Swap in the originals and run `lake build`; if `Bounds` also differs, Lean names the field.
6. **Privacy is not a security boundary against metaprograms.** Private names are reachable by
   metaprogramming. The control that matters is `admit` + replay, not visibility.
7. **Independent review.** Theorems and hostile tests were written by the same author in one
   session. The Lean kernel checks the proofs; it doesn't check that the theorems state the right
   things.

## Files

| Path | What |
| --- | --- |
| `IntrospectionTwin/Witness.lean` | `ReplayWitness` (private ctor), `synthesizeWitness`, `#introspect` |
| `IntrospectionTwin/Receipt.lean` | `Receipt` (private ctor), smart constructors, promotion, `Reachable` invariant |
| `IntrospectionTwin/Gate.lean` | `evaluateGate`, soundness, profiles |
| `IntrospectionTwin/Admit.lean` | `admit`: the spine's entry point |
| `IntrospectionTwin/Twin/*.lean` | State machine, `step_ok_iff` and corollaries |
| `Test/Harness.lean` | `#expect_admitted` / `#expect_rejected` |
| `Test/Hostile.lean` | Cases 1, 3–9, axiom pins, self-gating |
| `Test/NativeDecide.lean` | Case 2 (separate: replay refuses native code) |
| `Bypass/KernelBypass.lean` | Case 10 (never a default target) |
| `scripts/check_kernel_replay.sh` | lean4checker gate |
| `.github/workflows/ci.yml` | Build + hostile suite + replay on every push; FRESH replay nightly; replay record artifact |

`git log`: the v0 draft as pasted (not the `weaver/introspection-twin` tree), then v0.1, then
v0.1.1. `git diff HEAD~2` is the full review diff against the paste.
