"""Opt-in Codex acceptance state; never configure the personal client.

Native skill discovery, not plugin list output, establishes the boundary.
Authentication snapshots carry no refresh token and are removed after use.
"""

import base64
import json
import os
import select
import subprocess
import time
import tomllib
from contextlib import contextmanager
from pathlib import Path

PLUGIN_ID = 'tao-dev@tao-acceptance'
ROOT = Path(__file__).resolve().parents[2]


def environment(workspace):
    return os.environ | {'CODEX_HOME': str(workspace / 'client-state'),
                         'XDG_CONFIG_HOME': str(workspace / 'client-xdg'),
                         'GIT_CONFIG_GLOBAL': str(workspace / 'client-gitconfig')}


def configure(workspace, inside, plugin):
    if workspace.resolve().is_relative_to(ROOT) or not inside.resolve().is_relative_to(workspace.resolve()):
        raise RuntimeError('The acceptance workspace must be independent of the development repository.')
    state = workspace / 'client-state'
    state.mkdir(mode=0o700)
    outside = workspace / 'codex/outside'
    outside.mkdir(parents=True, exist_ok=True)
    subprocess.run(['git', '-c', 'init.defaultBranch=main', 'init', '--quiet', str(inside)],
                   check=True, env=environment(workspace), timeout=15)
    marketplace = inside / '.agents/plugins'
    marketplace.mkdir(parents=True)
    (marketplace / 'marketplace.json').write_text(json.dumps({
        'name': 'tao-acceptance', 'plugins': [{
            'name': 'tao-dev', 'source': {'source': 'local', 'path': './' + plugin.relative_to(inside).as_posix()},
            'policy': {'installation': 'AVAILABLE', 'authentication': 'ON_INSTALL'}, 'category': 'Productivity'}]}), encoding='utf-8')
    (inside / '.codex').mkdir()
    (inside / '.codex/config.toml').write_text(
        '[marketplaces.tao-acceptance]\nsource_type = "local"\nsource = ' + json.dumps(str(inside)) +
        '\n[plugins."' + PLUGIN_ID + '"]\nenabled = true\n[features]\nhooks = true\n', encoding='utf-8')
    config = ('check_for_update_on_startup = false\n[features]\nremote_plugin = false\napps = false\n[agents]\nenabled = false\n[projects.' + json.dumps(str(inside)) +
              ']\ntrust_level = "trusted"\n')
    (state / 'config.toml').write_text(config, encoding='utf-8')
    installed = subprocess.run(['codex', 'plugin', 'add', PLUGIN_ID, '--json'], cwd=inside,
                               env=environment(workspace), capture_output=True, text=True, timeout=45, check=False)
    if installed.returncode:
        raise RuntimeError('Isolated plugin installation failed: ' + installed.stderr)
    result = json.loads(installed.stdout)
    cached = Path(result['installedPath']).resolve()
    if not cached.is_relative_to(state.resolve()):
        raise RuntimeError('Client reported an installation outside its isolated state.')
    # plugin add enables the plugin at user scope. A missing marketplace in
    # plugin list does not suppress cached skills in model context.
    (state / 'config.toml').write_text(config + '[plugins."' + PLUGIN_ID + '"]\nenabled = false\n', encoding='utf-8')
    return cached


def discover(workspace, directories, kind):
    with (workspace / 'skills-query.stderr').open('w') as errors:
        process = subprocess.Popen(['codex', 'app-server'], cwd=workspace,
                                   env=environment(workspace), stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=errors)
        buffer = b''

        def send(value):
            process.stdin.write((json.dumps(value) + '\n').encode())
            process.stdin.flush()

        def receive(identity):
            nonlocal buffer
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                while b'\n' in buffer:
                    line, buffer = buffer.split(b'\n', 1)
                    value = json.loads(line)
                    if value.get('id') == identity:
                        if 'error' in value:
                            raise RuntimeError('Native skill query failed: ' + json.dumps(value['error']))
                        return value['result']
                ready, _, _ = select.select([process.stdout], [], [], max(0, deadline - time.monotonic()))
                if not ready:
                    break
                chunk = os.read(process.stdout.fileno(), 65536)
                if not chunk:
                    break
                buffer += chunk
            raise RuntimeError('Native skill query did not return a bounded response.')

        try:
            send({'id': 1, 'method': 'initialize', 'params': {'clientInfo': {'name': 'tao-acceptance', 'version': '0.1'},
                                                           'capabilities': {'experimentalApi': True}}})
            receive(1)
            send({'method': 'initialized'})
            params = {'cwds': [str(p) for p in directories]}
            if kind == 'skills':
                params['forceReload'] = True
            send({'id': 2, 'method': kind + '/list', 'params': params})
            result = receive(2)
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
    return result['data']


def skills(workspace, directories):
    rows = {}
    for row in discover(workspace, directories, 'skills'):
        if row.get('errors'):
            raise RuntimeError('Native skill scan reported errors.')
        rows[row['cwd']] = [skill for skill in row['skills'] if skill.get('pluginId') == PLUGIN_ID and skill.get('enabled')]
    return rows


def hook_inventory(workspace, inside):
    rows = discover(workspace, [inside, workspace / 'codex/outside'], 'hooks')
    return rows


def trust_test_hook(workspace, inside, plugin):
    rows = hook_inventory(workspace, inside)
    if any(row['errors'] or row['warnings'] for row in rows):
        raise RuntimeError('Hook discovery reported errors or warnings; trust was not changed.')
    hooks = [hook for row in rows for hook in row['hooks']]
    inside_hooks = next((row['hooks'] for row in rows if row['cwd'] == str(inside)), [])
    if len(hooks) != 1 or len(inside_hooks) != 1:
        raise RuntimeError('Trust requires exactly one known hook inside and no hooks outside.')
    hook = hooks[0]
    source = Path(hook['sourcePath']).resolve()
    cache = source.parents[2]
    expected = 'python3 -I -B "' + str(cache / 'skills/tao-dev/scripts/hook.py') + '"'
    if (not cache.is_relative_to((workspace / 'client-state').resolve()) or
            hook['pluginId'] != PLUGIN_ID or hook['eventName'] != 'postToolUse' or
            hook['handlerType'] != 'command' or hook['command'] != expected or
            hook['matcher'] != 'Write|Edit|apply_patch' or hook['timeoutSec'] != 35 or
            not hook['enabled'] or hook['isManaged']):
        raise RuntimeError('The discovered hook differs from the reviewed acceptance handler.')
    for folder in ('skills', 'com.openai'):
        for original in (ROOT / 'plugins/tao-dev' / folder).rglob('*'):
            if not original.is_file() or '__pycache__' in original.parts:
                continue
            relative = original.relative_to(ROOT / 'plugins/tao-dev')
            for package in (plugin, cache):
                target = package / relative
                if target.is_symlink() or not target.is_file() or target.read_bytes() != original.read_bytes():
                    raise RuntimeError('Installed hook resources differ from the reviewed source.')
    config = workspace / 'client-state/config.toml'
    config.write_text(config.read_text(encoding='utf-8') + '\n[hooks.state.' + json.dumps(hook['key']) +
                      ']\ntrusted_hash = ' + json.dumps(hook['currentHash']) + '\n', encoding='utf-8')
    after = hook_inventory(workspace, inside)
    trusted = [item for row in after for item in row['hooks']]
    if len(trusted) != 1 or trusted[0]['trustStatus'] != 'trusted':
        raise RuntimeError('The native client did not recognize the exact hook trust.')
    return trusted[0]


def check_boundary(workspace, inside):
    outside = workspace / 'codex/outside'
    rows = skills(workspace, [inside, outside])
    if len(rows.get(str(inside), [])) != 1 or rows.get(str(outside), []) or str(outside) not in rows:
        raise RuntimeError('Native skill discovery did not prove inside-only activation.')
    for item in rows[str(inside)]:
        if not Path(item['path']).resolve().is_relative_to((workspace / 'client-state').resolve()):
            raise RuntimeError('Native skill came from outside the isolated cache.')
    return rows


@contextmanager
def access_snapshot(workspace, timeout):
    """Reuse a current file-backed ChatGPT access token without token rotation."""
    state = workspace / 'client-state'
    original = Path.home() / '.codex/auth.json'
    source = json.loads(original.read_text(encoding='utf-8'))
    if source.get('auth_mode') != 'chatgpt':
        raise RuntimeError('This opt-in adapter requires existing file-backed ChatGPT authentication.')
    tokens = source['tokens']
    access = tokens['access_token']
    try:
        segment = access.split('.')[1]
        expires = json.loads(base64.urlsafe_b64decode(segment + '=' * (-len(segment) % 4)))['exp']
    except (ValueError, KeyError, IndexError) as exc:
        raise RuntimeError('Cannot determine the existing access token lifetime.') from exc
    if expires - time.time() <= timeout + 120:
        raise RuntimeError('Existing access token cannot cover this probe; no refresh or login attempted.')
    data = {key: source[key] for key in ('auth_mode', 'last_refresh') if key in source}
    data['tokens'] = {key: tokens[key] for key in ('access_token', 'id_token', 'account_id') if key in tokens}
    data['tokens']['refresh_token'] = ''
    config = tomllib.loads((Path.home() / '.codex/config.toml').read_text(encoding='utf-8'))
    if config.get('model_providers') or config.get('profile'):
        raise RuntimeError('Custom provider/profile authentication needs a separately reviewed adapter.')
    keys = ('model', 'model_provider', 'openai_base_url', 'chatgpt_base_url', 'forced_login_method', 'forced_chatgpt_workspace_id')
    prefix = '\n'.join(key + ' = ' + json.dumps(config[key]) for key in keys if key in config)
    prefix += '\ncli_auth_credentials_store = "file"\nmodel_reasoning_effort = "low"\nweb_search = "disabled"\n'
    current = (state / 'config.toml').read_text(encoding='utf-8')
    path = state / 'auth.json'
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        with os.fdopen(descriptor, 'w') as stream:
            json.dump(data, stream)
        (state / 'config.toml').write_text(prefix + current, encoding='utf-8')
        yield [v for k, v in tokens.items() if k.endswith('_token') and isinstance(v, str) and v]
    finally:
        path.unlink(missing_ok=True)
        (state / 'config.toml').write_text(current, encoding='utf-8')


def private_log(path):
    """Create a log readable only by its owner, before any child can write."""
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    return os.fdopen(descriptor, 'w', encoding='utf-8')


def redact(paths, values):
    for path in paths:
        text = path.read_text(encoding='utf-8')
        for value in values:
            text = text.replace(value, '[REDACTED]')
        path.write_text(text, encoding='utf-8')
