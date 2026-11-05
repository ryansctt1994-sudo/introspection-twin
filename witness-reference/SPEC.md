# Portable receipt witness v1

## Purpose and boundary

Provide an inspectable receipt admission boundary with a synthetic SQLite append
effect. An operator can reproduce the supplied cases without the author's machine
or private keys. This is not a Lean kernel checker, a production gate, an S5 run,
an origin-truth oracle, or evidence that the author/operator is independent.
TAXONOMY.md and cases.json define the fixed failure vocabulary and forgery set.

The witness trusts a locally pinned issuer public key, run identifier, subject,
audience, resource, and validity limits. It does not trust keys or policy settings
inside incoming receipts. The issuer key and witness result-signing key are
different. The fixture operator holds both; key separation is not independence.

## Wire format and admission

Input is a UTF-8 JSON object with exactly payload and signature. Limit input to
16 KiB. Reject duplicate keys anywhere, non-JSON numbers, unknown fields, and
incorrect types. Payload has exactly: version (integer 1), issuer_key_id, audience,
subject, run_id, nonce, issued_at, expires_at, effect, origin_claim. Context values
and origin_claim are bounded printable ASCII strings. Run ID and nonce are 32
random bytes encoded as 64 lowercase hexadecimal characters. Timestamps are
integer Unix seconds, never booleans. effect has exactly operation, resource,
value; operation is append and the resource must equal the pinned synthetic URI.
value is at most 128 printable ASCII characters; origin_claim is at most 240.

issuer_key_id is SHA-256 of the pinned raw 32-byte Ed25519 public key. signature
is a lowercase 128-character hex Ed25519 signature over the ASCII domain separator
PORTABLE-RECEIPT-v1, one LF byte, and canonical payload JSON: sorted ASCII keys,
no whitespace separators, ensure_ascii=true, no NaN. This is a defined restricted
JSON profile, not a claim of a general RFC 8785 implementation. No floats or
unbounded numbers are admitted. The witness uses its own clock: issue time may
be at most five seconds ahead; expiry must be after current time and issue time;
the maximum lifetime is 300 seconds. Incoming rho/delta/clock/policy overrides
are unknown fields and cannot change the pinned policy.

Only a valid signature, exact context, valid lifetime and unused nonce permit an
effect. Use an existing initialized SQLite database; never silently create an
empty replacement. BEGIN IMMEDIATE serializes admission, and insertion of the
nonce and effect is one transaction. A unique nonce prevents ordinary concurrent
double spending against that database. Missing/zeroed/broken state refuses; a
self-consistent authentic old snapshot is not detected without an external anchor.

The sole protected effect is insertion of the exact signed value in effects.
No shell command, URL, file path, or code from a receipt is executed. Return a
signed response binding attempt ID, raw request SHA-256, decision boolean, reason,
and effect ID if committed. A true decision is not, by itself, observed effect.
If a process dies after committing, the effect can exist without a usable response;
the external classifier must retain that fact and return unverifiable.

## Observation, baseline, and tests

The driver sends exact request bytes to a child process. The child emits an ingress
record after reading the bytes, before parsing them, and a signed final response.
The driver captures stdout/stderr and exit status and verifies response signatures
against its preloaded witness public key. It separately reads the SQLite sink via
a read-only connection before and after the process and correlates effect rows
with the attempt ID. Ambiguous or missing observations are never a clean refusal.

Each forgery gets a fresh fixture and a legitimate, signed, same-executor baseline
whose effect must be observed. Additional legitimate seeds required by F07/F09
must also work. F09's snapshot predates its seed, and the seed's observed effect
is retained in the driver's evidence after rollback. F10's fabrication is a
declared synthetic falsehood, not a discovery about any real external witness.
Fixture/operator labels and the tested bytes, versions, fingerprints, baseline
observations, process logs, sink observations, and all outcomes are published.
Test secrets are excluded from exported reports.

The implementation also needs controls for the six taxonomy branches, missing
state, and concurrent replay. These are conformance/operational controls, excluded
from the ten-forgery denominator. Positive baseline failure stops scored attempts
for that case. No unrecorded retry, case substitution, or post-result vocabulary
change is allowed. Changes are versioned and recorded; preserve earlier results.

## Claims and stranger reproduction

F09 and F10 intentionally exercise declared trust limits: privileged state rollback
and a lying trusted issuer. A successful signature authenticates a key's statement,
not its truth. A local database cannot prove it is the newest authentic copy.
External anti-rollback custody and independent event observation are future design
work, not inferred from this package. The harness does not simulate independence.

A reproducer must use their own machine and freshly generated keys, record their
identity/principal/relationships and package digest, and return the full exported
report. A different host or fresh key alone does not establish independence. An
operator attestation is a claim to review, not automatic independent qualification.
No stranger run, acceptance, hardware separation, or S5 verdict is claimed here.
