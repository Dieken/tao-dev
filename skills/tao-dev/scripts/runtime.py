"""Read-only entry dispatch with explicit optional document dependencies."""

import json
from pathlib import Path
import sys


SCRIPTS = Path(__file__).resolve().parent


def operation(argv):
    index = 0
    while index < len(argv):
        if argv[index] in ('--project', '--format', '--diagnostic-locale'):
            index += 2
        elif argv[index].startswith(('--project=', '--format=', '--diagnostic-locale=')):
            index += 1
        else:
            return argv[index]
    return 'unknown'


def tool_version():
    try:
        return json.loads((SCRIPTS / 'runtime.json').read_text(encoding='utf-8'))['version']
    except (OSError, ValueError, KeyError):
        return 'unknown'


def usage():
    return '\n'.join([
        f'tao-dev {tool_version()}',
        'Usage: python <skill>/scripts/tao.py [--project <directory>] <command>',
        '',
        'Document helpers (optional dependencies in your Python environment):',
        '  doctor, show, id new, new, status, verify, docs, project, retire',
        '  See <command> --help for options.',
        '',
        'Reading SKILL.md and using help/version never prepares dependencies.',
    ])


def main(argv=None, entry='tao.py'):
    sys.dont_write_bytecode = True
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    argv = list(sys.argv[1:] if argv is None else argv)
    command = operation(argv)
    if entry == 'tao.py' and command in ('--help', '-h', 'unknown'):
        print(usage())
        return 0
    if entry == 'tao.py' and command in ('--version', '-V'):
        print(f'tao-dev {tool_version()}')
        return 0
    try:
        if entry == 'validate_documents.py':
            from taolib.validator_cli import main as command_main
        else:
            from taolib.cli import main as command_main
        return command_main(argv)
    except ModuleNotFoundError as exc:
        requirements = SCRIPTS / ('requirements-publication.txt' if command == 'docs' else 'requirements.txt')
        message = (f'Optional document dependency is unavailable: {exc.name}. '
                   'Create a project-local virtual environment with python -m venv .venv, '
                   f'then use its Python to run -m pip install -r "{requirements}" '
                   'and invoke this script. Skill reading and help/version need no packages.')
        report = {'tool': 'tao-dev', 'command': command, 'status': 'not_run',
                  'outputs': {}, 'diagnostics': [{'severity': 'error', 'message': message}]}
        json_output = '--format=json' in argv or any(argv[i:i + 2] == ['--format', 'json'] for i in range(len(argv)))
        if json_output:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print(message, file=sys.stderr)
        return 2
