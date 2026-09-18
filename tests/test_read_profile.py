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
        for variant in [None, *rule.get('alternate_templates', {})]:
            value = read_profile(schema, locale, variant)
            assert value['schema'] == schema
            assert value['profile'] == rule
            assert '{{heading.' not in value['template']
            assert '{{label.' not in value['template']
            assert '{{DOC_ID}}' in value['template']
            assert 'profiles' not in value and 'locales' not in value
            assert value['entities_outside_registered_sections'] is False
    evidence = read_profile('evidence', locale, 'review')
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
                             '--locale', 'zh-Hans', '--template', 'review-adjudication'],
                            cwd=tmp_path, capture_output=True, text=True, check=True)
    assert '处置与范围' in json.loads(result.stdout)['template']
    assert before == {p.relative_to(skill): p.read_bytes() for p in skill.rglob('*') if p.is_file()}


@pytest.mark.parametrize('profile,locale,variant', [
    ('missing', 'en', None), ('evidence', '../en', None), ('plan', 'en', 'review'),
])
def test_profile_reader_rejects_unknown_selections(profile, locale, variant):
    with pytest.raises(ValueError):
        read_profile(profile, locale, variant)
