# Portable witness: observed author-controlled coverage

**2026-11-05: eight refused, two uncaught, zero excluded. Campaign exit 1.**
This is a new synthetic receipt witness reference, not an execution or audit of
Chris's target, Richard's gate, a Lean checker, or S5. No independent witnessing,
second physical machine, or stranger reproduction is established.

## Reproduce and inspect

- [Operator guide and reference implementation](../../../../witness-reference/README.md)
- [Frozen contract](../../../../witness-reference/SPEC.md), [taxonomy](../../../../witness-reference/TAXONOMY.md), and [ten-case plan](../../../../witness-reference/cases.json)
- [Outside reproduction invitation and principal/key-custody declaration](../../../../witness-reference/REPRODUCE.md)
- [Tested source ZIP](portable-witness-source.zip)
- [Full author public evidence ZIP](author-public-evidence.zip), [machine report](author-report.json), [case table](author-report.md)
- [Artifact hashes](ARTIFACTS.json), [operational controls](controls.log), [campaign output](campaign.log), and [actual exit](campaign.exit)

The repository's [MIT license](../../../../LICENSE) applies to the source.
The source ZIP contains the same 17 source files used in both runs below.
No witness implementation or frozen document was changed after observing results.

## Sequence and freeze

The design manifest was recorded and its hash posted in the authoring chat at
**2026-11-05T14:01:14Z**, before any controls or forgery execution. Its SHA-256 is
`272bdcfd4ec24c4ad5852403e09e121ed085d1657ea96130098808e8981f9b1d`.
It binds the spec, taxonomy and case plan, including the two predicted misses.
The [implementation inventory](implementation-before-run.json) was recorded at
14:18:22Z before execution. These are author-side records, not externally
trusted timestamping or independent proof of chronology.

The first campaign ran **14:18:35.760853Z–14:18:37.206393Z**, under Ryan's controlling
principal using Codex. Each case had a fresh fixture and observed legitimate
baseline. F07/F09 also had successful, separately recorded seed executions.

| Case | Mechanism | Observed result | Witness reason |
| --- | --- | --- | --- |
| F01 | Change effect after signing | refused | signature-invalid |
| F02 | Flip a signature bit | refused | signature-invalid |
| F03 | Substitute attacker signing key | refused | signature-invalid |
| F04 | Duplicate effect key, parser ambiguity | refused | duplicate-json-key |
| F05 | Authentic receipt for another audience | refused | context-audience |
| F06 | Authentic expired receipt | refused | expired |
| F07 | Replay the identical spent receipt | refused | nonce-spent |
| F08 | Signed allowed effect carrying extra effects | refused | payload-schema |
| F09 | Restore authentic pre-spend ledger, replay | effect-without-refusal | effect-committed |
| F10 | Trusted signer fabricates provenance | effect-without-refusal | effect-committed |

F09 requires privileged database rollback. The observer retained the first
execution outside the restored database and observed the replayed effect afterward.
F10 requires the trusted issuer key; its false provenance is a declared fixture
falsehood, not a finding about an actual third-party witness. Neither is a break
of Ed25519. Both are uncaught under the frozen broader forgery set, and their
predicted nature does not convert campaign exit 1 into success.

F08 establishes schema refusal only: this synthetic executor does not implement
`extra_effects`. There is no matched unguarded attack-effect control for that route,
so the result cannot establish that a real smuggling mechanism had teeth. This
package does not satisfy S5's C5 or qualify any external gate. The eight refusals
are finite input-rejection observations, not eight proven defenses against entire
attack classes or a statistical security estimate.

## Instrument and portability checks

Five operational tests passed: a separately observed legitimate effect; missing
state refusal without recreation; zero-byte state refusal; concurrent identical
nonce admission committing exactly once; and taxonomy conformance including
ambiguous observations. These tests are outside the ten-forgery denominator.

The public-export verifier checked 115 inventoried files plus the manifest,
response signatures, request correlation, observed sink rows and classification
consistency. Two copied-export negative controls were rejected: a missing log and
an altered response signature even after the attacker recomputed file hashes.
See [verifier-control output](export-verifier-controls.json). This verifies the
consistency of an author-controlled transcript; it cannot prove that an operator
did not fabricate an entire transcript with keys they control.

A second run followed the README from the source ZIP in a separate directory and
fresh virtual environment at **14:20:12.344858Z–14:20:13.758849Z**. All source hashes
matched and witness keys differed. It again observed eight refused, two uncaught,
exit 1, with five operational tests passing. This was the **same machine and same
principal**, a packaging/setup check rather than an outside reproduction:
[installation](source-zip-installation.log), [controls](source-zip-controls.log),
[report](source-zip-reproduction-report.json), [raw public evidence](source-zip-reproduction-evidence.zip),
[verifier output](source-zip-verification.log). Do not combine the repetitions into
twenty distinct mechanisms. Only Linux x86_64 / CPython 3.12.14 was exercised.

All 20 author fixture private keys were checked against every uncompressed export
member; no raw or hex key material or private-key file was present. The public
exports intentionally contain public keys, signatures, operator declarations,
synthetic canaries and local paths.

## What remains open

An outside operator must actually accept the invitation and return a complete
run, disclose relationships and principal control, and demonstrate their own key
custody. Nobody is designated independent by adding an agent or moving a process.
No outside participant has yet accepted or run this package.

F09 needs an anti-rollback anchor outside the party able to restore the ledger.
F10 needs independently controlled event observation and a precise attestation
contract. Adding another signature under the same principal resolves neither.
Those changes would need a separately versioned design and retained old results.

The six failure words remain exactly as frozen. S5's four outcomes and the existing
adjudicator limitations remain separate; this work produces no S5 verdict.
