"""Offline export consistency checks. Not independent witnessing or a campaign pass."""
from collections import Counter
import json
from pathlib import Path
import sys

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from .core import RESPONSE_DOMAIN, canonical, sha, strict_json
from .evidence import classify, legitimate_control_valid


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    return strict_json(path.read_bytes())


def verify_observation(directory, expected, public_key):
    observation = read_json(directory / "observation.json")
    require(observation == expected, f"embedded observation mismatch: {directory.name}")
    raw = (directory / "request.json").read_bytes()
    digest = sha(raw)
    require(observation["request_sha256"] == digest, "request digest")
    require(observation["witness_public_key"] == public_key.hex(), "witness key pin")
    require(observation["attempted"] is True and observation["coverage_complete"] is True,
            "incomplete observation; cannot fully verify this export")
    events = [strict_json(line) for line in (directory / "stdout.log").read_bytes().splitlines()]
    require(len(events) == 2, "raw event count")
    ingress, response = events
    require(ingress["kind"] == "ingress" and response["kind"] == "response", "raw event order")
    require(ingress["attempt_id"] == observation["attempt_id"] and
            ingress["request_sha256"] == digest and ingress["byte_count"] == len(raw), "ingress correlation")
    require(response == observation["signed_response"], "raw response differs from observation")
    payload = response["payload"]
    Ed25519PublicKey.from_public_bytes(public_key).verify(
        bytes.fromhex(response["signature"]), RESPONSE_DOMAIN + canonical(payload))
    require(type(payload["authorized"]) is bool, "malformed decision")
    require(payload["attempt_id"] == observation["attempt_id"] and payload["request_sha256"] == digest,
            "signed response correlation")
    before, after = observation["before"], observation["after"]
    require(isinstance(before, list) and isinstance(after, list), "missing sink observations")
    effects = [row for row in after if row["attempt_id"] == observation["attempt_id"]]
    require(all(row in after for row in before), "sink history changed inside attempt")
    require([row for row in after if row not in before] == effects and len(effects) <= 1,
            "unexplained sink changes")
    require(observation["effect_rows"] == effects and observation["effect_observed"] is bool(effects),
            "effect fact mismatch")
    require(observation["ingress_observed"] is True and
            observation["refusal_observed"] is (not payload["authorized"]) and
            observation["authorized_response"] is payload["authorized"], "response facts mismatch")
    require(observation["process_exit"] == (0 if payload["authorized"] else 1), "exit mismatch")
    if payload["authorized"]:
        require(len(effects) == 1 and payload["effect_id"] == effects[0]["id"], "missing claimed effect")
        request_payload = strict_json(raw)["payload"]
        row = effects[0]
        require(row["receipt_sha256"] == digest and row["nonce"] == request_payload["nonce"] and
                row["value"] == request_payload["effect"]["value"] and
                row["origin_claim"] == request_payload["origin_claim"], "effect differs from signed request")
    else:
        require(not effects and payload["effect_id"] is None, "refusal with effect")
    require(observation["errors"] == [], "observer errors")
    return observation


def verify(root):
    root = root.resolve()
    manifest = read_json(root / "MANIFEST.json")
    listed = set()
    for entry in manifest["files"]:
        relative = entry["path"]
        require(relative not in listed, "duplicate manifest entry")
        listed.add(relative)
        path = (root / relative).resolve()
        require(path.is_relative_to(root) and path.is_file(), "invalid manifest path")
        raw = path.read_bytes()
        require(len(raw) == entry["bytes"] and sha(raw) == entry["sha256"], "digest mismatch: " + relative)
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}
    require(actual == listed | {"MANIFEST.json"}, "missing or unlisted files")
    require(not any(p.endswith(".key") or "private/" in p for p in listed), "private-key path in export")
    design_hash = sha((root / "DESIGN-FREEZE.json").read_bytes())
    require((root / "DESIGN-FREEZE.sha256").read_text().split()[0] == design_hash, "design manifest digest")
    for entry in read_json(root / "DESIGN-FREEZE.json")["files"]:
        require(sha((root / entry["path"]).read_bytes()) == entry["sha256"], "frozen design digest")
    report = read_json(root / "report.json")
    require(report["design_manifest_sha256"] == design_hash, "report design digest")
    plan = read_json(root / "cases.json")
    require([case["id"] for case in report["cases"]] == plan["order"] and len(plan["order"]) == 10,
            "case inventory mismatch")
    for case in report["cases"]:
        directory = root / case["id"]
        pub = (directory / "witness.pub").read_bytes()
        baseline = verify_observation(directory / "baseline", case["baseline"], pub)
        require(legitimate_control_valid(baseline) and case["baseline_valid"] is True, "invalid baseline")
        setup = case["setup"]
        require(all(value is True for value in setup["required_controls"]), "failed setup control")
        for seed in setup["seed_observations"]:
            verify_observation(directory / "seed", seed, pub)
            require(legitimate_control_valid(seed), "invalid legitimate seed")
        observation = verify_observation(directory / "attempt", case["attempt"], pub)
        expected = classify(True, observation["attempted"], observation["coverage_complete"],
                            observation["ingress_observed"], observation["refusal_observed"],
                            observation["effect_observed"])
        require(case["outcome"] == expected, "classification mismatch: " + case["id"])
        if case["id"] in {"F07", "F09"}:
            require((directory / "seed/request.json").read_bytes() == (directory / "attempt/request.json").read_bytes(),
                    "replay is not the identical seeded receipt")
        if case["id"] == "F09":
            require(setup["observed_seed_effects_outside_rollback"] == setup["seed_observations"][0]["effect_rows"],
                    "missing pre-rollback positive observation")
            require(setup["after_restore_rows"] == observation["before"], "restored-state mismatch")
    counts = Counter(case["outcome"] for case in report["cases"])
    require(dict(counts) == report["counts"], "outcome counts")
    require(report["caught_cases"] == counts["refused"] and report["uncaught_cases"] == counts["effect-without-refusal"]
            and report["excluded_cases"] == 10-counts["refused"]-counts["effect-without-refusal"], "summary counts")
    expected_exit = 2 if any(k not in {"refused", "effect-without-refusal"} for k in counts) else 1 if counts["effect-without-refusal"] else 0
    require(report["campaign_exit_code"] == expected_exit, "campaign exit mismatch")
    print(json.dumps({"export_consistency_checked": True, "files": len(listed), "counts": dict(counts),
                      "campaign_exit_code": expected_exit, "independent_witnessing_established": False}))


if __name__ == "__main__":
    try:
        require(len(sys.argv) == 2, "usage: python -m portable_witness.verify_export PUBLIC_DIRECTORY")
        verify(Path(sys.argv[1]))
    except Exception as error:
        print("Export verification incomplete/failed: " + type(error).__name__ + ": " + str(error), file=sys.stderr)
        raise SystemExit(2)
