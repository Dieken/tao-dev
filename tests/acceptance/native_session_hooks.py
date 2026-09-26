"""Real Cursor and Kiro sessions that prove a native write triggers tao-dev."""

import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _terminate(process, number):
    if os.name == 'posix':
        os.killpg(process.pid, number)
    else:
        subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                       capture_output=True, timeout=5, check=False)


def _personal_state():
    home = Path.home()
    paths = (
        home / '.cursor/cli-config.json',
        home / '.cursor/config.json',
        home / '.kiro/settings/cli.json',
        home / '.kiro/settings/mcp.json',
    )
    return {
        str(path.relative_to(home)): hashlib.sha256(path.read_bytes()).hexdigest()
        if path.is_file() else None
        for path in paths
    }


def _environment(client, workspace):
    env = os.environ.copy()
    env['TAO_CLI_DIR'] = str(workspace / 'shared-cli')
    env['GIT_CONFIG_GLOBAL'] = str(workspace / 'gitconfig')
    env['XDG_CONFIG_HOME'] = str(workspace / 'xdg')
    if client == 'cursor':
        env['CURSOR_CONFIG_DIR'] = str(workspace / 'cursor-home')
    else:
        env['KIRO_HOME'] = str(workspace / 'kiro-home')
    return env


def _install(client, workspace, project, env):
    scripts = ROOT / 'plugins/tao-dev/skills/tao-dev/scripts'
    sys.path.insert(0, str(scripts))
    import install_clients
    variable = 'CURSOR_CONFIG_DIR' if client == 'cursor' else 'KIRO_HOME'
    previous = os.environ.get(variable)
    os.environ[variable] = env[variable]
    try:
        installed = install_clients.install_plugin(
            client, str(ROOT), 'tao-dev@tao-dev', 'project', project,
            python=Path(sys.executable))
        if client == 'cursor':
            source = Path(installed['plugin_path']) / 'com.cursor/hooks/hooks.json'
            target = project / '.cursor/hooks.json'
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())
        return installed
    finally:
        if previous is None:
            os.environ.pop(variable, None)
        else:
            os.environ[variable] = previous


def _command(client, prompt):
    if client == 'cursor':
        return ['agent', '-p', '--force', '--output-format', 'stream-json', prompt]
    return ['kiro-cli', 'chat', '--v3', '--no-interactive', '--trust-all-tools',
            '--output-format', 'stream-json', prompt]


def _run_kiro_tui(prompt, project, env, stdout_path, timeout):
    if os.name != 'posix':
        raise RuntimeError('Kiro V3 TUI hook acceptance requires a supported PTY runner.')
    import pty
    import select

    output = bytearray()
    pid, descriptor = pty.fork()
    if pid == 0:
        os.chdir(project)
        os.environ.clear()
        os.environ.update(env)
        os.execvp('kiro-cli', ['kiro-cli', 'chat', '--v3', '--trust-all-tools', prompt])
    accepted = False
    timed_out = False
    evidence = False
    deadline = time.monotonic() + timeout
    target = project / 'docs/probe.md'
    cache = project / 'tmp/tao/cache/hook.json'
    try:
        while time.monotonic() < deadline:
            ready, _, _ = select.select([descriptor], [], [], 0.2)
            if ready:
                try:
                    chunk = os.read(descriptor, 65536)
                except OSError:
                    break
                output.extend(chunk)
            plain = re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]', '', output.decode('utf-8', 'replace'))
            if not accepted and 'Yes, I accept' in plain:
                os.write(descriptor, b'\x1b[B\n')
                accepted = True
            if target.is_file() and cache.is_file():
                evidence = True
                break
        else:
            timed_out = True
    finally:
        try:
            os.killpg(pid, signal.SIGTERM)
        except PermissionError:
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        except ProcessLookupError:
            pass
        reap_deadline = time.monotonic() + 3
        while time.monotonic() < reap_deadline:
            try:
                done, _ = os.waitpid(pid, os.WNOHANG)
            except ChildProcessError:
                done = pid
            if done == pid:
                break
            time.sleep(0.05)
        else:
            try:
                os.killpg(pid, signal.SIGKILL)
            except PermissionError:
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            except ProcessLookupError:
                pass
            final_deadline = time.monotonic() + 2
            while time.monotonic() < final_deadline:
                try:
                    done, _ = os.waitpid(pid, os.WNOHANG)
                except ChildProcessError:
                    break
                if done == pid:
                    break
                time.sleep(0.05)
        os.close(descriptor)
        stdout_path.write_bytes(output)
    return 0 if evidence else 1, timed_out, evidence


def run(client, workspace, timeout=45):
    """Run one paid model turn in isolated client state and inspect raw output."""
    if client not in ('cursor', 'kiro'):
        raise ValueError('Real hook acceptance supports cursor or kiro.')
    if not 1 <= timeout <= 45:
        raise ValueError('Real hook acceptance timeout must be between 1 and 45 seconds.')
    workspace = Path(workspace).resolve()
    if workspace.exists() or workspace.is_relative_to(ROOT):
        raise RuntimeError('Choose a fresh acceptance workspace outside the repository.')
    project = workspace / client / 'inside'
    project.mkdir(parents=True)
    subprocess.run(['git', 'init', '-q', str(project)], check=True, timeout=15)
    (project / '.tao').mkdir()
    (project / '.tao/config.toml').write_text('version = 1\nlocale = "en"\n', encoding='utf-8')
    (project / 'docs').mkdir()
    env = _environment(client, workspace)
    before = _personal_state()
    installation = _install(client, workspace, project, env)
    if client == 'kiro':
        settings = workspace / 'kiro-home/settings/cli.json'
        settings.parent.mkdir(parents=True, exist_ok=True)
        settings.write_text(json.dumps({
            'chat.agentEngine': 'v3',
            'chat.disableTrustAllConfirmation': True,
        }) + '\n', encoding='utf-8')
    prompt = (
        'This is an isolated tao-dev hook acceptance project. Use your native file '
        'write tool to create docs/probe.md containing exactly "# Probe\\n". Do not '
        'run shell commands, checks, or the hook yourself, and do not repair the '
        'document. After the write, report the tao-dev hook feedback you actually '
        'received. Do not read or change files outside this project.'
    )
    artifact = ROOT / 'tmp/tao/client-acceptance' / f'{client}-hook-{time.time_ns()}'
    artifact.mkdir(parents=True)
    stdout_path = artifact / 'session.jsonl'
    stderr_path = artifact / 'session.stderr'
    timed_out = False
    terminated_after_evidence = False
    if client == 'kiro' and os.name == 'posix':
        exit_code, timed_out, terminated_after_evidence = _run_kiro_tui(
            prompt, project, env, stdout_path, timeout)
        stderr_path.write_text('', encoding='utf-8')
    else:
        process = None
        with stdout_path.open('w', encoding='utf-8') as stdout, stderr_path.open('w', encoding='utf-8') as stderr:
            process = subprocess.Popen(_command(client, prompt), cwd=project, env=env,
                                       stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
                                       text=True, start_new_session=True, encoding='utf-8')
            target = project / 'docs/probe.md'
            cache = project / 'tmp/tao/cache/hook.json'
            if client == 'cursor':
                deadline = time.monotonic() + timeout
                while process.poll() is None and time.monotonic() < deadline:
                    if target.is_file() and cache.is_file():
                        terminated_after_evidence = True
                        _terminate(process, signal.SIGTERM)
                        break
                    time.sleep(0.1)
                if process.poll() is None and not terminated_after_evidence:
                    timed_out = True
                    _terminate(process, signal.SIGTERM)
            else:
                try:
                    process.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    timed_out = True
                    _terminate(process, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                _terminate(process, signal.SIGKILL)
                process.wait(timeout=5)
        exit_code = 0 if terminated_after_evidence else process.returncode
    error = stderr_path.read_text(errors='replace', encoding='utf-8')
    target = project / 'docs/probe.md'
    exact_write = target.is_file() and target.read_text(encoding='utf-8') == '# Probe\n'
    cache = project / 'tmp/tao/cache/hook.json'
    hook_report = json.loads(cache.read_text(encoding='utf-8')) if cache.is_file() else {}
    hook_feedback = bool(hook_report.get('message'))
    after = _personal_state()
    summary = {
        'client': client,
        'exit_code': exit_code,
        'timed_out': timed_out,
        'terminated_after_evidence': terminated_after_evidence,
        'exact_native_write': exact_write,
        'hook_feedback_observed': hook_feedback,
        'personal_state_unchanged': before == after,
        'installation_id': installation['plugin_id'],
        'stdout': str(stdout_path),
        'stderr': str(stderr_path),
        'stderr_tail': error[-1000:],
    }
    (artifact / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    if timed_out or exit_code or not exact_write or not hook_feedback or before != after:
        raise RuntimeError('Native session/hook acceptance failed: ' + json.dumps(summary))
    return summary
