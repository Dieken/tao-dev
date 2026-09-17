"""The opt-in maintenance reviewer cannot silently use personal client state."""

from contextlib import contextmanager
import importlib.util
import os
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
            if os.name == 'posix':
                assert tmp_path.stat().st_mode & 0o777 == 0o700
                for stream in (kwargs['stdout'], kwargs['stderr']):
                    assert runner.os.fstat(stream.fileno()).st_mode & 0o777 == 0o600
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
    monkeypatch.setattr(runner, 'terminate', lambda process, number: observed.update(killed=process.pid))
    return observed


def test_review_uses_child_access_and_redacts_logs(tmp_path, monkeypatch):
    observed = fixture_runner(tmp_path, monkeypatch)
    tmp_path.chmod(0o755)
    result = runner.run_review(['fake-review'], 'synthetic fixture only', tmp_path, 30)
    # The workspace restriction is only claimed where the platform enforces it.
    assert result['workspace_restricted'] == (os.name == 'posix')
    assert result['exit_code'] == 0 and result['personal_configuration_unchanged']
    assert result['credentials_unchanged'] and result['error'] is None
    assert 'CLAUDE_CODE_OAUTH_TOKEN' not in observed['env']
    assert 'secret-test' not in (tmp_path / 'events.jsonl').read_text(encoding='utf-8')
    if os.name == 'posix':
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


@pytest.mark.parametrize('invalid', [False, 'severity', 'empty-summary', 'extra-field', 'duplicate-id',
                                     'provider-conflict'])
def test_runner_validates_the_record_before_advertising_it(tmp_path, monkeypatch, invalid):
    import json
    from types import SimpleNamespace
    bound = {'source_digest': 'a' * 64, 'policy_digest': 'b' * 64, 'change': 'CHG_fixture'}
    request = tmp_path / 'request.json'
    request.write_text(json.dumps({'outputs': {'request': {'binding': bound,
                       'required_reviews': ['independent-implementation-review']}}}), encoding='utf-8')
    monkeypatch.setattr(runner, 'ROOT', tmp_path)
    monkeypatch.setattr(runner, 'Project', lambda root: object())
    monkeypatch.setattr(runner, 'policy', lambda project: {})
    monkeypatch.setattr(runner, 'binding', lambda *args: bound)
    monkeypatch.setattr(runner.subprocess, 'run', lambda *args, **kwargs: SimpleNamespace(returncode=0))
    monkeypatch.setattr(runner.subprocess, 'check_output', lambda args, **kwargs:
                        'c' * 40 if 'rev-parse' in args else b'' if 'ls-files' in args else 'synthetic source')
    monkeypatch.setattr(runner.sys, 'argv', ['review_claude.py', '--request', str(request), '--tree', 'HEAD',
                                          '--reuse-claude-auth', '--files', 'example.py'])

    def fake_review(command, prompt, output, timeout):
        finding = dict(id='F1', severity='suggestion', location='example.py:1', problem='Example issue.',
                       disposition='open', rationale='Example evidence.')
        conclusion = dict(binding=bound, summary='Synthetic review.', findings=[finding], limitations=[])
        if invalid == 'severity':
            finding['severity'] = 'critical'
        elif invalid == 'empty-summary':
            conclusion['summary'] = ''
        elif invalid == 'extra-field':
            finding['rationale_note'] = ''
        elif invalid == 'duplicate-id':
            conclusion['findings'].append(dict(finding))
        result = dict(type='result', subtype='success', is_error=False, session_id='reviewer-context',
                      structured_output=conclusion, total_cost_usd=0)
        if invalid == 'provider-conflict':
            result['modelUsage'] = {'test-model': {'provider': 'different-provider'}}
        events = [dict(type='system', subtype='init', session_id='reviewer-context', apiProvider='test-provider'),
                  dict(type='assistant', message={'model': 'test-model'}), result]
        (output / 'events.jsonl').write_text('\n'.join(json.dumps(e) for e in events), encoding='utf-8')
        return dict(exit_code=0, timed_out=False, error=None, personal_configuration_unchanged=True,
                    credentials_unchanged=True)

    monkeypatch.setattr(runner, 'run_review', fake_review)
    assert runner.main() == (2 if invalid else 0)
    reports = list((tmp_path / 'tmp/tao/review-runs').glob('*/review.json'))
    assert len(reports) == (0 if invalid else 1)
    summaries = list((tmp_path / 'tmp/tao/review-runs').glob('*/summary.json'))
    assert len(summaries) == 1
    assert ('record_error' in json.loads(summaries[0].read_text(encoding='utf-8'))) is bool(invalid)
