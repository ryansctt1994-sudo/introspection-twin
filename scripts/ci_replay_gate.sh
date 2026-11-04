#!/usr/bin/env bash
# Evaluate actual replay execution and create an outcome-bound receipt only afterwards.
# No receipt is created by this gate if it is never invoked by CI.
# Optional third argument is the receipt filename; tests use a temporary file.
set -uo pipefail

replay_script="${1:-scripts/check_kernel_replay.sh}"
replay_log="${2:-replay.log}"
receipt_path="${3:-}"
if [[ -n "$receipt_path" ]]; then
  rm -f -- "$receipt_path" || exit 2
fi
: > "$replay_log" || exit 2

status="NOT_RUN"
replay_rc="NOT_OBSERVED"
tee_rc="NOT_OBSERVED"
if [[ ! -f "$replay_script" ]]; then
  echo "REPLAY GATE: NOT_RUN (script absent: $replay_script)" >> "$replay_log"
else
  # Do not let errexit discard the observed exit codes before recording them.
  bash "$replay_script" 2>&1 | tee "$replay_log"
  result=( "${PIPESTATUS[@]}" )
  replay_rc="${result[0]}"
  tee_rc="${result[1]}"
  status="FAILED"
fi

last_line=""
if [[ -f "$replay_log" ]]; then
  last_line="$(tail -n 1 "$replay_log")"
fi

fresh_requested="false"
fresh_verified="false"
if [[ "${FRESH:-0}" == "1" ]]; then
  fresh_requested="true"
  if grep -qxF '  fresh replay ok IntrospectionTwin (+ all dependencies)' "$replay_log"; then
    fresh_verified="true"
  fi
fi

if [[ "$status" != "NOT_RUN" && "$replay_rc" == "0" && "$tee_rc" == "0" \
      && "$last_line" == "KERNEL REPLAY: PASS" ]]; then
  if [[ "$fresh_requested" == "false" || "$fresh_verified" == "true" ]]; then
    status="PASS"
  fi
fi

# Pin the actual checked-out source tree (PR runs can be synthetic merge heads).
commit="$(git rev-parse HEAD 2>/dev/null)" || exit 2
tree="$(git rev-parse 'HEAD^{tree}' 2>/dev/null)" || exit 2
toolchain="$(cat lean-toolchain 2>/dev/null)" || exit 2

# The observation-bound record is written atomically AFTER exit-code capture.
# On a missing script, no replay exit status is invented: NOT_OBSERVED is literal.
if [[ -n "$receipt_path" ]]; then
  tmp_path="$receipt_path.tmp.$$"
  {
    echo "schema: ci-replay-observed-v1"
    echo "commit: $commit"
    echo "tree: $tree"
    echo "toolchain: $toolchain"
    echo "fresh_requested: $fresh_requested"
    echo "fresh_verified: $fresh_verified"
    echo "replay_exit_status: $replay_rc"
    echo "tee_exit_status: $tee_rc"
    echo "observed_status: $status"
    echo "last_replay_log_line: $last_line"
  } > "$tmp_path" && mv -- "$tmp_path" "$receipt_path" || exit 2
fi

if [[ "$status" != "PASS" ]]; then
  echo "REPLAY GATE: $status (replay exit $replay_rc, tee exit $tee_rc)" >&2
  exit 1
fi
echo "REPLAY GATE: PASS"
