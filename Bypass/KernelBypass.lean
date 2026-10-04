import Test.Harness

/-!
# Kernel bypass (deliberately poisoned — never a default build target)

A metaprogram adds `bypass_false : False` with proof `True.intro`, skipping the kernel
(`debug.skipKernelTC`). The kernel would reject it: `True.intro` does not have type `False`.

**The in-process gate is fooled**, and this file asserts that it is: the declaration exists,
is a theorem, uses no axioms and no sorry. `collectAxioms` cannot see what the kernel never
checked. This is the self-grading hole.

The defense is outside this process: `scripts/check_kernel_replay.sh` replays this module's
`.olean` through a fresh kernel with lean4checker, and REQUIRES that replay to fail.
-/

open Lean Elab Command in
elab "#add_unchecked_false" : command => liftCoreM do
  let decl := Declaration.thmDecl {
    name := `bypass_false, levelParams := [], type := mkConst ``False, value := mkConst ``True.intro }
  withOptions (fun o => o.setBool `debug.skipKernelTC true) (addDecl decl)

#add_unchecked_false

-- KNOWN HOLE, asserted so it cannot silently change: the in-process gate admits it.
#expect_admitted bypass_false under empty

-- And it is usable as a proof of False inside this process.
theorem bypass_anything : 1 = 2 := bypass_false.elim
