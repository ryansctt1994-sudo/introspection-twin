"""Receipt validation and one transactional synthetic effect boundary."""
from __future__ import annotations

import hashlib
from contextlib import closing
import json
import os
from pathlib import Path
import re
import secrets
import sqlite3
import time

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

MAX_RECEIPT = 16384
RECEIPT_DOMAIN = b"PORTABLE-RECEIPT-v1\n"
RESPONSE_DOMAIN = b"PORTABLE-WITNESS-v1\n"
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
HEX128 = re.compile(r"[0-9a-f]{128}\Z")
PAYLOAD_FIELDS = {"version", "issuer_key_id", "audience", "subject", "run_id", "nonce",
                  "issued_at", "expires_at", "effect", "origin_claim"}


class Refusal(Exception):
    pass


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                      allow_nan=False).encode("ascii")


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise Refusal("duplicate-json-key")
        result[key] = value
    return result


def _bad_number(value):
    raise Refusal("unsupported-number")


def strict_json(raw: bytes):
    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs,
                          parse_constant=_bad_number, parse_float=_bad_number)
    except (ValueError, UnicodeError, RecursionError) as error:
        raise Refusal("malformed-json") from error


def printable(value, limit):
    return isinstance(value, str) and 0 < len(value) <= limit and all(32 <= ord(c) <= 126 for c in value)


def raw_private(key):
    return key.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw,
                             serialization.NoEncryption())


def raw_public(key):
    return key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)


def write_secret(path, data):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(data)


def initialize(root: Path, operator: str):
    """Create a new fixture only. Never silently reuse or reset existing state."""
    root.mkdir(parents=True, exist_ok=False)
    state = root / "state"
    state.mkdir()
    issuer = Ed25519PrivateKey.generate()
    witness = Ed25519PrivateKey.generate()
    write_secret(root / "issuer.key", raw_private(issuer))
    write_secret(state / "witness.key", raw_private(witness))
    (state / "witness.pub").write_bytes(raw_public(witness))
    policy = {"version": 1, "operator": operator, "state_id": secrets.token_hex(32),
              "issuer_public_key": raw_public(issuer).hex(),
              "issuer_key_id": sha(raw_public(issuer)), "run_id": secrets.token_hex(32),
              "audience": "portable-witness", "subject": "synthetic-operator",
              "resource": "fixture://witness-canary", "clock_skew_seconds": 5,
              "max_lifetime_seconds": 300}
    (state / "trust.json").write_text(json.dumps(policy, indent=2) + "\n", encoding="utf-8")
    with closing(sqlite3.connect(state / "effects.sqlite")) as conn, conn:
        conn.executescript("""
          PRAGMA journal_mode=DELETE;
          CREATE TABLE metadata (id INTEGER PRIMARY KEY CHECK(id=1), state_id TEXT NOT NULL);
          CREATE TABLE spent (nonce TEXT PRIMARY KEY, receipt_sha256 TEXT NOT NULL);
          CREATE TABLE effects (id INTEGER PRIMARY KEY, attempt_id TEXT UNIQUE NOT NULL,
            nonce TEXT UNIQUE NOT NULL, value TEXT NOT NULL, receipt_sha256 TEXT NOT NULL,
            origin_claim TEXT NOT NULL);
        """)
        conn.execute("INSERT INTO metadata VALUES (1, ?)", (policy["state_id"],))
    return policy


def make_payload(policy, value="synthetic-canary", now=None):
    now = int(time.time()) if now is None else now
    return {"version": 1, "issuer_key_id": policy["issuer_key_id"],
            "audience": policy["audience"], "subject": policy["subject"],
            "run_id": policy["run_id"], "nonce": secrets.token_hex(32),
            "issued_at": now, "expires_at": now + 240,
            "effect": {"operation": "append", "resource": policy["resource"], "value": value},
            "origin_claim": "Fixture issuer assertion; not independently witnessed"}


def signed_receipt(payload, private_key: bytes):
    key = Ed25519PrivateKey.from_private_bytes(private_key)
    return canonical({"payload": payload,
                      "signature": key.sign(RECEIPT_DOMAIN + canonical(payload)).hex()})


def validate(raw, policy, now):
    if len(raw) > MAX_RECEIPT:
        raise Refusal("receipt-too-large")
    envelope = strict_json(raw)
    if not isinstance(envelope, dict) or set(envelope) != {"payload", "signature"}:
        raise Refusal("envelope-schema")
    p, signature = envelope["payload"], envelope["signature"]
    if not isinstance(p, dict) or set(p) != PAYLOAD_FIELDS:
        raise Refusal("payload-schema")
    if type(p["version"]) is not int or p["version"] != 1:
        raise Refusal("version")
    for name in ("issuer_key_id", "run_id", "nonce"):
        if not isinstance(p[name], str) or not HEX64.fullmatch(p[name]):
            raise Refusal("identifier-schema")
    for name, limit in (("audience", 128), ("subject", 128), ("origin_claim", 240)):
        if not printable(p[name], limit):
            raise Refusal("string-schema")
    for name in ("issued_at", "expires_at"):
        if type(p[name]) is not int or not 0 <= p[name] < 2**53:
            raise Refusal("timestamp-schema")
    effect = p["effect"]
    if not isinstance(effect, dict) or set(effect) != {"operation", "resource", "value"}:
        raise Refusal("effect-schema")
    if effect["operation"] != "append" or effect["resource"] != policy["resource"]:
        raise Refusal("effect-scope")
    if not printable(effect["value"], 128):
        raise Refusal("value-schema")
    if not isinstance(signature, str) or not HEX128.fullmatch(signature):
        raise Refusal("signature-schema")
    for name in ("issuer_key_id", "audience", "subject", "run_id"):
        if p[name] != policy[name]:
            raise Refusal("context-" + name)
    try:
        public = bytes.fromhex(policy["issuer_public_key"])
        if sha(public) != policy["issuer_key_id"]:
            raise Refusal("pinned-key-mismatch")
        Ed25519PublicKey.from_public_bytes(public).verify(
            bytes.fromhex(signature), RECEIPT_DOMAIN + canonical(p))
    except InvalidSignature as error:
        raise Refusal("signature-invalid") from error
    if p["issued_at"] > now + policy["clock_skew_seconds"]:
        raise Refusal("issued-in-future")
    if p["expires_at"] <= now:
        raise Refusal("expired")
    if not 0 < p["expires_at"] - p["issued_at"] <= policy["max_lifetime_seconds"]:
        raise Refusal("lifetime")
    return p


def connect_existing(path, readonly=False):
    return sqlite3.connect(path.resolve().as_uri() + ("?mode=ro" if readonly else "?mode=rw"),
                           uri=True, timeout=10)


def admit(state: Path, raw: bytes, attempt: str, request_hash: str):
    policy = json.loads((state / "trust.json").read_text(encoding="utf-8"))
    payload = validate(raw, policy, int(time.time()))
    db = state / "effects.sqlite"
    if not db.is_file() or db.stat().st_size == 0:
        raise Refusal("state-unavailable")
    conn = None
    try:
        conn = connect_existing(db)
        conn.execute("BEGIN IMMEDIATE")
        if conn.execute("PRAGMA quick_check").fetchone() != ("ok",):
            raise Refusal("state-integrity")
        if conn.execute("SELECT state_id FROM metadata WHERE id=1").fetchall() != [(policy["state_id"],)]:
            raise Refusal("state-identity")
        if conn.execute("SELECT 1 FROM spent WHERE nonce=?", (payload["nonce"],)).fetchone():
            raise Refusal("nonce-spent")
        conn.execute("INSERT INTO spent VALUES (?, ?)", (payload["nonce"], request_hash))
        cursor = conn.execute("INSERT INTO effects (attempt_id,nonce,value,receipt_sha256,origin_claim) VALUES (?,?,?,?,?)",
                              (attempt, payload["nonce"], payload["effect"]["value"], request_hash,
                               payload["origin_claim"]))
        effect_id = cursor.lastrowid
        conn.commit()
        return effect_id
    except sqlite3.Error as error:
        raise Refusal("state-error") from error
    finally:
        if conn is not None:
            conn.close()


def response(state, attempt, request_hash, authorized, reason, effect_id):
    p = {"version": 1, "attempt_id": attempt, "request_sha256": request_hash,
         "authorized": authorized, "reason": reason, "effect_id": effect_id}
    key = Ed25519PrivateKey.from_private_bytes((state / "witness.key").read_bytes())
    return {"kind": "response", "payload": p,
            "signature": key.sign(RESPONSE_DOMAIN + canonical(p)).hex()}


def snapshot(db):
    with closing(connect_existing(db, readonly=True)) as conn:
        conn.row_factory = sqlite3.Row
        return [dict(row) for row in conn.execute("SELECT * FROM effects ORDER BY id")]
