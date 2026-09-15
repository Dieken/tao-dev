"""Project setup discovers existing contracts and only writes approved configuration."""
import json
from test_workflows import call


def test_empty_inspection_is_read_only_and_has_no_tool_recommendations(tmp_path, capsys):
    code, report = call(tmp_path, capsys, 'project', 'inspect')
    assert code == 0, report
    assert report['outputs']['stacks'] == []
    assert report['outputs']['candidates'] == []
    assert list(tmp_path.iterdir()) == []


def test_monorepo_commands_are_candidates_not_executed_checks(tmp_path, capsys):
    app = tmp_path / 'apps/web'; app.mkdir(parents=True)
    (app / 'package.json').write_text(json.dumps({'scripts': {'test': 'touch NEVER', 'lint': 'eslint .', 'dev': 'vite'}}))
    (app / 'pnpm-lock.yaml').write_text('lockfileVersion: 9\n')
    (tmp_path / 'pyproject.toml').write_text('[project]\nname="example"\n[dependency-groups]\ndev=["pytest>=8", "ruff"]\n')
    ignored = tmp_path / 'node_modules/third'; ignored.mkdir(parents=True)
    (ignored / 'package.json').write_text('{}')
    code, report = call(tmp_path, capsys, 'project', 'inspect')
    assert code == 0, report
    data = report['outputs']
    assert {s['language'] for s in data['stacks']} == {'python', 'javascript'}
    assert any(c['argv'] == ['pnpm', '--dir', 'apps/web', 'run', 'test'] for c in data['candidates'])
    assert not any('dev' == c['id'] for c in data['candidates'])
    assert not (app / 'NEVER').exists()
    assert all(c['execution'] == 'not_run' for c in data['candidates'])


def test_configuration_is_validated_idempotent_and_compare_before_replace(tmp_path, capsys):
    draft = tmp_path / 'setup.toml'; draft.write_text('version=1\nlocale="en"\n[documents]\ninclude=[]\n')
    code, report = call(tmp_path, capsys, 'project', 'configure', '--from', 'setup.toml')
    assert code == 0, report
    target = tmp_path / '.tao/config.toml'; first = target.stat().st_mtime_ns
    digest = report['outputs']['config_digest']
    code, report = call(tmp_path, capsys, 'project', 'configure', '--from', 'setup.toml')
    assert code == 0 and report['outputs']['state'] == 'unchanged'
    assert target.stat().st_mtime_ns == first
    draft.write_text('version=1\nlocale="zh-Hans"\n')
    code, _ = call(tmp_path, capsys, 'project', 'configure', '--from', 'setup.toml')
    assert code == 1 and 'locale="en"' in target.read_text()
    code, report = call(tmp_path, capsys, 'project', 'configure', '--from', 'setup.toml', '--expect', digest)
    assert code == 0, report
    draft.write_text('version=1\n[verification]\nchecks=[]\ninputs=["src/**"]\n')
    code, _ = call(tmp_path, capsys, 'project', 'configure', '--from', 'setup.toml', '--expect', report['outputs']['config_digest'])
    assert code == 2 and 'zh-Hans' in target.read_text()
