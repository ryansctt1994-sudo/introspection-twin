import Lean

/-!
# Replay witnesses

A `ReplayWitness` records what the local Lean environment says about one declaration.

**Construction is private to this file.** The only way ordinary code can obtain a witness is
`synthesizeWitness`, which reads the environment. v0 had a public constructor, so anyone could
write `{ kernelAccepted := true, sorryCount := 0, usedAxioms := [] }` and every gate theorem
stayed true while the gate opened.

What privacy does NOT stop: metaprograms (which can reach private names) and code inside this
file. The real control is that the authority spine synthesizes the witness itself, in its own
process (`Admit.admit`), and never accepts one as input.

What `kernelAccepted` means: the declaration is present in this environment. Normally that
implies the kernel checked it, but a metaprogram can add declarations without kernel checking
(`debug.skipKernelTC`). Only an independent replay of the `.olean` files (lean4checker) closes
that; see `scripts/check_kernel_replay.sh` and `Test/KernelBypass.lean`.
-/

namespace IntrospectionTwin

open Lean

structure ReplayWitness where
  private mk ::
  kernelAccepted : Bool
  /-- The claim is a `theorem`, not a `def`, `opaque` or `axiom`. -/
  isTheorem      : Bool
  sorryCount     : Nat
  usedAxioms     : List String
deriving Repr, DecidableEq

/-- A witness is clean for an axiom allowance when the declaration exists, is a theorem,
uses no `sorry`, and uses only allowed axioms. -/
def ReplayWitness.clean (w : ReplayWitness) (allowed : List String) : Bool :=
  w.kernelAccepted && w.isTheorem && w.sorryCount == 0 && w.usedAxioms.all (allowed.contains ·)

theorem ReplayWitness.clean_spec (w : ReplayWitness) (allowed : List String) :
    w.clean allowed = true ↔
      w.kernelAccepted = true ∧ w.isTheorem = true ∧ w.sorryCount = 0 ∧
      ∀ ax ∈ w.usedAxioms, ax ∈ allowed := by
  simp [ReplayWitness.clean, List.all_eq_true, and_assoc]

/-- Read the environment. Names are compared as `Name`s here, not strings. -/
def synthesizeWitness (declName : Name) : CoreM ReplayWitness := do
  let env ← getEnv
  match env.find? declName with
  | none => return ⟨false, false, 0, []⟩
  | some info =>
    let axioms ← Lean.collectAxioms declName
    let hasSorry := axioms.contains ``sorryAx
    let isThm := match info with
      | .thmInfo _ => true
      | _ => false
    return ⟨true, isThm, if hasSorry then 1 else 0, axioms.toList.map (·.toString)⟩

/-- `#introspect foo` prints the witness for `foo`. Informational only. -/
elab "#introspect " id:ident : command => do
  let declName := id.getId
  let w ← Lean.Elab.Command.liftCoreM (synthesizeWitness declName)
  Lean.logInfo m!"introspect {declName}:\n  kernel={w.kernelAccepted}\n  theorem={w.isTheorem}\n  sorryCount={w.sorryCount}\n  usedAxioms={w.usedAxioms}"

end IntrospectionTwin
