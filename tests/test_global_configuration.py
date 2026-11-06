"""Global config checks allow Codex token refresh, not account changes."""

import json
from pathlib import Path

from acceptance import clients

AUTH_KEY = str(Path('.codex') / 'auth.json')
CONFIG_KEY = str(Path('.codex') / 'config.toml')


def write_auth(home, *, account='account-a', access='access-a', refresh='refresh-a', refreshed=1):
    path = home / '.codex/auth.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        'auth_mode': 'chatgpt',
        'last_refresh': refreshed,
        'tokens': {
            'account_id': account,
            'access_token': access,
            'refresh_token': refresh,
            'id_token': 'id-' + access,
        },
    }), encoding='utf-8')
    return path


def test_codex_global_snapshot_ignores_periodic_token_rotation(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, 'home', lambda: tmp_path)
    write_auth(tmp_path)
    before = clients.global_configuration()
    write_auth(tmp_path, access='access-b', refresh='refresh-b', refreshed=2)
    after = clients.global_configuration()

    assert before == after
    fingerprint = after[AUTH_KEY]
    assert len(fingerprint) == 64
    assert 'access-' not in fingerprint and 'refresh-' not in fingerprint


def test_codex_global_snapshot_detects_account_and_config_changes(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, 'home', lambda: tmp_path)
    write_auth(tmp_path)
    before = clients.global_configuration()
    write_auth(tmp_path, account='account-b', access='access-b', refresh='refresh-b', refreshed=2)
    changed_account = clients.global_configuration()
    assert before[AUTH_KEY] != changed_account[AUTH_KEY]

    config = tmp_path / '.codex/config.toml'
    config.write_text('check_for_update_on_startup = false\n', encoding='utf-8')
    before_config = clients.global_configuration()
    config.write_text('check_for_update_on_startup = true\n', encoding='utf-8')
    after_config = clients.global_configuration()
    assert before_config[CONFIG_KEY] != after_config[CONFIG_KEY]


def test_codex_auth_snapshot_detects_malformed_file_changes(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, 'home', lambda: tmp_path)
    path = tmp_path / '.codex/auth.json'
    path.parent.mkdir(parents=True)
    path.write_text('{broken', encoding='utf-8')
    before = clients.global_configuration()
    path.write_text('{different', encoding='utf-8')
    after = clients.global_configuration()
    assert before[AUTH_KEY] != after[AUTH_KEY]
