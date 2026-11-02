# Formalization Audit — Flagship Verdict 001
**Audited declaration:** `IntrospectionTwin.evaluateGate_sound`  
**Repository:** `ryansctt1994-sudo/introspection-twin`  
**Source commit:** `60881a01be683f0189a80c6cb31eddf1d953410c` (repair PR #7; not merged into `main`)  
**Lean:** `leanprover/lean4:v4.22.0`  
**Auditor:** owner-assisted, not an independent audit  
**Disposition:** **PASS — theorem's stated structural implication; NOT ESTABLISHED — independently kernel-checked proof or source/commit authenticity as a consequence of this theorem alone.**

## 1. Theorem / exact scope

`IntrospectionTwin/Gate.lean` states: whenever `evaluateGate r c = true`, (i) `r.status = .kernel_checked`, (ii) subject and claim match the supplied condition, and (iii) a retained witness `w` exists with `w.kernelAccepted = true`, `w.isTheorem = true`, `w.sorryCount = 0` and every `w.usedAxioms` member on the condition's allowlist.

This is a theorem **about fields of in-memory `Receipt`/`ReplayWitness` values**. It is not a theorem that Lean's kernel checked the declaration, that those fields faithfully describe it, that `subject.commitHash` identifies the current compiled environment, or that a deployed authorization broker enforced a decision. `Gate.lean` calls the theorem “End-to-end soundness”; this is broader language than its statement proves unless one explicitly supplies the trust assumptions on witness construction and kernel replay.

`IntrospectionTwin/Witness.lean` defines `kernelAccepted` operationally as **a declaration being found** by `env.find?`, not a kernel replay result. This is the central assumption gap and it is directly testable.

## 2. Reproduction & axiom trace

**Original checked code** (Git object IDs):

- `IntrospectionTwin/Gate.lean`: `782fc5cbe0231406cb82278c915dbefc2efec9ad`
- `IntrospectionTwin/Witness.lean`: `f9e2c16248595849ab8e2ebc089b5487f9a84f3f`
- `Test/Hostile.lean`: `327cb0b1125e7ef44911c670d322178d56365d7c`
- `Bypass/KernelBypass.lean`: `7f8b6cad5bc90121744f291062bf21e6ce9bf7fa`
- `lean-toolchain`: `6ac6d4c4ce9f2e1f08f2ca97b60a31cc39de23ef`

A hosted November 2 repaired workflow [#41524819549](https://github.com/ryansctt1994-sudo/introspection-twin/actions/runs/41524819549) records a passing library/hostile-suite build and separate-process replay of ten expected honest modules plus refusal of the two poisoned modules. Its source files above match the audited commit. **This is origin-hosted CI evidence, not this auditor's independent local `lake build`.** A separate dedicated audit job must show the direct printed axiom line before this sample is called axiom-output reproduced.

Reproduce with Lean 4.22.0:

```bash
 git clone https://github.com/ryansctt1994-sudo/introspection-twin.git
 cd introspection-twin
 git checkout 60881a01be683f0189a80c6cb31eddf1d953410c
 lake build
 lake env lean Audits/Flagship.lean
```

`Test/Hostile.lean` contains a compile-enforced `#guard_msgs` assertion expecting:

```text
'IntrospectionTwin.evaluateGate_sound' depends on axioms: [propext, Quot.sound]
```

This is the expected **transitive axiom dependency** output for this declaration. Neither `sorryAx` nor `Classical.choice` is in that expected list. The exact hosted raw output of `Audits/Flagship.lean`, when available, is the direct evidence record; absent it, the above is a guarded source expectation, not an independently reproduced measurement.

## 3. Adversarial zoo / attempted falsification

The pre-existing hostile suite `Test/Hostile.lean`, `Test/NativeDecide.lean`, and `Bypass/KernelBypass.lean` supplies concrete controls rather than hypothetical attack names:

| Fixture | Observable result / limit |
|---|---|
| Honest `rfl`, `propext`, excluded middle | Positive admissions only under appropriate profiles; rejects-everything gate fails |
| Three-deep `sorry` dependency | Rejected by gate under every profile |
| Custom false axiom | Rejected; distinguishes theorem from axiom |
| `«Quot.sound»` spoofed one-component name | Rejected in test; **name comparison remains string-based**, relies on escaping behavior |
| Prop-valued `def`, missing declaration, forged ordinary constructor | Rejected, or fails compilation |
| Cross-claim/subject checked receipt | `admit` reopens and recomputes the witness; test rejects mismatch |
| `native_decide` with lying compiled implementation | Adversarial false theorem builds but gate rejects `Lean.ofReduceBool`; external checker refuses module |
| `debug.skipKernelTC` poisoned theorem `bypass_false : False` | **In-process gate ADMITTED an invalid declaration.** Separate-process `lean4checker` refuses poisoned module. |

The last row falsifies any interpretation of `evaluateGate_sound` as a standalone guarantee of kernel validity. The theorem's own statement remains true: `kernelAccepted` is an environment-presence field, not an independently checked certificate.

Separate CI failure/control evidence, not theorem proof: [October 25 false-green #40193705109](https://github.com/ryansctt1994-sudo/introspection-twin/actions/runs/40193705109); [November 2 deliberately red #41524615205](https://github.com/ryansctt1994-sudo/introspection-twin/actions/runs/41524615205); [November 2 corrected green #41524819549](https://github.com/ryansctt1994-sudo/introspection-twin/actions/runs/41524819549). These show execution/reporting boundaries, not a mathematical counterexample to the theorem.

## Claim-to-theorem verdict

| Proposed claim | Verdict | Ground |
|---|---|---|
| A passing `evaluateGate` entails the stated receipt fields and a clean retained witness | **SUPPORTED** by theorem's formal statement, conditional on a genuine successful Lean build/replay |
| A passing `evaluateGate` alone proves an independently kernel-validated declaration | **NOT ESTABLISHED**; unchecked-kernel counterexample falsifies this stronger statement |
| A passing receipt proves the compiled declaration corresponds to the listed commit | **NOT ESTABLISHED**; `commitHash` string is checked for equality only, not bound to source/env |
| A receipt proves signed provenance or a deployed action was authorized/executed | **NOT ESTABLISHED**; neither appears in theorem's conclusion |

### Release note

**Owner-assisted source audit, public draft.** Hosted build and poison-refusal evidence exists; a dedicated hosted direct axiom-print check is part of this sample's acceptance; independent operator qualification remains outstanding. `E2 · W0 · O0 — HOLD` is unchanged. Do not interpret this report as a security certification or as approval to deploy the system.