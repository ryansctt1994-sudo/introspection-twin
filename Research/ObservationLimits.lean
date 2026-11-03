import IntrospectionTwin

/-!
# Observation Limits: two kinds of assurance failure

This file is a model-level formalization. It does NOT prove that any concrete
GitHub workflow or external witness implementation satisfies the model.

1. Erased evidence: observation maps different histories to the same value.
   No downstream deterministic decision can recover the distinction.
2. Ignored evidence: full records differ, but a lossy reporter maps them to
   identical results. A richer reporter can distinguish them.
3. Plumbing example: the exit status of a producer is masked if a pipeline
   returns only the final stage's status, even when the producer prints PASS.
4. Frozen payoff example: a fixed pair of outcome counts can change net sign
   under a different failure cost without any change in the decisions.
-/

namespace IntrospectionTwin.ObservationLimits

universe u v w

/-- One observation is insufficient to distinguish two histories with conflicting
required decisions. This is a pure reachability/information statement, not
an assertion about any particular monitor's implementation. -/
theorem indistinguishable_histories_cannot_satisfy_opposed_decisions
    {History : Type u} {Obs : Type v} {Verdict : Type w}
    (observe : History → Obs)
    (decideFrom : Obs → Verdict)
    (h₁ h₂ : History)
    (required₁ required₂ : Verdict)
    (sameObs : observe h₁ = observe h₂)
    (conflict : required₁ ≠ required₂) :
    ¬ (decideFrom (observe h₁) = required₁ ∧
       decideFrom (observe h₂) = required₂) := by
  intro bothCorrect
  apply conflict
  calc
    required₁ = decideFrom (observe h₁) := bothCorrect.1.symm
    _ = decideFrom (observe h₂) := congrArg decideFrom sameObs
    _ = required₂ := bothCorrect.2

/-- Different raw records may be collapsed by a lossy report. The difference
is still present upstream of the reporting function. -/
theorem lossy_reporting_hides_available_distinction
    {Raw : Type u} {Summary : Type v} {Verdict : Type w}
    (summarize : Raw → Summary) (judge : Summary → Verdict)
    (raw₁ raw₂ : Raw)
    (rawDifferent : raw₁ ≠ raw₂)
    (summariesEqual : summarize raw₁ = summarize raw₂) :
    raw₁ ≠ raw₂ ∧ judge (summarize raw₁) = judge (summarize raw₂) :=
  ⟨rawDifferent, congrArg judge summariesEqual⟩

/-- Toy histories for the *evidence-destroyed* class: the local endpoint
omits an effect bit. This does not claim a single bit handles arbitrary histories. -/
structure ToyHistory where
  effectOccurred : Bool
deriving Repr, DecidableEq

def localEndpoint (_ : ToyHistory) : Unit := ()
def independentBit (h : ToyHistory) : Bool := h.effectOccurred

def effectHistory : ToyHistory := ⟨true⟩
def noEffectHistory : ToyHistory := ⟨false⟩

theorem endpoint_collapses_but_independent_bit_separates :
    effectHistory ≠ noEffectHistory ∧
    localEndpoint effectHistory = localEndpoint noEffectHistory ∧
    independentBit effectHistory ≠ independentBit noEffectHistory := by
  decide

/-- Toy raw process record. The marker is untrusted program output, while
the exit code is a separate recorded observation. -/
structure ReplayEvent where
  exitCode : Nat
  printedPass : Bool
deriving Repr, DecidableEq

def verdictFromPrintedText (r : ReplayEvent) : Bool := r.printedPass
def verdictFromExitAndText (r : ReplayEvent) : Bool :=
  decide (r.exitCode = 0) && r.printedPass

def fakePass : ReplayEvent := ⟨23, true⟩
def actualPass : ReplayEvent := ⟨0, true⟩

theorem fake_pass_indistinguishable_to_text_only_reporter :
    fakePass ≠ actualPass ∧
    verdictFromPrintedText fakePass = verdictFromPrintedText actualPass := by
  decide

theorem combined_verdict_rejects_fake_pass :
    verdictFromExitAndText fakePass = false ∧
    verdictFromExitAndText actualPass = true := by
  decide

theorem nonzero_exit_cannot_be_reported_as_verified
    (r : ReplayEvent) (nonzero : r.exitCode ≠ 0) :
    verdictFromExitAndText r = false := by
  simp [verdictFromExitAndText, nonzero]

/-- Minimal two-command pipeline models (not a formal Bash semantics).
With pipefail, when the last command succeeds the producer status survives. -/
def finalStageOnly (_producerStatus teeStatus : Nat) : Nat := teeStatus
def twoStagePipefail (producerStatus teeStatus : Nat) : Nat :=
  if teeStatus = 0 then producerStatus else teeStatus

theorem pipefail_exposes_masked_failure
    (producerStatus : Nat) (failed : producerStatus ≠ 0) :
    finalStageOnly producerStatus 0 = 0 ∧
    twoStagePipefail producerStatus 0 = producerStatus ∧
    twoStagePipefail producerStatus 0 ≠ 0 := by
  simp [finalStageOnly, twoStagePipefail, failed]

/-- Fixed-decision payoff accounting: avoided failures earn the failure
cost, while missed successes each cost one reward unit. This is a
counterfactual rescore, NOT a claim about reoptimized monitor behavior. -/
def fixedDecisionNet (avoidedFailures missedSuccesses failureCost : Nat) : Int :=
  (failureCost : Int) * (avoidedFailures : Int) -
    (missedSuccesses : Int)

theorem frozen_counts_change_value_sign :
    fixedDecisionNet 9169 43531 4 < 0 ∧
    fixedDecisionNet 9169 43531 5 > 0 := by
  decide

#print axioms indistinguishable_histories_cannot_satisfy_opposed_decisions
#print axioms nonzero_exit_cannot_be_reported_as_verified
#print axioms pipefail_exposes_masked_failure
#print axioms frozen_counts_change_value_sign

end IntrospectionTwin.ObservationLimits
