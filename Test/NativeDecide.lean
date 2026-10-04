import Test.Harness

/-!
# `native_decide` over a lying implementation

`answer` is `false` to the kernel, but its compiled implementation returns `true`.
`native_decide` trusts compiled code, so `hostile_lie : answer = true` is accepted, while
`rfl` proves `answer = false`. Together: **a proof of `False` that builds in v4.22.0.**

Two independent defenses, both asserted:
* the gate: the only trace is the axiom `Lean.ofReduceBool`, which no profile allows;
* kernel replay: lean4checker cannot re-run compiled code and refuses this module
  (`scripts/check_kernel_replay.sh` requires that refusal).

`@[extern]` is the same attack class: compiled code the kernel never sees.
-/

open IntrospectionTwin.Test


def hostileFakeAnswer : Bool := true
@[implemented_by hostileFakeAnswer] def answer : Bool := false
theorem hostile_lie : answer = true := by native_decide
theorem hostile_truth : answer = false := rfl
theorem hostile_false : False := by
  have h := hostile_lie
  rw [hostile_truth] at h
  exact Bool.false_ne_true h

#expect_admitted hostile_truth under empty       -- the honest half is fine
#expect_rejected hostile_lie under classical
#expect_rejected hostile_false under empty
#expect_rejected hostile_false under constructive
#expect_rejected hostile_false under classical

