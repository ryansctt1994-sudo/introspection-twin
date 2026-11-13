#!/usr/bin/env python3
"""Observe schedule delivery/completion, never infer kernel replay qualification.

Exit 0: on-time successful completion metadata; 1: liveness/execution finding;
2: inconclusive observation; 3: not due or within a declared waiting window.
Works outside Actions with the public read-only API; GITHUB_TOKEN is optional.
"""
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
from urllib.parse import urlencode
from urllib.request import Request, urlopen

UTC = timezone.utc


def timestamp(value):
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.utcoffset() != timedelta(0):
        raise ValueError("timestamps must be UTC and timezone-aware")
    return result


def iso(value):
    return value.isoformat(timespec="seconds").replace("+00:00", "Z")


def expected_slot(policy, now):
    minute, hour, day, month, weekday = policy["cron_utc"].split()
    if (day, month, weekday) != ("*", "*", "*"):
        raise ValueError("only a single daily UTC schedule is supported")
    due = now.replace(hour=int(hour), minute=int(minute), second=0, microsecond=0)
    if due > now:
        due -= timedelta(days=1)
    return max(due, timestamp(policy["first_expected_at"]))


def api_json(url):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "replay-liveness-v1"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    with urlopen(Request(url, headers=headers), timeout=30) as response:
        return json.load(response)


def collect(policy, due, now, get=api_json):
    """Retain queried data; incomplete pagination never proves absence."""
    base = "https://api.github.com/repos/" + policy["repository"]
    workflow_url = base + "/actions/workflows/" + str(policy["workflow_id"])
    workflow = get(workflow_url)
    end = min(now, due + timedelta(days=1) - timedelta(seconds=1))
    query = urlencode({"event": "schedule", "branch": policy["branch"],
                       "created": iso(due) + ".." + iso(end), "per_page": 100})
    url = workflow_url + "/runs?" + query
    runs = []
    queries = [workflow_url]
    total = None
    for page in range(1, 11):
        page_url = url + "&page=" + str(page)
        data = get(page_url)
        queries.append(page_url)
        if total is not None and total != data["total_count"]:
            raise ValueError("run listing changed during pagination; retry observation")
        total = data["total_count"]
        runs.extend(data["workflow_runs"])
        if len(runs) >= total:
            break
    if len(runs) != total or len({r["id"] for r in runs}) != total:
        raise ValueError("incomplete or duplicate run listing")
    return {"workflow": workflow, "runs": runs, "complete": True, "queries": queries}


def evaluate(policy, due, now, observation):
    arrival = due + timedelta(seconds=policy["arrival_grace_seconds"])
    completion = due + timedelta(seconds=policy["completion_grace_seconds"])
    result = {
        "schema": "schedule-liveness-v1", "repository": policy["repository"],
        "workflow_id": policy["workflow_id"], "expected_at": iso(due),
        "arrival_deadline": iso(arrival), "completion_deadline": iso(completion),
        "observed_at": iso(now), "qualification": "NOT_ASSESSED",
        "independence": "SAME_PRINCIPAL; no independent witness claimed",
        "slot_attribution": "API creation-time window; verify trigger-record.json for exact cron",
    }

    def finish(status, code):
        result.update(status=status, exit_code=code)
        return result

    if not 0 < policy["arrival_grace_seconds"] < policy["completion_grace_seconds"] < 86400:
        return finish("INCONCLUSIVE", 2)
    if now < due:
        return finish("NOT_DUE", 3)
    result["observation"] = observation
    if not observation.get("complete"):
        return finish("INCONCLUSIVE", 2)
    workflow = observation["workflow"]
    if workflow["id"] != policy["workflow_id"] or workflow["path"] != policy["workflow_path"]:
        return finish("INCONCLUSIVE", 2)
    result["workflow_state"] = workflow["state"]
    if workflow["state"] != "active":
        return finish("WORKFLOW_NOT_ACTIVE", 1)
    runs = [r for r in observation["runs"] if
            r["event"] == "schedule" and r["workflow_id"] == policy["workflow_id"] and
            r["head_branch"] == policy["branch"] and
            due <= timestamp(r["created_at"]) < due + timedelta(days=1)]
    if any(timestamp(r["created_at"]) > now for r in runs):
        return finish("INCONCLUSIVE", 2)
    if not runs:
        return finish("MISSED_SCHEDULE", 1) if now > arrival else finish("AWAITING_RUN", 3)
    if len(runs) != 1 or runs[0]["run_attempt"] != 1:
        return finish("INCONCLUSIVE", 2)
    run = runs[0]
    result["run"] = {k: run[k] for k in (
        "id", "html_url", "head_sha", "event", "run_attempt", "created_at", "status", "conclusion")}
    created = timestamp(run["created_at"])
    result["dispatch_lag_seconds"] = (created - due).total_seconds()
    result["execution_duration_seconds"] = None
    result["execution_duration_upper_bound_seconds"] = None
    if run.get("run_started_at"):
        started = timestamp(run["run_started_at"])
        if created <= started <= now:
            result["queue_delay_seconds"] = (started - created).total_seconds()
            if run["status"] == "completed":
                if run.get("completed_at"):
                    ended = timestamp(run["completed_at"])
                    if started <= ended <= now:
                        result["execution_duration_seconds"] = (ended - started).total_seconds()
                elif run.get("updated_at"):
                    updated = timestamp(run["updated_at"])
                    if started <= updated <= now:
                        result["execution_duration_upper_bound_seconds"] = (updated - started).total_seconds()
    if timestamp(run["created_at"]) > arrival:
        return finish("LATE_RUN", 1)
    if run["status"] != "completed":
        return finish("COMPLETION_OVERDUE", 1) if now > completion else finish("RUNNING", 3)
    if run["conclusion"] != "success":
        return finish("RUN_FAILED", 1)
    # updated_at is only a conservative upper bound on completion, not a precise
    # finish time. A later bound cannot certify an on-time completion.
    updated = timestamp(run["updated_at"])
    if updated < timestamp(run["created_at"]) or updated > now:
        return finish("INCONCLUSIVE", 2)
    if updated > completion:
        return finish("COMPLETION_NOT_VERIFIED_IN_WINDOW", 1)
    return finish("COMPLETED_ON_TIME", 0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", default=".github/replay-schedule.json")
    parser.add_argument("--expected-at", help="explicit UTC slot; default is most recent configured slot")
    parser.add_argument("--output", default="schedule-liveness.json")
    args = parser.parse_args()
    now = datetime.now(UTC)
    try:
        raw = Path(args.policy).read_bytes()
        policy = json.loads(raw)
        due = timestamp(args.expected_at) if args.expected_at else expected_slot(policy, now)
        observation = collect(policy, due, now) if now >= due else {}
        result = evaluate(policy, due, now, observation)
        result["policy_sha256"] = hashlib.sha256(raw).hexdigest()
    except Exception as error:
        result = {"schema": "schedule-liveness-v1", "status": "INCONCLUSIVE", "exit_code": 2,
                  "observed_at": iso(now), "qualification": "NOT_ASSESSED",
                  "error": type(error).__name__ + ": " + str(error)}
    text = json.dumps(result, indent=2) + "\n"
    destination = Path(args.output)
    temporary = destination.with_name(destination.name + ".tmp")
    temporary.write_text(text)
    temporary.replace(destination)
    print(text, end="")
    return result["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
