# Portable witness observed results

Operator: Codex, author-controlled workspace

Run: 2026-11-05T14:18:35.760853Z to 2026-11-05T14:18:37.206393Z

Scope: Finite author-selected cases only; no probability bound or independence claim

| Case | Forgery | Observed outcome |
| --- | --- | --- |
| F01 | post-signature effect substitution | refused |
| F02 | signature bit flip | refused |
| F03 | substitute signer | refused |
| F04 | duplicate effect key | refused |
| F05 | cross-audience receipt | refused |
| F06 | expired receipt | refused |
| F07 | spent nonce replay | refused |
| F08 | allowed effect carrying extra effects | refused |
| F09 | authentic ledger rollback | effect-without-refusal |
| F10 | trusted signer fabricates provenance | effect-without-refusal |

Caught: 8/10; uncaught: 2/10; excluded: 0/10.
Campaign process exit: 1. An expected uncaught case still makes the campaign nonzero.

F09 tests privileged authentic-state rollback; F10 tests a lying trusted signer.
Fresh keys and separate local processes do not establish independent custody or witnessing.
