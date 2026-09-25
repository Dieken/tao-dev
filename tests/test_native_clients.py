"""Native client readiness skips probes when a CLI is missing or logged out."""

import json
from pathlib import Path

import native_clients


def test_skip_reason_reports_missing_cli(monkeypatch):
    monkeypatch.setattr(native_clients.shutil, 'which', lambda name: None)
    assert 'not installed' in native_clients.skip_reason('codex')


def test_skip_reason_reports_logged_out_without_ci_override(monkeypatch, tmp_path):
    monkeypatch.delenv('TAO_TEST_NATIVE_CLIENTS', raising=False)
    monkeypatch.setattr(native_clients.shutil, 'which', lambda name: '/bin/true')
    monkeypatch.setattr(native_clients, '_claude_logged_in', lambda: False)
    monkeypatch.setattr(native_clients, '_codex_logged_in', lambda: False)
    monkeypatch.setattr(native_clients, '_cursor_logged_in', lambda: False)
    for client in ('claude', 'codex', 'cursor'):
        assert 'not logged in' in native_clients.skip_reason(client)


def test_ci_override_skips_login_requirement(monkeypatch):
    monkeypatch.setenv('TAO_TEST_NATIVE_CLIENTS', '1')
    monkeypatch.setattr(native_clients.shutil, 'which', lambda name: '/bin/true')
    monkeypatch.setattr(native_clients, '_claude_logged_in', lambda: False)
    assert native_clients.skip_reason('claude') is None


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
