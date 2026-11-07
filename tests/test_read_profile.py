"""A selected contract is readable without unrelated profiles or locale loading."""
import json
import shutil
import subprocess
import sys

import pytest

from read_profile import ASSETS, read_profile


@pytest.mark.parametrize('locale', ['en', 'zh-Hans'])
def test_profile_reader_localizes_every_registered_template(locale):
    registry = json.loads((ASSETS / 'document-profiles.json').read_text(encoding='utf-8'))
    for schema, rule in registry['profiles'].items():
        value = read_profile(schema, locale)
        assert value['schema'] == schema
        assert value['profile'] == rule
        assert '{{heading.' not in value['template']
        assert '{{label.' not in value['template']
        assert '{{DOC_ID}}' in value['template']
        assert 'profiles' not in value and 'locales' not in value
        assert value['entities_outside_registered_sections'] is False
        assert set(rule['required_sections']) <= set(rule['sections'])
        assert 'approval_requires' not in rule
    evidence = read_profile('evidence', locale)
    assert 'entities' not in evidence and 'tasks' not in evidence
    plan = read_profile('plan', locale)
    assert plan['tasks'] == registry['tasks']
    assert set(plan['entities']) == {'ADR', 'UC'}


def test_profile_reader_runs_from_copied_skill_without_writing(tmp_path):
    skill = tmp_path / 'copied skill'
    shutil.copytree(ASSETS, skill / 'assets')
    (skill / 'scripts').mkdir()
    script = skill / 'scripts/read_profile.py'
    shutil.copyfile(ASSETS.parent / 'scripts/read_profile.py', script)
    before = {p.relative_to(skill): p.read_bytes() for p in skill.rglob('*') if p.is_file()}
    result = subprocess.run([sys.executable, '-I', '-B', str(script), 'evidence',
                             '--locale', 'zh-Hans'],
                            cwd=tmp_path, capture_output=True, text=True,
                            encoding='utf-8', check=True)
    assert '检查' in json.loads(result.stdout)['template']
    assert before == {p.relative_to(skill): p.read_bytes() for p in skill.rglob('*') if p.is_file()}


@pytest.mark.parametrize('profile,locale', [
    ('missing', 'en'), ('evidence', '../en'), ('workflow', 'en'), ('handoff', 'en'),
])
def test_profile_reader_rejects_unknown_selections(profile, locale):
    with pytest.raises(ValueError):
        read_profile(profile, locale)
