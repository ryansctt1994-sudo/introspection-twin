import IntrospectionTwin.Gate

/-!
# Admit: the spine's entry point

The spine never accepts a receipt's witness or status as evidence. It:
1. names the declaration from **its own** condition (`c.expectedClaim`), not from the receipt,
2. synthesizes the witness itself, in its own process,
3. reopens the receipt (dropping any status or witness it arrived with), promotes, and gates.

Step 1 matters: if the declaration were taken from the receipt, a clean trivial lemma could be
checked while the receipt claimed a different theorem.
-/

namespace IntrospectionTwin

open Lean

/-- The pure core of `admit`. -/
def admitCore (c : GateCondition) (r : Receipt) (w : ReplayWitness) : Bool :=
  evaluateGate (promoteToChecked r.reopen w) c

/-- Whatever the receipt arrived with, admission depends only on the fresh witness. -/
theorem admitCore_sound (c : GateCondition) (r : Receipt) (w : ReplayWitness)
    (h : admitCore c r w = true) :
    r.subject = c.expectedSubject ∧ r.claimId = c.expectedClaim ∧
    w.kernelAccepted = true ∧ w.isTheorem = true ∧ w.sorryCount = 0 ∧
    ∀ ax ∈ w.usedAxioms, ax ∈ c.allowedAxioms := by
  obtain ⟨hs, hsub, hcl, w', hw', hrest⟩ := evaluateGate_sound _ c h
  have hopen : r.reopen.status = .sketched ∨ r.reopen.status = .foreign_attestation :=
    Or.inl rfl
  have hp := (promote_open_iff r.reopen w hopen).mp hs
  -- the witness on the promoted receipt is exactly the fresh one
  have : w' = w := by
    unfold promoteToChecked at hw'
    simp only [Receipt.reopen] at hw' hp
    simp [hp] at hw'
    exact hw'.symm
  subst this
  refine ⟨?_, ?_, hrest⟩
  · rw [promote_preserves_subject] at hsub; exact hsub
  · rw [(promote_preserves_claim _ _).1] at hcl; exact hcl

/-- What the spine calls. The witness comes from the environment, for the condition's claim. -/
def admit (c : GateCondition) (r : Receipt) : CoreM Bool := do
  let w ← synthesizeWitness c.expectedClaim.toName
  return admitCore c r w

end IntrospectionTwin
