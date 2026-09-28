"""Credential lifetime and native-discovery boundaries; no real client calls."""

import base64
import json
import os
import stat
import time
from pathlib import Path

import pytest
from acceptance import isolated_codex as adapter


def fake_auth(tmp_path, monkeypatch, *, expires=600):
    home = tmp_path / 'personal'
    (home / '.codex').mkdir(parents=True)
    payload = base64.urlsafe_b64encode(json.dumps({'exp': time.time() + expires}).encode()).decode().rstrip('=')
    auth = home / '.codex/auth.json'
    auth.write_text(json.dumps({'auth_mode': 'chatgpt', 'tokens': {
        'access_token': 'header.' + payload + '.signature',
        'refresh_token': 'must-never-be-copied', 'id_token': 'test-id', 'account_id': 'test-account'}}), encoding='utf-8')
    (home / '.codex/config.toml').write_text('model = "configured-model"\n', encoding='utf-8')
    monkeypatch.setattr(Path, 'home', lambda: home)
    workspace = tmp_path / 'experiment'
    state = workspace / 'client-state'
    state.mkdir(parents=True)
    (state / 'config.toml').write_text('check_for_update_on_startup = false\n', encoding='utf-8')
    return workspace, auth


def test_access_copy_excludes_refresh_and_cleans_up_after_failure(tmp_path, monkeypatch):
    workspace, source = fake_auth(tmp_path, monkeypatch)
    before = source.read_bytes()
    config = workspace / 'client-state/config.toml'
    original_config = config.read_bytes()
    copy = workspace / 'client-state/auth.json'
    with pytest.raises(RuntimeError, match='probe failed'), adapter.access_snapshot(workspace, 90):
        if os.name == 'posix':
            assert stat.S_IMODE(copy.stat().st_mode) == 0o600
            assert json.loads(copy.read_text(encoding='utf-8'))['tokens']['refresh_token'] == ''
            assert 'must-never-be-copied' not in copy.read_text(encoding='utf-8')
        raise RuntimeError('probe failed')
    assert not copy.exists()
    assert source.read_bytes() == before
    assert config.read_bytes() == original_config
    with adapter.access_snapshot(workspace, 90):
        assert copy.exists()
    assert not copy.exists()


def test_expiring_access_fails_before_writing_credentials(tmp_path, monkeypatch):
    workspace, source = fake_auth(tmp_path, monkeypatch, expires=150)
    before = source.read_bytes()
    with pytest.raises(RuntimeError, match='no refresh'), adapter.access_snapshot(workspace, 90):
        pytest.fail('Expired credentials must not be exposed.')
    assert not (workspace / 'client-state/auth.json').exists()
    assert source.read_bytes() == before


@pytest.mark.parametrize('outside', [[], [{'name': 'tao-dev'}]])
def test_actual_skill_discovery_controls_boundary(tmp_path, monkeypatch, outside):
    inside = tmp_path / 'codex/inside'
    rows = {str(inside): [{'path': str(tmp_path / 'client-state/plugins/tao-dev/SKILL.md')}],
            str(tmp_path / 'codex/outside'): outside}
    monkeypatch.setattr(adapter, 'skills', lambda *args: rows)
    if outside:
        with pytest.raises(RuntimeError, match='inside-only'):
            adapter.check_boundary(tmp_path, inside)
    else:
        assert adapter.check_boundary(tmp_path, inside) == rows


def test_secret_values_are_removed_from_probe_logs(tmp_path):
    log = tmp_path / 'events.jsonl'
    log.write_text('token-secret token-secret visible', encoding='utf-8')
    adapter.redact([log], ['token-secret'])
    assert log.read_text(encoding='utf-8') == '[REDACTED] [REDACTED] visible'


def test_codex_compatibility_package_has_one_manifest_and_original_runtime(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(adapter.ROOT / 'scripts'))
    from package_plugin import SOURCE, build
    target = build(tmp_path / 'plugin', codex_legacy=True)
    assert not (target / 'plugin.json').exists()
    assert not (target / '.claude-plugin').exists()
    assert not (target / 'commands').exists()
    manifest = json.loads((target / '.codex-plugin/plugin.json').read_text(encoding='utf-8'))
    assert manifest['hooks'] == './com.openai/hooks/hooks.json'
    for folder in ('skills', 'com.openai'):
        for source in (SOURCE / folder).rglob('*'):
            if source.is_file() and '__pycache__' not in source.parts:
                assert (target / source.relative_to(SOURCE)).read_bytes() == source.read_bytes()
    with pytest.raises(ValueError, match='must be new'):
        build(target, codex_legacy=True)


def fake_app_server(monkeypatch, messages):
    class Input:
        def __init__(self):
            self.writes = []

        def write(self, value):
            self.writes.append(value)

        def flush(self):
            pass

        def close(self):
            pass

    class Output:
        def __iter__(self):
            return iter((json.dumps(message) if not isinstance(message, str) else message) + '\n'
                        for message in messages)

        def close(self):
            pass

    class Process:
        pid = 123

        def __init__(self):
            self.stdin = Input()
            self.stdout = Output()
            self.terminated = False

        def poll(self):
            return 0 if self.terminated else None

        def terminate(self):
            self.terminated = True

        def wait(self, timeout=None):
            self.terminated = True
            return 0

    process = Process()
    calls = []

    def start(*args, **kwargs):
        calls.append((args, kwargs))
        return process

    monkeypatch.setattr(adapter.subprocess, 'Popen', start)
    monkeypatch.setattr(adapter, '_terminate_process_tree',
                        lambda child, force=False: child.terminate())
    return process, calls


def test_native_discovery_uses_portable_bounded_pipe_reader(tmp_path, monkeypatch):
    process, calls = fake_app_server(monkeypatch, [
        {'method': 'server/notification', 'params': {}},
        {'id': 1, 'result': {}},
        {'id': 2, 'result': {'data': [{'cwd': str(tmp_path)}]}},
    ])

    result = adapter.discover(tmp_path, [tmp_path], 'skills')

    assert result == [{'cwd': str(tmp_path)}]
    assert calls[0][1]['text'] is True
    assert calls[0][1]['encoding'] == 'utf-8'
    assert calls[0][1]['start_new_session'] is (os.name != 'nt')
    requests = [json.loads(value) for value in process.stdin.writes]
    assert [request['method'] for request in requests] == ['initialize', 'initialized', 'skills/list']
    assert requests[2]['params'] == {'cwds': [str(tmp_path)], 'forceReload': True}
    assert process.terminated


def test_native_discovery_deadline_is_not_extended_by_queued_notifications(tmp_path, monkeypatch):
    process, _ = fake_app_server(monkeypatch, [
        {'id': 1, 'result': {}},
        {'method': 'server/notification', 'params': {}},
        'invalid JSON that must remain unread after the deadline',
    ])
    moments = iter((0, 0, 0, 0, 20))
    monkeypatch.setattr(adapter.time, 'monotonic', lambda: next(moments))

    with pytest.raises(RuntimeError, match='bounded response'):
        adapter.discover(tmp_path, [tmp_path], 'skills')

    assert process.terminated


def test_unexpected_hooks_cannot_be_trusted(tmp_path, monkeypatch):
    inside = tmp_path / 'codex/inside'
    monkeypatch.setattr(adapter, 'hook_inventory', lambda *args: [
        {'cwd': str(inside), 'errors': [], 'warnings': [], 'hooks': [{}, {}]}])
    with pytest.raises(RuntimeError, match='exactly one known hook'):
        adapter.trust_test_hook(tmp_path, inside, tmp_path / 'plugin')
    assert not (tmp_path / 'client-state/config.toml').exists()


@pytest.mark.parametrize('symlink', [False, True])
def test_private_logs_never_overwrite_existing_files(tmp_path, symlink):
    from acceptance.isolated_codex import private_log
    target = tmp_path / 'existing'
    target.write_text('keep these bytes', encoding='utf-8')
    log = tmp_path / 'log' if symlink else target
    if symlink:
        log.symlink_to(target)
    with pytest.raises(FileExistsError):
        private_log(log)
    assert target.read_text(encoding='utf-8') == 'keep these bytes'



def provider_auth(tmp_path, monkeypatch, *, env_key=False):
    home = tmp_path / 'personal'
    (home / '.codex').mkdir(parents=True)
    token = 'opaque-provider-token'
    credential = 'TAO_TEST_CODEX_TOKEN'
    provider_key = 'env_key' if env_key else 'experimental_bearer_token'
    value = provider_key + ' = ' + (json.dumps(token) if not env_key else json.dumps(credential))
    config = (
        'model = "provider-model"\n'
        'model_provider = "test-provider"\n'
        'model_reasoning_summary = "none"\n'
        '[model_providers."test-provider"]\n'
        'base_url = "https://models.example.test/v1"\n'
        + value + '\n'
        'requires_openai_auth = false\n'
    )
    (home / '.codex/config.toml').write_text(config, encoding='utf-8')
    if env_key:
        monkeypatch.setenv(credential, token)
    monkeypatch.setattr(Path, 'home', lambda: home)
    workspace = tmp_path / 'experiment'
    state = workspace / 'client-state'
    state.mkdir(parents=True)
    original = 'check_for_update_on_startup = false\n'
    (state / 'config.toml').write_text(original, encoding='utf-8')
    return workspace, state / 'config.toml', token, original


def test_provider_bearer_is_scoped_and_cleaned_up(tmp_path, monkeypatch):
    workspace, config, token, original = provider_auth(tmp_path, monkeypatch)
    with adapter.access_snapshot(workspace, 90) as secrets:
        assert secrets == [token]
        assert not (workspace / 'client-state/auth.json').exists()
        assert token in config.read_text(encoding='utf-8')
        if os.name == 'posix':
            assert stat.S_IMODE(config.stat().st_mode) == 0o600
    assert config.read_text(encoding='utf-8') == original
    assert token not in config.read_text(encoding='utf-8')


def test_provider_env_key_is_reused_without_writing_secret(tmp_path, monkeypatch):
    workspace, config, token, original = provider_auth(tmp_path, monkeypatch, env_key=True)
    with adapter.access_snapshot(workspace, 90) as secrets:
        assert secrets == [token]
        assert token not in config.read_text(encoding='utf-8')
        assert 'env_key = "TAO_TEST_CODEX_TOKEN"' in config.read_text(encoding='utf-8')
    assert config.read_text(encoding='utf-8') == original
