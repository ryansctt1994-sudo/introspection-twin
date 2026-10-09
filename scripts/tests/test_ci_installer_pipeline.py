"""Exercise the checked-in elan installer step with controlled curl failures.

This is CI shell orchestration evidence only, not Lean/kernel verification.
The stub simulates downloaded installer output; no network or installer runs.
"""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import textwrap
import unittest

WORKFLOW = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "ci.yml"
STEP = "      - name: Install elan (toolchain comes from lean-toolchain)"


def installer_step() -> str:
    lines = WORKFLOW.read_text(encoding="utf-8").splitlines()
    idx = next((i for i, line in enumerate(lines) if line == STEP), None)
    if idx is None or idx + 1 >= len(lines) or lines[idx + 1].strip() != "run: |":
        raise ValueError("elan install step missing or malformed")
    body = []
    for line in lines[idx + 2:]:
        if line and not line.startswith("          "):
            break
        body.append(line)
    if not body:
        raise ValueError("empty elan install script")
    return textwrap.dedent("\n".join(body))


class InstallerPipelineTests(unittest.TestCase):
    def run_step(self, mode: str) -> tuple[subprocess.CompletedProcess[str], str]:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            curl = bin_dir / "curl"
            curl.write_text(
                "#!/bin/sh\n"
                "case \"$STUB_MODE\" in\n"
                "  fail_download) exit 17 ;;\n"
                "  fail_install) printf 'exit 23\\n'; exit 0 ;;\n"
                "  good) printf 'exit 0\\n'; exit 0 ;;\n"
                "  *) exit 99 ;;\n"
                "esac\n", encoding="utf-8",
            )
            curl.chmod(0o755)
            github_path = root / "github_path"
            env = dict(
                os.environ,
                PATH=str(bin_dir) + os.pathsep + os.environ.get("PATH", ""),
                STUB_MODE=mode,
                GITHUB_PATH=str(github_path),
            )
            result = subprocess.run(
                ["bash", "-e", "-c", installer_step()], cwd=root, env=env,
                capture_output=True, text=True, timeout=10,
            )
            return result, github_path.read_text() if github_path.exists() else ""

    def test_successful_installer_succeeds(self):
        result, path = self.run_step("good")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("/.elan/bin", path)

    def test_failed_download_fails_even_when_shell_accepts_empty_input(self):
        result, path = self.run_step("fail_download")
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(path, "")

    def test_downloaded_installer_failure_fails(self):
        result, path = self.run_step("fail_install")
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(path, "")


if __name__ == "__main__":
    unittest.main()
