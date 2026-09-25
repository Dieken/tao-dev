"""Native CLI plugin installation, scoped activation and conservative discovery.

No model calls are used. Config writes use Codex's own TOML editor; a temporary
client home lets that editor preserve project config without starting client
state databases in the project. Marketplace registrations may be shared and
are deliberately retained on uninstall.
"""
from __future__ import annotations

import hashlib
import json
import os
import queue
import re
import shlex
import shutil
import subprocess
import tempfile
import threading
import time
import tomllib
from contextlib import nullcontext
from pathlib import Path


class ClientError(ValueError):
    """Native client failure, including resources already changed."""
    def __init__(self, message, files=()):
        super().__init__(message)
        self.files = list(files)


def _home(client):
    homes = {
        'codex': ('CODEX_HOME', '.codex'),
        'claude': ('CLAUDE_CONFIG_DIR', '.claude'),
        'cursor': ('CURSOR_CONFIG_DIR', '.cursor'),
        'kiro': ('KIRO_HOME', '.kiro'),
    }
    if client not in homes:
        raise ClientError('Client must be claude/codex/cursor/kiro')
    variable, default = homes[client]
    return Path(os.environ.get(variable, str(Path.home() / default))).expanduser().resolve()


def _read_json(path):
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (ValueError, OSError) as exc:
        raise ClientError(f'Cannot read native metadata {path}: {exc}') from exc


def _config(path):
    if not path.exists():
        return {}
    try:
        return tomllib.loads(path.read_text(encoding='utf-8'))
    except (ValueError, OSError) as exc:
        raise ClientError(f'Cannot read native configuration {path}: {exc}') from exc


def _executable(name):
    """Windows ships the clients as .cmd shims, so a bare name never resolves."""
    resolved = shutil.which(name)
    if not resolved:
        raise ClientError(f'{name} CLI is not on PATH.')
    return resolved


def _run(args, project, *, json_output=True):
    name, *rest = args
    try:
        result = subprocess.run([_executable(name), *rest], cwd=project, stdin=subprocess.DEVNULL,
                                capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=180)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ClientError(f'{name} native command failed: {exc}') from exc
    if result.returncode:
        raise ClientError(f'{" ".join(args[:3])} failed: {(result.stderr or result.stdout).strip()}')
    if not json_output:
        return result.stdout
    try:
        return json.loads(result.stdout)
    except ValueError as exc:
        raise ClientError(f'{name} returned invalid JSON: {result.stdout[:300]}') from exc


def _rpc(method, params, project, *, home=None, staged_config=None):
    """Portable, bounded JSON-RPC exchange; stdout reader works on Windows too."""
    env = os.environ.copy()
    if home is not None:
        env['CODEX_HOME'] = str(home)
    try:
        process = subprocess.Popen([_executable('codex'), 'app-server'], cwd=project, env=env,
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.DEVNULL, text=True, encoding='utf-8')
    except OSError as exc:
        raise ClientError(f'Cannot start Codex app-server: {exc}') from exc
    responses = queue.Queue()

    def read():
        try:
            for line in process.stdout:
                responses.put(line)
        finally:
            responses.put(None)

    reader = threading.Thread(target=read, daemon=True)
    reader.start()

    def exchange(identity, name, values):
        process.stdin.write(json.dumps({'id': identity, 'method': name, 'params': values}) + '\n')
        process.stdin.flush()
        deadline = time.monotonic() + 30
        while True:
            try:
                line = responses.get(timeout=max(0, deadline - time.monotonic()))
            except queue.Empty as exc:
                raise ClientError(f'Codex {name} timed out') from exc
            if line is None:
                raise ClientError(f'Codex exited before answering {name}')
            try:
                value = json.loads(line)
            except ValueError as exc:
                raise ClientError('Codex app-server returned invalid JSON') from exc
            if value.get('id') != identity:
                continue
            if 'error' in value:
                raise ClientError(f'Codex {name}: {json.dumps(value["error"])}')
            return value['result']

    try:
        exchange(1, 'initialize', {'clientInfo': {'name': 'tao-installer', 'version': '0.1'},
                                   'capabilities': {'experimentalApi': True}})
        process.stdin.write(json.dumps({'method': 'initialized'}) + '\n')
        process.stdin.flush()
        # Keep the copied input out of Codex's startup config load. On Windows,
        # that load can hold the file while batchWrite replaces it atomically.
        if staged_config is not None:
            (Path(home) / 'config.toml').write_bytes(staged_config)
        return exchange(2, method, params)
    except (BrokenPipeError, OSError) as exc:
        raise ClientError(f'Codex app-server communication failed: {exc}') from exc
    finally:
        if process.poll() is None:
            process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        reader.join(timeout=1)
        process.stdin.close()
        process.stdout.close()


def _key(*parts):
    return '.'.join(part if part and all(c.isascii() and (c.isalnum() or c in '_-') for c in part) else json.dumps(part, ensure_ascii=False) for part in parts)


def _write_config(path, values):
    """Native lossless TOML editing, with optimistic protection of the input."""
    path = Path(path)
    if path.is_symlink() or path.parent.is_symlink():
        raise ClientError(f'Refusing to replace symlinked client configuration: {path}')
    original = path.read_bytes() if path.exists() else None
    with tempfile.TemporaryDirectory(prefix='tao-config-') as temporary:
        scratch = Path(temporary).resolve()
        target = scratch / 'config.toml'
        _rpc('config/batchWrite', {'filePath': str(target), 'edits': [
            {'keyPath': key, 'value': value, 'mergeStrategy': 'replace'} for key, value in values
        ]}, scratch, home=scratch, staged_config=original)
        updated = target.read_bytes()
    if (path.read_bytes() if path.exists() else None) != original:
        raise ClientError(f'Client configuration changed concurrently; retry: {path}')
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix='.tao-config-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(updated)
        if original is not None:
            os.chmod(temporary, path.stat().st_mode & 0o777)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def validate_scope(client, scope, project):
    if client not in ('claude', 'codex', 'cursor', 'kiro') or scope not in ('user', 'project', 'local'):
        raise ClientError('Client must be claude/codex/cursor/kiro and scope user/project/local')
    project = Path(project).expanduser().resolve()
    if not project.is_dir():
        raise ClientError(f'Project directory does not exist: {project}')
    # Codex, Cursor, and Kiro have repository/user scopes only. Claude-style
    # local spelling is a compatibility alias that maps to project.
    return 'project' if client in ('codex', 'cursor', 'kiro') and scope == 'local' else scope


def _valid_id(plugin_id):
    if not isinstance(plugin_id, str) or plugin_id.split('@', 1)[0] != 'tao-dev' or '@' not in plugin_id:
        raise ClientError('Only the exact tao-dev plugin name with a marketplace is supported')
    marketplace = plugin_id.split('@', 1)[1]
    if not marketplace or any(c in marketplace for c in '/\\\x00\r\n') or marketplace in ('.', '..'):
        raise ClientError('Invalid tao-dev marketplace identity')
    return marketplace


def _command_line(argv, *, windows=None):
    """Serialize argv for the shell used by a Codex command hook."""
    values = [str(value) for value in argv]
    windows = os.name == 'nt' if windows is None else windows
    return subprocess.list2cmdline(values) if windows else shlex.join(values)


def _hook_relative(client):
    return {
        'claude': Path('hooks/hooks.json'),
        'codex': Path('com.openai/hooks/hooks.json'),
        'cursor': Path('com.cursor/hooks/hooks.json'),
    }[client]


def _bind_hook(client, plugin, python):
    """Replace the portable hook command with this installation's exact paths."""
    plugin = Path(plugin).resolve()
    python = Path(python).resolve()
    script = plugin / 'skills/tao-dev/scripts/hook.py'
    path = plugin / _hook_relative(client)
    if (client not in ('claude', 'codex', 'cursor') or path.is_symlink() or script.is_symlink()
            or not path.is_file() or not script.is_file()
            or not path.resolve().is_relative_to(plugin)):
        raise ClientError('Cannot bind an invalid tao-dev hook installation')
    definition = _read_json(path)
    if client == 'cursor':
        try:
            handlers = definition['hooks']['postToolUse']
            handler = handlers[0]
        except (KeyError, IndexError, TypeError) as exc:
            raise ClientError('Cannot bind an invalid tao-dev hook definition') from exc
        if (set(definition) != {'version', 'hooks'} or definition.get('version') != 1
                or set(definition.get('hooks', {})) != {'postToolUse'}
                or len(handlers) != 1 or set(handler) != {'command', 'matcher', 'timeout'}
                or handler.get('matcher') != 'Write' or handler.get('timeout') != 35):
            raise ClientError('Cannot bind an unexpected tao-dev hook definition')
        portable = 'python3 -I -B "${CURSOR_PLUGIN_ROOT}/skills/tao-dev/scripts/hook.py"'
        bound = _command_line([python, '-I', '-B', script])
        if handler.get('command') not in (portable, bound):
            raise ClientError('Cannot bind an unexpected tao-dev hook command')
        handler['command'] = bound
    else:
        try:
            groups = definition['hooks']['PostToolUse']
            group = groups[0]
            handlers = group['hooks']
            handler = handlers[0]
        except (KeyError, IndexError, TypeError) as exc:
            raise ClientError('Cannot bind an invalid tao-dev hook definition') from exc
        handler_keys = {'type', 'command', 'args', 'timeout'} if client == 'claude' else {
            'type', 'command', 'timeout'}
        if (set(definition) != {'hooks'} or set(definition.get('hooks', {})) != {'PostToolUse'}
                or len(groups) != 1 or set(group) != {'matcher', 'hooks'}
                or group.get('matcher') != ('Write|Edit' if client == 'claude' else 'Write|Edit|apply_patch')
                or len(handlers) != 1 or set(handler) != handler_keys
                or handler.get('type') != 'command' or handler.get('timeout') != 35):
            raise ClientError('Cannot bind an unexpected tao-dev hook definition')
        if client == 'claude':
            portable = ('python3', ['-I', '-B', '${CLAUDE_PLUGIN_ROOT}/skills/tao-dev/scripts/hook.py'])
            bound = (str(python), ['-I', '-B', str(script)])
            if (handler.get('command'), handler.get('args')) not in (portable, bound):
                raise ClientError('Cannot bind an unexpected tao-dev hook command')
            handler['command'], handler['args'] = bound
        else:
            portable = 'python3 -I -B "${PLUGIN_ROOT}/skills/tao-dev/scripts/hook.py"'
            bound = _command_line([python, '-I', '-B', script])
            if handler.get('command') not in (portable, bound) or 'args' in handler or 'commandWindows' in handler:
                raise ClientError('Cannot bind an unexpected tao-dev hook command')
            handler['command'] = bound
    original = path.read_bytes()
    updated = (json.dumps(definition, indent=2) + '\n').encode()
    if path.read_bytes() != original:
        raise ClientError(f'Hook definition changed concurrently; retry: {path}')
    descriptor, temporary = tempfile.mkstemp(prefix='.tao-hook-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(updated)
        os.chmod(temporary, path.stat().st_mode & 0o777)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return path


def _tree_digest(path):
    digest = hashlib.sha256()
    path = Path(path)
    if path.is_file():
        return hashlib.sha256(path.read_bytes()).hexdigest()
    for child in sorted(path.rglob('*')):
        if child.is_symlink():
            raise ClientError(f'Refusing symlinked Kiro activation content: {child}')
        if child.is_file() and child.name != '.tao-owned.json':
            digest.update(child.relative_to(path).as_posix().encode() + b'\0' + child.read_bytes())
    return digest.hexdigest()


def _kiro_paths(home, project, scope):
    boundary = home if scope == 'user' else project
    root = home if scope == 'user' else project / '.kiro'
    root = root.absolute()
    if not root.is_relative_to(boundary.absolute()):
        raise ClientError('Kiro activation escapes its scope root')
    if scope == 'project' and root == home.absolute():
        raise ClientError('KIRO_HOME overlaps this project .kiro directory; user and project scopes would collide')
    skill, hook = root / 'skills/tao-dev', root / 'hooks/tao-dev.json'
    for path in (root, root / 'skills', skill, root / 'hooks', hook):
        if path.is_symlink():
            raise ClientError(f'Refusing symlinked Kiro activation path: {path}')
    return skill, hook


def _kiro_plugin_from_marketplace(source):
    source = Path(source).resolve()
    catalog = source / '.claude-plugin/marketplace.json'
    if not catalog.is_file():
        raise ClientError('Kiro source has no tao-dev marketplace catalog')
    data = _read_json(catalog)
    entries = [entry for entry in data.get('plugins', []) if entry.get('name') == 'tao-dev']
    if len(entries) != 1 or not isinstance(entries[0].get('source'), str):
        raise ClientError('Kiro marketplace must identify exactly one tao-dev plugin')
    plugin = (source / entries[0]['source']).resolve()
    if not plugin.is_relative_to(source) or not (plugin / 'skills/tao-dev/SKILL.md').is_file():
        raise ClientError('Kiro marketplace plugin must stay inside its source and contain tao-dev skill')
    return plugin


def _kiro_cache_base(home, plugin_id):
    marketplace = _valid_id(plugin_id)
    base = home / 'plugins/cache' / marketplace / 'tao-dev'
    for path in (home / 'plugins', home / 'plugins/cache', home / 'plugins/cache' / marketplace, base):
        if path.is_symlink():
            raise ClientError(f'Refusing symlinked Kiro plugin cache path: {path}')
    return base


def _materialize_kiro_plugin(source, plugin_id, home, *, ref=None):
    temporary = None
    try:
        source_path = Path(source)
        if source_path.is_dir():
            plugin_src = _kiro_plugin_from_marketplace(source_path)
        else:
            temporary = Path(tempfile.mkdtemp(prefix='.tao-kiro-src-'))
            argv = ['git', 'clone', '--depth', '1']
            if ref:
                argv += ['--branch=' + ref]
            argv += ['--', source, str(temporary / 'repository')]
            completed = subprocess.run(argv, capture_output=True, text=True, encoding='utf-8',
                                       errors='replace', check=False)
            if completed.returncode:
                raise ClientError(f'git clone failed: {(completed.stderr or completed.stdout).strip()}')
            plugin_src = _kiro_plugin_from_marketplace(temporary / 'repository')
        manifest = _read_json(plugin_src / '.claude-plugin/plugin.json')
        if manifest.get('name') != 'tao-dev':
            raise ClientError('Kiro source has an invalid tao-dev manifest')
        version = manifest.get('version', '0.0.0')
        if not isinstance(version, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._+-]{0,127}', version):
            raise ClientError('Kiro plugin version must be a safe single path segment')
        base = _kiro_cache_base(home, plugin_id)
        base.mkdir(parents=True, exist_ok=True)
        destination = base / version
        if destination.resolve().parent != base.resolve():
            raise ClientError('Kiro plugin cache path escapes its owner')
        owner = destination / '.tao-owned.json'
        if destination.exists():
            if (destination.is_symlink() or owner.is_symlink() or not owner.is_file()
                    or _read_json(owner).get('component') != 'kiro-cache'
                    or _read_json(owner).get('plugin_id') != plugin_id):
                raise ClientError(f'Refusing to replace unmanaged Kiro plugin cache: {destination}')
            shutil.rmtree(destination)
        stage = Path(tempfile.mkdtemp(prefix='.tao-kiro-cache-', dir=base))
        try:
            shutil.copytree(plugin_src, stage / 'plugin', ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.git'))
            (stage / 'plugin/.tao-owned.json').write_text(json.dumps({
                'schema': 1, 'component': 'kiro-cache', 'plugin_id': plugin_id}) + '\n', encoding='utf-8')
            (stage / 'plugin').rename(destination)
        finally:
            shutil.rmtree(stage, ignore_errors=True)
        return destination, version
    finally:
        if temporary is not None:
            shutil.rmtree(temporary, ignore_errors=True)


def _kiro_git_info(project):
    completed = subprocess.run(['git', '-C', str(project), 'rev-parse', '--show-toplevel', '--git-path', 'info/exclude'],
                               capture_output=True, text=True, encoding='utf-8', errors='replace', check=False)
    lines = completed.stdout.splitlines()
    if completed.returncode or len(lines) != 2:
        return None, None
    root, exclude = Path(lines[0]).resolve(), Path(lines[1])
    if not exclude.is_absolute():
        exclude = (project / exclude).resolve()
    return root, exclude


def _kiro_private_exclude(project, paths):
    root, exclude = _kiro_git_info(project)
    if root is None:
        return None
    entries = []
    for path in paths:
        try:
            relative = path.resolve().relative_to(root).as_posix()
        except ValueError:
            continue
        tracked = subprocess.run(['git', '-C', str(root), 'ls-files', '--error-unmatch', '--', relative],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        if tracked.returncode == 0:
            raise ClientError(f'Refusing to replace tracked Kiro activation: {path}')
        entries.append('/' + relative.rstrip('/') + ('/' if path.suffix == '' else ''))
    current = exclude.read_text(encoding='utf-8') if exclude.exists() else ''
    missing = [entry for entry in entries if entry not in current.splitlines()]
    if missing:
        exclude.parent.mkdir(parents=True, exist_ok=True)
        exclude.write_text(current + ('\n' if current and not current.endswith('\n') else '') + '\n'.join(missing) + '\n',
                           encoding='utf-8', newline='\n')
    return exclude


def _publish_kiro(plugin, plugin_id, version, scope, home, project, python):
    skill, hook = _kiro_paths(home, project, scope)
    marker = skill / '.tao-owned.json'
    if skill.exists() and (skill.is_symlink() or not marker.is_file() or _read_json(marker).get('plugin_id') != plugin_id):
        raise ClientError(f'Refusing to replace unmanaged Kiro skill: {skill}')
    previous = _read_json(marker) if marker.is_file() else {}
    if skill.exists() and previous.get('skill_digest') != _tree_digest(skill):
        raise ClientError(f'Refusing to replace modified Kiro skill: {skill}')
    if hook.exists() and previous.get('hook_digest') != _tree_digest(hook):
        raise ClientError(f'Refusing to replace unmanaged or modified Kiro hook: {hook}')
    exclude = _kiro_private_exclude(project, [skill, hook]) if scope == 'project' else None
    skill.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='.tao-kiro-skill-', dir=skill.parent))
    try:
        shutil.copytree(plugin / 'skills/tao-dev', stage / 'tao-dev',
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        definition = _read_json(plugin / 'com.kiro/hooks/tao-dev.json')
        definition['hooks'][0]['action']['command'] = _command_line([
            Path(python).resolve(), '-I', '-B', skill / 'scripts/hook.py', '--host', 'kiro'])
        hook.parent.mkdir(parents=True, exist_ok=True)
        hook_bytes = (json.dumps(definition, indent=2) + '\n').encode()
        hook_digest = hashlib.sha256(hook_bytes).hexdigest()
        skill_digest = _tree_digest(stage / 'tao-dev')
        (stage / 'tao-dev/.tao-owned.json').write_text(json.dumps({
            'schema': 1, 'id': 'tao-dev', 'plugin_id': plugin_id, 'plugin_path': str(plugin),
            'version': version, 'scope': scope, 'project': None if scope == 'user' else str(project),
            'skill_digest': skill_digest, 'hook_digest': hook_digest}) + '\n', encoding='utf-8', newline='\n')
        backup = skill.with_name('.tao-dev-previous')
        if backup.exists():
            raise ClientError(f'Previous Kiro skill update needs inspection: {backup}')
        if skill.exists():
            skill.rename(backup)
        (stage / 'tao-dev').rename(skill)
        descriptor, temporary = tempfile.mkstemp(prefix='.tao-kiro-hook-', dir=hook.parent)
        try:
            with os.fdopen(descriptor, 'wb') as stream:
                stream.write(hook_bytes)
            os.replace(temporary, hook)
        finally:
            Path(temporary).unlink(missing_ok=True)
        shutil.rmtree(backup, ignore_errors=True)
    finally:
        shutil.rmtree(stage, ignore_errors=True)
    files = [str(skill), str(hook)]
    if exclude is not None:
        files.append(str(exclude))
    return skill, hook, files


def _discover_kiro(home, project):
    result = []
    for scope, target in [('user', None), ('project', project)]:
        try:
            skill, hook = _kiro_paths(home, project, scope)
        except ClientError:
            continue
        marker = skill / '.tao-owned.json'
        if not skill.is_dir() or skill.is_symlink() or not marker.is_file():
            continue
        owned = _read_json(marker)
        plugin = Path(owned.get('plugin_path', ''))
        if owned.get('id') != 'tao-dev' or not plugin.is_absolute() or not plugin.is_dir():
            continue
        result.append(_native_row(owned.get('plugin_id', 'tao-dev@tao-dev'), scope, target, plugin,
                                  owned.get('version', 'unknown'), [str(skill), str(hook)],
                                  enabled=hook.is_file() and owned.get('hook_digest') == _tree_digest(hook)))
    return result


def _native_row(plugin_id, scope, project, plugin, version, files, *, enabled=True):
    return {'native': True, 'id': plugin_id, 'plugin_id': plugin_id, 'scope': scope,
            'project': str(project) if project is not None else None,
            'plugin_path': str(plugin), 'version': version, 'files': list(dict.fromkeys(files)), 'enabled': enabled}


def discover(client, project):
    project = Path(project).expanduser().resolve()
    if client not in ('claude', 'codex', 'cursor', 'kiro'):
        raise ClientError('Client must be claude/codex/cursor/kiro')
    home = _home(client)
    if client == 'kiro':
        return _discover_kiro(home, project)
    if client == 'cursor':
        return _discover_cursor(home, project)
    if client == 'claude':
        registry = home / 'plugins/installed_plugins.json'
        result = []
        for plugin_id, entries in _read_json(registry).get('plugins', {}).items():
            if plugin_id.split('@', 1)[0] != 'tao-dev':
                continue
            for entry in entries:
                scope = entry.get('scope')
                if scope not in ('user', 'project', 'local') or not entry.get('installPath'):
                    continue
                target = Path(entry['projectPath']).resolve() if entry.get('projectPath') and scope != 'user' else None
                if scope != 'user' and target is None:
                    continue
                config = home / 'settings.json' if scope == 'user' else target / ('.claude/settings.local.json' if scope == 'local' else '.claude/settings.json')
                plugin = Path(entry['installPath']).resolve()
                result.append(_native_row(plugin_id, scope, target, plugin, entry.get('version'), [str(config), str(registry), str(plugin.parent)]))
        return result
    user_config = home / 'config.toml'
    user = _config(user_config)
    configs = [(None, user_config, user)]
    projects = {project}
    for location, data in user.get('projects', {}).items():
        if isinstance(data, dict) and data.get('trust_level') == 'trusted' and Path(location).is_absolute():
            projects.add(Path(location).resolve())
    for target in sorted(projects):
        config = target / '.codex/config.toml'
        if config.exists():
            configs.append((target, config, _config(config)))
    project_ids = {plugin_id for target, _, data in configs if target is not None
                   for plugin_id in data.get('plugins', {})}
    result = []
    for target, config, data in configs:
        for plugin_id, settings in data.get('plugins', {}).items():
            if plugin_id.split('@', 1)[0] != 'tao-dev' or not isinstance(settings, dict):
                continue
            enabled = settings.get('enabled', True)
            if not isinstance(enabled, bool):
                continue
            # Native add writes a user key even for a project installation.
            # Suppress that disabled boundary key while project entries exist.
            if target is None and not enabled and plugin_id in project_ids:
                continue
            marketplace = _valid_id(plugin_id)
            base = home / 'plugins/cache' / marketplace / 'tao-dev'
            candidates = []
            if base.is_dir() and not base.is_symlink():
                for candidate in base.iterdir():
                    manifest = next((candidate / name for name in ('.codex-plugin/plugin.json', 'plugin.json', '.claude-plugin/plugin.json')
                                     if (candidate / name).is_file()), candidate / '.codex-plugin/plugin.json')
                    if (candidate.is_dir() and not candidate.is_symlink() and manifest.is_file()
                            and candidate.resolve().is_relative_to(base.absolute())):
                        metadata = _read_json(manifest)
                        if metadata.get('name') == 'tao-dev':
                            candidates.append((candidate.stat().st_mtime_ns, candidate, metadata.get('version', candidate.name)))
            if not candidates:
                continue
            _, plugin, version = max(candidates, key=lambda row: (row[0], str(row[1])))
            result.append(_native_row(plugin_id, 'user' if target is None else 'project', target,
                                      plugin.resolve(), version, [str(config), str(base)], enabled=enabled))
    return result


def _cursor_plugin_key(plugin_id):
    return f'{_valid_id(plugin_id)}/tao-dev'


def _cursor_manifest(plugin):
    path = plugin / '.cursor-plugin/plugin.json'
    if not path.is_file():
        raise ClientError(f'Cursor plugin is missing .cursor-plugin/plugin.json: {plugin}')
    data = _read_json(path)
    if data.get('name') != 'tao-dev':
        raise ClientError(f'Cursor plugin name must be tao-dev: {plugin}')
    return data


def _cursor_plugin_from_marketplace(source):
    source = Path(source).resolve()
    catalog = source / '.cursor-plugin/marketplace.json'
    if not catalog.is_file():
        catalog = source / '.claude-plugin/marketplace.json'
    if not catalog.is_file():
        raise ClientError('Cursor marketplace has no .cursor-plugin/marketplace.json catalog')
    data = _read_json(catalog)
    entries = [entry for entry in data.get('plugins', []) if entry.get('name') == 'tao-dev']
    if len(entries) != 1:
        raise ClientError('Cursor marketplace must identify exactly one tao-dev plugin')
    entry = entries[0].get('source')
    if isinstance(entry, dict):
        entry = entry.get('path')
    if not isinstance(entry, str):
        raise ClientError('Invalid Cursor marketplace plugin source')
    plugin = (source / entry).resolve()
    if not plugin.is_relative_to(source):
        raise ClientError('Cursor marketplace plugin must stay inside its source directory')
    _cursor_manifest(plugin)
    return plugin, data.get('name') or 'tao-dev'


def _publish_cursor_local(home, plugin, plugin_id):
    """User-scope activation: Cursor discovers ~/.cursor/plugins/local/<name>."""
    local_root = home / 'plugins/local'
    local_root.mkdir(parents=True, exist_ok=True)
    destination = local_root / 'tao-dev'
    marker = destination / '.tao-owned.json'
    if destination.exists():
        if destination.is_symlink() or not marker.is_file() or _read_json(marker).get('id') != 'tao-dev':
            raise ClientError(f'Refusing to replace unmanaged Cursor local plugin: {destination}')
    stage = Path(tempfile.mkdtemp(prefix='.tao-cursor-local-', dir=local_root))
    try:
        shutil.copytree(plugin, stage / 'tao-dev', ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.git'))
        (stage / 'tao-dev' / '.tao-owned.json').write_text(
            json.dumps({'schema': 1, 'id': 'tao-dev', 'plugin_id': plugin_id}) + '\n',
            encoding='utf-8', newline='\n')
        backup = local_root / '.tao-dev-previous'
        if backup.exists():
            raise ClientError(f'Previous Cursor local plugin update needs inspection: {backup}')
        if destination.exists():
            destination.rename(backup)
        (stage / 'tao-dev').rename(destination)
        if backup.exists():
            shutil.rmtree(backup)
    finally:
        shutil.rmtree(stage, ignore_errors=True)
    return destination


def _enable_cursor_project(project, plugin_id, *, git_url=None, git_ref=None):
    settings = project / '.cursor/settings.json'
    settings.parent.mkdir(parents=True, exist_ok=True)
    data = _read_json(settings) if settings.exists() else {}
    if settings.exists() and (not isinstance(data, dict) or (
            'plugins' in data and not isinstance(data.get('plugins'), dict))):
        raise ClientError(f'Cannot update Cursor project settings: {settings}')
    plugins = data.setdefault('plugins', {})
    entry = {'enabled': True}
    if git_url:
        entry['gitUrl'] = git_url
        if git_ref:
            entry['gitRef'] = git_ref
    plugins[_cursor_plugin_key(plugin_id)] = entry
    _write_json(settings, data)
    return settings


def _materialize_cursor_plugin(marketplace_source, plugin_id, home, *, ref=None):
    marketplace = _valid_id(plugin_id)
    source = Path(marketplace_source)
    temporary = None
    try:
        if source.is_dir():
            plugin_src, _ = _cursor_plugin_from_marketplace(source)
        else:
            temporary = Path(tempfile.mkdtemp(prefix='.tao-cursor-src-'))
            argv = ['git', 'clone', '--depth', '1']
            if ref:
                argv += ['--branch=' + ref]
            argv += ['--', marketplace_source, str(temporary / 'repository')]
            completed = subprocess.run(argv, capture_output=True, text=True, encoding='utf-8',
                                       errors='replace', check=False)
            if completed.returncode:
                raise ClientError(f'git clone failed: {(completed.stderr or completed.stdout).strip()}')
            plugin_src, _ = _cursor_plugin_from_marketplace(temporary / 'repository')
        version = _cursor_manifest(plugin_src).get('version', '0.0.0')
        base = home / 'plugins/cache' / marketplace / 'tao-dev'
        base.mkdir(parents=True, exist_ok=True)
        destination = base / version
        if destination.exists():
            if destination.is_symlink() or not (destination / '.cursor-plugin/plugin.json').is_file():
                raise ClientError(f'Refusing to replace unmanaged Cursor plugin cache: {destination}')
            shutil.rmtree(destination)
        stage = Path(tempfile.mkdtemp(prefix='.tao-cursor-cache-', dir=base))
        try:
            shutil.copytree(plugin_src, stage / 'plugin',
                            ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.git'))
            (stage / 'plugin').rename(destination)
        finally:
            shutil.rmtree(stage, ignore_errors=True)
        return destination, version
    finally:
        if temporary is not None:
            shutil.rmtree(temporary, ignore_errors=True)


def _discover_cursor(home, project):
    result = []
    local = home / 'plugins/local/tao-dev'
    marker = local / '.tao-owned.json'
    if local.is_dir() and not local.is_symlink() and marker.is_file():
        ownership = _read_json(marker)
        if ownership.get('id') == 'tao-dev':
            plugin_id = ownership.get('plugin_id') or 'tao-dev@tao-dev'
            try:
                version = _cursor_manifest(local).get('version', local.name)
            except ClientError:
                version = local.name
            result.append(_native_row(plugin_id, 'user', None, local, version,
                                      [str(local), str(marker)]))
    settings = project / '.cursor/settings.json'
    if settings.is_file():
        for key, entry in _read_json(settings).get('plugins', {}).items():
            if not isinstance(entry, dict) or entry.get('enabled') is not True:
                continue
            name = key.split('/', 1)[-1]
            marketplace = key.split('/', 1)[0] if '/' in key else 'tao-dev'
            if name != 'tao-dev':
                continue
            plugin_id = f'tao-dev@{marketplace}'
            base = home / 'plugins/cache' / marketplace / 'tao-dev'
            plugin = None
            version = 'unknown'
            if base.is_dir() and not base.is_symlink():
                candidates = [path for path in base.iterdir()
                              if path.is_dir() and not path.is_symlink()
                              and (path / '.cursor-plugin/plugin.json').is_file()]
                if candidates:
                    plugin = max(candidates, key=lambda path: path.stat().st_mtime_ns)
                    version = _cursor_manifest(plugin).get('version', plugin.name)
            if plugin is None:
                continue
            result.append(_native_row(plugin_id, 'project', project, plugin, version,
                                      [str(settings), str(plugin.parent)]))
    return result


def _runs_owned_script(command, script, python):
    """Accept the installed command whatever path spelling the client reports."""
    if python is not None:
        return command == _command_line([python, '-I', '-B', script])
    prefix = 'python3 -I -B "'
    if not isinstance(command, str) or not command.startswith(prefix) or not command.endswith('"'):
        return False
    # Codex substitutes ${PLUGIN_ROOT} in place, so a Windows installation keeps
    # the portable tail's separators inside an otherwise native path. Compare the
    # path itself, but lexically: a link to the script is not the owned script.
    return Path(command[len(prefix):-1]) == script


def _trust_hook(project, plugin_id, plugin, python=None):
    rows = _rpc('hooks/list', {'cwds': [str(project)]}, project).get('data', [])
    hooks = [hook for row in rows for hook in row.get('hooks', []) if hook.get('pluginId') == plugin_id]
    if any(row.get('errors') for row in rows) or len(hooks) != 1:
        raise ClientError('Cannot verify the exact installed tao-dev hook inventory')
    hook = hooks[0]
    script = plugin / 'skills/tao-dev/scripts/hook.py'
    checks = {
        'source': Path(hook.get('sourcePath', '')).resolve().is_relative_to(plugin.resolve()),
        'script': script.is_file() and script.resolve().is_relative_to(plugin.resolve()),
        'command': _runs_owned_script(hook.get('command'), script, python),
        'event': hook.get('eventName') == 'postToolUse',
        'handler': hook.get('handlerType') == 'command',
        'matcher': hook.get('matcher') == 'Write|Edit|apply_patch',
        'timeout': hook.get('timeoutSec') == 35,
        'ownership': bool(hook.get('enabled')) and not hook.get('isManaged'),
        'hash': bool(hook.get('currentHash')),
        'key': str(hook.get('key', '')).startswith(plugin_id + ':'),
    }
    differing = [name for name, holds in checks.items() if not holds]
    if differing:
        raise ClientError('Installed tao-dev hook differs from the expected owned hook; '
                          f'trust was not changed: {", ".join(differing)}')
    path = _home('codex') / 'config.toml'
    _write_config(path, [(_key('hooks', 'state', hook['key'], 'trusted_hash'), hook['currentHash'])])
    after = _rpc('hooks/list', {'cwds': [str(project)]}, project).get('data', [])
    if not any(item.get('key') == hook['key'] and item.get('trustStatus') == 'trusted'
               for row in after for item in row.get('hooks', [])):
        raise ClientError('Codex did not recognize the installed hook trust', [str(path)])
    return [str(path)]


def _verify_skills(project, plugin_id, plugin):
    rows = _rpc('skills/list', {'cwds': [str(project)], 'forceReload': True}, project).get('data', [])
    skills = [skill for row in rows for skill in row.get('skills', [])
              if skill.get('pluginId') == plugin_id and skill.get('enabled') is True]
    if any(row.get('errors') for row in rows) or not skills or any(
            not Path(skill.get('path', '')).resolve().is_relative_to(plugin) for skill in skills):
        raise ClientError('Codex does not report enabled skills from the installed tao-dev cache')
    return {'native_skills_enabled': True, 'method': 'skills/list', 'skill_count': len(skills)}


def _source_identity(value):
    for prefix in ('https://github.com/', 'http://github.com/', 'git@github.com:'):
        if value.startswith(prefix):
            value = value[len(prefix):]
            break
    return value.rstrip('/').removesuffix('.git')


def _same_directory(configured, source):
    """Compare local sources by identity rather than by spelling.

    A client records the path in its own canonical form. Windows
    canonicalization returns the extended-length form, which pathlib reads as
    another drive, so no string comparison recognizes the directory just
    registered.
    """
    if not str(configured).strip():
        return False
    left, right = Path(configured).expanduser(), Path(source).expanduser()
    try:
        return left.samefile(right)
    except OSError:
        return left.resolve() == right.resolve()


def _check_codex_source(catalog, source):
    if not catalog:
        return
    configured = catalog.get('source', '')
    if catalog.get('source_type') == 'local':
        matches = _same_directory(configured, source)
    else:
        matches = _source_identity(configured) == _source_identity(source)
    if not matches:
        raise ClientError('The Codex marketplace name is already registered to a different source; '
                          'use a distinct marketplace name or update the native registration '
                          f'explicitly: registered {configured!r}, requested {source!r}')


def _content_snapshot(path):
    path = Path(path)
    if not path.exists():
        return None
    if path.is_symlink():
        raise ClientError(f'Refusing to snapshot symlinked Kiro activation: {path}')
    if path.is_file():
        return {'type': 'file', 'content': path.read_bytes()}
    if any(child.is_symlink() for child in path.rglob('*')):
        raise ClientError(f'Refusing to snapshot symlinked Kiro activation content: {path}')
    return {'type': 'directory', 'files': {
        child.relative_to(path).as_posix(): child.read_bytes()
        for child in path.rglob('*') if child.is_file()
    }}


def _restore_content(path, saved):
    path = Path(path)
    if path.exists():
        if path.is_symlink():
            raise ClientError(f'Refusing to restore over symlinked Kiro activation: {path}')
        shutil.rmtree(path) if path.is_dir() else path.unlink()
    if saved is None:
        return
    if saved['type'] == 'file':
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(saved['content'])
        return
    path.mkdir(parents=True, exist_ok=True)
    for relative, content in saved['files'].items():
        target = path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)


def _snapshot(path):
    if path.is_file():
        return path.read_bytes()
    if path.is_dir():
        return tuple(sorted((child.name, child.stat().st_mtime_ns) for child in path.iterdir()))
    return None


def _check_claude_source(known, source, ref):
    configured = known.get('source', {})
    kind = configured.get('source')
    if kind in ('directory', 'file'):
        matches = _same_directory(configured.get('path', ''), source)
    else:
        prior = configured.get('repo') or configured.get('url')
        matches = bool(prior) and _source_identity(prior) == _source_identity(source)
    if not matches or (ref is not None and configured.get('ref') != ref):
        raise ClientError('The Claude marketplace name is already registered to a different source/ref; '
                          'use a distinct marketplace name or update the native registration '
                          f'explicitly: registered {configured!r}, requested {source!r}')


def _claude_scope_enabled(rows, plugin_id, scope, project):
    return any(row.get('id') == plugin_id and row.get('scope') == scope and row.get('enabled') is True
               and (scope == 'user' or Path(row.get('projectPath', '')).resolve() == project) for row in rows)


def install_plugin(client, marketplace_source, plugin_id, scope, project, *, ref=None, python=None):
    project = Path(project).expanduser().resolve()
    scope = validate_scope(client, scope, project)
    marketplace = _valid_id(plugin_id)
    home = _home(client)
    watched = [home / 'config.toml', home / 'settings.json',
               home / 'plugins/installed_plugins.json', home / 'plugins/known_marketplaces.json',
               home / 'plugins/cache' / marketplace / 'tao-dev', home / 'plugins/local/tao-dev',
               project / '.codex/config.toml', project / '.claude/settings.json',
               project / '.claude/settings.local.json', project / '.cursor/settings.json']
    if client == 'kiro':
        skill, hook = _kiro_paths(home, project, scope)
        watched.extend([skill, hook])
    before = {path: _snapshot(path) for path in watched}
    files = []
    warnings = []
    try:
        home.mkdir(parents=True, exist_ok=True)
        if client == 'kiro':
            if python is None:
                raise ClientError('Kiro installation requires the validated Python interpreter')
            plugin, version = _materialize_kiro_plugin(marketplace_source, plugin_id, home, ref=ref)
            skill, hook, activation_files = _publish_kiro(
                plugin, plugin_id, version, scope, home, project, python)
            files.extend([str(plugin.parent), *activation_files])
            return {
                'plugin_id': plugin_id, 'plugin_path': str(plugin), 'plugin_base': str(plugin.parent),
                'version': version, 'files': list(dict.fromkeys(files)), 'warnings': warnings,
                'activation': {'schema': 1, 'skill': str(skill), 'hook': str(hook),
                               'skill_digest': _tree_digest(skill), 'hook_digest': _tree_digest(hook),
                               'machine_bound': True},
                'verification': {'native_skills_enabled': True, 'native_hook_installed': True,
                                 'kiro_engine': 'v3', 'method': 'Kiro V3 filesystem discovery'},
            }
        if client == 'cursor':
            plugin, version = _materialize_cursor_plugin(marketplace_source, plugin_id, home, ref=ref)
            files.append(str(plugin.parent))
            git_url = None if Path(marketplace_source).is_dir() else marketplace_source
            if scope == 'user':
                local = _publish_cursor_local(home, plugin, plugin_id)
                if python is not None:
                    _bind_hook(client, local, python)
                files.extend([str(local), str(local / '.tao-owned.json')])
                plugin = local
            else:
                if python is not None:
                    _bind_hook(client, plugin, python)
                settings = _enable_cursor_project(project, plugin_id, git_url=git_url, git_ref=ref)
                files.append(str(settings))
            verification = {
                'native_plugin_enabled': True,
                'method': ('~/.cursor/plugins/local/tao-dev' if scope == 'user'
                           else '.cursor/settings.json plugins entry'),
                'cursor_reload_required': True,
            }
            return {'plugin_id': plugin_id, 'plugin_path': str(plugin), 'plugin_base': str(plugin.parent),
                    'version': version, 'files': list(dict.fromkeys(files)), 'warnings': warnings,
                    'verification': verification}
        if client == 'claude':
            prior = discover(client, project)
            known = _read_json(home / 'plugins/known_marketplaces.json')
            if marketplace not in known:
                source = marketplace_source + ('#' + ref if ref else '')
                _run(['claude', 'plugin', 'marketplace', 'add', source, '--scope', scope], project, json_output=False)
            else:
                _check_claude_source(known[marketplace], marketplace_source, ref)
                _run(['claude', 'plugin', 'marketplace', 'update', marketplace], project, json_output=False)
            settings = home / 'settings.json' if scope == 'user' else project / ('.claude/settings.local.json' if scope == 'local' else '.claude/settings.json')
            files.extend([str(settings), str(home / 'plugins/known_marketplaces.json')])
            exists = any(row['plugin_id'] == plugin_id and row['scope'] == scope and row['project'] == (None if scope == 'user' else str(project)) for row in prior)
            _run(['claude', 'plugin', 'update' if exists else 'install', plugin_id, '--scope', scope], project, json_output=False)
            if exists:
                native = _run(['claude', 'plugin', 'list', '--json'], project)
                if not _claude_scope_enabled(native, plugin_id, scope, project):
                    _run(['claude', 'plugin', 'enable', plugin_id, '--scope', scope], project, json_output=False)
            entries = [row for row in discover(client, project) if row['plugin_id'] == plugin_id and row['scope'] == scope and row['project'] == (None if scope == 'user' else str(project))]
            if not entries:
                raise ClientError('Claude did not report the installed tao-dev scope')
            entry = entries[0]
            plugin = Path(entry['plugin_path'])
            version = entry['version']
            files.extend(entry['files'])
            expected_base = home / 'plugins/cache' / marketplace / 'tao-dev'
            if not plugin.is_relative_to(expected_base) or plugin == expected_base:
                raise ClientError(f'Claude installed tao-dev outside its expected native cache: {plugin}')
            if python is not None:
                _bind_hook(client, plugin, python)
            native = _run(['claude', 'plugin', 'list', '--json'], project)
            if not _claude_scope_enabled(native, plugin_id, scope, project):
                raise ClientError('Claude does not report the requested native scope as enabled')
            inventory = _run(['claude', 'plugin', 'details', plugin_id], project, json_output=False)
            if 'Skills (' not in inventory or 'Hooks (' not in inventory:
                raise ClientError('Claude did not report the installed tao-dev skills and hooks')
            verification = {'native_plugin_enabled': True, 'native_component_inventory': inventory.strip(),
                            'method': 'claude plugin list --json; claude plugin details'}
        else:
            user_path = home / 'config.toml'
            prior = _config(user_path)
            prior_user = prior.get('plugins', {}).get(plugin_id, {}).get('enabled') is True
            _check_codex_source(prior.get('marketplaces', {}).get(marketplace), marketplace_source)
            added = _run(['codex', 'plugin', 'marketplace', 'add', marketplace_source,
                          *(['--ref', ref] if ref else []), '--json'], project)
            if added.get('marketplaceName', marketplace) != marketplace:
                raise ClientError('Source marketplace name does not match the requested tao-dev identity')
            files.append(str(user_path))
            catalog = _config(user_path).get('marketplaces', {}).get(marketplace)
            # add refreshes local catalogs; upgrade refreshes a Git checkout.
            if catalog and catalog.get('source_type') == 'git':
                _run(['codex', 'plugin', 'marketplace', 'upgrade', marketplace, '--json'], project)
            _write_config(user_path, [(_key('projects', str(project), 'trust_level'), 'trusted')])
            activation = user_path if scope == 'user' else project / '.codex/config.toml'
            if scope != 'user' and catalog:
                _write_config(activation, [(_key('marketplaces', marketplace), catalog)])
                files.append(str(activation))
            try:
                installed = _run(['codex', 'plugin', 'add', plugin_id, '--json'], project)
                if installed.get('installedPath'):
                    plugin = Path(installed['installedPath']).resolve()
            finally:
                # Native add may partially succeed before returning a failure.
                # Restore the user boundary on both success and failure.
                _write_config(user_path, [(_key('plugins', plugin_id, 'enabled'), scope == 'user' or prior_user)])
            if not installed.get('installedPath'):
                raise ClientError('Codex did not return an installed plugin path')
            plugin = Path(installed['installedPath']).resolve()
            expected_base = home / 'plugins/cache' / marketplace / 'tao-dev'
            if not plugin.is_relative_to(expected_base) or plugin == expected_base:
                raise ClientError(f'Codex installed tao-dev outside its expected native cache: {plugin}')
            files.append(str(plugin.parent))
            version = _read_json(plugin / '.codex-plugin/plugin.json').get('version', plugin.name)
            if python is not None:
                _bind_hook(client, plugin, python)
            edits = [(_key('plugins', plugin_id, 'enabled'), True), ('features.hooks', True)]
            _write_config(activation, edits)
            files.append(str(activation))
            files.extend(_trust_hook(project, plugin_id, plugin, python))
            verification = _verify_skills(project, plugin_id, plugin)
            verification['native_hook_trusted'] = True
        return {'plugin_id': plugin_id, 'plugin_path': str(plugin), 'plugin_base': str(plugin.parent),
                'version': version, 'files': list(dict.fromkeys(files)), 'warnings': warnings,
                'verification': verification}
    except (ValueError, OSError) as exc:
        for path in watched:
            try:
                if _snapshot(path) != before[path]:
                    files.append(str(path))
            except OSError:
                pass  # Preserve the original actionable failure.
        failure = ClientError(str(exc), list(dict.fromkeys(files + getattr(exc, 'files', []))))
        if 'plugin' in locals():
            failure.plugin_path = str(plugin)
        raise failure from exc


def remove_activation(client, plugin_id, scope, project, *, keep_plugin=False, keep_activation=False,
                      activation=None):
    project = Path(project).expanduser().resolve()
    if client not in ('claude', 'codex', 'cursor', 'kiro') or scope not in ('user', 'project', 'local'):
        raise ClientError('Client must be claude/codex/cursor/kiro and scope user/project/local')
    scope = 'project' if client in ('codex', 'cursor', 'kiro') and scope == 'local' else scope
    _valid_id(plugin_id)
    if keep_activation:
        return {'files': [], 'warnings': ['Shared activation is still used by another installation.']}
    home = _home(client)
    rows = discover(client, project)
    selected_project = None if scope == 'user' else str(project)
    selected = [row for row in rows if row['plugin_id'] == plugin_id and row['project'] == selected_project
                and (row['scope'] == scope or client in ('codex', 'cursor', 'kiro'))]
    others = [row for row in rows if row['plugin_id'] == plugin_id and
              not (row['project'] == selected_project and (row['scope'] == scope or client in ('codex', 'cursor', 'kiro')))]
    watched = [home / 'config.toml', home / 'settings.json', home / 'plugins/installed_plugins.json',
               home / 'plugins/cache' / _valid_id(plugin_id) / 'tao-dev', home / 'plugins/local/tao-dev',
               project / '.codex/config.toml', project / '.claude/settings.json',
               project / '.claude/settings.local.json', project / '.cursor/settings.json']
    before = {path: _snapshot(path) for path in watched}
    files = []
    warnings = []
    if client == 'kiro':
        _kiro_cache_base(home, plugin_id)
    for row in rows:
        if row['plugin_id'] == plugin_id and row['project'] == selected_project:
            base = home / 'plugins/cache' / _valid_id(plugin_id) / 'tao-dev'
            cached = Path(row['plugin_path']).resolve()
            local = home / 'plugins/local/tao-dev'
            if client == 'cursor' and cached == local.resolve():
                continue
            if not cached.is_relative_to(base) or cached == base:
                raise ClientError(f'Refusing native uninstall with an unowned cache path: {cached}')
    try:
        if client == 'kiro':
            skill, hook = _kiro_paths(home, project, scope)
            marker = skill / '.tao-owned.json'
            owned = _read_json(marker) if marker.is_file() and not marker.is_symlink() else {}
            expected_skill = owned.get('skill_digest') or (activation or {}).get('skill_digest')
            expected_hook = owned.get('hook_digest') or (activation or {}).get('hook_digest')
            if skill.exists():
                if (skill.is_symlink() or marker.is_symlink() or not marker.is_file()
                        or owned.get('plugin_id') != plugin_id or expected_skill != _tree_digest(skill)):
                    raise ClientError(f'Refusing to remove modified or unmanaged Kiro skill: {skill}')
            if hook.exists() and expected_hook != _tree_digest(hook):
                raise ClientError(f'Refusing to remove modified or unmanaged Kiro hook: {hook}')
            base = _kiro_cache_base(home, plugin_id)
            owned_caches = []
            if not others and not keep_plugin and base.is_dir():
                for cached in list(base.iterdir()):
                    owner = cached / '.tao-owned.json'
                    if not cached.is_dir() or cached.is_symlink() or owner.is_symlink() or not owner.is_file():
                        continue
                    try:
                        owner_data = _read_json(owner)
                    except ClientError:
                        continue
                    if (owner_data.get('component') == 'kiro-cache'
                            and owner_data.get('plugin_id') == plugin_id):
                        owned_caches.append(cached)
            if skill.exists():
                shutil.rmtree(skill)
                files.append(str(skill))
            if hook.exists():
                hook.unlink()
                files.append(str(hook))
            for cached in owned_caches:
                shutil.rmtree(cached)
                files.append(str(cached))
            if base.is_dir() and not any(base.iterdir()):
                base.rmdir()
                files.append(str(base))
        elif client == 'cursor':
            if scope == 'user':
                local = home / 'plugins/local/tao-dev'
                marker = local / '.tao-owned.json'
                if local.exists():
                    if local.is_symlink() or not marker.is_file() or _read_json(marker).get('id') != 'tao-dev':
                        raise ClientError(f'Refusing to remove unmanaged Cursor local plugin: {local}')
                    shutil.rmtree(local)
                    files.append(str(local))
            else:
                settings = project / '.cursor/settings.json'
                if settings.exists():
                    data = _read_json(settings)
                    plugins = data.get('plugins', {})
                    key = _cursor_plugin_key(plugin_id)
                    if key in plugins:
                        plugins.pop(key)
                        if plugins:
                            data['plugins'] = plugins
                        else:
                            data.pop('plugins', None)
                        if data:
                            _write_json(settings, data)
                        else:
                            settings.unlink()
                        files.append(str(settings))
            if selected and not others and not keep_plugin:
                base = home / 'plugins/cache' / _valid_id(plugin_id) / 'tao-dev'
                if base.is_dir() and not base.is_symlink():
                    shutil.rmtree(base)
                    files.append(str(base))
        elif client == 'claude':
            settings = home / 'settings.json' if scope == 'user' else project / ('.claude/settings.local.json' if scope == 'local' else '.claude/settings.json')
            if not selected:
                data = _read_json(settings)
                enabled = data.get('enabledPlugins', {})
                if plugin_id in enabled:
                    enabled.pop(plugin_id)
                    _write_json(settings, data)
            elif scope != 'user' and not project.is_dir():
                _remove_stale_claude_registration(home, plugin_id, scope, project)
                warnings.append('Deleted project registration removed; native cache retained for ownership-checked cleanup.')
            else:
                with _command_directory(project) as cwd:
                    _run(['claude', 'plugin', 'uninstall', plugin_id, '--scope', scope, '--keep-data'], cwd, json_output=False)
            settings = home / 'settings.json' if scope == 'user' else project / ('.claude/settings.local.json' if scope == 'local' else '.claude/settings.json')
            if settings.exists():
                files.append(str(settings))
            files.append(str(home / 'plugins/installed_plugins.json'))
        else:
            config = home / 'config.toml' if scope == 'user' else project / '.codex/config.toml'
            key = _key('plugins', plugin_id)
            # Explicit false prevents native default enablement when project
            # scopes still retain a shared installed cache.
            values = [(key + '.enabled', False)] if scope == 'user' and (others or keep_plugin) else [(key, None)]
            if config.exists():
                _write_config(config, values)
                files.append(str(config))
            if selected and not others and not keep_plugin:
                with _command_directory(project) as cwd:
                    _run(['codex', 'plugin', 'remove', plugin_id, '--json'], cwd)
                files.extend([str(home / 'config.toml'), str(home / 'plugins/cache' / _valid_id(plugin_id) / 'tao-dev')])
                trust = _config(home / 'config.toml').get('hooks', {}).get('state', {})
                owned = [(_key('hooks', 'state', key), None) for key in trust if key.startswith(plugin_id + ':')]
                if owned:
                    _write_config(home / 'config.toml', owned)
        if others or keep_plugin:
            warnings.append('Native cache remains shared with another installation.')
        warnings.append('Marketplace registrations are retained because other plugins may use them.')
        return {'files': list(dict.fromkeys(files)), 'warnings': warnings}
    except (ValueError, OSError) as exc:
        for path in watched:
            try:
                if _snapshot(path) != before[path]:
                    files.append(str(path))
            except OSError:
                pass
        raise ClientError(str(exc), list(dict.fromkeys(files + getattr(exc, 'files', [])))) from exc


def _command_directory(project):
    """Native commands can run without recreating a deleted consuming project."""
    return nullcontext(project) if project.is_dir() else tempfile.TemporaryDirectory(prefix='tao-uninstall-')


def _write_json(path, data):
    if path.is_symlink() or path.parent.is_symlink():
        raise ClientError(f'Refusing to replace symlinked native metadata: {path}')
    descriptor, temporary = tempfile.mkstemp(prefix='.tao-metadata-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
        if path.exists():
            os.chmod(temporary, path.stat().st_mode & 0o777)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def _matches_claude_scope(entry, scope, project):
    return entry.get('scope') == scope and (
        scope == 'user' or Path(entry.get('projectPath', '')).resolve() == project)


def _remove_stale_claude_registration(home, plugin_id, scope, project):
    path = home / 'plugins/installed_plugins.json'
    data = _read_json(path)
    plugins = data.get('plugins', {})
    entries = plugins.get(plugin_id, [])
    retained = [entry for entry in entries if not _matches_claude_scope(entry, scope, project)]
    if retained == entries:
        return
    if retained:
        plugins[plugin_id] = retained
    else:
        plugins.pop(plugin_id, None)
    _write_json(path, data)


def _capture_entries(data, paths):
    result = []
    for parts in paths:
        value = data
        present = True
        for part in parts:
            if not isinstance(value, dict) or part not in value:
                present = False
                value = None
                break
            value = value[part]
        result.append({'parts': parts, 'present': present, 'value': value})
    return result


def snapshot_activation(client, plugin_id, scope, project):
    """Capture only this identity's native activation for caller-owned rollback.

    The caller must preserve prior source and cache bytes before upgrading. This
    snapshot intentionally contains no authentication or unrelated configuration.
    """
    project = Path(project).expanduser().resolve()
    scope = validate_scope(client, scope, project)
    marketplace = _valid_id(plugin_id)
    home = _home(client)
    snapshot = {'client': client, 'plugin_id': plugin_id, 'scope': scope,
                'project': str(project), 'home': str(home), 'configs': []}
    if client == 'kiro':
        skill, hook = _kiro_paths(home, project, scope)
        snapshot['kiro_activation'] = [
            {'path': str(skill), 'saved': _content_snapshot(skill)},
            {'path': str(hook), 'saved': _content_snapshot(hook)},
        ]
        if scope == 'project':
            _, exclude = _kiro_git_info(project)
            if exclude is not None:
                snapshot['kiro_activation'].append(
                    {'path': str(exclude), 'saved': _content_snapshot(exclude)})
    elif client == 'codex':
        paths = [home / 'config.toml']
        if scope != 'user':
            paths.append(project / '.codex/config.toml')
        for path in paths:
            data = _config(path)
            keys = [['plugins', plugin_id], ['marketplaces', marketplace], ['features', 'hooks']]
            if path == home / 'config.toml':
                keys.append(['projects', str(project), 'trust_level'])
                keys.extend(['hooks', 'state', key] for key in data.get('hooks', {}).get('state', {})
                            if key.startswith(plugin_id + ':'))
            snapshot['configs'].append({'path': str(path), 'format': 'toml',
                                        'entries': _capture_entries(data, keys)})
    elif client == 'cursor':
        if scope == 'user':
            local = home / 'plugins/local/tao-dev'
            snapshot['local_plugin'] = str(local) if local.exists() else None
        else:
            path = project / '.cursor/settings.json'
            snapshot['configs'].append({'path': str(path), 'format': 'json', 'entries': _capture_entries(
                _read_json(path) if path.exists() else {}, [['plugins', _cursor_plugin_key(plugin_id)]])})
    else:
        paths = [home / 'settings.json']
        if scope != 'user':
            paths.append(project / ('.claude/settings.local.json' if scope == 'local' else '.claude/settings.json'))
        for path in paths:
            snapshot['configs'].append({'path': str(path), 'format': 'json', 'entries': _capture_entries(
                _read_json(path), [['enabledPlugins', plugin_id], ['extraKnownMarketplaces', marketplace]])})
        path = home / 'plugins/known_marketplaces.json'
        snapshot['configs'].append({'path': str(path), 'format': 'json',
                                    'entries': _capture_entries(_read_json(path), [[marketplace]])})
        registry = home / 'plugins/installed_plugins.json'
        snapshot['registration'] = [entry for entry in _read_json(registry).get('plugins', {}).get(plugin_id, [])
                                    if _matches_claude_scope(entry, scope, project)]
    base = home / 'plugins/cache' / marketplace / 'tao-dev'
    snapshot['cache_paths'] = [str(path.resolve()) for path in base.iterdir() if path.is_dir()] if base.is_dir() else []
    return snapshot


def _restore_json_entries(data, entries):
    for entry in entries:
        parent = data
        parts = entry['parts']
        for part in parts[:-1]:
            if part not in parent:
                if not entry['present']:
                    break
                parent[part] = {}
            if not isinstance(parent[part], dict):
                raise ClientError('Native configuration structure changed during installation; rollback stopped')
            parent = parent[part]
        else:
            if entry['present']:
                parent[parts[-1]] = entry['value']
            else:
                parent.pop(parts[-1], None)
    return data


def restore_activation(snapshot, *, attempted_plugin_path=None):
    """Restore captured entries and optionally discard one new failed cache.

    Restore prior source/cache bytes before calling. Only an explicitly supplied
    attempted cache path, absent from the original snapshot, can be removed.
    Callers serialize transactions for the same native plugin identity.
    """
    client = snapshot['client']
    plugin_id = snapshot['plugin_id']
    scope = snapshot['scope']
    project = Path(snapshot['project'])
    home = Path(snapshot['home'])
    if home != _home(client):
        raise ClientError('Client home changed since the activation snapshot; rollback stopped')
    marketplace = _valid_id(plugin_id)
    files = []
    warnings = []
    try:
        if client == 'kiro':
            for item in snapshot.get('kiro_activation', []):
                _restore_content(Path(item['path']), item['saved'])
                files.append(item['path'])
        for config in snapshot['configs']:
            path = Path(config['path'])
            entries = list(config['entries'])
            if not path.exists() and not any(entry['present'] for entry in entries):
                continue
            if config['format'] == 'toml':
                if path == home / 'config.toml':
                    prior = {tuple(entry['parts']) for entry in entries}
                    entries.extend({'parts': ['hooks', 'state', key], 'present': False, 'value': None}
                                   for key in _config(path).get('hooks', {}).get('state', {})
                                   if key.startswith(plugin_id + ':') and ('hooks', 'state', key) not in prior)
                _write_config(path, [(_key(*entry['parts']), entry['value'] if entry['present'] else None)
                                     for entry in entries])
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                _write_json(path, _restore_json_entries(_read_json(path), entries))
            files.append(str(path))
        if client == 'claude':
            path = home / 'plugins/installed_plugins.json'
            data = _read_json(path)
            plugins = data.setdefault('plugins', {})
            entries = [entry for entry in plugins.get(plugin_id, [])
                       if not _matches_claude_scope(entry, scope, project)]
            entries.extend(snapshot.get('registration', []))
            if entries:
                plugins[plugin_id] = entries
            else:
                plugins.pop(plugin_id, None)
            if path.exists() or entries:
                path.parent.mkdir(parents=True, exist_ok=True)
                _write_json(path, data)
                files.append(str(path))
        if attempted_plugin_path:
            attempted = Path(attempted_plugin_path)
            base = home / 'plugins/cache' / marketplace / 'tao-dev'
            if attempted.resolve() not in {Path(path) for path in snapshot['cache_paths']} and attempted.exists():
                if (attempted.is_symlink() or attempted.resolve().parent != base or
                        not attempted.is_dir()):
                    raise ClientError(f'Refusing rollback of unowned plugin cache: {attempted}')
                manifest = next((attempted / name for name in (
                    '.codex-plugin/plugin.json', '.claude-plugin/plugin.json',
                    '.cursor-plugin/plugin.json', 'plugin.json')
                                 if (attempted / name).is_file()), None)
                if manifest is None or _read_json(manifest).get('name') != 'tao-dev':
                    raise ClientError(f'Cannot verify the attempted cache identity: {attempted}')
                shutil.rmtree(attempted)
                files.append(str(attempted))
        base = home / 'plugins/cache' / marketplace / 'tao-dev'
        prior_paths = {Path(path) for path in snapshot['cache_paths']}
        current_paths = {path.resolve() for path in base.iterdir() if path.is_dir()} if base.is_dir() else set()
        if client == 'codex' and current_paths - prior_paths:
            warnings.append('Newer cached versions remain; native version rollback could not be verified.')
        if prior_paths - current_paths:
            warnings.append('Previous cached versions remain missing; restore the saved cache before retrying.')
        return {'files': list(dict.fromkeys(files)), 'warnings': warnings}
    except (ValueError, OSError) as exc:
        raise ClientError(str(exc), files + getattr(exc, 'files', [])) from exc
