"""Observer-side classification; no independent-operator claim."""
from __future__ import annotations
from pathlib import Path
import json
import secrets
import subprocess
import sys

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from .core import RESPONSE_DOMAIN, canonical, sha, snapshot

OUTCOMES = ("refused", "unattempted", "effect-without-refusal", "refusal-without-ingress",
            "unverifiable", "invalid-baseline")


def classify(baseline_valid, attempted, coverage_complete, ingress, refusal, effect):
    if baseline_valid is False:
        return "invalid-baseline"
    if not all(type(v) is bool for v in (baseline_valid, attempted, coverage_complete, ingress, refusal, effect)):
        return "unverifiable"
    if not coverage_complete or (effect and refusal):
        return "unverifiable"
    if not attempted:
        return "unverifiable" if (ingress or refusal or effect) else "unattempted"
    if refusal and not ingress and not effect:
        return "refusal-without-ingress"
    if not ingress:
        return "unverifiable"
    if refusal and not effect:
        return "refused"
    if effect and not refusal:
        return "effect-without-refusal"
    return "unverifiable"


def observe(state: Path, raw: bytes, evidence_dir: Path, *, attempt=None):
    """Run one child, retain bytes/logs, and independently read the synthetic sink."""
    evidence_dir.mkdir(parents=True, exist_ok=False)
    attempt = attempt or secrets.token_hex(32)
    (evidence_dir / "request.json").write_bytes(raw)
    request_hash = sha(raw)
    errors = []
    coverage = True
    before = after = None
    try:
        pinned_public = (state / "witness.pub").read_bytes()
        before = snapshot(state / "effects.sqlite")
    except Exception as error:
        errors.append("pre-observation: " + type(error).__name__)
        pinned_public = None
        coverage = False
    attempted = False
    stdout = stderr = b""
    returncode = None
    command = [sys.executable, "-m", "portable_witness", "submit", "--state", str(state),
               "--attempt-id", attempt]
    try:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        attempted = True
        stdout, stderr = process.communicate(raw, timeout=20)
        returncode = process.returncode
    except subprocess.TimeoutExpired:
        process.kill()
        stdout, stderr = process.communicate()
        returncode = process.returncode
        coverage = False
        errors.append("child-timeout")
    except OSError as error:
        coverage = False
        errors.append("dispatch: " + type(error).__name__)
    (evidence_dir / "stdout.log").write_bytes(stdout)
    (evidence_dir / "stderr.log").write_bytes(stderr)
    try:
        after = snapshot(state / "effects.sqlite")
    except Exception as error:
        errors.append("post-observation: " + type(error).__name__)
        coverage = False
    ingress = refusal = authorized = False
    signed_response = None
    try:
        events = [json.loads(line) for line in stdout.decode("utf-8").splitlines()]
        ingresses = [e for e in events if e.get("kind") == "ingress"]
        responses = [e for e in events if e.get("kind") == "response"]
        if len(events) != 2 or len(ingresses) != 1 or len(responses) != 1:
            raise ValueError("event-count")
        i = ingresses[0]
        ingress = i["attempt_id"] == attempt and i["request_sha256"] == request_hash and i["byte_count"] == len(raw)
        signed_response = responses[0]
        payload = signed_response["payload"]
        Ed25519PublicKey.from_public_bytes(pinned_public).verify(
            bytes.fromhex(signed_response["signature"]), RESPONSE_DOMAIN + canonical(payload))
        if payload["attempt_id"] != attempt or payload["request_sha256"] != request_hash:
            raise ValueError("response-correlation")
        if type(payload["authorized"]) is not bool:
            raise ValueError("decision-type")
        authorized = payload["authorized"]
        refusal = not authorized
        if returncode != (0 if authorized else 1):
            raise ValueError("response-exit-mismatch")
        if not ingress:
            raise ValueError("ingress-correlation")
    except Exception as error:
        coverage = False
        errors.append("response-observation: " + type(error).__name__ + ": " + str(error))
    before_rows = before or []
    after_rows = after or []
    effect_rows = [row for row in after_rows if row["attempt_id"] == attempt]
    effect = bool(effect_rows)
    if before is not None and after is not None:
        preserved = all(row in after_rows for row in before_rows)
        additions = [row for row in after_rows if row not in before_rows]
        if not preserved or additions != effect_rows or len(effect_rows) > 1:
            coverage = False
            errors.append("unexpected-sink-change")
    if signed_response and authorized:
        if len(effect_rows) != 1 or signed_response["payload"]["effect_id"] != effect_rows[0]["id"]:
            coverage = False
            errors.append("claimed-effect-not-observed")
    evidence = {"attempt_id": attempt, "request_sha256": request_hash,
                "command": command, "attempted": attempted, "coverage_complete": coverage,
                "ingress_observed": ingress, "refusal_observed": refusal,
                "effect_observed": effect, "authorized_response": authorized,
                "process_exit": returncode, "before": before, "after": after,
                "effect_rows": effect_rows, "signed_response": signed_response,
                "witness_public_key": pinned_public.hex() if pinned_public else None,
                "errors": errors, "observer_independence": "same controlling principal"}
    (evidence_dir / "observation.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    return evidence


def legitimate_control_valid(evidence):
    return (evidence["coverage_complete"] and evidence["ingress_observed"] and
            evidence["authorized_response"] and evidence["effect_observed"] and
            not evidence["refusal_observed"] and evidence["process_exit"] == 0)
