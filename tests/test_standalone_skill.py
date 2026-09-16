"""A copied skill runs without a plugin manifest, launcher or client CLI."""

import hashlib
import json
import re
import shutil
from urllib.parse import unquote, urlsplit

from test_documents import spec
from test_runtime import bare_python, invoke, prepare, SCRIPTS  # noqa: F401


def inventory(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file()}


def test_standalone_resources_remain_inside_skill():
    skill = SCRIPTS.parent
    links = []
    for page in [skill / 'SKILL.md', *sorted((skill / 'references').glob('*.md'))]:
        for target in re.findall(r'\]\(([^\s)]+)\)', page.read_text()):
            url = urlsplit(target)
            if url.scheme or not url.path:
                continue
            resolved = (page.parent / unquote(url.path)).resolve()
            assert resolved.is_relative_to(skill), (page, target)
            assert resolved.exists(), (page, target)
            links.append(resolved)
    assert skill / 'scripts/tao.py' in links
    assert skill / 'references/engineering.md' in links


def test_copied_skill_from_different_cwd_without_prepared_dependencies(bare_python, tmp_path):
    skill = tmp_path / 'client skills 中文/tao-dev'
    shutil.copytree(SCRIPTS.parent, skill, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    before = inventory(skill)
    project = tmp_path / 'business project'
    (project / 'docs').mkdir(parents=True)
    (project / 'docs/spec.md').write_text(spec())
    elsewhere = tmp_path / 'unrelated cwd'
    elsewhere.mkdir()
    data = tmp_path / 'runtime data'
    scripts = skill / 'scripts'
    def call(*args):
        return invoke(bare_python, data, '--project', str(project), *args,
                      scripts=scripts, cwd=elsewhere, extra={'PATH': ''})
    doctor = call('doctor')
    assert doctor.returncode == 2
    assert json.loads(doctor.stdout)['outputs']['runtime']['state'] == 'missing'
    missing = call('verify', '--only', 'docs')
    assert missing.returncode == 2
    assert json.loads(missing.stdout)['status'] == 'not_run'
    assert not data.exists()
    prepare(bare_python, data, scripts=scripts)
    assert call('doctor').returncode == 0
    verified = call('verify', '--only', 'docs')
    assert verified.returncode == 0, verified.stdout + verified.stderr
    value = json.loads(verified.stdout)
    assert value['coverage'] == 'partial'
    assert any(d['path'] == 'docs/spec.md' for d in value['outputs']['documents']['definitions'].values())
    # Query an actually discovered ID instead of relying on fixture numbering.
    identifier = next(iter(value['outputs']['documents']['definitions']))
    shown = call('show', identifier)
    assert shown.returncode == 0, shown.stdout + shown.stderr
    assert call('status').returncode in (0, 2)
    assert not list(elsewhere.iterdir())
    assert inventory(skill) == before
    assert not list(skill.parent.glob('.*plugin*'))
