"""Guard GitHub's actual shell step against tee masking a failed Lean build.

These test CI orchestration with a stub executable, not Lean/kernel evidence.
"""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import textwrap
import unittest

WORKFLOW = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "ci.yml"
STEP = "      - name: Build library and run hostile suite"


def build_step() -> str:
    """Read commands from the checked-in CI step, not a test-only copy."""
    lines = WORKFLOW.read_text(encoding="utf-8").splitlines()
    idx = next((i for i, line in enumerate(lines) if line.startswith(STEP)), None)
    if idx is None or lines[idx + 1].strip() != "run: |":
        raise ValueError("required Lean build step missing or malformed")
    body = []
    for line in lines[idx + 2 :]:
        if line and not line.startswith("          "):
            break
        body.append(line)
    if not body:
        raise ValueError("empty build script")
    return textwrap.dedent("\n".join(body))


class BuildPipelineTests(unittest.TestCase):
    def run_step(self, status: int, output: str = "build ok") -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            binary = root / "bin"
            binary.mkdir()
            fake_lake = binary / "lake"
            fake_lake.write_text(
                "#!/bin/sh\nprintf '%s\\n' " + repr(output) + "\nexit " + str(status) + "\n",
                encoding="utf-8",
            )
            fake_lake.chmod(0o755)
            env = dict(os.environ, PATH=str(binary) + os.pathsep + os.environ.get("PATH", ""))
            return subprocess.run(
                ["bash", "-e", "-c", build_step()],
                cwd=root, env=env, capture_output=True, text=True, timeout=10,
            )

    def test_successful_build_passes(self):
        result = self.run_step(0)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_failed_build_fails_even_when_tee_succeeds(self):
        result = self.run_step(17, output="BUILD FAILED")
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_warning_fails_even_when_build_succeeds(self):
        result = self.run_step(0, output="warning: would be silently accepted")
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
