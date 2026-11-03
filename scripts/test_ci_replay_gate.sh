#!/usr/bin/env bash
# Tests the same replay gate invoked in CI, without requiring the Lean toolchain.
set -euo pipefail
cd "$(dirname "$0")/.."

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

cat > "$tmp/pass.sh" <<'SCRIPT'
printf 'honest replay\nKERNEL REPLAY: PASS\n'
SCRIPT
cat > "$tmp/empty.sh" <<'SCRIPT'
exit 0
SCRIPT
cat > "$tmp/error.sh" <<'SCRIPT'
printf 'Permission denied\n' >&2
exit 126
SCRIPT
cat > "$tmp/fake_pass.sh" <<'SCRIPT'
printf 'KERNEL REPLAY: PASS\n'
exit 23
SCRIPT
cat > "$tmp/trailing_line.sh" <<'SCRIPT'
printf 'KERNEL REPLAY: PASS\nreplay incomplete\n'
SCRIPT
cat > "$tmp/substr.sh" <<'SCRIPT'
printf 'prefix KERNEL REPLAY: PASS\n'
SCRIPT

assert_accept() {
  local name="$1"
  if ! bash scripts/ci_replay_gate.sh "$tmp/$name.sh" "$tmp/$name.log" \
      "$tmp/$name.record" > "$tmp/$name.out" 2>&1; then
    echo "FAIL: expected acceptance for $name" >&2
    cat "$tmp/$name.out" >&2
    exit 1
  fi
  grep -qx 'observed_status: PASS' "$tmp/$name.record"
  grep -qx 'replay_exit_status: 0' "$tmp/$name.record"
  grep -qx 'tee_exit_status: 0' "$tmp/$name.record"
  echo "POSITIVE CONTROL ACCEPTED: $name"
}
assert_reject() {
  local name="$1"
  local expected="${2:-FAILED}"
  if bash scripts/ci_replay_gate.sh "$tmp/$name.sh" "$tmp/$name.log" \
      "$tmp/$name.record" > "$tmp/$name.out" 2>&1; then
    echo "FAIL: expected rejection for $name" >&2
    cat "$tmp/$name.out" >&2
    exit 1
  fi
  grep -qx "observed_status: $expected" "$tmp/$name.record"
  if [[ "$expected" == "NOT_RUN" ]]; then
    grep -qx 'replay_exit_status: NOT_OBSERVED' "$tmp/$name.record"
  fi
  echo "NEGATIVE CONTROL REJECTED: $name ($expected)"
}

# The fixtures are not executable: invoking a script with Bash must still work.
assert_accept pass
assert_reject empty
assert_reject error
assert_reject fake_pass
assert_reject trailing_line
assert_reject substr

# Old success must not survive into a subsequent empty replay.
printf 'KERNEL REPLAY: PASS\n' > "$tmp/empty.log"
assert_reject empty

# A missing script produces NOT_RUN, never an invented success or exit code.
assert_reject missing_script NOT_RUN

# A scheduled FRESH request cannot pass from a generic PASS marker alone.
if FRESH=1 bash scripts/ci_replay_gate.sh "$tmp/pass.sh" "$tmp/fresh_missing.log" \
    "$tmp/fresh_missing.record" > "$tmp/fresh_missing.out" 2>&1; then
  echo "FAIL: an unverified FRESH request was accepted" >&2
  exit 1
fi
grep -qx 'fresh_requested: true' "$tmp/fresh_missing.record"
grep -qx 'fresh_verified: false' "$tmp/fresh_missing.record"
grep -qx 'observed_status: FAILED' "$tmp/fresh_missing.record"

# A genuine fresh-replay log must independently carry the fresh completion marker.
cat > "$tmp/fresh.sh" <<'SCRIPT'
printf '  fresh replay ok IntrospectionTwin (+ all dependencies)\n'
printf 'KERNEL REPLAY: PASS\n'
SCRIPT
FRESH=1 bash scripts/ci_replay_gate.sh "$tmp/fresh.sh" "$tmp/fresh.log" \
    "$tmp/fresh.record" > "$tmp/fresh.out" 2>&1
grep -qx 'fresh_requested: true' "$tmp/fresh.record"
grep -qx 'fresh_verified: true' "$tmp/fresh.record"
grep -qx 'observed_status: PASS' "$tmp/fresh.record"

echo "REPLAY GATE CONTROLS: PASS"
