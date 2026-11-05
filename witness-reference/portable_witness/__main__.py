from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import secrets
import sys

from . import __version__
from .core import MAX_RECEIPT, Refusal, admit, canonical, initialize, make_payload, response, signed_receipt


def main():
    parser = argparse.ArgumentParser(description="Portable local receipt witness; synthetic SQLite effects only.")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init", help="Create a new local fixture with fresh, non-independent test keys")
    init.add_argument("--root", type=Path, required=True)
    init.add_argument("--operator", required=True)
    issue = sub.add_parser("issue", help="Issue a legitimate synthetic receipt")
    issue.add_argument("--root", type=Path, required=True)
    issue.add_argument("--value", default="synthetic-canary")
    issue.add_argument("--output", type=Path, required=True)
    submit = sub.add_parser("submit", help="Read a receipt on stdin; emit ingress and signed result JSONL")
    submit.add_argument("--state", type=Path, required=True)
    submit.add_argument("--attempt-id", default=None)
    campaign = sub.add_parser("campaign", help="Run frozen forgeries; export evidence; uncaught cases exit nonzero")
    campaign.add_argument("--output", type=Path, required=True)
    campaign.add_argument("--operator", required=True)
    campaign.add_argument("--operator-principal", default="undeclared")
    campaign.add_argument("--relationship", default="undeclared")
    args = parser.parse_args()
    if args.command == "init":
        policy = initialize(args.root.resolve(), args.operator)
        print(json.dumps({"fixture": str(args.root.resolve()), "issuer_fingerprint": policy["issuer_key_id"],
                          "independence": "not established"}))
        return 0
    if args.command == "issue":
        if args.output.exists():
            parser.error("receipt output already exists; choose a new path")
        policy = json.loads((args.root / "state/trust.json").read_text())
        args.output.write_bytes(signed_receipt(make_payload(policy, args.value), (args.root / "issuer.key").read_bytes()))
        print(str(args.output))
        return 0
    if args.command == "campaign":
        from .campaign import run_campaign
        return run_campaign(args.output.resolve(), args.operator, args.operator_principal, args.relationship)
    attempt = args.attempt_id or secrets.token_hex(32)
    digest = hashlib.sha256()
    raw = bytearray()
    count = 0
    while True:
        block = sys.stdin.buffer.read(65536)
        if not block:
            break
        digest.update(block)
        count += len(block)
        if len(raw) <= MAX_RECEIPT:
            raw.extend(block[:MAX_RECEIPT + 1 - len(raw)])
    request_hash = digest.hexdigest()
    print(canonical({"kind": "ingress", "attempt_id": attempt,
                     "request_sha256": request_hash, "byte_count": count}).decode(), flush=True)
    try:
        effect_id = admit(args.state, bytes(raw), attempt, request_hash)
        result = response(args.state, attempt, request_hash, True, "effect-committed", effect_id)
        code = 0
    except Refusal as error:
        result = response(args.state, attempt, request_hash, False, str(error), None)
        code = 1
    print(canonical(result).decode(), flush=True)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
