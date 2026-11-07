"""A complete copied skill runs without checkout-relative resources or setup."""

import json
import re
import shutil

import pytest
import yaml

from test_runtime import SCRIPTS, invoke
from test_documents import spec


def snapshot(root):
    return {path.relative_to(root).as_posix(): path.read_bytes() if path.is_file() else None
            for path in root.rglob('*')}


@pytest.fixture
def copied_skill(tmp_path):
    skill = tmp_path / 'copied skill 中文/tao-dev'
    shutil.copytree(SCRIPTS.parent, skill, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    home, project, elsewhere = (tmp_path / name for name in ('home', 'business project', 'elsewhere'))
    for path in (home, project, elsewhere):
        path.mkdir()
    for relative in ('.claude/settings.json', '.codex/config.toml', '.cursor/hooks.json', '.kiro/settings.json'):
        path = home / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('User-owned settings\n', encoding='utf-8')
    return skill, home, project, elsewhere


def test_copied_skill_help_and_dependency_diagnostics_are_read_only(copied_skill):
    skill, home, project, elsewhere = copied_skill
    before = {root: snapshot(root) for root in copied_skill}
    for option in ('--help', '--version'):
        result = invoke(option, cwd=elsewhere, home=home, scripts=skill / 'scripts')
        assert result.returncode == 0, result.stderr
        assert result.stdout
        assert not result.stderr
    result = invoke('--project', str(project), '--format=json', 'status',
                    cwd=elsewhere, home=home, scripts=skill / 'scripts')
    assert result.returncode == 2, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert report['command'] == 'status'
    assert report['status'] == 'not_run'
    assert report['outputs'] == {}
    diagnostic, = report['diagnostics']
    assert diagnostic['severity'] == 'error'
    assert str(skill / 'scripts/requirements.txt') in diagnostic['message']
    assert str(SCRIPTS) not in diagnostic['message']
    for root, contents in before.items():
        assert snapshot(root) == contents


@pytest.mark.parametrize('locale', ['en', 'zh-Hans'])
def test_copied_skill_uses_bundled_resources_with_prepared_dependencies(copied_skill, locale):
    skill, home, project, elsewhere = copied_skill
    before = {root: snapshot(root) for root in (skill, home, elsewhere)}

    def command(*arguments):
        result = invoke('--project', str(project), '--format=json', *arguments,
                        cwd=elsewhere, home=home, scripts=skill / 'scripts', site_packages=True)
        assert result.returncode == 0, result.stdout + result.stderr
        return json.loads(result.stdout)

    doctor = command('doctor')
    assert doctor['status'] == 'passed'
    assert doctor['outputs']['project'] == str(project.resolve())
    assert doctor['outputs']['managed_sources'] == 0
    assert 'tao.project.plan/v0.1' in doctor['schemas']
    assert {'new', 'id.new', 'status', 'verify.docs'} <= set(doctor['capabilities'])
    assert not {'install', 'upgrade', 'list', 'uninstall'} & set(doctor['capabilities'])

    identifiers = command('id', 'new', 'REQ', '--count', '2')['outputs']['ids']
    assert len(set(identifiers)) == 2
    assert all(re.fullmatch(r'REQ_[0-9]{8}_[0-9A-HJKMNP-TV-Z]{16}', value) for value in identifiers)
    (project / 'docs').mkdir()
    (project / 'docs/spec.md').write_text(spec(), encoding='utf-8')
    verified = command('verify')
    assert verified['status'] == 'passed'
    assert verified['outputs']['documents']['valid']

    created = command('new', '--slug', 'copied-skill', '--locale', locale)['outputs']
    document = project / created['path']
    metadata = yaml.safe_load(document.read_text(encoding='utf-8').split('---', 2)[1])
    assert metadata['schema'] == 'tao.project.plan/v0.1'
    assert metadata['locale'] == locale
    assert metadata['id'] == created['ids']['DOC_ID']
    assert metadata['change'] == created['ids']['CHG_ID']
    assert created['draft_complete'] is False
    contents = document.read_bytes()
    repeated = invoke('--project', str(project), '--format=json', 'new', '--slug', 'copied-skill',
                      '--locale', locale, cwd=elsewhere, home=home, scripts=skill / 'scripts', site_packages=True)
    assert repeated.returncode == 1, repeated.stdout + repeated.stderr
    assert json.loads(repeated.stdout)['status'] == 'failed'
    assert document.read_bytes() == contents
    for root, contents in before.items():
        assert snapshot(root) == contents
