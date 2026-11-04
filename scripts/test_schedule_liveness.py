#!/usr/bin/env python3
"""Adversarial metadata fixtures, not evidence of a scheduled Lean run."""
from copy import deepcopy
from datetime import timedelta
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import check_schedule_liveness as checker

ROOT = Path(__file__).resolve().parents[1]
POLICY = json.loads((ROOT / ".github/replay-schedule.json").read_text())
DUE = checker.timestamp(POLICY["first_expected_at"])


class ScheduleLiveness(unittest.TestCase):
    def setUp(self):
        self.observation = {"complete": True, "workflow": {
            "id": POLICY["workflow_id"], "path": POLICY["workflow_path"], "state": "active"},
            "runs": []}

    def run_fixture(self, **changes):
        run = {"id": 1, "workflow_id": POLICY["workflow_id"], "head_branch": "main",
               "head_sha": "a" * 40, "event": "schedule", "run_attempt": 1,
               "created_at": checker.iso(DUE + timedelta(minutes=2)),
               "updated_at": checker.iso(DUE + timedelta(minutes=8)),
               "status": "completed", "conclusion": "success", "html_url": "https://example.invalid/run/1"}
        run.update(changes)
        self.observation["runs"].append(run)
        return run

    def verdict(self, minutes=42):
        return checker.evaluate(POLICY, DUE, DUE + timedelta(minutes=minutes), self.observation)

    def test_deadline_turns_absence_into_finding(self):
        self.assertEqual(self.verdict(19)["status"], "AWAITING_RUN")
        result = self.verdict(21)
        self.assertEqual((result["status"], result["exit_code"]), ("MISSED_SCHEDULE", 1))

    def test_success_metadata_never_qualifies_replay(self):
        self.run_fixture()
        result = self.verdict()
        self.assertEqual(result["status"], "COMPLETED_ON_TIME")
        self.assertEqual(result["qualification"], "NOT_ASSESSED")

    def test_push_pr_dispatch_cannot_satisfy_schedule(self):
        for event in ("push", "pull_request", "workflow_dispatch"):
            with self.subTest(event=event):
                self.observation["runs"] = []
                self.run_fixture(event=event)
                self.assertEqual(self.verdict()["status"], "MISSED_SCHEDULE")

    def test_stale_or_other_workflow_or_branch_cannot_satisfy(self):
        for changes in ({"created_at": checker.iso(DUE - timedelta(days=1))},
                        {"workflow_id": 999}, {"head_branch": "branch"}):
            self.observation["runs"] = []
            self.run_fixture(**changes)
            self.assertEqual(self.verdict()["status"], "MISSED_SCHEDULE")

    def test_late_success_retains_finding(self):
        self.run_fixture(created_at=checker.iso(DUE + timedelta(minutes=21)))
        self.assertEqual(self.verdict()["status"], "LATE_RUN")

    def test_stuck_run_has_deadline(self):
        self.run_fixture(status="queued", conclusion=None)
        self.assertEqual(self.verdict(21)["status"], "RUNNING")
        self.assertEqual(self.verdict(41)["status"], "COMPLETION_OVERDUE")

    def test_failed_or_cancelled_run_is_not_success(self):
        for conclusion in ("failure", "cancelled", "timed_out", "skipped", None):
            self.observation["runs"] = []
            self.run_fixture(conclusion=conclusion)
            self.assertEqual(self.verdict()["status"], "RUN_FAILED")

    def test_late_completion_bound_not_certified(self):
        self.run_fixture(updated_at=checker.iso(DUE + timedelta(minutes=41)))
        self.assertEqual(self.verdict()["status"], "COMPLETION_NOT_VERIFIED_IN_WINDOW")

    def test_disabled_state_is_finding(self):
        self.observation["workflow"]["state"] = "disabled_inactivity"
        self.assertEqual(self.verdict()["status"], "WORKFLOW_NOT_ACTIVE")

    def test_incomplete_observation_never_proves_absence(self):
        self.observation["complete"] = False
        self.assertEqual(self.verdict()["status"], "INCONCLUSIVE")

    def test_rerun_and_duplicate_are_ambiguous(self):
        self.run_fixture(run_attempt=2)
        self.assertEqual(self.verdict()["status"], "INCONCLUSIVE")
        self.observation["runs"] = []
        self.run_fixture()
        self.run_fixture(id=2)
        self.assertEqual(self.verdict()["status"], "INCONCLUSIVE")

    def test_future_api_timestamp_is_inconclusive(self):
        self.run_fixture(created_at=checker.iso(DUE + timedelta(minutes=60)))
        self.assertEqual(self.verdict()["status"], "INCONCLUSIVE")

    def test_not_due_does_not_create_a_miss(self):
        self.assertEqual(self.verdict(-1)["status"], "NOT_DUE")

    def test_next_day_before_trigger_still_audits_previous_slot(self):
        self.assertEqual(checker.expected_slot(POLICY, DUE + timedelta(hours=23)), DUE)
        self.assertEqual(checker.expected_slot(POLICY, DUE - timedelta(hours=1)), DUE)

    def test_policy_matches_single_daily_cron(self):
        workflow = (ROOT / POLICY["workflow_path"]).read_text()
        lines = [line.strip() for line in workflow.splitlines() if "- cron:" in line]
        self.assertEqual(len(lines), 1)
        self.assertIn('"' + POLICY["cron_utc"] + '"', lines[0])

    def test_truncated_pagination_is_inconclusive_not_absence(self):
        def get(url):
            if "/runs?" not in url:
                return self.observation["workflow"]
            return {"total_count": 1, "workflow_runs": []}
        with self.assertRaisesRegex(ValueError, "incomplete"):
            checker.collect(POLICY, DUE, DUE + timedelta(hours=1), get)

    def test_api_failure_writes_inconclusive_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "receipt.json"
            args = ["check", "--policy", str(ROOT / ".github/replay-schedule.json"),
                    "--expected-at", "2020-01-01T00:00:00Z", "--output", str(output)]
            with patch("sys.argv", args), patch.object(checker, "collect", side_effect=OSError("API unavailable")), patch("builtins.print"):
                self.assertEqual(checker.main(), 2)
            self.assertEqual(json.loads(output.read_text())["status"], "INCONCLUSIVE")


if __name__ == "__main__":
    unittest.main()
