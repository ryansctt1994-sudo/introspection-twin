import IntrospectionTwin.Receipt

/-!
# The authority gate

Pure query: `evaluateGate : Receipt → GateCondition → Bool`.

v0 checked the status flag and the receipt's *declared* allowance (`allowedAxioms`), never the
axioms actually used. The gate now checks the retained witness directly against the
condition's allowance, so `evaluateGate_sound` states the property the spine relies on with no
extra hypotheses.

The gate grades a receipt; it does not produce evidence. Use `Admit.admit`, which synthesizes
the witness itself, as the spine's entry point.
-/

namespace IntrospectionTwin

def emptyAxiomProfile : List String := []
def constructiveAxiomProfile : List String := ["propext", "Quot.sound"]
def classicalAxiomProfile : List String := ["propext", "Quot.sound", "Classical.choice"]

structure GateCondition where
  expectedSubject : Subject
  expectedClaim   : String
  allowedAxioms   : List String
deriving Repr, DecidableEq

def profileCovers (profile : List String) (receiptAllowed : List String) : Bool :=
  receiptAllowed.all (fun ax => profile.contains ax)

def evaluateGate (r : Receipt) (c : GateCondition) : Bool :=
  decide (r.status = .kernel_checked) &&
  decide (r.subject = c.expectedSubject) &&
  decide (r.claimId = c.expectedClaim) &&
  profileCovers c.allowedAxioms r.allowedAxioms &&
  (match r.witness with
   | some w => w.clean c.allowedAxioms
   | none => false)

/-! ## Soundness: what passing the gate means -/

/-- **End-to-end soundness.** If the gate passes, the receipt is kernel-checked for the expected
subject and claim, and carries a witness showing the declaration exists, is a theorem, uses no
`sorry`, and uses only axioms the *condition* allows. -/
theorem evaluateGate_sound (r : Receipt) (c : GateCondition) (h : evaluateGate r c = true) :
    r.status = .kernel_checked ∧
    r.subject = c.expectedSubject ∧
    r.claimId = c.expectedClaim ∧
    ∃ w, r.witness = some w ∧
      w.kernelAccepted = true ∧ w.isTheorem = true ∧ w.sorryCount = 0 ∧
      ∀ ax ∈ w.usedAxioms, ax ∈ c.allowedAxioms := by
  unfold evaluateGate at h
  simp only [Bool.and_eq_true, decide_eq_true_eq] at h
  obtain ⟨⟨⟨⟨hs, hsub⟩, hcl⟩, _⟩, hw⟩ := h
  refine ⟨hs, hsub, hcl, ?_⟩
  cases hr : r.witness with
  | none => simp [hr] at hw
  | some w =>
    simp only [hr] at hw
    exact ⟨w, rfl, (ReplayWitness.clean_spec w c.allowedAxioms).mp hw⟩

theorem gate_rejects_unverified (r : Receipt) (c : GateCondition)
    (h : r.status ≠ .kernel_checked) : evaluateGate r c = false := by
  unfold evaluateGate; simp [h]

theorem gate_rejects_no_witness (r : Receipt) (c : GateCondition)
    (h : r.witness = none) : evaluateGate r c = false := by
  unfold evaluateGate; simp [h]

theorem gate_requires_subject_match (r : Receipt) (c : GateCondition)
    (h : evaluateGate r c = true) : r.subject = c.expectedSubject :=
  (evaluateGate_sound r c h).2.1

theorem gate_rejects_promoted_sorry (r : Receipt) (w : ReplayWitness) (c : GateCondition)
    (hOpen : r.status = .sketched ∨ r.status = .foreign_attestation)
    (hSorry : w.sorryCount ≠ 0) :
    evaluateGate (promoteToChecked r w) c = false :=
  gate_rejects_unverified _ _ (promoted_sorry_not_checked r w hOpen hSorry)

/-- The axiom check is against the condition, not the receipt's own declaration: a witness
using an axiom outside `c.allowedAxioms` fails even if the receipt allowed it. -/
theorem gate_rejects_disallowed_axiom (r : Receipt) (c : GateCondition) (w : ReplayWitness)
    (hw : r.witness = some w) (ax : String) (hUsed : ax ∈ w.usedAxioms)
    (hNot : ax ∉ c.allowedAxioms) : evaluateGate r c = false := by
  cases h : evaluateGate r c
  · rfl
  · obtain ⟨_, _, _, w', hw', _, _, _, hall⟩ := evaluateGate_sound r c h
    rw [hw] at hw'; cases hw'
    exact absurd (hall ax hUsed) hNot

/-! ## Profile facts -/

theorem empty_rejects_constructive :
    profileCovers emptyAxiomProfile constructiveAxiomProfile = false := by decide
theorem constructive_covers_constructive :
    profileCovers constructiveAxiomProfile constructiveAxiomProfile = true := by decide
theorem constructive_rejects_choice :
    profileCovers constructiveAxiomProfile classicalAxiomProfile = false := by decide
theorem classical_covers_classical :
    profileCovers classicalAxiomProfile classicalAxiomProfile = true := by decide
theorem no_profile_allows_sorry :
    emptyAxiomProfile.contains "sorryAx" = false ∧
    constructiveAxiomProfile.contains "sorryAx" = false ∧
    classicalAxiomProfile.contains "sorryAx" = false := by decide
/-- `native_decide` trusts compiled code (`Lean.ofReduceBool`); no profile admits it. -/
theorem no_profile_allows_native_decide :
    emptyAxiomProfile.contains "Lean.ofReduceBool" = false ∧
    constructiveAxiomProfile.contains "Lean.ofReduceBool" = false ∧
    classicalAxiomProfile.contains "Lean.ofReduceBool" = false := by decide

end IntrospectionTwin
