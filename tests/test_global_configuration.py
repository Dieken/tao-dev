"""Installation never alters client settings, home, or another project."""

import pytest

from test_installation import args, snapshot, source, project  # noqa: F401
import installation as install
from install_clients import PROJECT_SKILLS


@pytest.mark.parametrize('client', PROJECT_SKILLS)
def test_lifecycle_preserves_home_and_project_client_settings(tmp_path, monkeypatch, source, project, client):  # noqa: F811
    home = tmp_path / 'home'
    home.mkdir()
    other = tmp_path / 'other-project'
    other.mkdir()
    for variable in ('HOME', 'USERPROFILE', 'CODEX_HOME', 'CLAUDE_CONFIG_DIR', 'CURSOR_CONFIG_DIR', 'KIRO_HOME',
                     'TAO_RUNTIME_DIR', 'TAO_CLI_DIR', 'XDG_DATA_HOME', 'LOCALAPPDATA'):
        monkeypatch.setenv(variable, str(home))
    for root in (home, project, other):
        for relative in ('.claude/settings.json', '.codex/config.toml', '.cursor/hooks.json', '.kiro/settings.json'):
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('User-owned settings\n', encoding='utf-8')
    before = {root: snapshot(root) for root in (home, project, other)}
    install.deploy(args('install', project, source, client))
    install.deploy(args('upgrade', project, source, client))
    install.inventory(args('list', project, client=client))
    install.uninstall(args('uninstall', project, client=client))
    for root, files in before.items():
        assert snapshot(root) == files


def test_home_cannot_be_selected_as_project(tmp_path, monkeypatch, source):  # noqa: F811
    home = tmp_path / 'home'
    home.mkdir()
    monkeypatch.setenv('HOME', str(home))
    monkeypatch.setenv('USERPROFILE', str(home))
    with pytest.raises(install.InstallError, match='home or filesystem root'):
        install.deploy(args('install', home, source))
    assert list(home.iterdir()) == []
