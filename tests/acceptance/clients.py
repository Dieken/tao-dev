"""Opt-in real CLI probes; never install or register components globally."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import tomllib

ROOT = Path(__file__).resolve().parents[2]
PLUGIN = ROOT / 'plugins/tao-dev'


def global_configuration():
    home = Path.home()
    paths = [home / '.codex/config.toml', home / '.codex/hooks.json',
             home / '.agents/plugins/marketplace.json', home / '.claude/settings.json',
             home / '.claude/plugins/installed_plugins.json',
             home / '.claude/plugins/known_marketplaces.json']
    return {str(p.relative_to(home)): hashlib.sha256(p.read_bytes()).hexdigest()
            if p.is_file() else None for p in paths}


def prepare(directory, client):
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / 'local plugins/tao-dev'
    shutil.copytree(PLUGIN, target, dirs_exist_ok=True, ignore=shutil.ignore_patterns('__pycache__'))
    (directory / '.tao').mkdir(exist_ok=True)
    (directory / '.tao/config.toml').write_text('version = 1\nlocale = "en"\n')
    (directory / 'docs').mkdir(exist_ok=True)
    (directory / 'example.py').write_text('from pathlib import Path\n\ndef export(path, value):\n    Path(path).write_text(value)\n')
    (directory / 'requirements.txt').write_text('Export must refuse to overwrite an existing file and preserve its bytes.\n')
    if client == 'codex':
        skill = directory / '.agents/skills/tao-dev'
        if not skill.exists():
            skill.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(target / 'skills/tao-dev', skill)
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client', choices=['claude', 'codex'], required=True)
    parser.add_argument('--case', choices=['inside', 'outside', 'review', 'write', 'recover'], required=True)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--timeout', type=int, default=180)
    args = parser.parse_args()
    if args.client == 'codex':
        version = subprocess.check_output(['codex', '--version'], text=True).strip()
        if '0.154.0' in version:
            print(json.dumps({'client':'codex', 'status':'blocked', 'reason':'The tested client persists project trust globally, even with an invocation override. Strict-isolation probes are disabled for this version.'}))
            return 2
    directory = args.workspace.resolve() / args.client / ('outside' if args.case == 'outside' else 'recovery-' + str(time.time_ns()) if args.case == 'recover' else 'inside')
    directory.mkdir(parents=True, exist_ok=True)
    plugin = None if args.case == 'outside' else prepare(directory, args.client)
    env = os.environ.copy()
    env['TAO_PYTHON'] = sys.executable
    env['TAO_RUNTIME_DIR'] = str(args.workspace.resolve() / 'runtime')
    if plugin:
        setup = subprocess.run([sys.executable, str(plugin / 'skills/tao-dev/scripts/tao.py'),
                                'setup', '--wheelhouse', str(ROOT / 'tmp/tao/wheels'), '--format', 'json'],
                               env=env, capture_output=True, text=True, timeout=180)
        if setup.returncode:
            raise RuntimeError('Isolated offline runtime preparation failed: ' + setup.stdout + setup.stderr)
    recovery = None
    if args.case == 'recover':
        from recovery import prepare as prepare_recovery
        recovery = prepare_recovery(directory, plugin, env=env)
    boundary = ('This is an isolated CLI acceptance experiment. Do not install, register, or change any global skill, plugin, marketplace, hook or client configuration. '
                'Use scratch paths only inside this experiment directory. Do not search outside this experiment directory or read authentication files. Do not use network tools or delegate. ')
    if args.case in ('inside', 'outside'):
        prompt = boundary + ('Using only your already advertised skills and commands, report whether tao-dev is available and its exact invocation name. Do not search the filesystem. If available, invoke its status operation, read only its relevant runtime references and run its doctor/status with the configured Python interpreter. Report limitations accurately. Interpreter: ' + sys.executable if args.case == 'inside' else 'Using only your already advertised skills and commands, report whether tao-dev is available and its exact invocation name. Do not use any tools or search the filesystem. Reply with a short JSON object.')
    elif args.case == 'recover':
        prompt = boundary + 'Use tao-dev to continue solely from the persisted handoff at ' + recovery['handoff'] + '. Repair example.py with the smallest change. Do not modify check.py, requirements.txt, .tao or plugin resources. Preserve the existing plan and IDs. Detect stale evidence after the code change, run configured verification, and update the existing task checkbox and plan summary only using actual results. Do not create a new plan or ask for already supplied requirements. Use Python interpreter ' + sys.executable + '. Finish with the measured checks, outcomes and limits.'
    elif args.case == 'review':
        prompt = boundary + 'Use the available tao-dev review guidance to independently review example.py against requirements.txt. Do not change either file. Identify a concrete trigger, evidence and minimal fix; do not invent findings. This is your first review: no other reviewer conclusions are provided. Keep the response concise.'
    else:
        prompt = boundary + 'Use a native file Write/Edit/apply_patch tool to create docs/probe.md containing exactly "# Probe\n". This deliberately invalid document tests hook feedback. Do not fix it, run checks manually, or invoke the hook yourself. Report any hook feedback actually observed.'
    if args.client == 'claude':
        command = ['claude', '-p', '--no-session-persistence', '--output-format', 'stream-json', '--verbose', '--strict-mcp-config', '--permission-mode', 'acceptEdits', '--permission-prompts', 'none', '--allowedTools', 'Read,Glob,Grep,Skill,Bash,Write,Edit']
        if plugin:
            command += ['--plugin-dir', str(plugin)]
        if args.case == 'review':
            command += ['--agent', 'tao-dev:reviewer']
    else:
        command = ['codex', '-c', 'projects.' + json.dumps(str(directory)) + '.trust_level="trusted"', '-a', 'never', 'exec', '--ephemeral', '--json', '--skip-git-repo-check', '--sandbox', 'workspace-write']
    config_file = Path.home() / '.codex/config.toml'
    codex_before = tomllib.loads(config_file.read_text()) if config_file.exists() else {}
    before = global_configuration()
    logdir = ROOT / 'tmp/tao/client-acceptance'
    logdir.mkdir(parents=True, exist_ok=True)
    name = args.client + '-' + args.case + '-' + str(time.time_ns())
    start = time.monotonic()
    timed_out = False
    with (logdir / (name + '.jsonl')).open('w') as stdout, (logdir / (name + '.stderr')).open('w') as stderr:
        process = subprocess.Popen(command, cwd=directory, env=env, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr, text=True, start_new_session=True)
        try:
            process.communicate(prompt, timeout=args.timeout)
        except subprocess.TimeoutExpired:
            import signal
            os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=10)
            timed_out = True
    after = global_configuration()
    codex_after = tomllib.loads(config_file.read_text()) if config_file.exists() else {}
    report = {'log_prefix': name, 'client': args.client, 'case': args.case, 'exit_code': process.returncode,
              'timed_out': timed_out, 'elapsed_seconds': round(time.monotonic() - start, 3),
              'global_configuration_unchanged': before == after,
              'changed_global_files': [p for p in before if before[p] != after[p]],
              'changed_codex_sections': [k for k in codex_before.keys() | codex_after.keys() if codex_before.get(k) != codex_after.get(k)],
              'loading': 'session-plugin-dir' if plugin and args.client == 'claude' else 'project-native-skill' if plugin else 'no-test-loading',
              'native_codex_plugin_tested': False, 'recovery': recovery,
              'codex_model_configuration': {'model': codex_before.get('model'), 'provider': codex_before.get('model_provider', 'openai')} if args.client == 'codex' else None}
    (logdir / (name + '.summary.json')).write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return 1 if timed_out or process.returncode or not report['global_configuration_unchanged'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
