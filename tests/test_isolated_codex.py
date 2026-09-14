"""Credential lifetime and native-discovery boundaries; no real client calls."""

import base64
import json
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
        'refresh_token': 'must-never-be-copied', 'id_token': 'test-id', 'account_id': 'test-account'}}))
    (home / '.codex/config.toml').write_text('model = "configured-model"\n')
    monkeypatch.setattr(Path, 'home', lambda: home)
    workspace = tmp_path / 'experiment'
    state = workspace / 'client-state'
    state.mkdir(parents=True)
    (state / 'config.toml').write_text('check_for_update_on_startup = false\n')
    return workspace, auth


def test_access_copy_excludes_refresh_and_cleans_up_after_failure(tmp_path, monkeypatch):
    workspace, source = fake_auth(tmp_path, monkeypatch)
    before = source.read_bytes()
    config = workspace / 'client-state/config.toml'
    original_config = config.read_bytes()
    copy = workspace / 'client-state/auth.json'
    with pytest.raises(RuntimeError, match='probe failed'):
        with adapter.access_snapshot(workspace, 90):
            assert stat.S_IMODE(copy.stat().st_mode) == 0o600
            assert json.loads(copy.read_text())['tokens']['refresh_token'] == ''
            assert 'must-never-be-copied' not in copy.read_text()
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
    with pytest.raises(RuntimeError, match='no refresh'):
        with adapter.access_snapshot(workspace, 90):
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
    log.write_text('token-secret token-secret visible')
    adapter.redact([log], ['token-secret'])
    assert log.read_text() == '[REDACTED] [REDACTED] visible'


def test_codex_compatibility_package_has_one_manifest_and_original_runtime(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(adapter.ROOT / 'scripts'))
    from package_plugin import build, SOURCE
    target = build(tmp_path / 'plugin', codex_legacy=True)
    assert not (target / 'plugin.json').exists()
    assert not (target / '.claude-plugin').exists()
    assert not (target / 'commands').exists()
    manifest = json.loads((target / '.codex-plugin/plugin.json').read_text())
    assert manifest['hooks'] == './com.openai/hooks/hooks.json'
    for folder in ('skills', 'com.openai'):
        for source in (SOURCE / folder).rglob('*'):
            if source.is_file() and '__pycache__' not in source.parts:
                assert (target / source.relative_to(SOURCE)).read_bytes() == source.read_bytes()
    with pytest.raises(ValueError, match='must be new'):
        build(target, codex_legacy=True)


def test_unexpected_hooks_cannot_be_trusted(tmp_path, monkeypatch):
    inside = tmp_path / 'codex/inside'
    monkeypatch.setattr(adapter, 'hook_inventory', lambda *args: [
        {'cwd': str(inside), 'errors': [], 'warnings': [], 'hooks': [{}, {}]}])
    with pytest.raises(RuntimeError, match='exactly one known hook'):
        adapter.trust_test_hook(tmp_path, inside, tmp_path / 'plugin')
    assert not (tmp_path / 'client-state/config.toml').exists()
