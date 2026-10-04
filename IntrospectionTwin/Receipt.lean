import IntrospectionTwin.Witness

/-!
# Receipts

**Construction is private to this file.** Outside it, a receipt can only be:
* opened with `Receipt.sketch` or `Receipt.foreign` (status `sketched` / `foreign_attestation`,
  no witness), or
* produced by `promoteToChecked` / `reopen`.

So `kernel_checked` is reachable only through `promoteToChecked`, and only with a clean witness
attached (`checked_has_clean_witness`). v0 had a public constructor:
`{ status := .kernel_checked, .. }` was a valid receipt.

The receipt is still in-memory Lean data. Serialized, it is a claim, not evidence: across a
process or network boundary it needs a signature, or the consumer re-runs `Admit.admit`.
-/

namespace IntrospectionTwin

inductive Status where
  | sketched
  | foreign_attestation
  | rejected
  | kernel_checked
deriving Repr, DecidableEq, Inhabited

structure Subject where
  repoUri       : String
  commitHash    : String
  toolchainHash : String
deriving Repr, DecidableEq

inductive Lens where
  | compilerDump   (flag : String)
  | kernelTrace
  | externalProver (providerId : String)
deriving Repr, DecidableEq

structure Receipt where
  private mk ::
  subject        : Subject
  lens           : Lens
  claimId        : String
  evidenceDigest : String
  producer       : String
  allowedAxioms  : List String
  /-- Retained on promotion (v0 dropped it, so the end-to-end theorem was unprovable). -/
  witness        : Option ReplayWitness
  status         : Status
deriving Repr, DecidableEq

/-- Open a receipt for local checking. -/
def Receipt.sketch (subject : Subject) (lens : Lens) (claimId evidenceDigest producer : String)
    (allowedAxioms : List String) : Receipt :=
  ⟨subject, lens, claimId, evidenceDigest, producer, allowedAxioms, none, .sketched⟩

/-- Record an external prover's claim. It can be promoted only by a local witness. -/
def Receipt.foreign (subject : Subject) (providerId claimId evidenceDigest producer : String)
    (allowedAxioms : List String) : Receipt :=
  ⟨subject, .externalProver providerId, claimId, evidenceDigest, producer, allowedAxioms, none,
    .foreign_attestation⟩

/-- Back to `sketched`, witness dropped: lets a consumer re-check from scratch. -/
def Receipt.reopen (r : Receipt) : Receipt :=
  { r with witness := none, status := .sketched }

def promoteToChecked (r : Receipt) (w : ReplayWitness) : Receipt :=
  match r.status with
  | .sketched | .foreign_attestation =>
    if w.clean r.allowedAxioms then { r with witness := some w, status := .kernel_checked }
    else { r with witness := some w, status := .rejected }
  | .kernel_checked | .rejected => r

/-! ## Promotion theorems -/

theorem promote_preserves_subject (r : Receipt) (w : ReplayWitness) :
    (promoteToChecked r w).subject = r.subject := by
  unfold promoteToChecked; split <;> (try split) <;> rfl

theorem promote_preserves_claim (r : Receipt) (w : ReplayWitness) :
    (promoteToChecked r w).claimId = r.claimId ∧
    (promoteToChecked r w).allowedAxioms = r.allowedAxioms := by
  unfold promoteToChecked; split <;> (try split) <;> exact ⟨rfl, rfl⟩

/-- An open receipt is promoted iff the witness is clean. -/
theorem promote_open_iff (r : Receipt) (w : ReplayWitness)
    (hOpen : r.status = .sketched ∨ r.status = .foreign_attestation) :
    (promoteToChecked r w).status = .kernel_checked ↔ w.clean r.allowedAxioms = true := by
  unfold promoteToChecked
  rcases hOpen with h | h <;> simp only [h] <;> split <;> simp_all

theorem promote_not_checked_without_witness (r : Receipt) (w : ReplayWitness)
    (hOpen : r.status = .sketched ∨ r.status = .foreign_attestation)
    (hBad : w.clean r.allowedAxioms = false) :
    (promoteToChecked r w).status ≠ .kernel_checked := by
  rw [Ne, promote_open_iff r w hOpen]; simp [hBad]

theorem promoted_sorry_not_checked (r : Receipt) (w : ReplayWitness)
    (hOpen : r.status = .sketched ∨ r.status = .foreign_attestation)
    (hSorry : w.sorryCount ≠ 0) :
    (promoteToChecked r w).status ≠ .kernel_checked := by
  apply promote_not_checked_without_witness r w hOpen
  simp [ReplayWitness.clean, hSorry]

theorem promote_checked_cases (r : Receipt) (w : ReplayWitness)
    (hc : (promoteToChecked r w).status = .kernel_checked) :
    (promoteToChecked r w = r ∧ r.status = .kernel_checked) ∨
    ((promoteToChecked r w).witness = some w ∧ w.clean r.allowedAxioms = true ∧
     (promoteToChecked r w).allowedAxioms = r.allowedAxioms) := by
  unfold promoteToChecked at hc ⊢
  split at hc <;>
    first
    | (left; exact ⟨rfl, hc⟩)
    | (right; split at hc <;> simp_all <;> done)
    | (exfalso; simp_all; done)

/-! ## The invariant the private constructor buys

`Reachable r` says `r` was built by the public API. Because the constructor is private, every
receipt that code outside this file can hold is `Reachable` — that step is enforced by Lean's
visibility rules, not by a theorem, and metaprograms are outside it. -/

inductive Reachable : Receipt → Prop
  | sketch (s l c e p a) : Reachable (Receipt.sketch s l c e p a)
  | foreign (s pid c e p a) : Reachable (Receipt.foreign s pid c e p a)
  | promote {r} (w) : Reachable r → Reachable (promoteToChecked r w)
  | reopen {r} : Reachable r → Reachable r.reopen

/-- Every reachable `kernel_checked` receipt carries a witness that is clean for its own
allowance. A checked status without a clean witness cannot be built through the API. -/
theorem checked_has_clean_witness {r : Receipt} (hr : Reachable r)
    (hc : r.status = .kernel_checked) :
    ∃ w, r.witness = some w ∧ w.clean r.allowedAxioms = true := by
  induction hr with
  | sketch => simp [Receipt.sketch] at hc
  | foreign => simp [Receipt.foreign] at hc
  | reopen => simp [Receipt.reopen] at hc
  | @promote r w hr ih =>
    rcases promote_checked_cases r w hc with ⟨heq, hrc⟩ | ⟨hw, hcl, ha⟩
    · rw [heq]; exact ih hrc
    · exact ⟨w, hw, by rw [ha]; exact hcl⟩

end IntrospectionTwin
