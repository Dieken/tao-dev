"""Reuse existing Claude access credentials only within explicit experiments."""

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def environment(workspace):
    return os.environ | {'CLAUDE_CONFIG_DIR': str(workspace / 'client-config'),
                         'XDG_CONFIG_HOME': str(workspace / 'xdg-config'),
                         'GIT_CONFIG_GLOBAL': str(workspace / 'gitconfig'),
                         'CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC': '1'}


def read_credentials():
    if sys.platform == 'darwin':
        result = subprocess.run(['security', 'find-generic-password', '-s', 'Claude Code-credentials', '-w'],
                                capture_output=True, text=True, timeout=15, check=False, encoding='utf-8')
        if result.returncode == 0:
            return result.stdout.strip()
    path = Path.home() / '.claude/.credentials.json'
    if path.is_file():
        return path.read_text(encoding='utf-8')
    raise RuntimeError('Existing Claude file/Keychain access credentials are unavailable; no login attempted.')


@contextmanager
def access_environment(workspace, timeout):
    settings_path = Path.home() / '.claude/settings.json'
    settings = json.loads(settings_path.read_text(encoding='utf-8')) if settings_path.exists() else {}
    try:
        raw = read_credentials()
    except RuntimeError:
        raw = None
    env = environment(workspace)
    routing = ('ANTHROPIC_API_KEY', 'ANTHROPIC_AUTH_TOKEN', 'ANTHROPIC_BASE_URL',
               'CLAUDE_CODE_USE_BEDROCK', 'CLAUDE_CODE_USE_VERTEX', 'CLAUDE_CODE_USE_FOUNDRY')
    env.pop('CLAUDE_CODE_OAUTH_REFRESH_TOKEN', None)
    env.pop('CLAUDE_CODE_OAUTH_SCOPES', None)
    if raw is not None:
        digest = hashlib.sha256(raw.encode()).digest()
        data = json.loads(raw).get('claudeAiOauth', {})
        if not data.get('accessToken') or data.get('expiresAt', 0) / 1000 - time.time() <= timeout + 120:
            raise RuntimeError('Existing Claude access token cannot cover this probe; no refresh attempted.')
        if settings.get('apiKeyHelper') or any(env.get(key) or settings.get('env', {}).get(key) for key in routing):
            raise RuntimeError('Custom Claude provider routing needs a separately reviewed adapter.')
        env['CLAUDE_CODE_OAUTH_TOKEN'] = data['accessToken']
        if (isinstance(settings.get('model'), str)
                and re.fullmatch(r'[A-Za-z0-9._-]+', settings['model'])):
            env['ANTHROPIC_MODEL'] = settings['model']
        secrets = [value for key, value in data.items() if key.endswith('Token') and isinstance(value, str)]
        source = 'credentials'
    else:
        configured = settings.get('env') or {}
        token_keys = [key for key in ('ANTHROPIC_API_KEY', 'ANTHROPIC_AUTH_TOKEN')
                      if isinstance(configured.get(key), str) and configured[key].strip()]
        if settings.get('apiKeyHelper') or len(token_keys) != 1:
            raise RuntimeError('Existing Claude file/Keychain access credentials are unavailable; no login attempted.')
        for key in routing:
            env.pop(key, None)
        env.pop('ANTHROPIC_MODEL', None)
        for key in routing:
            value = configured.get(key)
            if isinstance(value, str) and value.strip():
                env[key] = value
        token = configured[token_keys[0]]
        env[token_keys[0]] = token
        model = configured.get('ANTHROPIC_MODEL')
        if isinstance(model, str) and re.fullmatch(r'[A-Za-z0-9._-]+', model):
            env['ANTHROPIC_MODEL'] = model
        secrets = [token]
        digest = hashlib.sha256(settings_path.read_bytes()).digest()
        source = 'settings'
    try:
        yield env, secrets
    finally:
        env.pop('CLAUDE_CODE_OAUTH_TOKEN', None)
        if source == 'credentials':
            if hashlib.sha256(read_credentials().encode()).digest() != digest:
                raise RuntimeError('Personal Claude credentials changed during the experiment; no restoration attempted.')
        elif hashlib.sha256(settings_path.read_bytes()).digest() != digest:
            raise RuntimeError('Personal Claude settings changed during the experiment; no restoration attempted.')


def install_arguments(scope):
    """Return a non-interactive install command supported by current Claude CLIs."""
    return ['plugin', 'install', 'tao-dev@tao-runtime-test', '--scope', scope, '--yes']


def configure(workspace, inside, scope):
    config = workspace / 'client-config'
    config.mkdir(mode=0o700)
    marketplace = workspace / 'marketplace'
    shutil.copytree(ROOT / 'plugins/tao-dev', marketplace / 'plugins/tao-dev',
                    ignore=shutil.ignore_patterns('__pycache__'))
    (marketplace / '.claude-plugin').mkdir()
    (marketplace / '.claude-plugin/marketplace.json').write_text(json.dumps({
        'name': 'tao-runtime-test', 'owner': {'name': 'tao-dev acceptance'},
        'plugins': [{'name': 'tao-dev', 'source': './plugins/tao-dev'}]}), encoding='utf-8')
    (inside / '.gitignore').write_text('.claude/settings.local.json\n', encoding='utf-8')
    for arguments in (['plugin', 'marketplace', 'add', str(marketplace)],
                      install_arguments(scope)):
        result = subprocess.run(['claude', *arguments], cwd=inside, env=environment(workspace),
                                capture_output=True, text=True, timeout=300, check=False, encoding='utf-8')
        if result.returncode:
            raise RuntimeError('Isolated Claude plugin configuration failed: ' + result.stdout + result.stderr)


def lifecycle(workspace, scope):
    if workspace.exists() or workspace.is_relative_to(ROOT):
        raise RuntimeError('Choose a fresh lifecycle workspace outside the repository.')
    inside = workspace / 'claude/inside'
    inside.mkdir(parents=True)
    configure(workspace, inside, scope)

    manifest = workspace / 'marketplace/plugins/tao-dev/.claude-plugin/plugin.json'
    data = json.loads(manifest.read_text(encoding='utf-8'))
    initial_version = data['version']
    match = re.fullmatch(r'(\d+)\.(\d+)\.(\d+)', initial_version)
    if match is None:
        raise RuntimeError(
            f'Claude lifecycle requires a three-part semantic version; got {initial_version!r}.')
    major, minor, patch = match.groups()
    updated_version = f'{major}.{minor}.{int(patch) + 1}'
    runs = []

    def command(*arguments):
        result = subprocess.run(['claude', 'plugin', *arguments], cwd=inside, env=environment(workspace),
                                capture_output=True, text=True, timeout=300, check=False, encoding='utf-8')
        if result.returncode:
            raise RuntimeError('Native Claude lifecycle operation failed: ' + result.stdout + result.stderr)
        try:
            value = json.loads(result.stdout)
        except json.JSONDecodeError:
            value = result.stdout.strip()
        runs.append({'operation': arguments[0], 'result': value})
        return value

    def installed(enabled, version):
        rows = [item for item in command('list', '--json') if item['id'] == 'tao-dev@tao-runtime-test']
        if len(rows) != 1 or rows[0]['enabled'] != enabled or rows[0]['version'] != version or rows[0]['scope'] != scope:
            raise RuntimeError('Native Claude plugin state does not match the requested lifecycle transition.')
        if not Path(rows[0]['installPath']).resolve().is_relative_to(workspace):
            raise RuntimeError('Native Claude installation escaped the experiment.')

    installed(True, initial_version)
    command('disable', 'tao-dev@tao-runtime-test', '--scope', scope)
    installed(False, initial_version)
    command('enable', 'tao-dev@tao-runtime-test', '--scope', scope)
    installed(True, initial_version)
    data['version'] = updated_version
    manifest.write_text(json.dumps(data), encoding='utf-8')
    command('update', 'tao-dev@tao-runtime-test', '--scope', scope, '--yes')
    installed(True, updated_version)
    command('uninstall', 'tao-dev@tao-runtime-test', '--scope', scope, '--yes')
    if any(item['id'] == 'tao-dev@tao-runtime-test' for item in command('list', '--json')):
        raise RuntimeError('Uninstalled Claude plugin still appears in native state.')
    return {'client': 'claude', 'scope': scope, 'runs': runs, 'model_called': False}
