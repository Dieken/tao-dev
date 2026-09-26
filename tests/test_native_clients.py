"""Native readiness uses the same CLI/session rules locally and in CI."""

import json

import native_clients


def test_cli_probe_only_requires_executable(monkeypatch):
    monkeypatch.setattr(native_clients.shutil, 'which', lambda name: '/bin/true')
    monkeypatch.setattr(native_clients, 'logged_in', lambda client: False)
    for client in ('claude', 'codex', 'cursor', 'kiro'):
        assert native_clients.cli_skip_reason(client) is None


def test_cli_probe_reports_missing_executable(monkeypatch):
    monkeypatch.setattr(native_clients.shutil, 'which', lambda name: None)
    for client in ('claude', 'codex', 'cursor', 'kiro'):
        assert 'not installed' in native_clients.cli_skip_reason(client)
        assert 'not installed' in native_clients.session_skip_reason(client)


def test_session_probe_requires_existing_login(monkeypatch):
    monkeypatch.setattr(native_clients.shutil, 'which', lambda name: '/bin/true')
    monkeypatch.setattr(native_clients, 'logged_in', lambda client: False)
    for client in ('claude', 'codex', 'cursor', 'kiro'):
        assert 'not logged in' in native_clients.session_skip_reason(client)


def test_session_probe_accepts_installed_logged_in_client(monkeypatch):
    monkeypatch.setattr(native_clients.shutil, 'which', lambda name: '/bin/true')
    monkeypatch.setattr(native_clients, 'logged_in', lambda client: True)
    for client in ('claude', 'codex', 'cursor', 'kiro'):
        assert native_clients.session_skip_reason(client) is None


def test_claude_login_accepts_configured_third_party_auth(monkeypatch, tmp_path):
    home = tmp_path / 'home'
    settings = home / '.claude/settings.json'
    settings.parent.mkdir(parents=True)
    settings.write_text(json.dumps({'env': {
        'ANTHROPIC_AUTH_TOKEN': 'test-token',
        'ANTHROPIC_BASE_URL': 'https://models.example.test',
        'ANTHROPIC_MODEL': 'test-model',
    }}), encoding='utf-8')
    monkeypatch.setattr(native_clients.Path, 'home', classmethod(lambda cls: home))
    monkeypatch.setattr(native_clients.sys, 'platform', 'linux')
    assert native_clients._claude_logged_in() is True


def test_codex_login_accepts_configured_third_party_provider(monkeypatch, tmp_path):
    home = tmp_path / 'home'
    config = home / '.codex/config.toml'
    config.parent.mkdir(parents=True)
    config.write_text(
        'model_provider = "yingmi"\n'
        '[model_providers.yingmi]\n'
        'base_url = "https://models.example.test/v1"\n'
        'experimental_bearer_token = "test-token"\n'
        'requires_openai_auth = false\n',
        encoding='utf-8')
    monkeypatch.setattr(native_clients.Path, 'home', classmethod(lambda cls: home))
    assert native_clients._codex_logged_in() is True


def test_codex_login_rejects_provider_without_auth_material(monkeypatch, tmp_path):
    home = tmp_path / 'home'
    config = home / '.codex/config.toml'
    config.parent.mkdir(parents=True)
    config.write_text(
        'model_provider = "yingmi"\n'
        '[model_providers.yingmi]\n'
        'base_url = "https://models.example.test/v1"\n'
        'requires_openai_auth = false\n',
        encoding='utf-8')
    monkeypatch.setattr(native_clients.Path, 'home', classmethod(lambda cls: home))
    assert native_clients._codex_logged_in() is False


def test_cursor_login_accepts_cli_config_auth_info(monkeypatch, tmp_path):
    home = tmp_path / 'home'
    home.mkdir()
    config = home / '.cursor/cli-config.json'
    config.parent.mkdir()
    config.write_text(json.dumps({'authInfo': {'email': 'user@example.com'}}), encoding='utf-8')
    monkeypatch.setattr(native_clients.Path, 'home', classmethod(lambda cls: home))
    monkeypatch.setattr(native_clients.subprocess, 'run',
                        lambda *a, **k: (_ for _ in ()).throw(native_clients.subprocess.TimeoutExpired('agent', 1)))
    assert native_clients._cursor_logged_in() is True


def test_kiro_login_uses_read_only_whoami(monkeypatch):
    calls = []

    class Result:
        returncode = 0
        stdout = 'Logged in with a test provider'
        stderr = ''

    def run(arguments, **kwargs):
        calls.append((arguments, kwargs))
        return Result()

    monkeypatch.setattr(native_clients.subprocess, 'run', run)
    assert native_clients._kiro_logged_in() is True
    assert calls[0][0] == ['kiro-cli', 'whoami']
    assert calls[0][1]['check'] is False
