"""The entry point dispatches installation before optional document imports."""

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

import runtime


SCRIPTS = Path(__file__).resolve().parents[1] / 'skills/tao-dev/scripts'


def invoke(*args, cwd, home, scripts=SCRIPTS):
    env = dict(os.environ, HOME=str(home), USERPROFILE=str(home), PYTHONUTF8='1')
    # -S excludes site packages even when pytest itself uses a prepared venv.
    return subprocess.run([sys.executable, '-I', '-S', '-B', str(scripts / 'tao.py'), *args],
                          cwd=cwd, env=env, text=True, encoding='utf-8', capture_output=True)


@pytest.mark.parametrize('prefix', [[], ['--project', '/project'], ['--project=/project'], ['--format=json']])
def test_operation_skips_global_option_values(prefix):
    assert runtime.operation([*prefix, 'install'])[0] == 'install'


def test_stdlib_help_and_version_are_read_only(tmp_path):
    home = tmp_path / 'home'
    home.mkdir()
    for option in ('--help', '--version'):
        result = invoke(option, cwd=tmp_path, home=home)
        assert result.returncode == 0, result.stderr
        assert 'tao-dev' in result.stdout
    assert list(home.iterdir()) == []
    assert list(tmp_path.iterdir()) == [home]


def test_install_commands_work_without_site_packages(tmp_path):
    home = tmp_path / 'home'
    project = tmp_path / 'project'
    home.mkdir()
    project.mkdir()
    for command in ('install', 'upgrade', 'list', 'uninstall'):
        result = invoke('--project', str(project), command, '--client', 'codex', '--format', 'json',
                        cwd=tmp_path, home=home)
        assert result.returncode == 0, result.stdout + result.stderr
        report = json.loads(result.stdout)
        assert report['command'] == command and report['status'] == 'passed'
    assert list(home.iterdir()) == []
    assert not (project / '.agents/skills/tao-dev').exists()


def test_document_dependency_error_is_actionable_and_never_installs(tmp_path):
    home = tmp_path / 'home'
    project = tmp_path / 'project'
    home.mkdir()
    project.mkdir()
    result = invoke('--project', str(project), '--format', 'json', 'status', cwd=project, home=home)
    assert result.returncode == 2, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert report['status'] == 'not_run'
    message = report['diagnostics'][0]['message']
    assert 'Optional document dependency' in message
    assert 'python -m venv .venv' in message
    assert 'requirements.txt' in message
    assert list(home.iterdir()) == []
    assert list(project.iterdir()) == []


def test_installation_errors_are_structured_without_optional_imports(tmp_path):
    home = tmp_path / 'home'
    home.mkdir()
    missing = tmp_path / 'missing'
    result = invoke('install', '--project', str(missing), '--client', 'codex', '--format=json',
                    cwd=tmp_path, home=home)
    assert result.returncode == 2
    assert 'does not exist' in json.loads(result.stdout)['diagnostics'][0]['message']
    assert not missing.exists() and not list(home.iterdir())
