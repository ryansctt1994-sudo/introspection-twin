"""Guard the checked-in kernel-replay CI step against tee masking.

These tests exercise workflow orchestration with a stub script. They are not
Lean replay evidence and do not establish an independent witness.
"""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import textwrap
import unittest

WORKFLOW = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "ci.yml"
STEP = "      - name: Independent kernel replay"


def replay_step() -> str:
    """Read commands from the checked-in CI step, not a test-only copy."""
    lines = WORKFLOW.read_text(encoding="utf-8").splitlines()
    idx = next((i for i, line in enumerate(lines) if line.startswith(STEP)), None)
    if idx is None or lines[idx + 1].strip() != "env:":
        raise ValueError("required kernel replay step missing or malformed")
    body_at = next(
        (i for i in range(idx + 1, len(lines)) if lines[i].strip() == "run: |"),
        None,
    )
    if body_at is None:
        raise ValueError("kernel replay run block missing")
    body = []
    for line in lines[body_at + 1 :]:
        if line and not line.startswith("          "):
            break
        body.append(line)
    if not body:
        raise ValueError("empty replay script")
    return textwrap.dedent("\n".join(body))


class ReplayPipelineTests(unittest.TestCase):
    def run_step(self, status: int, output: str) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            scripts = root / "scripts"
            scripts.mkdir()
            stub = scripts / "check_kernel_replay.sh"
            stub.write_text(
                "#!/bin/sh\nprintf '%s\\n' " + repr(output) + "\nexit " + str(status) + "\n",
                encoding="utf-8",
            )
            stub.chmod(0o755)
            return subprocess.run(
                ["bash", "-e", "-c", replay_step()],
                cwd=root,
                env=dict(os.environ),
                capture_output=True,
                text=True,
                timeout=10,
            )

    def test_exact_pass_marker_succeeds(self):
        result = self.run_step(0, "KERNEL REPLAY: PASS")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("KERNEL REPLAY: PASS", result.stdout)

    def test_failed_replay_fails_even_when_tee_succeeds(self):
        result = self.run_step(17, "KERNEL REPLAY: FAIL")
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_zero_exit_without_exact_pass_marker_fails(self):
        result = self.run_step(0, "KERNEL REPLAY: PASS ")
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_pass_marker_cannot_mask_nonzero_exit(self):
        result = self.run_step(9, "KERNEL REPLAY: PASS")
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
