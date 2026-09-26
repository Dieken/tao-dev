"""Existing Claude access is scoped to a child and never refreshed by probes."""

import json
import os
import time
from pathlib import Path

import pytest
from acceptance import isolated_claude as adapter


def credentials(tmp_path, monkeypatch, *, seconds=600):
    monkeypatch.setattr(Path, 'home', lambda: tmp_path)
    for key in ('ANTHROPIC_API_KEY', 'ANTHROPIC_AUTH_TOKEN', 'ANTHROPIC_BASE_URL',
                'CLAUDE_CODE_USE_BEDROCK', 'CLAUDE_CODE_USE_VERTEX', 'CLAUDE_CODE_USE_FOUNDRY'):
        monkeypatch.delenv(key, raising=False)
    raw = json.dumps({'claudeAiOauth': {'accessToken': 'access-test', 'refreshToken': 'refresh-test',
                                      'expiresAt': (time.time() + seconds) * 1000}})
    monkeypatch.setattr(adapter, 'read_credentials', lambda: raw)
    return raw


def test_access_is_child_only_and_refresh_is_not_forwarded(tmp_path, monkeypatch):
    credentials(tmp_path, monkeypatch)
    monkeypatch.setenv('CLAUDE_CODE_OAUTH_REFRESH_TOKEN', 'parent-refresh')
    before = dict(os.environ)
    with adapter.access_environment(tmp_path / 'experiment', 90) as (env, secrets):
        assert env['CLAUDE_CODE_OAUTH_TOKEN'] == 'access-test'
        assert 'CLAUDE_CODE_OAUTH_REFRESH_TOKEN' not in env
        assert env['CLAUDE_CONFIG_DIR'] == str(tmp_path / 'experiment/client-config')
        assert 'refresh-test' in secrets
        assert dict(os.environ) == before
    assert 'CLAUDE_CODE_OAUTH_TOKEN' not in env
    assert dict(os.environ) == before
    assert not list(tmp_path.iterdir())


def test_expired_access_never_starts_a_probe(tmp_path, monkeypatch):
    credentials(tmp_path, monkeypatch, seconds=150)
    with (pytest.raises(RuntimeError, match='no refresh'),
          adapter.access_environment(tmp_path, 90)):
        pytest.fail('Access would expire during this probe.')


def test_personal_credential_change_invalidates_probe_without_rollback(tmp_path, monkeypatch):
    raw = credentials(tmp_path, monkeypatch)
    values = iter([raw, raw + ' '])
    monkeypatch.setattr(adapter, 'read_credentials', lambda: next(values))
    with (pytest.raises(RuntimeError, match='no restoration'),
          adapter.access_environment(tmp_path, 90) as (env, _)):
        pass
    assert 'CLAUDE_CODE_OAUTH_TOKEN' not in env


def test_custom_route_is_not_silently_replaced(tmp_path, monkeypatch):
    credentials(tmp_path, monkeypatch)
    monkeypatch.setenv('ANTHROPIC_BASE_URL', 'https://example.invalid')
    with (pytest.raises(RuntimeError, match='provider routing'),
          adapter.access_environment(tmp_path, 90)):
        pytest.fail('Configured routing must not be replaced.')


def test_malformed_personal_model_override_is_not_forwarded(tmp_path, monkeypatch):
    credentials(tmp_path, monkeypatch)
    settings = tmp_path / '.claude/settings.json'
    settings.parent.mkdir()
    settings.write_text(json.dumps({'model': 'opus[1m'}), encoding='utf-8')

    with adapter.access_environment(tmp_path / 'experiment', 90) as (env, _):
        assert 'ANTHROPIC_MODEL' not in env


def test_valid_personal_model_override_is_forwarded(tmp_path, monkeypatch):
    credentials(tmp_path, monkeypatch)
    settings = tmp_path / '.claude/settings.json'
    settings.parent.mkdir()
    settings.write_text(json.dumps({'model': 'claude-sonnet-4-5'}), encoding='utf-8')

    with adapter.access_environment(tmp_path / 'experiment', 90) as (env, _):
        assert env['ANTHROPIC_MODEL'] == 'claude-sonnet-4-5'


@pytest.mark.parametrize('client', ['claude', 'codex'])
def test_personal_state_probe_is_rejected_before_starting_client(tmp_path, monkeypatch, client):
    import sys

    from acceptance import clients
    monkeypatch.setattr(sys, 'argv', ['clients.py', '--client', client, '--case', 'inside',
                                     '--workspace', str(tmp_path / 'experiment')])
    monkeypatch.setattr(clients.subprocess, 'Popen', lambda *args, **kwargs: pytest.fail('Client must not start.'))
    assert clients.main() == 2
    assert not (tmp_path / 'experiment').exists()


def test_expiring_credentials_produce_a_structured_runner_failure(tmp_path, monkeypatch, capsys):
    import importlib
    from contextlib import contextmanager
    from types import SimpleNamespace

    from acceptance import clients
    monkeypatch.syspath_prepend(str(Path(__file__).parent / 'acceptance'))
    native = importlib.import_module('isolated_claude')
    monkeypatch.setattr(clients, 'ROOT', tmp_path / 'source')
    monkeypatch.setattr(Path, 'home', lambda: tmp_path / 'home')
    monkeypatch.setattr(clients, 'global_configuration', dict)
    monkeypatch.setattr(clients, 'prepare', lambda *args, **kwargs: tmp_path / 'plugin')
    monkeypatch.setattr(native, 'configure', lambda *args: None)
    monkeypatch.setattr(clients.subprocess, 'run', lambda *args, **kwargs:
                        SimpleNamespace(returncode=0, stdout='', stderr=''))
    monkeypatch.setattr(clients.subprocess, 'Popen', lambda *args, **kwargs: pytest.fail('No model may start.'))

    @contextmanager
    def expired(*args):
        raise RuntimeError('Existing access cannot cover the probe; no refresh attempted.')
        yield

    monkeypatch.setattr(native, 'access_environment', expired)
    monkeypatch.setattr(clients.sys, 'argv', ['clients.py', '--client', 'claude', '--case', 'inside',
                        '--claude-scope', 'project', '--reuse-claude-auth', '--workspace', str(tmp_path / 'experiment')])
    assert clients.main() == 2
    result = json.loads(capsys.readouterr().out)
    assert result['status'] == 'blocked' and result['exit_code'] is None
    assert 'no refresh' in result['reason']
    saved = next((tmp_path / 'source/tmp/tao/client-acceptance').glob('*.summary.json'))
    assert json.loads(saved.read_text(encoding='utf-8')) == result



def test_install_command_is_noninteractive_without_unsupported_json(tmp_path):
    command = adapter.install_arguments('project')
    assert command == [
        'plugin', 'install', 'tao-dev@tao-runtime-test',
        '--scope', 'project', '--yes',
    ]
    assert '--json' not in command



def test_configured_settings_auth_is_scoped_to_child(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, 'home', lambda: tmp_path)
    monkeypatch.setattr(adapter, 'read_credentials',
                        lambda: (_ for _ in ()).throw(RuntimeError('no keychain')))
    settings = tmp_path / '.claude/settings.json'
    settings.parent.mkdir(parents=True)
    original = json.dumps({'env': {
        'ANTHROPIC_AUTH_TOKEN': 'settings-access',
        'ANTHROPIC_BASE_URL': 'https://models.example.test',
        'ANTHROPIC_MODEL': 'test-model',
        'ANTHROPIC_DEFAULT_HAIKU_MODEL': 'test-haiku',
        'ANTHROPIC_SMALL_FAST_MODEL': 'test-fast',
        'CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC': '0',
        'CLAUDE_CODE_ATTRIBUTION_HEADER': 'test-attribution',
    }})
    settings.write_text(original, encoding='utf-8')
    before = settings.read_bytes()
    with adapter.access_environment(tmp_path / 'experiment', 90) as (env, secrets):
        assert env['ANTHROPIC_AUTH_TOKEN'] == 'settings-access'
        assert env['ANTHROPIC_BASE_URL'] == 'https://models.example.test'
        assert env['ANTHROPIC_MODEL'] == 'test-model'
        assert env['ANTHROPIC_DEFAULT_HAIKU_MODEL'] == 'test-haiku'
        assert env['ANTHROPIC_SMALL_FAST_MODEL'] == 'test-fast'
        assert env['CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC'] == '0'
        assert env['CLAUDE_CODE_ATTRIBUTION_HEADER'] == 'test-attribution'
        assert 'settings-access' in secrets
    assert settings.read_bytes() == before
