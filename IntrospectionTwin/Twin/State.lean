import IntrospectionTwin.Twin.Bounds
import IntrospectionTwin.Twin.Observation

/-!
# Twin state machine

`step` admits an observation only if all six guards hold. `step_ok_iff` characterizes success
exactly; every other theorem here is a corollary of it.

Not yet here: tamper evidence. Sequence numbers give ordering, not tamper evidence; a
`prevDigest` SHA-256 chain over observations is the next step (needs a SHA-256 implementation
in Lean, or a digest computed outside and checked here).
-/

namespace IntrospectionTwin.Twin

structure TwinState where
  bounds             : TwinBounds
  lastSequenceId     : Nat
  gasConsumed        : Nat
  observationHistory : List Observation
deriving Repr

inductive TransitionError where
  | outOfOrderSequence (expected : Nat) (got : Nat)
  | unapprovedTool     (digest : String)
  | commandDisallowed  (cmd : String)
  | outputSizeExceeded (bytes : Nat) (max : Nat)
  | identityMismatch   (expected : String) (got : String)
  | creditExceeded     (consumed : Nat) (budget : Nat)
deriving Repr, DecidableEq

def step (st : TwinState) (obs : Observation) (cost : Nat) : Except TransitionError TwinState := do
  if obs.agentId != st.bounds.agentIdentity then
    throw (TransitionError.identityMismatch st.bounds.agentIdentity obs.agentId)

  if obs.sequenceId != st.lastSequenceId + 1 then
    throw (TransitionError.outOfOrderSequence (st.lastSequenceId + 1) obs.sequenceId)

  if ¬ (st.bounds.allowedTools.contains obs.toolRecord.digestSHA256) then
    throw (TransitionError.unapprovedTool obs.toolRecord.digestSHA256)

  if ¬ (st.bounds.commandAllowlist.contains obs.command) then
    throw (TransitionError.commandDisallowed obs.command)

  if obs.outputBytes > st.bounds.maxOutputBytes then
    throw (TransitionError.outputSizeExceeded obs.outputBytes st.bounds.maxOutputBytes)

  let newGas := st.gasConsumed + cost
  if newGas > st.bounds.maxGasBudget then
    throw (TransitionError.creditExceeded newGas st.bounds.maxGasBudget)

  return { st with
    lastSequenceId     := obs.sequenceId,
    gasConsumed        := newGas,
    observationHistory := obs :: st.observationHistory
  }

set_option linter.unusedSimpArgs false in
/-- **Exact characterization.** `step` succeeds iff every guard holds, and then the new state
is determined. (v0 proved only the shape of the result; this is the converse it lacked.) -/
theorem step_ok_iff (st : TwinState) (obs : Observation) (cost : Nat) (st' : TwinState) :
    step st obs cost = Except.ok st' ↔
      (obs.agentId = st.bounds.agentIdentity ∧
       obs.sequenceId = st.lastSequenceId + 1 ∧
       st.bounds.allowedTools.contains obs.toolRecord.digestSHA256 = true ∧
       st.bounds.commandAllowlist.contains obs.command = true ∧
       obs.outputBytes ≤ st.bounds.maxOutputBytes ∧
       st.gasConsumed + cost ≤ st.bounds.maxGasBudget) ∧
      st' = { st with
        lastSequenceId     := obs.sequenceId,
        gasConsumed        := st.gasConsumed + cost,
        observationHistory := obs :: st.observationHistory } := by
  unfold step
  by_cases h1 : obs.agentId = st.bounds.agentIdentity <;>
  by_cases h2 : obs.sequenceId = st.lastSequenceId + 1 <;>
  by_cases h3 : st.bounds.allowedTools.contains obs.toolRecord.digestSHA256 = true <;>
  by_cases h4 : st.bounds.commandAllowlist.contains obs.command = true <;>
  by_cases h5 : st.bounds.maxOutputBytes < obs.outputBytes <;>
  by_cases h6 : st.bounds.maxGasBudget < st.gasConsumed + cost <;>
  simp [h1, h2, h3, h4, h5, h6, bind, Except.bind, pure, Except.pure] <;>
  first
  | omega
  | (constructor <;> intro h <;> first | exact h.symm | omega | simp_all)

/-- **Safety inversion.** A successful step implies every guard held. -/
theorem step_safety_inversion (st : TwinState) (obs : Observation) (cost : Nat) (st' : TwinState)
    (h : step st obs cost = Except.ok st') :
    obs.agentId = st.bounds.agentIdentity ∧
    obs.sequenceId = st.lastSequenceId + 1 ∧
    st.bounds.allowedTools.contains obs.toolRecord.digestSHA256 = true ∧
    st.bounds.commandAllowlist.contains obs.command = true ∧
    obs.outputBytes ≤ st.bounds.maxOutputBytes ∧
    st.gasConsumed + cost ≤ st.bounds.maxGasBudget :=
  ((step_ok_iff st obs cost st').mp h).1

theorem step_ok_shape (st : TwinState) (obs : Observation) (cost : Nat) (st' : TwinState)
    (h : step st obs cost = Except.ok st') :
    st' = { st with
      lastSequenceId     := obs.sequenceId,
      gasConsumed        := st.gasConsumed + cost,
      observationHistory := obs :: st.observationHistory } :=
  ((step_ok_iff st obs cost st').mp h).2

theorem step_bounds_stable (st : TwinState) (obs : Observation) (cost : Nat) (st' : TwinState)
    (h : step st obs cost = Except.ok st') : st'.bounds = st.bounds := by
  rw [step_ok_shape st obs cost st' h]

theorem step_monotonic_history (st : TwinState) (obs : Observation) (cost : Nat) (st' : TwinState)
    (h : step st obs cost = Except.ok st') :
    st'.observationHistory.length = st.observationHistory.length + 1 := by
  rw [step_ok_shape st obs cost st' h]; simp

theorem step_sequence_advances (st : TwinState) (obs : Observation) (cost : Nat) (st' : TwinState)
    (h : step st obs cost = Except.ok st') : st'.lastSequenceId = st.lastSequenceId + 1 := by
  rw [step_ok_shape st obs cost st' h]; exact (step_safety_inversion st obs cost st' h).2.1

theorem step_gas_accounted (st : TwinState) (obs : Observation) (cost : Nat) (st' : TwinState)
    (h : step st obs cost = Except.ok st') : st'.gasConsumed = st.gasConsumed + cost := by
  rw [step_ok_shape st obs cost st' h]

/-- Gas is weakly monotone. (v0's summary said "strictly"; that holds only for `cost > 0`.) -/
theorem step_gas_monotone (st : TwinState) (obs : Observation) (cost : Nat) (st' : TwinState)
    (h : step st obs cost = Except.ok st') : st.gasConsumed ≤ st'.gasConsumed := by
  rw [step_gas_accounted st obs cost st' h]; omega

theorem step_gas_strict (st : TwinState) (obs : Observation) (cost : Nat) (st' : TwinState)
    (h : step st obs cost = Except.ok st') (hc : 0 < cost) : st.gasConsumed < st'.gasConsumed := by
  rw [step_gas_accounted st obs cost st' h]; omega

/-- The budget is never exceeded after a successful step. -/
theorem step_within_budget (st : TwinState) (obs : Observation) (cost : Nat) (st' : TwinState)
    (h : step st obs cost = Except.ok st') : st'.gasConsumed ≤ st'.bounds.maxGasBudget := by
  rw [step_gas_accounted st obs cost st' h, step_bounds_stable st obs cost st' h]
  exact (step_safety_inversion st obs cost st' h).2.2.2.2.2

end IntrospectionTwin.Twin
