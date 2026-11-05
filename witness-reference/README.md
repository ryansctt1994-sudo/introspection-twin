# Portable receipt witness

A standalone reference implementation and a frozen, ten-case forgery campaign.
It verifies signed receipts and applies a synthetic SQLite append effect. The
driver captures raw inputs, signed responses, process diagnostics, and separate
before/after reads of the effect sink. No target hardware or author's keys are needed.

This is a local instrument, not a production gate or an S5 execution. The operator
controls the issuer, witness, sink, and observer. Fresh keys and separate processes
do not make that operator independent. The known limits are authentic state
rollback and false provenance signed by a trusted issuer. These remain uncaught
cases and make the campaign exit nonzero; they are never scored as successes.

## Get the exact source

Install Git and Python 3.11 or newer, including `venv` and `pip`. CPython on Linux
is the author validation target; macOS and Windows commands are provided but do
not imply those platforms have been tested. No Docker, cloud account, API token,
hardware device, or system service is required. Allow roughly 100 MB for Python
dependencies and a few MB for evidence. Network access is needed only for source
and dependencies; the controls and campaign perform no network requests.

From a terminal in a writable directory:

```sh
git clone --branch witness/portable-reference-v1 --single-branch https://github.com/ryansctt1994-sudo/introspection-twin.git witness-checkout
cd witness-checkout
git rev-parse HEAD
cd witness-reference
```

Record the printed commit SHA with your report. If you received a source ZIP,
extract it and enter its `portable-witness` directory instead. Record that ZIP's
SHA-256. The campaign additionally inventories every source file's digest.

## Install and run: Linux or macOS

Run these commands from the source directory containing this README:

```sh
python3 -m venv ../witness-venv
../witness-venv/bin/python -m pip install --only-binary=:all: -r requirements.txt
../witness-venv/bin/python -m unittest discover -s tests -v
```

Stop if installation or controls fail. Preserve their output; do not describe a
campaign with a broken instrument as a clean result. Then run the frozen cases,
replacing the three identity strings with your actual declarations:

```sh
../witness-venv/bin/python -m portable_witness campaign --output ../witness-run-001 --operator "Your name or public handle" --operator-principal "Person or organization controlling this run" --relationship "Your relationship to the author, spec, and target"
campaign_exit=$?
printf 'Campaign exit: %s\n' "$campaign_exit"
../witness-venv/bin/python -m portable_witness.verify_export ../witness-run-001/public
```

In a shell using `set -e`, wrap the campaign command in `if ...; then
campaign_exit=0; else campaign_exit=$?; fi` so its intentionally nonzero result
does not prevent you from retaining evidence. Do not replace the exit with zero.

## Install and run: Windows PowerShell

From the same source directory, with Python 3.11+ available as `py -3`:

```powershell
py -3 -m venv ..\witness-venv
..\witness-venv\Scripts\python.exe -m pip install --only-binary=:all: -r requirements.txt
..\witness-venv\Scripts\python.exe -m unittest discover -s tests -v
..\witness-venv\Scripts\python.exe -m portable_witness campaign --output ..\witness-run-001 --operator "Your name or public handle" --operator-principal "Person or organization controlling this run" --relationship "Your relationship to the author, spec, and target"
$campaignExit = $LASTEXITCODE
Write-Output "Campaign exit: $campaignExit"
..\witness-venv\Scripts\python.exe -m portable_witness.verify_export ..\witness-run-001\public
```

Check each installation/control command's exit before continuing. The verifier's
exit is separate from the campaign's exit; capture `$campaignExit` immediately.

## Interpret and share

`witness-run-001/public/report.md` is the human report; `report.json` contains every
classification, baseline, environment, source digest, setup detail, and observation.
Each case directory contains exact `request.json` bytes, `stdout.log`, `stderr.log`,
`observation.json`, public trust settings and witness public key. F07 and F09 also
retain seed observations. F09 retains the observed seed outside the restored sink.
`MANIFEST.json` inventories exported files; `public-evidence.zip` contains only
that public directory, with no private signing keys.

The six trial outcomes are exactly `refused`, `unattempted`,
`effect-without-refusal`, `refusal-without-ingress`, `unverifiable`, and
`invalid-baseline`. See [TAXONOMY.md](TAXONOMY.md) for predicates and precedence.
Process exits are diagnostics, not extra verdict words:

| Campaign exit | Meaning |
| --- | --- |
| 0 | All ten refused, every required baseline valid, coverage complete. |
| 1 | At least one observed effect-without-refusal; no excluded cases. |
| 2 | Invalid, unverifiable, unattempted, or other incomplete case; takes precedence over 1. |

The frozen prediction is eight refusals and two uncaught cases, exit **1**. Read
your actual report. A matching prediction does not make the campaign green.
Ten chosen cases yield a finite coverage count, not a failure-rate bound.

The export verifier checks file digests, response signatures, correlations and
reported classifications. Its zero exit means those consistency checks completed;
it does not mean the campaign caught every forgery, the sink observations are
independently true, or the key owner is independent. An unsigned manifest can be
replaced along with its files. Pin the source and export hashes through a separate
channel before relying on someone else's archive.

Share `public-evidence.zip`, its SHA-256, your recorded source SHA/ZIP hash, the
campaign exit, controls output, and the declaration in [REPRODUCE.md](REPRODUCE.md).
Keep `private/` on your machine: it contains the deliberately local issuer and
witness signing keys, SQLite fixtures and rollback snapshots. Exported operator
strings and local paths are public; choose their values with that in mind.

Hash a ZIP using `sha256sum FILE` on Linux, `shasum -a 256 FILE` on macOS, or
`Get-FileHash FILE -Algorithm SHA256` in PowerShell. Name who actually computed the
hash. This software cannot supply independent key custody on another person's behalf.

## Inspect one receipt manually (optional)

Using the installed interpreter, substitute its Windows path when applicable:

```sh
../witness-venv/bin/python -m portable_witness init --root ../manual-fixture --operator "Your handle"
../witness-venv/bin/python -m portable_witness issue --root ../manual-fixture --value canary --output ../receipt.json
../witness-venv/bin/python -m portable_witness submit --state ../manual-fixture/state < ../receipt.json
```

Submit promptly: the receipt expires after four minutes. The first submission
emits ingress and a signed authorization, exiting 0. Resubmitting those same bytes
refuses the spent nonce (or expiry if late), exiting 1. This manual command alone
does not provide the campaign's separate effect observation. On PowerShell use
`cmd /c` for binary-preserving input redirection, or use the campaign directly.

## Troubleshooting and limits

- `venv` unavailable: install your distribution's Python venv package, commonly
  `python3-venv`, then retry in a new environment. Python below 3.11 is unsupported.
- No matching binary wheel: record Python version, platform and pip output. Do
  not silently change dependency versions. This release uses pinned packages and
  prebuilt wheels; unsupported architectures are a reproducibility limitation.
- Output directory exists: use a new suffix, such as `witness-run-002`. Runs never
  overwrite earlier evidence. Keep failed runs and explain why you ran again.
- Design digest mismatch: stop. Compare `DESIGN-FREEZE.json` to the published hash;
  frozen files cannot be edited silently. Implementation changes need a new source
  digest and preserved results, even when the taxonomy remains unchanged.
- Incomplete observations or subprocess timeout: inspect that case's logs. Missing
  diagnostics are `unverifiable`, never proof of refusal.
- Missing or zero-byte state is refused. An authentic older, internally consistent
  database is different: F09 demonstrates the absence of external anti-rollback
  protection. Deleting rows consistently is also outside this instrument's guarantee.
- The trusted issuer can lie in `origin_claim`; F10 demonstrates this. Signatures
  authenticate the key's statement, not the truth of the event it describes.
- Receipt-controlled data is never executed. Effects are confined to a synthetic
  SQLite row. This CLI is not a hardened network daemon, an availability proof,
  a real target adapter, or evidence about Chris's gate, Richard's spec, or S5.

[SPEC.md](SPEC.md) defines the format and trust boundary; [cases.json](cases.json)
defines the ten cases. The design freeze was recorded before any control/forgery
execution at **2026-11-05T14:01:14Z**. SHA-256 of `DESIGN-FREEZE.json`:
`272bdcfd4ec24c4ad5852403e09e121ed085d1657ea96130098808e8981f9b1d`.
That timestamp is an author-side record, not a trusted timestamping service.
