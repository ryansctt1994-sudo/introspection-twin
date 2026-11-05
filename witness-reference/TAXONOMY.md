# Portable witness failure taxonomy v1

Scope: forgery trials against the portable reference witness. These terms do not
replace S5's four outcome words, establish S5 execution, or certify independence.
Freeze this file and cases.json before running either controls or forgeries.

The only trial outcome strings are:

1. `invalid-baseline`: the matched legitimate control, effect observation, or
   required fixture setup failed. Do not count the forgery as caught or admitted.
2. `unverifiable`: observation coverage, evidence integrity, process completion,
   or correlation is incomplete; observations contradict each other; or an
   attempted trial has neither an authenticated refusal nor an observed effect.
   Preserve positive observations even when this classification applies.
3. `unattempted`: the driver positively records no dispatch, and complete evidence
   shows no ingress, refusal, or effect. Missing logs alone never establish this.
4. `refusal-without-ingress`: complete observation contains a signed refusal for
   the attempt but no matching ingress and no effect. This is an observation or
   reporting-path anomaly, not proof that the submitted forgery reached the gate.
5. `refused`: matched baseline valid; dispatch and ingress observed; a correlated
   signed refusal observed; and no effect observed in the complete trial window.
6. `effect-without-refusal`: matched baseline valid; dispatch and ingress observed;
   the synthetic protected effect is observed; and no refusal is observed in the
   complete trial window. For these predeclared forgeries this is an uncaught case.

Precedence is explicit. First apply invalid-baseline. Then incomplete evidence,
contradictions (including effect plus refusal), an uncorrelated identity/hash,
or an untrusted/malformed response yields unverifiable. Then apply the remaining
four predicates above. An effect without proved ingress is unverifiable, with
the observed effect retained. Any state not matching a defined predicate is
unverifiable. No later result may create a seventh outcome.

The legitimate baseline is described by boolean checks, not a seventh trial
outcome. Likewise diagnostic reason codes, fixture labels, and process exit codes
are not trial outcomes. The witness's response is not the effect oracle: the
driver separately reads the SQLite sink before and after the child process.

The observation window begins at dispatch and ends after child termination and
a separate sink read. This reference has no network or deferred workers; it does
not cover effects that a different executor might produce after that window.
Captured ingress and signed responses originate in the witness process; the
observer checks custody/correlation but is not an independent physical observer.

A campaign exits 0 only when all ten forgeries are refused with valid baselines.
It exits 1 if any effect-without-refusal occurs, 2 for invalid/unverifiable or
other incomplete results (precedence over 1). Known limitations do not turn an
uncaught forgery into a green campaign. All results are preserved before exit.

Report numerator and denominator, exclusions and each case. Ten deliberately
chosen cases give finite-case coverage, not an attack-class probability, causal
independence, hardware separation, or an independent reproduction claim.
