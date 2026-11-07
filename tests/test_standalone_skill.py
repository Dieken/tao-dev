"""A copied skill installs independently with only the standard library."""

import json
import shutil

from test_installation import snapshot
from test_runtime import SCRIPTS, invoke


def test_copied_skill_installs_from_unrelated_cwd_without_packages(tmp_path):
    skill = tmp_path / 'copied skill 中文/tao-dev'
    shutil.copytree(SCRIPTS.parent, skill, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    before = snapshot(skill)
    home, project, elsewhere = (tmp_path / name for name in ('home', 'business project', 'elsewhere'))
    for path in (home, project, elsewhere):
        path.mkdir()
    for command in ('install', 'upgrade', 'list', 'uninstall'):
        result = invoke(command, '--project', str(project), '--client', 'kiro', '--format=json',
                        cwd=elsewhere, home=home, scripts=skill / 'scripts')
        assert result.returncode == 0, result.stdout + result.stderr
        assert json.loads(result.stdout)['status'] == 'passed'
    assert snapshot(skill) == before
    assert not list(home.iterdir())
    assert not list(elsewhere.iterdir())
    assert not list(skill.parent.glob('.*plugin*'))
    assert not (project / '.kiro/skills/tao-dev').exists()
