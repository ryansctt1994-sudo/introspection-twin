"""Conformance/operational controls; not additional scored forgery cases."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from portable_witness.core import RESPONSE_DOMAIN, canonical, initialize, make_payload, signed_receipt, snapshot
from portable_witness.evidence import classify, legitimate_control_valid, observe


class TaxonomyControls(unittest.TestCase):
    def test_fixed_categories_and_ambiguous_observations(self):
        fixtures = [
            ((False, True, True, True, True, False), "invalid-baseline"),
            ((True, False, True, False, False, False), "unattempted"),
            ((True, True, True, True, True, False), "refused"),
            ((True, True, True, True, False, True), "effect-without-refusal"),
            ((True, True, True, False, True, False), "refusal-without-ingress"),
            ((True, True, False, True, True, False), "unverifiable"),
            ((True, True, True, True, True, True), "unverifiable"),
            ((True, True, True, False, False, True), "unverifiable"),
            ((True, False, True, False, False, True), "unverifiable"),
            ((True, True, True, True, False, False), "unverifiable"),
        ]
        for args, expected in fixtures:
            with self.subTest(args=args):
                self.assertEqual(classify(*args), expected)


class BoundaryControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.fixture = self.root / "fixture"
        self.policy = initialize(self.fixture, "operational-control")
        self.state = self.fixture / "state"
        self.key = (self.fixture / "issuer.key").read_bytes()

    def receipt(self):
        return signed_receipt(make_payload(self.policy), self.key)

    def submit(self, raw, attempt):
        run = subprocess.run([sys.executable, "-m", "portable_witness", "submit", "--state", str(self.state),
                              "--attempt-id", attempt], input=raw, capture_output=True, timeout=20)
        events = [json.loads(line) for line in run.stdout.splitlines()]
        self.assertEqual(events[0]["kind"], "ingress")
        response = events[-1]
        Ed25519PublicKey.from_public_bytes((self.state / "witness.pub").read_bytes()).verify(
            bytes.fromhex(response["signature"]), RESPONSE_DOMAIN + canonical(response["payload"]))
        return run, response["payload"]

    def test_legitimate_effect_is_observed_separately(self):
        evidence = observe(self.state, self.receipt(), self.root / "evidence")
        self.assertTrue(legitimate_control_valid(evidence))
        self.assertEqual(len(evidence["before"]), 0)
        self.assertEqual(len(evidence["after"]), 1)

    def test_missing_state_is_not_recreated(self):
        db = self.state / "effects.sqlite"
        db.unlink()
        run, response = self.submit(self.receipt(), "missing-state")
        self.assertEqual(run.returncode, 1)
        self.assertFalse(response["authorized"])
        self.assertFalse(db.exists())

    def test_zero_byte_state_refuses(self):
        db = self.state / "effects.sqlite"
        db.write_bytes(b"")
        run, response = self.submit(self.receipt(), "zero-state")
        self.assertEqual(run.returncode, 1)
        self.assertFalse(response["authorized"])
        self.assertEqual(db.stat().st_size, 0)

    def test_concurrent_same_nonce_commits_once(self):
        raw = self.receipt()
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(self.submit, raw, "concurrent-" + str(n)) for n in (1, 2)]
            results = [f.result() for f in futures]
        self.assertEqual(sorted(r.returncode for r, _ in results), [0, 1])
        self.assertEqual(sum(p["authorized"] for _, p in results), 1)
        self.assertEqual(len(snapshot(self.state / "effects.sqlite")), 1)


if __name__ == "__main__":
    unittest.main()
