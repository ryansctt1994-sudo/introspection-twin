import Test.Harness

/-!
# Hostile test suite

Every case runs the spine's real entry point (`admit`). A wrong verdict is a build error.

* **Positive controls** first: a gate that rejects everything would pass every hostile case,
  so each profile must also be shown to ADMIT what it should.
* **Hostile cases**: deep sorry, a custom axiom, an axiom whose name spoofs an allowed one, a
  Prop-valued `def`, a missing declaration, a stale checked receipt, forged receipts and
  witnesses.
* **Harness non-vacuity**: a wrong expectation must fail.

Two cases live elsewhere. `native_decide` over a lying `implemented_by` (a real proof of `False`
in v4.22.0) is `Test/NativeDecide.lean`, because kernel replay refuses native code. A declaration
added without kernel checking would poison the `.olean` files; it is `Bypass/KernelBypass.lean`,
built only by `scripts/check_kernel_replay.sh`.
-/

open IntrospectionTwin IntrospectionTwin.Test

/-! ## Positive controls: each profile admits what it should -/

theorem ctl_rfl : 2 + 2 = 4 := rfl
theorem ctl_propext (p q : Prop) (h : p ↔ q) : p = q := propext h
theorem ctl_em (p : Prop) : p ∨ ¬p := Classical.em p

#expect_admitted ctl_rfl under empty
#expect_admitted ctl_rfl under constructive
#expect_admitted ctl_rfl under classical
#expect_rejected ctl_propext under empty
#expect_admitted ctl_propext under constructive
#expect_rejected ctl_em under constructive
#expect_admitted ctl_em under classical

/-! ## 1. `sorry` three dependencies deep -/

/-- warning: declaration uses 'sorry' -/
#guard_msgs in
theorem hostile_s0 : 1 = 1 := sorry
theorem hostile_s1 : 1 = 1 := hostile_s0
theorem hostile_s2 : 1 = 1 := hostile_s1
theorem hostile_s3 : 1 = 1 := hostile_s2

#expect_rejected hostile_s3 under empty
#expect_rejected hostile_s3 under constructive
#expect_rejected hostile_s3 under classical

/-! ## 2. `native_decide` over a lying implementation: see `Test/NativeDecide.lean`

It lives in its own module because kernel replay (lean4checker) cannot re-run compiled code
and refuses any module containing a `native_decide` proof. The gate rejects it too. -/

/-! ## 3. A custom axiom -/

axiom hostile_bad : False
theorem hostile_ax : 1 = 2 := hostile_bad.elim

#expect_rejected hostile_ax under classical
#expect_rejected hostile_bad under classical     -- the axiom itself, claimed as a theorem

/-! ## 4. An axiom whose name spoofs an allowed one

`«Quot.sound»` is a single-component name that prints like the real two-component
`Quot.sound`. It is rejected because `Name.toString` escapes it as `«Quot.sound»`. That is
correct but fragile: axiom identity should be compared as `Name`, not `String`
(see README, open items). -/

axiom «Quot.sound» : False
theorem hostile_spoof : 1 = 2 := «Quot.sound».elim

#expect_rejected hostile_spoof under constructive
#expect_rejected hostile_spoof under classical

/-! ## 5. A Prop-valued `def`, not a theorem -/

def hostile_def : 1 = 1 := rfl
#expect_rejected hostile_def under classical

/-! ## 6. A declaration that does not exist -/

#expect_rejected hostile_missing under classical

/-! ## 7. A stale checked receipt cannot carry a different claim through

A receipt honestly promoted for `ctl_rfl` is `kernel_checked`. Presented to a condition that
expects `hostile_s3`, `admit` reopens it and re-checks `hostile_s3` itself: rejected. -/

open Lean Elab Command in
elab "#test_stale_receipt" : command => do
  let honest := Receipt.sketch testSubject .kernelTrace "ctl_rfl" "" "test" classicalAxiomProfile
  let w ← liftCoreM (synthesizeWitness `ctl_rfl)
  let checked := promoteToChecked honest w
  unless checked.status == .kernel_checked do throwError "setup: honest promotion failed"
  let swapped : GateCondition := ⟨testSubject, "hostile_s3", classicalAxiomProfile⟩
  if ← liftCoreM (admit swapped checked) then
    throwError "a checked receipt for ctl_rfl was admitted for hostile_s3"
  let otherSubject : GateCondition :=
    ⟨⟨"local://elsewhere", "other", "leanprover/lean4:v4.22.0"⟩, "ctl_rfl", classicalAxiomProfile⟩
  if ← liftCoreM (admit otherSubject checked) then
    throwError "a receipt was admitted for a different subject"
  let same : GateCondition := ⟨testSubject, "ctl_rfl", classicalAxiomProfile⟩
  unless ← liftCoreM (admit same checked) do
    throwError "control: the honest receipt should be admitted for its own claim"

#test_stale_receipt

/-! ## 8. Forgery does not compile outside the defining files -/

def hostileSubject : Subject := ⟨"a", "b", "c"⟩

/-- error: invalid {...} notation, constructor for 'IntrospectionTwin.Receipt' is marked as private -/
#guard_msgs in
def forgedStructInstance : Receipt :=
  { subject := hostileSubject, lens := .kernelTrace, claimId := "x", evidenceDigest := "", producer := "me", allowedAxioms := [], witness := none, status := .kernel_checked }

/-- error: invalid ⟨...⟩ notation, constructor for `IntrospectionTwin.Receipt` is marked as private -/
#guard_msgs in
def forgedAnonymous : Receipt := ⟨hostileSubject, .kernelTrace, "x", "", "me", [], none, .kernel_checked⟩

/-- error: invalid {...} notation, constructor for 'IntrospectionTwin.Receipt' is marked as private -/
#guard_msgs in
def forgedUpdate : Receipt :=
  { Receipt.sketch hostileSubject .kernelTrace "x" "" "me" [] with status := .kernel_checked }

/-- error: unknown constant 'IntrospectionTwin.Receipt.mk' -/
#guard_msgs in
def forgedByName := Receipt.mk hostileSubject .kernelTrace "x" "" "me" [] none .kernel_checked

/-- error: invalid ⟨...⟩ notation, constructor for `IntrospectionTwin.ReplayWitness` is marked as private -/
#guard_msgs in
def forgedWitness : ReplayWitness := ⟨true, true, 0, []⟩

/-! ## 9. The harness itself can fail -/

/--
error: expected ADMITTED but gate said REJECTED for hostile_ax under classical (witness: kernel=true, theorem=true, sorry=0, axioms=[hostile_bad])
-/
#guard_msgs in
#expect_admitted hostile_ax under classical

/--
error: expected REJECTED but gate said ADMITTED for ctl_rfl under empty (witness: kernel=true, theorem=true, sorry=0, axioms=[])
-/
#guard_msgs in
#expect_rejected ctl_rfl under empty

/-! ## 10. The library's own theorems, pinned and run through its own gate

The gate and receipt theorems are constructive. The step theorems use `Classical.choice`
(from `by_cases`/`omega`): standard classical Lean, but stated here rather than hidden. -/

#expect_admitted IntrospectionTwin.evaluateGate_sound under constructive
#expect_admitted IntrospectionTwin.admitCore_sound under constructive
#expect_admitted IntrospectionTwin.checked_has_clean_witness under constructive
#expect_rejected IntrospectionTwin.Twin.step_safety_inversion under constructive
#expect_admitted IntrospectionTwin.Twin.step_safety_inversion under classical


/-- info: 'IntrospectionTwin.evaluateGate_sound' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in
#print axioms evaluateGate_sound

/-- info: 'IntrospectionTwin.admitCore_sound' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in
#print axioms admitCore_sound

/-- info: 'IntrospectionTwin.checked_has_clean_witness' depends on axioms: [propext] -/
#guard_msgs in
#print axioms checked_has_clean_witness

/-- info: 'IntrospectionTwin.Twin.step_safety_inversion' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms IntrospectionTwin.Twin.step_safety_inversion
