"""Client adaptation uses each client's project skill directory."""

import pytest

from install_clients import PROJECT_SKILLS, destination


@pytest.mark.parametrize(('client', 'relative'), [
    ('claude', '.claude/skills/tao-dev'),
    ('codex', '.agents/skills/tao-dev'),
    ('cursor', '.cursor/skills/tao-dev'),
    ('kiro', '.kiro/skills/tao-dev'),
])
def test_native_project_paths(tmp_path, client, relative):
    assert destination(tmp_path, client) == tmp_path / relative
    assert PROJECT_SKILLS[client] == relative
    assert not list(tmp_path.iterdir())


def test_unknown_client_has_no_fallback(tmp_path):
    with pytest.raises(ValueError, match='Unsupported client'):
        destination(tmp_path, 'unknown')
    assert not list(tmp_path.iterdir())
