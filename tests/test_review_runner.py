"""The opt-in maintenance reviewer cannot silently use personal client state."""

from contextlib import contextmanager
import importlib.util
from pathlib import Path
import subprocess

import pytest

SPEC = importlib.util.spec_from_file_location(
    'maintenance_review_runner', Path(__file__).resolve().parents[1] / 'scripts/review_claude.py')
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


def fixture_runner(tmp_path, monkeypatch, *, changed=False, expired=False, timeout=False):
    states = iter([{'config': 'before'}, {'config': 'after' if changed else 'before'}])
    monkeypatch.setattr(runner, 'global_configuration', lambda: next(states))
    observed = {}

    @contextmanager
    def access(workspace, seconds):
        assert workspace == tmp_path and seconds == 30
        if expired:
            raise RuntimeError('No refresh attempted.')
        env = {'CLAUDE_CONFIG_DIR': str(workspace / 'client-config'),
               'CLAUDE_CODE_OAUTH_TOKEN': 'secret-test'}
        observed['env'] = env
        try:
            yield env, ['secret-test']
        finally:
            env.pop('CLAUDE_CODE_OAUTH_TOKEN', None)

    class Process:
        pid = 12345
        returncode = None

        def __init__(self, command, **kwargs):
            observed['started'] = True
            assert kwargs['env']['CLAUDE_CODE_OAUTH_TOKEN'] == 'secret-test'
            assert kwargs['env']['CLAUDE_CONFIG_DIR'] == str(tmp_path / 'client-config')
            assert kwargs['cwd'] == tmp_path and kwargs['start_new_session']
            kwargs['stdout'].write('secret-test\n')

        def communicate(self, prompt, timeout):
            assert prompt == 'synthetic fixture only'
            if timeout and observed.get('timeout'):
                raise subprocess.TimeoutExpired('fake-review', timeout)
            self.returncode = 0

        def poll(self):
            return self.returncode

        def wait(self, timeout=None):
            self.returncode = -15
            return self.returncode

    observed['timeout'] = timeout
    monkeypatch.setattr(runner, 'access_environment', access)
    monkeypatch.setattr(runner.subprocess, 'Popen', Process)
    monkeypatch.setattr(runner.os, 'killpg', lambda pid, sig: observed.update(killed=pid))
    return observed


def test_review_uses_child_access_and_redacts_logs(tmp_path, monkeypatch):
    observed = fixture_runner(tmp_path, monkeypatch)
    result = runner.run_review(['fake-review'], 'synthetic fixture only', tmp_path, 30)
    assert result['exit_code'] == 0 and result['personal_configuration_unchanged']
    assert result['credentials_unchanged'] and result['error'] is None
    assert 'CLAUDE_CODE_OAUTH_TOKEN' not in observed['env']
    assert 'secret-test' not in (tmp_path / 'events.jsonl').read_text()
    assert (tmp_path / 'client-config').stat().st_mode & 0o777 == 0o700
    assert not list(tmp_path.rglob('.credentials.json'))


@pytest.mark.parametrize('changed,expired,timeout', [(True, False, False), (False, True, False), (False, False, True)])
def test_review_failures_cannot_become_importable_results(tmp_path, monkeypatch, changed, expired, timeout):
    observed = fixture_runner(tmp_path, monkeypatch, changed=changed, expired=expired, timeout=timeout)
    result = runner.run_review(['fake-review'], 'synthetic fixture only', tmp_path, 30)
    assert not runner.review_succeeded(result)
    if changed:
        assert result['changed_files'] == ['config']
    if expired:
        assert 'started' not in observed and result['error'] == 'RuntimeError'
    if timeout:
        assert observed['killed'] == 12345 and result['timed_out']
    assert not (tmp_path / 'review.json').exists()


@pytest.mark.parametrize('options', [[], ['--reuse-claude-auth', '--timeout', '0'],
                                   ['--reuse-claude-auth', '--budget-usd', 'nan']])
def test_invalid_review_invocation_stops_before_reading_inputs(monkeypatch, options):
    monkeypatch.setattr(runner.sys, 'argv', ['review_claude.py', '--request', 'absent.json',
                                          '--tree', 'unresolved', '--files', 'README.md', *options])
    with pytest.raises(SystemExit) as result:
        runner.main()
    assert result.value.code == 2
