#!/usr/bin/env bash
# Logging/exit propagation controls using a mock checker, not Lean replay evidence.
set -euo pipefail
cd "$(dirname "$0")/.."
test_root="$(mktemp -d)"
trap 'rm -rf "$test_root"' EXIT
mkdir -p "$test_root/fixture/scripts" "$test_root/bin"
cp scripts/check_kernel_replay.sh "$test_root/fixture/scripts/"
cp -R IntrospectionTwin Test "$test_root/fixture/"
real_tee="$(command -v tee)"
export real_tee
cat > "$test_root/bin/lake" <<'SCRIPT'
#!/usr/bin/env bash
case "$1" in
  build) exit 0 ;;
  env) shift; exec "$@" ;;
  *) exit 90 ;;
esac
SCRIPT
cat > "$test_root/bin/checker" <<'SCRIPT'
#!/usr/bin/env bash
printf 'CHECKER_STDERR:%s\n' "$1" >&2
case "$1" in
  --fresh) exit "${MOCK_FRESH_EXIT:-0}" ;;
  Bypass.KernelBypass) printf "'bypass_false' has type\n" >&2; exit 1 ;;
  Test.NativeDecide) printf '_nativeDecide_\n' >&2; exit 1 ;;
  *) exit 0 ;;
esac
SCRIPT
cat > "$test_root/bin/tee" <<'SCRIPT'
#!/usr/bin/env bash
"$real_tee" "$@" || exit "$?"
exit "${MOCK_TEE_EXIT:-0}"
SCRIPT
chmod +x "$test_root/bin/lake" "$test_root/bin/checker" "$test_root/bin/tee"
export PATH="$test_root/bin:$PATH"
export LEAN4CHECKER="$test_root/bin/checker"

# Green baseline: success still exposes actual stderr in the job stream and file.
FRESH=1 bash "$test_root/fixture/scripts/check_kernel_replay.sh" > "$test_root/green.log" 2>&1
grep -qx 'CHECKER_STDERR:IntrospectionTwin.Gate' "$test_root/green.log"
grep -qx 'CHECKER_STDERR:--fresh' "$test_root/green.log"
grep -qx 'CHECKER_STDERR:--fresh' "$test_root/fixture/fresh-replay-output.txt"
grep -qx 'fresh_checker_exit_status: 0' "$test_root/green.log"
grep -qx 'fresh_log_tee_exit_status: 0' "$test_root/green.log"
[[ "$(tail -n 1 "$test_root/green.log")" == 'KERNEL REPLAY: PASS' ]]

if FRESH=1 MOCK_FRESH_EXIT=23 bash "$test_root/fixture/scripts/check_kernel_replay.sh" \
    > "$test_root/checker-red.log" 2>&1; then
  echo 'FAIL: fresh checker failure was masked' >&2
  exit 1
fi
grep -qx 'CHECKER_STDERR:--fresh' "$test_root/checker-red.log"
grep -qx 'fresh_checker_exit_status: 23' "$test_root/checker-red.log"
[[ "$(tail -n 1 "$test_root/checker-red.log")" == 'KERNEL REPLAY: FAIL' ]]

if FRESH=1 MOCK_TEE_EXIT=73 bash "$test_root/fixture/scripts/check_kernel_replay.sh" \
    > "$test_root/logger-red.log" 2>&1; then
  echo 'FAIL: checker log capture failure was masked' >&2
  exit 1
fi
grep -qx 'fresh_checker_exit_status: 0' "$test_root/logger-red.log"
grep -qx 'fresh_log_tee_exit_status: 73' "$test_root/logger-red.log"
[[ "$(tail -n 1 "$test_root/logger-red.log")" == 'KERNEL REPLAY: FAIL' ]]
echo 'CHECKER DIAGNOSTIC CONTROLS: PASS (mock checker; not kernel evidence)'
