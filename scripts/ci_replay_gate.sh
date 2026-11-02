#!/usr/bin/env bash
# Fail closed unless the replay command exits zero AND ends with the exact PASS sentinel.
# The overridable command is used only by the negative-control test harness.
set -euo pipefail

replay_script="${1:-scripts/check_kernel_replay.sh}"
replay_log="${2:-replay.log}"

# An old successful result must not survive into a later failed run.
: > "$replay_log"

# bash invocation does not require the checkout to retain an executable file bit.
# pipefail prevents tee from masking the replay process exit code.
bash "$replay_script" 2>&1 | tee "$replay_log"

if [[ "$(tail -n 1 "$replay_log")" != "KERNEL REPLAY: PASS" ]]; then
  echo "REPLAY GATE: FAIL (missing exact final PASS sentinel)" >&2
  exit 1
fi

echo "REPLAY GATE: PASS"
