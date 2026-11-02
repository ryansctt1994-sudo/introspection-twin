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
  if ! bash scripts/ci_replay_gate.sh "$tmp/$name.sh" "$tmp/$name.log" > "$tmp/$name.out" 2>&1; then
    echo "FAIL: expected acceptance for $name" >&2
    cat "$tmp/$name.out" >&2
    exit 1
  fi
  echo "POSITIVE CONTROL ACCEPTED: $name"
}
assert_reject() {
  local name="$1"
  if bash scripts/ci_replay_gate.sh "$tmp/$name.sh" "$tmp/$name.log" > "$tmp/$name.out" 2>&1; then
    echo "FAIL: expected rejection for $name" >&2
    cat "$tmp/$name.out" >&2
    exit 1
  fi
  echo "NEGATIVE CONTROL REJECTED: $name"
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

echo "REPLAY GATE CONTROLS: PASS"
