"""Exercise shell orchestration only; these stubs are not Lean replay evidence."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'check_kernel_replay.sh'


class ReplayDriverTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'scripts').mkdir()
        shutil.copyfile(SCRIPT, self.root / 'scripts/check_kernel_replay.sh')
        for directory in ('IntrospectionTwin', 'Test', 'Bypass', 'bin'):
            (self.root / directory).mkdir()
        for i in range(9):
            (self.root / f'IntrospectionTwin/M{i}.lean').touch()
        (self.root / 'IntrospectionTwin.lean').touch()
        (self.root / 'Test/NativeDecide.lean').touch()
        (self.root / 'Bypass/KernelBypass.lean').touch()
        self.env = dict(os.environ, PATH=str(self.root / 'bin') + os.pathsep + os.environ['PATH'],
                        LEAN4CHECKER='checker', FRESH='0', STUB_MODE='ok')
        self.executable('checker', '#!/bin/sh\nexit 0\n')
        self.executable('lake', '''#!/bin/sh
if [ "$1" = build ]; then
  [ "$STUB_MODE" != build_failure ]; exit $?
fi
[ "$STUB_MODE" != honest_failure ] || exit 1
[ "$STUB_MODE" != accept_poison ] || exit 0
[ "$STUB_MODE" != wrong_refusal ] || { echo wrong; exit 1; }
case "$3" in
  Bypass.KernelBypass) echo "'bypass_false' has type"; exit 1 ;;
  Test.NativeDecide) echo "_nativeDecide_"; exit 1 ;;
  Bypass.NewPoison) echo "unexpected poison"; exit 1 ;;
  --fresh) [ "$STUB_MODE" != fresh_failure ]; exit $? ;;
esac
exit 0
''')

    def executable(self, name, source):
        path = self.root / 'bin' / name
        path.write_text(source)
        path.chmod(0o755)

    def run_driver(self, success=False):
        result = subprocess.run(['bash', 'scripts/check_kernel_replay.sh'], cwd=self.root,
                                env=self.env, text=True, capture_output=True, timeout=10)
        self.assertEqual(result.returncode == 0, success, result.stdout + result.stderr)
        self.assertEqual('KERNEL REPLAY: PASS' in result.stdout, success)

    def test_valid_orchestration(self):
        self.run_driver(success=True)

    def test_build_failure(self):
        self.env['STUB_MODE'] = 'build_failure'
        self.run_driver()

    def test_honest_replay_failure(self):
        self.env['STUB_MODE'] = 'honest_failure'
        self.run_driver()

    def test_poison_must_not_be_accepted(self):
        self.env['STUB_MODE'] = 'accept_poison'
        self.run_driver()

    def test_refusal_reason_must_match(self):
        self.env['STUB_MODE'] = 'wrong_refusal'
        self.run_driver()

    def test_failed_discovery_with_partial_output(self):
        self.executable('find', '#!/bin/sh\n/usr/bin/find "$@"\nexit 1\n')
        self.run_driver()

    def test_new_bypass_module_is_replayed(self):
        (self.root / 'Bypass/NewPoison.lean').touch()
        self.run_driver()

    def test_missing_root_is_rejected(self):
        (self.root / 'IntrospectionTwin.lean').unlink()
        self.run_driver()

    def test_too_few_modules_is_rejected(self):
        (self.root / 'IntrospectionTwin/M0.lean').unlink()
        self.run_driver()

    def test_fresh_replay_failure(self):
        self.env.update(FRESH='1', STUB_MODE='fresh_failure')
        self.run_driver()


if __name__ == '__main__':
    unittest.main()
