import IntrospectionTwin

/-!
# Test harness

`#expect_admitted d under p` / `#expect_rejected d under p` run the spine's real entry point
(`admit`: witness synthesized from the environment, receipt reopened, promoted, gated) for
declaration `d` against profile `p` (`empty`, `constructive`, `classical`).

A wrong verdict is a build error, so `lake build` is the test run.
-/

namespace IntrospectionTwin.Test

open Lean Elab Command

def testSubject : Subject := ⟨"local://introspection-twin", "test", "leanprover/lean4:v4.22.0"⟩

def profileOf : String → Option (List String)
  | "empty" => some emptyAxiomProfile
  | "constructive" => some constructiveAxiomProfile
  | "classical" => some classicalAxiomProfile
  | _ => none

def runExpectation (decl : Name) (profile : String) (expectAdmit : Bool) : CommandElabM Unit := do
  let some allowed := profileOf profile | throwError "unknown profile '{profile}'"
  let claim := decl.toString
  let r := Receipt.sketch testSubject .kernelTrace claim "" "test-harness" allowed
  let c : GateCondition := ⟨testSubject, claim, allowed⟩
  let ok ← liftCoreM (admit c r)
  if ok != expectAdmit then
    let w ← liftCoreM (synthesizeWitness decl)
    throwError "expected {if expectAdmit then "ADMITTED" else "REJECTED"} but gate said {if ok then "ADMITTED" else "REJECTED"} for {decl} under {profile} (witness: kernel={w.kernelAccepted}, theorem={w.isTheorem}, sorry={w.sorryCount}, axioms={w.usedAxioms})"

syntax (name := expectAdmitted) "#expect_admitted " ident " under " ident : command
syntax (name := expectRejected) "#expect_rejected " ident " under " ident : command

elab_rules : command
  | `(#expect_admitted $d:ident under $p:ident) => runExpectation d.getId p.getId.toString true
  | `(#expect_rejected $d:ident under $p:ident) => runExpectation d.getId p.getId.toString false

end IntrospectionTwin.Test
