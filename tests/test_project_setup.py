"""Project setup inspects document settings and validates explicit configuration."""
import hashlib
import json
import subprocess
import sys

import pytest

from taolib.cli import main
from test_documents import spec


def call(root, capsys, *args):
    code = main(["--project", str(root), "--format", "json", *args])
    return code, json.loads(capsys.readouterr().out)


def test_empty_inspection_reports_document_defaults_without_writing(tmp_path, capsys):
    code, report = call(tmp_path, capsys, 'project', 'inspect')
    assert code == 0, report
    data = report['outputs']
    assert data['documents'] == {'include': ['docs/**/*.md'], 'exclude': [],
                                 'book_root': None, 'section_redirects': {}}
    assert data['paths'] == {'plans': 'docs/plans', 'retired': 'docs/retired', 'temporary': 'tmp/tao'}
    assert data['managed_sources'] == []
    assert data['config_digest'] is None
    assert not {'stacks', 'candidates', 'configured_checks', 'ci_files', 'manifests'} & data.keys()
    assert list(tmp_path.iterdir()) == []


def test_inspection_reports_effective_document_settings_without_executing_commands(tmp_path, capsys, monkeypatch):
    (tmp_path / '.tao').mkdir()
    config = tmp_path / '.tao/config.toml'
    config.write_text('version=1\nlocale="en"\n[ui]\nlocale="zh-Hans"\n'
                      '[documents]\ninclude=["manual/*.md"]\nexclude=["manual/excluded.md"]\n'
                      'book_root="manual/spec.md"\n[paths]\ntemporary="generated"\n', encoding='utf-8')
    (tmp_path / 'manual').mkdir()
    (tmp_path / 'manual/spec.md').write_text(spec(), encoding='utf-8')
    (tmp_path / 'manual/excluded.md').write_text('Not managed', encoding='utf-8')
    (tmp_path / 'package.json').write_text(json.dumps({'scripts': {'test': 'touch NEVER'}}), encoding='utf-8')
    before = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}

    def forbidden(*args, **kwargs):
        pytest.fail('Project inspection must not execute a process')

    monkeypatch.setattr(subprocess, 'Popen', forbidden)
    code, report = call(tmp_path, capsys, 'project', 'inspect')
    assert code == 0, report
    data = report['outputs']
    assert data['locale'] == 'en' and data['diagnostic_locale'] == 'zh-Hans'
    assert data['documents']['book_root'] == 'manual/spec.md'
    assert data['documents']['include'] == ['manual/*.md']
    assert data['documents']['exclude'] == ['manual/excluded.md']
    assert data['paths']['temporary'] == 'generated'
    assert data['managed_sources'] == ['manual/spec.md']
    assert data['config_digest'] == hashlib.sha256(config.read_bytes()).hexdigest()
    assert {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()} == before


def test_configuration_is_validated_idempotent_and_compare_before_replace(tmp_path, capsys):
    draft = tmp_path / 'setup.toml'; draft.write_text('version=1\nlocale="en"\n[documents]\ninclude=[]\n', encoding='utf-8')
    code, report = call(tmp_path, capsys, 'project', 'configure', '--from', 'setup.toml')
    assert code == 0, report
    target = tmp_path / '.tao/config.toml'; first = target.stat().st_mtime_ns
    digest = report['outputs']['config_digest']
    code, report = call(tmp_path, capsys, 'project', 'configure', '--from', 'setup.toml')
    assert code == 0 and report['outputs']['state'] == 'unchanged'
    assert target.stat().st_mtime_ns == first
    draft.write_text('version=1\nlocale="zh-Hans"\n', encoding='utf-8')
    code, _ = call(tmp_path, capsys, 'project', 'configure', '--from', 'setup.toml')
    assert code == 1 and 'locale="en"' in target.read_text(encoding='utf-8')
    code, report = call(tmp_path, capsys, 'project', 'configure', '--from', 'setup.toml', '--expect', digest)
    assert code == 0, report
    draft.write_text('version=1\n[verification]\nchecks=[]\ninputs=["src/**"]\n', encoding='utf-8')
    code, _ = call(tmp_path, capsys, 'project', 'configure', '--from', 'setup.toml', '--expect', report['outputs']['config_digest'])
    assert code == 2 and 'zh-Hans' in target.read_text(encoding='utf-8')


@pytest.mark.parametrize('command', [
    ('verify',), ('verify', '--dry-run'), ('verify', '--simplified'),
    ('doctor',), ('status',), ('project', 'inspect'),
    ('project', 'configure', '--from', 'setup.toml'),
])
def test_legacy_verification_configuration_is_rejected_without_execution_or_writes(tmp_path, capsys, monkeypatch, command):
    content = ('version=1\n[verification]\ninputs=["check.py"]\n'
               '[[verification.checks]]\nid="tests"\nargv=['
               + json.dumps(sys.executable) + ', "check.py"]\ntimeout_seconds=5\n')
    (tmp_path / 'check.py').write_text('from pathlib import Path\nPath("ran").touch()\n', encoding='utf-8')
    if command[:2] == ('project', 'configure'):
        (tmp_path / 'setup.toml').write_text(content, encoding='utf-8')
    else:
        (tmp_path / '.tao').mkdir()
        (tmp_path / '.tao/config.toml').write_text(content, encoding='utf-8')
    before = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}

    def forbidden(*args, **kwargs):
        pytest.fail('Rejected verification configuration must not execute a process')

    monkeypatch.setattr(subprocess, 'Popen', forbidden)
    code, report = call(tmp_path, capsys, *command)
    assert code == 2 and report['status'] == 'not_run'
    assert report['diagnostics']
    assert report['outputs'] == {}
    assert {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()} == before
    assert not (tmp_path / 'tmp').exists()
    assert not (tmp_path / 'ran').exists()
