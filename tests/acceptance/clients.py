"""Opt-in real CLI probes; never install or register components globally."""

import argparse
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import time
import tomllib
from contextlib import nullcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLUGIN = ROOT / 'plugins/tao-dev'


def global_configuration():
    home = Path.home()
    paths = [home / '.codex/config.toml', home / '.codex/hooks.json', home / '.codex/auth.json',
             home / '.claude.json', home / '.gitconfig', home / '.gitignore',
             home / '.agents/plugins/marketplace.json', home / '.claude/settings.json',
             home / '.claude/plugins/installed_plugins.json',
             home / '.claude/plugins/known_marketplaces.json']
    return {str(p.relative_to(home)): hashlib.sha256(p.read_bytes()).hexdigest()
            if p.is_file() else None for p in paths}


def prepare(directory, client, *, native_plugin=False, codex_legacy=False):
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / 'local plugins/tao-dev'
    if codex_legacy:
        sys.path.insert(0, str(ROOT / 'scripts'))
        from package_plugin import build
        build(target, codex_legacy=True)
    else:
        shutil.copytree(PLUGIN, target, dirs_exist_ok=True, ignore=shutil.ignore_patterns('__pycache__'))
    (directory / '.tao').mkdir(exist_ok=True)
    (directory / '.tao/config.toml').write_text('version = 1\nlocale = "en"\n')
    (directory / 'docs').mkdir(exist_ok=True)
    (directory / 'example.py').write_text('from pathlib import Path\n\ndef export(path, value):\n    Path(path).write_text(value)\n')
    (directory / 'requirements.txt').write_text('Export must refuse to overwrite an existing file and preserve its bytes.\n')
    if client == 'codex' and not native_plugin:
        skill = directory / '.agents/skills/tao-dev'
        if not skill.exists():
            skill.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(target / 'skills/tao-dev', skill)
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client', choices=['claude', 'codex'], required=True)
    parser.add_argument('--case', choices=['inside', 'outside', 'review', 'write', 'recover', 'plan', 'verify'], required=True)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--timeout', type=int, default=180)
    parser.add_argument('--isolated-codex', action='store_true', help='Use fresh experiment-only native plugin state.')
    parser.add_argument('--reuse-codex-auth', action='store_true', help='Temporarily reuse existing unexpired access credentials without a refresh token.')
    parser.add_argument('--codex-legacy', action='store_true', help='Test the generated compatibility package required for 0.154.0 native hooks.')
    parser.add_argument('--trust-test-hook', action='store_true', help='Trust only the exact, locally verified tao-dev hook in experiment state.')
    parser.add_argument('--disable-hooks', action='store_true', help='Exercise explicit verification with client hooks disabled.')
    parser.add_argument('--claude-scope', choices=['user', 'project', 'local'], help='Use a native installation in fresh experiment-only Claude state.')
    parser.add_argument('--reuse-claude-auth', action='store_true', help='Reuse the existing Claude access token in the child environment only.')
    args = parser.parse_args()
    if args.isolated_codex != args.reuse_codex_auth or args.isolated_codex and args.client != 'codex':
        parser.error('Native Codex probes require both isolation and explicit access reuse.')
    if bool(args.claude_scope) != args.reuse_claude_auth or args.claude_scope and args.client != 'claude':
        parser.error('Claude scope probes require explicit existing access reuse.')
    if (args.codex_legacy or args.trust_test_hook) and not args.isolated_codex:
        parser.error('Codex packaging and hook options require isolated native probes.')
    if args.disable_hooks and not (args.isolated_codex or args.claude_scope):
        parser.error('Hook disabling requires isolated native probes.')
    if args.timeout <= 0:
        parser.error('timeout must be positive.')
    if (args.isolated_codex or args.claude_scope) and (args.workspace.exists() and any(args.workspace.iterdir()) or args.workspace.resolve().is_relative_to(ROOT)):
        parser.error('Isolated client probes require a fresh workspace outside the repository.')
    if not (args.isolated_codex or args.claude_scope):
        print(json.dumps({'client': args.client, 'status': 'blocked',
                          'reason': 'Model probes require explicit isolated client state. Personal-state loading is not tested by this runner.'}))
        return 2
    before = global_configuration()
    directory = args.workspace.resolve() / args.client / ('outside' if args.case == 'outside' else 'recovery-' + str(time.time_ns()) if args.case == 'recover' else 'inside')
    directory.mkdir(parents=True, exist_ok=True)
    plugin = None if args.case == 'outside' else prepare(directory, args.client, native_plugin=args.isolated_codex, codex_legacy=args.codex_legacy)
    env = os.environ.copy()
    native_boundary = None
    if args.isolated_codex:
        import isolated_codex
        workspace = args.workspace.resolve()
        inside = workspace / 'codex/inside' if args.case == 'outside' else directory
        if plugin is None:
            plugin = prepare(inside, args.client, native_plugin=True, codex_legacy=args.codex_legacy)
        isolated_codex.configure(workspace, inside, plugin)
        native_boundary = isolated_codex.check_boundary(workspace, inside)
        if args.trust_test_hook:
            isolated_codex.trust_test_hook(workspace, inside, plugin)
        if args.disable_hooks:
            config = inside / '.codex/config.toml'
            config.write_text(config.read_text().replace('hooks = true', 'hooks = false'))
        env = isolated_codex.environment(workspace)
    if args.claude_scope:
        import isolated_claude
        workspace = args.workspace.resolve()
        inside = workspace / 'claude/inside' if args.case == 'outside' else directory
        if plugin is None:
            plugin = prepare(inside, args.client)
        isolated_claude.configure(workspace, inside, args.claude_scope)
        env = isolated_claude.environment(workspace)
        if args.disable_hooks:
            settings = workspace / 'client-config/settings.json'
            value = json.loads(settings.read_text()) if settings.exists() else {}
            value['disableAllHooks'] = True
            settings.write_text(json.dumps(value))
    env['TAO_PYTHON'] = sys.executable
    env['TAO_RUNTIME_DIR'] = str(args.workspace.resolve() / 'runtime')
    if plugin:
        setup = subprocess.run([sys.executable, str(plugin / 'skills/tao-dev/scripts/tao.py'),
                                'setup', '--wheelhouse', str(ROOT / 'tmp/tao/wheels'), '--format', 'json'],
                               env=env, capture_output=True, text=True, timeout=180, check=False)
        if setup.returncode:
            raise RuntimeError('Isolated offline runtime preparation failed: ' + setup.stdout + setup.stderr)
    recovery = None
    if args.case in ('recover', 'verify'):
        from recovery import prepare as prepare_recovery
        recovery = prepare_recovery(directory, plugin, env=env)
    boundary = ('This is an isolated CLI acceptance experiment. Do not install, register, or change any global skill, plugin, marketplace, hook or client configuration. '
                'Use scratch paths only inside this experiment directory. Do not search outside this experiment directory or read authentication files. Do not use network tools or delegate. ')
    if args.isolated_codex or args.claude_scope:
        boundary += ('The experiment workspace is ' + str(args.workspace.resolve()) + ', including its installed plugin cache and runtime. '
                     'The core runtime is already prepared. Preserve TAO_RUNTIME_DIR=' + env['TAO_RUNTIME_DIR'] +
                     ' and TAO_PYTHON=' + sys.executable + '; do not substitute another runtime directory. ')
    if args.case in ('inside', 'outside'):
        prompt = boundary + ('Using only your already advertised skills and commands, report whether tao-dev is available and its exact invocation name. Do not search the filesystem. If available, invoke its status operation, follow its required starting references and run its doctor/status with the configured Python interpreter. Report limitations accurately. Interpreter: ' + sys.executable if args.case == 'inside' else 'Using only your already advertised skills and commands, report whether tao-dev is available and its exact invocation name. Do not use any tools or search the filesystem. Reply with a short JSON object.')
    elif args.case == 'recover':
        prompt = boundary + 'Use tao-dev to continue solely from the persisted handoff at ' + recovery['handoff'] + '. Repair example.py with the smallest change. Do not modify check.py, requirements.txt, .tao or plugin resources. Preserve the existing plan and IDs. Detect stale evidence after the code change, run configured verification, and update the existing task checkbox and plan summary only using actual results. Do not create a new plan or ask for already supplied requirements. Use Python interpreter ' + sys.executable + '. Finish with the measured checks, outcomes and limits.'
    elif args.case == 'review':
        prompt = boundary + 'Use the available tao-dev review guidance to independently review example.py against requirements.txt. Do not change either file. Identify a concrete trigger, evidence and minimal fix; do not invent findings. This is your first review: no other reviewer conclusions are provided. Keep the response concise.'
    elif args.case == 'plan':
        prompt = boundary + ('Use the native tao-dev new operation with this goal: plan how to make export refuse existing files and preserve their exact bytes. '
                             'Read example.py and requirements.txt. Create and fully fill one compact English plan with concrete acceptance, minimal design and tasks. '
                             'For this tiny change, aim for roughly 300 words and at most two tasks; keep the handoff to a few sentences. '
                             'These are size guidelines, not exact limits: do not count words or edit solely to hit a word count. '
                             'Do not implement the repair or change requirements, configuration or plugin resources. Then invoke the native tao-dev handoff operation '
                             'to save a concise persisted handoff for the same change and IDs. Use native Skill entries on Claude; Codex uses its advertised skill. '
                             'Actually validate the documents, leave implementation tasks open, and report only the paths and measured outcomes.')
    elif args.case == 'verify':
        prompt = boundary + ('Invoke the native tao-dev verify operation on the existing change ' + recovery['change'] +
                             '. This is a verification-only request: the example deliberately violates the existing requirement. '
                             'Use the actual Skill entry on Claude. Do not repair code, edit requirements or configuration, or check off tasks. '
                             'Run full verification and report its measured result and why readiness is or is not satisfied. '
                             'An honestly reported failed verification is the expected outcome of this acceptance experiment.')
    else:
        prompt = boundary + 'Use a native file Write/Edit/apply_patch tool to create docs/probe.md containing exactly "# Probe\n". This deliberately invalid document tests hook feedback. Do not fix it, run checks manually, or invoke the hook yourself. Report any hook feedback actually observed.'
    if args.client == 'claude':
        command = ['claude', '-p', '--no-session-persistence', '--output-format', 'stream-json', '--verbose', '--strict-mcp-config', '--permission-mode', 'acceptEdits', '--permission-prompts', 'none', '--max-budget-usd', '2', '--tools', 'Read,Glob,Grep,Skill,Bash,Write,Edit', '--allowedTools', 'Read,Glob,Grep,Skill,Bash,Write,Edit']
        if args.case == 'review':
            command += ['--agent', 'tao-dev:reviewer']
        if args.case == 'plan':
            command += ['--effort', 'low']
    else:
        command = ['codex', '-c', 'projects.' + json.dumps(str(directory)) + '.trust_level="trusted"', '-a', 'never', 'exec', '--ephemeral', '--json', '--skip-git-repo-check', '--sandbox', 'workspace-write']
    config_file = Path.home() / '.codex/config.toml'
    codex_before = tomllib.loads(config_file.read_text()) if config_file.exists() else {}
    logdir = ROOT / 'tmp/tao/client-acceptance'
    logdir.mkdir(parents=True, exist_ok=True)
    name = args.client + '-' + args.case + '-' + str(time.time_ns())
    start = time.monotonic()
    timed_out = False
    logs = [logdir / (name + suffix) for suffix in ('.jsonl', '.stderr')]
    credentials = isolated_codex.access_snapshot(args.workspace.resolve(), args.timeout) if args.isolated_codex else nullcontext([])
    if args.claude_scope:
        credentials = isolated_claude.access_environment(args.workspace.resolve(), args.timeout)
    secrets = []
    process = None
    try:
        with credentials as values, logs[0].open('w') as stdout, logs[1].open('w') as stderr:
            if args.claude_scope:
                scoped, secrets = values
                env = scoped | {key: env[key] for key in ('TAO_RUNTIME_DIR', 'TAO_PYTHON')}
            else:
                secrets = values
            process = subprocess.Popen(command, cwd=directory, env=env, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr, text=True, start_new_session=True)
            try:
                process.communicate(prompt, timeout=args.timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
            finally:
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGTERM)
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait()
    finally:
        if args.isolated_codex or args.claude_scope:
            from isolated_codex import redact
            redact([p for p in logs if p.exists()], secrets)
    after = global_configuration()
    codex_after = tomllib.loads(config_file.read_text()) if config_file.exists() else {}
    report = {'log_prefix': name, 'client': args.client, 'case': args.case, 'exit_code': process.returncode,
              'timed_out': timed_out, 'elapsed_seconds': round(time.monotonic() - start, 3),
              'global_configuration_unchanged': before == after,
              'changed_global_files': [p for p in before if before[p] != after[p]],
              'changed_codex_sections': [k for k in codex_before.keys() | codex_after.keys() if codex_before.get(k) != codex_after.get(k)],
              'loading': 'isolated-native-plugin',
              'claude_scope': args.claude_scope,
              'native_codex_plugin_tested': args.isolated_codex, 'native_skill_boundary': native_boundary, 'recovery': recovery,
              'package_format': 'codex-legacy' if args.codex_legacy else 'public',
              'hook_trust': args.trust_test_hook, 'hooks_disabled': args.disable_hooks,
              'codex_model_configuration': {'model': codex_before.get('model'), 'provider': codex_before.get('model_provider', 'openai')} if args.client == 'codex' else None}
    (logdir / (name + '.summary.json')).write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return 1 if timed_out or process.returncode or not report['global_configuration_unchanged'] else 0


if __name__ == '__main__':
    initial = global_configuration()
    try:
        result = main()
    finally:
        final = global_configuration()
        if initial != final:
            print(json.dumps({'isolation_guard': 'failed', 'changed_global_files': [p for p in initial if initial[p] != final[p]]}))
    raise SystemExit(result if initial == final else 1)
