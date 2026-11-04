#!/usr/bin/env bash
# Independent kernel replay: lean4checker re-checks the compiled .olean files in a fresh kernel,
# outside the process that built them. This closes the self-grading hole that `collectAxioms`
# cannot (see Bypass/KernelBypass.lean).
#
# Requires: lean4checker built for leanprover/lean4:v4.22.0
#   git clone https://github.com/leanprover/lean4checker && cd lean4checker
#   git checkout v4.22.0 && lake build
#   export LEAN4CHECKER=$PWD/.lake/build/bin/lean4checker
#
# Usage: scripts/check_kernel_replay.sh        (FRESH=1 also replays all dependencies, ~5 min)
#
# Passes only if:
#   * every library and honest test module replays cleanly, and
#   * both poisoned modules are REFUSED, each for its own expected reason.
set -u
cd "$(dirname "$0")/.."
LC="${LEAN4CHECKER:-lean4checker}"
command -v "$LC" >/dev/null 2>&1 || [ -x "$LC" ] || { echo "lean4checker not found (set LEAN4CHECKER)"; exit 1; }

lake build >/dev/null || { echo "FAIL: lake build"; exit 1; }
lake build Bypass >/dev/null || { echo "FAIL: lake build Bypass"; exit 1; }

fail=0
must_pass() {
  local out
  echo "  checker stdout+stderr: $1"
  if out=$(lake env "$LC" "$1" 2>&1); then
    printf '%s\n' "$out"
    echo "  replay ok      $1"
  else
    printf '%s\n' "$out"
    echo "  FAIL           $1 should replay cleanly:"
    fail=1
  fi
}
must_refuse() {  # module, expected substring of the refusal
  local out
  echo "  checker stdout+stderr: $1"
  if out=$(lake env "$LC" "$1" 2>&1); then
    printf '%s\n' "$out"
    echo "  FAIL           $1 replayed cleanly but must be refused"
    fail=1
  elif echo "$out" | grep -qF "$2"; then
    printf '%s\n' "$out"
    echo "  refused ok     $1  ($2)"
  else
    printf '%s\n' "$out"
    echo "  FAIL           $1 refused for the wrong reason:"
    fail=1
  fi
}

# Discover modules from the source tree: a module missing from a hand-written list would
# never be replayed. Every module is checked unless it is one of the two known-poisoned ones.
POISONED="Bypass.KernelBypass Test.NativeDecide"
mods=$(find IntrospectionTwin Test -name '*.lean' | sed 's/\.lean$//; s#/#.#g' | sort; echo IntrospectionTwin)
echo "Honest modules (must replay):"
n=0
for m in $mods; do
  case " $POISONED " in *" $m "*) continue ;; esac
  must_pass "$m"; n=$((n+1))
done
[ "$n" -ge 10 ] || { echo "  FAIL           only $n modules discovered; expected at least 10"; fail=1; }
echo "Poisoned modules (must be refused):"
must_refuse Bypass.KernelBypass "'bypass_false' has type"
must_refuse Test.NativeDecide "_nativeDecide_"

# Optional, slower (~5 min): replay the library AND every dependency (Init, Lean) from scratch.
if [ "${FRESH:-0}" = "1" ]; then
  # The CLI treats names as prefixes. A unique leaf importing IntrospectionTwin
  # selects exactly one .olean and carries its transitive Lean/Init dependencies.
  # Stream the actual checker diagnostics to the job log AND preserve the file.
  # Capture both exits before another command overwrites PIPESTATUS.
  echo "Fresh checker stdout+stderr: Test.FreshReplayRoot"
  lake env "$LC" --fresh Test.FreshReplayRoot 2>&1 | tee fresh-replay-output.txt
  fresh_status=( "${PIPESTATUS[@]}" )
  echo "fresh_checker_exit_status: ${fresh_status[0]}"
  echo "fresh_log_tee_exit_status: ${fresh_status[1]}"
  if [[ "${fresh_status[0]}" == "0" && "${fresh_status[1]}" == "0" ]]; then
    echo "  fresh replay ok IntrospectionTwin (+ all dependencies)"
  else
    echo "  FAIL           fresh replay of IntrospectionTwin"
    fail=1
  fi
fi

[ $fail -eq 0 ] && echo "KERNEL REPLAY: PASS" || echo "KERNEL REPLAY: FAIL"
exit $fail
