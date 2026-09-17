"""Plans use the user-facing name while retaining change identities."""
from taolib.cli import dispatch, arguments
from taolib.project import Project


def test_new_plan_uses_configured_plans_directory(tmp_path):
    (tmp_path / '.tao').mkdir()
    (tmp_path / '.tao/config.toml').write_text('version = 1\nlocale = "en"\n[paths]\nplans = "docs/plans"\n', encoding='utf-8')
    project = Project(tmp_path)
    report, code = dispatch(arguments(['--project', str(project.root), 'new', '--slug', 'filter']))
    assert code == 0
    path = tmp_path / report['outputs']['path']
    assert path.relative_to(tmp_path).parts[:2] == ('docs', 'plans')
    assert 'schema: tao.project.plan/v0.1' in path.read_text(encoding='utf-8')
    assert report['outputs']['ids']['CHG_ID'].startswith('CHG_')
