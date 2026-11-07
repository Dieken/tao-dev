"""Entry points stay read-only until an explicitly requested domain operation."""

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


SCRIPTS = Path(__file__).resolve().parents[1] / 'skills/tao-dev/scripts'


def invoke(*args, cwd, home, scripts=SCRIPTS, site_packages=False):
    env = dict(os.environ, HOME=str(home), USERPROFILE=str(home), PYTHONUTF8='1')
    # Exclude site packages unless the caller explicitly exercises prepared dependencies.
    options = ['-I', '-B'] if site_packages else ['-I', '-S', '-B']
    return subprocess.run([sys.executable, *options, str(scripts / 'tao.py'), *args],
                          cwd=cwd, env=env, text=True, encoding='utf-8', capture_output=True)


@pytest.mark.parametrize('prefix', [[], ['--project', '/project'], ['--project=/project'],
                                    ['--format=json'], ['--diagnostic-locale', 'en']])
def test_stdlib_help_and_version_are_read_only(tmp_path, prefix):
    home = tmp_path / 'home'
    home.mkdir()
    version = json.loads((SCRIPTS / 'runtime.json').read_text(encoding='utf-8'))['version']
    for option in ('--help', '-h', '--version', '-V'):
        result = invoke(*prefix, option, cwd=tmp_path, home=home)
        assert result.returncode == 0, result.stderr
        assert result.stdout
        assert not result.stderr
        if option in ('--version', '-V'):
            assert result.stdout.strip() == f'tao-dev {version}'
    assert list(home.iterdir()) == []
    assert list(tmp_path.iterdir()) == [home]


@pytest.mark.parametrize(('command', 'requirements'), [
    (['status'], 'requirements.txt'),
    (['docs', 'build'], 'requirements-publication.txt'),
])
@pytest.mark.parametrize('output_format', [['--format', 'json'], ['--format=json']])
def test_missing_dependencies_report_without_preparing_environment(tmp_path, command, requirements, output_format):
    home = tmp_path / 'home'
    project = tmp_path / 'project'
    home.mkdir()
    project.mkdir()
    result = invoke('--project', str(project), *output_format, *command, cwd=project, home=home)
    assert result.returncode == 2, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert report['tool'] == 'tao-dev'
    assert report['command'] == command[0]
    assert report['status'] == 'not_run'
    assert report['outputs'] == {}
    diagnostic, = report['diagnostics']
    assert diagnostic['severity'] == 'error'
    assert str(SCRIPTS / requirements) in diagnostic['message']
    assert not result.stderr
    assert list(home.iterdir()) == []
    assert list(project.iterdir()) == []
    assert set(tmp_path.iterdir()) == {home, project}


def test_missing_dependencies_use_stderr_for_text_output(tmp_path):
    home = tmp_path / 'home'
    home.mkdir()
    result = invoke('status', cwd=tmp_path, home=home)
    assert result.returncode == 2
    assert not result.stdout
    assert str(SCRIPTS / 'requirements.txt') in result.stderr
    assert list(home.iterdir()) == []
    assert list(tmp_path.iterdir()) == [home]


@pytest.mark.parametrize('command', ['install', 'upgrade', 'list', 'uninstall', 'handoff'])
def test_removed_management_commands_are_rejected_without_writes(tmp_path, command):
    home = tmp_path / 'home'
    project = tmp_path / 'project'
    home.mkdir()
    project.mkdir()
    result = invoke('--project', str(project), '--format=json', command,
                    cwd=tmp_path, home=home, site_packages=True)
    assert result.returncode == 2, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert report['status'] == 'not_run'
    assert report['outputs'] == {}
    diagnostic, = report['diagnostics']
    assert diagnostic['rule_id'] == 'TAO-CLI-001'
    assert diagnostic['severity'] == 'error'
    assert list(home.iterdir()) == []
    assert list(project.iterdir()) == []
    assert set(tmp_path.iterdir()) == {home, project}
