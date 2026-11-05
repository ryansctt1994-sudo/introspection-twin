"""Frozen ten-case campaign. Known uncaught cases remain a nonzero result."""
from __future__ import annotations
from collections import Counter
from contextlib import closing
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import shutil
import sqlite3
import time
import zipfile

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from .core import canonical, initialize, make_payload, raw_private, sha, signed_receipt, snapshot
from .evidence import classify, legitimate_control_valid, observe

PACKAGE = Path(__file__).resolve().parents[1]


def now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def source_inventory():
    return [{"path": p.relative_to(PACKAGE).as_posix(), "bytes": p.stat().st_size,
             "sha256": sha(p.read_bytes())} for p in sorted(PACKAGE.rglob("*"))
            if p.is_file() and not any(part in {".git", ".venv", "__pycache__"}
                                      for part in p.relative_to(PACKAGE).parts)
            and p.suffix != ".pyc"]


def verify_design():
    raw = (PACKAGE / "DESIGN-FREEZE.json").read_bytes()
    expected = (PACKAGE / "DESIGN-FREEZE.sha256").read_text().split()[0]
    if sha(raw) != expected:
        raise ValueError("Design manifest digest mismatch; do not silently revise a frozen design")
    design = json.loads(raw)
    for entry in design["files"]:
        if sha((PACKAGE / entry["path"]).read_bytes()) != entry["sha256"]:
            raise ValueError("Frozen design changed: " + entry["path"])
    return expected


def copy_database(source, destination):
    with closing(sqlite3.connect(source)) as src, closing(sqlite3.connect(destination)) as dst:
        src.backup(dst)


def prepare_forgery(case, fixture, policy, public):
    """Returns the submitted bytes and setup observations, never a verdict."""
    private = (fixture / "issuer.key").read_bytes()
    state = fixture / "state"
    payload = make_payload(policy, "forgery-" + case)
    legitimate = signed_receipt(payload, private)
    setup = {"required_controls": [], "seed_observations": []}
    if case == "F01":
        envelope = json.loads(legitimate)
        envelope["payload"]["effect"]["value"] = "substituted-after-signing"
        forged = canonical(envelope)
    elif case == "F02":
        envelope = json.loads(legitimate)
        signature = bytearray.fromhex(envelope["signature"])
        signature[0] ^= 1
        envelope["signature"] = signature.hex()
        forged = canonical(envelope)
    elif case == "F03":
        forged = signed_receipt(payload, raw_private(Ed25519PrivateKey.generate()))
    elif case == "F04":
        envelope = json.loads(legitimate)
        altered = dict(payload["effect"], value="first-key-hidden-effect")
        payload_bytes = (b'{"effect":' + canonical(altered) + b"," + canonical(payload)[1:])
        forged = b'{"payload":' + payload_bytes + b',"signature":' + canonical(envelope["signature"]) + b'}'
    elif case == "F05":
        payload["audience"] = "another-witness"
        forged = signed_receipt(payload, private)
    elif case == "F06":
        clock = int(time.time())
        payload["issued_at"], payload["expires_at"] = clock - 120, clock - 60
        forged = signed_receipt(payload, private)
    elif case in {"F07", "F09"}:
        backup = fixture / "before-seed.sqlite"
        if case == "F09":
            copy_database(state / "effects.sqlite", backup)
            setup["pre_seed_snapshot_sha256"] = sha(backup.read_bytes())
        seed = observe(state, legitimate, public / "seed")
        setup["seed_observations"].append(seed)
        setup["required_controls"].append(legitimate_control_valid(seed))
        if case == "F09":
            setup["observed_seed_effects_outside_rollback"] = seed["effect_rows"]
            # All connections are closed; backup is a valid, older state with the
            # same instance identity. No private key or trust configuration changes.
            copy_database(backup, state / "effects.sqlite")
            setup["after_restore_rows"] = snapshot(state / "effects.sqlite")
            setup["required_controls"].append(not any(
                row["nonce"] == payload["nonce"] for row in setup["after_restore_rows"]))
        forged = legitimate
    elif case == "F08":
        payload["extra_effects"] = [{"operation": "append", "resource": policy["resource"],
                                    "value": "unapproved-extra"}]
        forged = signed_receipt(payload, private)
    elif case == "F10":
        payload["origin_claim"] = "An independent external witness observed this event; fixture declares this claim fabricated"
        setup["fabrication_declared_by_fixture_author"] = True
        setup["external_observation_actually_performed"] = False
        forged = signed_receipt(payload, private)
    else:
        raise ValueError("Unfrozen case ID")
    return forged, setup


def run_campaign(output: Path, operator: str, principal: str, relationship: str):
    if output == PACKAGE or PACKAGE in output.parents:
        raise ValueError("Choose an output directory outside the source package")
    design_hash = verify_design()
    output.mkdir(parents=True, exist_ok=False)
    private_root, public_root = output / "private", output / "public"
    private_root.mkdir()
    public_root.mkdir()
    plan = json.loads((PACKAGE / "cases.json").read_text())
    cases = plan["cases"]
    if [c["id"] for c in cases] != plan["order"] or len(cases) != 10:
        raise ValueError("Frozen case inventory mismatch")
    report = {"schema": "portable-witness-campaign/1", "started_at": now(),
              "operator": operator, "operator_principal": principal,
              "relationship_to_author": relationship,
              "independence": "operator declaration only; not established by this software",
              "environment": {"system": platform.system(), "machine": platform.machine(),
                              "python": platform.python_version()},
              "design_manifest_sha256": design_hash, "source_files": source_inventory(),
              "run_kind": "synthetic local reference; not S5", "cases": []}
    for item in cases:
        case_id = item["id"]
        fixture = private_root / case_id
        public = public_root / case_id
        public.mkdir()
        row = {"id": case_id, "name": item["name"], "required_access": item["required_access"],
               "predicted_outcome": item["predicted_outcome"], "baseline_valid": False,
               "outcome": "invalid-baseline", "attempt": None}
        try:
            policy = initialize(fixture, operator)
            (public / "trust.json").write_text(json.dumps(policy, indent=2) + "\n")
            (public / "witness.pub").write_bytes((fixture / "state/witness.pub").read_bytes())
            baseline_raw = signed_receipt(make_payload(policy, "legitimate-baseline"),
                                          (fixture / "issuer.key").read_bytes())
            baseline = observe(fixture / "state", baseline_raw, public / "baseline")
            row["baseline"] = baseline
            if legitimate_control_valid(baseline):
                forged, setup = prepare_forgery(case_id, fixture, policy, public)
                row["setup"] = setup
                row["baseline_valid"] = all(setup["required_controls"])
                if row["baseline_valid"]:
                    attempt = observe(fixture / "state", forged, public / "attempt")
                    row["attempt"] = attempt
                    row["outcome"] = classify(True, attempt["attempted"], attempt["coverage_complete"],
                                               attempt["ingress_observed"], attempt["refusal_observed"],
                                               attempt["effect_observed"])
        except Exception as error:
            row["driver_error"] = type(error).__name__ + ": " + str(error)
            # Setup/construction errors invalidate the baseline for scoring.
            # Any already observed effect remains in the retained observation files.
            row["outcome"] = "unverifiable" if row["attempt"] is not None else "invalid-baseline"
        row["prediction_matched"] = row["outcome"] == row["predicted_outcome"]
        report["cases"].append(row)
        print(case_id + ": " + row["outcome"], flush=True)
    counts = Counter(row["outcome"] for row in report["cases"])
    exit_code = (2 if any(row["outcome"] not in {"refused", "effect-without-refusal"}
                          for row in report["cases"])
                 else 1 if counts["effect-without-refusal"] else 0)
    report.update(completed_at=now(), counts=dict(counts), campaign_exit_code=exit_code,
                  coverage_statement="Finite author-selected cases only; no probability bound or independence claim",
                  caught_cases=counts["refused"], uncaught_cases=counts["effect-without-refusal"],
                  excluded_cases=10-counts["refused"]-counts["effect-without-refusal"])
    (public_root / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = ["# Portable witness observed results", "", "Operator: " + operator,
             "", "Run: " + report["started_at"] + " to " + report["completed_at"],
             "", "Scope: " + report["coverage_statement"], "",
             "| Case | Forgery | Observed outcome |", "| --- | --- | --- |"]
    lines += [f"| {r['id']} | {r['name']} | {r['outcome']} |" for r in report["cases"]]
    lines += ["", f"Caught: {report['caught_cases']}/10; uncaught: {report['uncaught_cases']}/10; excluded: {report['excluded_cases']}/10.",
              f"Campaign process exit: {exit_code}. An expected uncaught case still makes the campaign nonzero.",
              "", "F09 tests privileged authentic-state rollback; F10 tests a lying trusted signer.",
              "Fresh keys and separate local processes do not establish independent custody or witnessing."]
    (public_root / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    for name in ("TAXONOMY.md", "cases.json", "SPEC.md", "DESIGN-FREEZE.json", "DESIGN-FREEZE.sha256"):
        shutil.copyfile(PACKAGE / name, public_root / name)
    manifest = {"schema": "portable-witness-export/1", "files": [
        {"path": p.relative_to(public_root).as_posix(), "bytes": p.stat().st_size, "sha256": sha(p.read_bytes())}
        for p in sorted(public_root.rglob("*")) if p.is_file()]}
    (public_root / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    with zipfile.ZipFile(output / "public-evidence.zip", "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file in sorted(public_root.rglob("*")):
            if file.is_file():
                archive.write(file, file.relative_to(public_root).as_posix())
    print(json.dumps({"report": str(public_root / "report.json"), "counts": dict(counts),
                      "campaign_exit_code": exit_code, "public_export": str(output / "public-evidence.zip")}))
    return exit_code
