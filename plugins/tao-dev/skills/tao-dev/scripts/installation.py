"""Explicit, standard-library installation management for complete plugins."""

import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile

import installed_runtime as state

DEFAULT_MARKETPLACE = 'Dieken/tao-dev'
SCRIPTS = Path(__file__).resolve().parent
PLUGIN = SCRIPTS.parents[2]
MARKER = '.tao-owned.json'


class InstallError(ValueError):
    def __init__(self, message, files=()):
        super().__init__(message)
        self.files = list(files)


def arguments(argv):
    parser = argparse.ArgumentParser(prog='tao')
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('install', 'uninstall'):
        command = commands.add_parser(name)
        command.add_argument('--client', choices=('claude', 'codex'), required=True)
        command.add_argument('--project', type=Path, default=Path.cwd())
        command.add_argument('--format', choices=('text', 'json'), default='text')
        if name == 'install':
            command.add_argument('--scope', choices=('user', 'project', 'repo', 'local'), default='user')
            sources = command.add_mutually_exclusive_group()
            sources.add_argument('--marketplace')
            sources.add_argument('--source')
            command.add_argument('--ref')
            command.add_argument('--wheelhouse', type=Path)
            command.add_argument('--bin-dir', type=Path,
                                 help='CLI launcher directory; defaults to ~/.local/bin.')
        else:
            command.add_argument('--list', action='store_true', help='Only discover installations.')
            command.add_argument('--id', help='Installation identifier shown by --list.')
            command.add_argument('--yes', action='store_true', help='Confirm only the explicit --id.')
    args = parser.parse_args(argv)
    if args.command == 'install':
        if args.client == 'codex' and args.scope in ('repo', 'local'):
            args.scope = 'project'
        elif args.client == 'claude' and args.scope == 'repo':
            parser.error('Claude scopes are user, project and local; repo is a Codex alias.')
    args.project = args.project.resolve()
    if not args.project.is_dir():
        parser.error('--project must be an existing directory.')
    if args.command == 'uninstall' and args.yes and not args.id:
        parser.error('--yes requires an explicit --id; it never selects all installations.')
    return args


def run(argv, *, cwd=None, env=None, timeout=180):
    completed = subprocess.run([str(arg) for arg in argv], cwd=cwd, env=env,
                               stdin=subprocess.DEVNULL, capture_output=True, text=True,
                               timeout=timeout)
    if completed.returncode:
        raise InstallError(f'{argv[0]} failed: {completed.stderr.strip() or completed.stdout.strip()}')
    return completed.stdout


def source_spec(args, previous):
    if args.source is not None:
        kind, location = 'source', args.source
    elif args.marketplace is not None:
        kind, location = 'marketplace', args.marketplace
    elif previous:
        if args.ref and Path(previous['source']['location']).is_dir():
            raise InstallError('--ref requires a Git source, not a local directory.')
        return previous['source'] | ({'ref': args.ref} if args.ref else {})
    else:
        kind, location = 'marketplace', DEFAULT_MARKETPLACE
    path = Path(location).expanduser()
    if path.exists():
        if args.ref:
            raise InstallError('--ref requires a Git source, not a local directory.')
        location = str(path.resolve())
    elif not location.startswith(('https://', 'ssh://', 'git@')):
        if location.startswith(('.', '/', '~')) or location.count('/') != 1:
            raise InstallError('Source does not exist; use a directory, Git URL, or owner/repo.')
        location = 'https://github.com/' + location + '.git'
    return {'kind': kind, 'location': location, 'ref': args.ref}


def materialize(spec, destination):
    source = Path(spec['location'])
    if source.is_dir():
        return source.resolve()
    argv = ['git', 'clone', '--depth', '1']
    if spec.get('ref'):
        argv += ['--branch=' + spec['ref']]
    argv += ['--', spec['location'], str(destination)]
    run(argv)
    return destination


def plugin_root(source):
    for candidate in (source, source / 'plugins/tao-dev'):
        if (candidate / 'skills/tao-dev/scripts/runtime.json').is_file():
            return candidate
    raise InstallError('Source must contain the complete tao-dev plugin, including its CLI runtime.')


def catalog_plugin(source, client):
    names = ('.agents/plugins/marketplace.json', '.claude-plugin/marketplace.json') if client == 'codex' else (
        '.claude-plugin/marketplace.json',)
    catalog = next((source / name for name in names if (source / name).is_file()), None)
    if catalog is None:
        raise InstallError('Marketplace has no supported catalog; use --source for a plugin directory.')
    data = json.loads(catalog.read_text(encoding='utf-8'))
    entries = [entry for entry in data['plugins'] if entry.get('name') == 'tao-dev']
    if len(entries) != 1:
        raise InstallError('Marketplace must identify exactly one tao-dev plugin.')
    entry = entries[0]['source']
    if isinstance(entry, dict):
        if entry.get('source') != 'local':
            raise InstallError('This installer requires the tao-dev plugin inside its marketplace repository.')
        entry = entry['path']
    if not isinstance(entry, str):
        raise InstallError('Invalid marketplace plugin source.')
    target = (source / entry).resolve()
    if not target.is_relative_to(source.resolve()):
        raise InstallError('Marketplace plugin must stay inside the source directory.')
    return plugin_root(target), 'tao-dev@' + data['name']


def copy_plugin(source, destination):
    if source.is_symlink() or any(path.is_symlink() for path in source.rglob('*')):
        raise InstallError('Plugin sources must not contain symbolic links.')
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.git'))


def local_catalog(source, destination, client, identifier):
    """Materialize a private source snapshot; changed contents get a new cache key."""
    plugin = destination / 'plugins/tao-dev'
    copy_plugin(source, plugin)
    digest = hashlib.sha256()
    for path in sorted(plugin.rglob('*')):
        if path.is_file():
            digest.update(path.relative_to(plugin).as_posix().encode() + b'\0' + path.read_bytes())
    build = digest.hexdigest()[:12]
    manifest_paths = [plugin / '.codex-plugin/plugin.json', plugin / '.claude-plugin/plugin.json']
    public = plugin / 'plugin.json'
    if client == 'codex' and public.exists():
        manifest = json.loads(public.read_text())
        codex = {key: manifest[key] for key in ('name', 'version', 'description')}
        codex['hooks'] = manifest.get('extensions', {}).get('com.openai', {}).get(
            'hooks', './com.openai/hooks/hooks.json')
        manifest_paths[0].parent.mkdir(exist_ok=True)
        manifest_paths[0].write_text(json.dumps(codex, indent=2) + '\n')
        public.unlink()
    for path in [*manifest_paths, public]:
        if path.exists():
            manifest = json.loads(path.read_text())
            original = manifest.get('version', '0.0.0').split('+')[0]
            manifest['version'] = original + '+local.' + build
            path.write_text(json.dumps(manifest, indent=2) + '\n')
    name = 'tao-dev-' + identifier
    entry = {'name': 'tao-dev', 'source': './plugins/tao-dev'}
    catalog = {'name': name, 'plugins': [entry]}
    if client == 'codex':
        entry.update(source={'source': 'local', 'path': './plugins/tao-dev'},
                     policy={'installation': 'AVAILABLE', 'authentication': 'ON_INSTALL'}, category='Productivity')
        path = destination / '.agents/plugins/marketplace.json'
    else:
        catalog['owner'] = {'name': 'tao-dev'}
        path = destination / '.claude-plugin/marketplace.json'
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(catalog, indent=2) + '\n')
    return plugin, 'tao-dev@' + name


def owned_root(root, identifier):
    if root.is_symlink():
        raise InstallError('Installation root must not be a symbolic link.')
    marker = root / MARKER
    if root.exists():
        if marker.is_symlink() or not marker.is_file() or json.loads(marker.read_text()).get('id') != identifier:
            raise InstallError(f'Refusing to reuse a directory without tao-dev ownership: {root}')
    else:
        root.mkdir(parents=True)
        marker.write_text(json.dumps({'schema': 1, 'id': identifier}) + '\n')


@contextmanager
def installation_lock(root):
    lock = root / 'install.lock'
    try:
        lock.mkdir()
    except FileExistsError as exc:
        raise InstallError(f'Another installation owns {lock}; retry when it finishes.') from exc
    try:
        yield
    finally:
        lock.rmdir()


def clean_environment():
    return {key: value for key, value in os.environ.items()
            if not key.startswith('TAO_') and key not in ('CLAUDE_PLUGIN_DATA', 'PYTHONPATH', 'PYTHONHOME')}


def prepare(plugin, python, runtime_dir, project, wheelhouse):
    env = clean_environment() | {'TAO_PYTHON': str(python), 'TAO_RUNTIME_DIR': str(runtime_dir)}
    entry = plugin / 'skills/tao-dev/scripts/tao.py'
    argv = [python, '-I', '-B', entry, 'setup', '--format', 'json']
    if wheelhouse:
        argv += ['--wheelhouse', wheelhouse]
    result = json.loads(run(argv, cwd=project, env=env, timeout=300))
    runtime = dict(result.get('outputs', {}).get('runtime', {}))
    publication = runtime.pop('publication', {})
    if (result.get('status') != 'passed' or runtime.get('state') != 'ready'
            or publication.get('state') != 'ready'):
        raise InstallError('Dependency preparation did not report both runtimes ready.')
    return [runtime, publication]


def doctor(plugin, python, project):
    result = json.loads(run([python, '-I', '-B', plugin / 'skills/tao-dev/scripts/tao.py',
                             'doctor', '--format', 'json'], cwd=project, env=clean_environment(), timeout=60))
    runtime = result.get('outputs', {}).get('runtime', {})
    if result.get('status') != 'passed' or runtime.get('state') != 'ready' or runtime.get('publication', {}).get('state') != 'ready':
        raise InstallError('Installed doctor must report both core and publication runtimes ready.')
    return result


def collapse_paths(paths):
    result = []
    for path in sorted({str(Path(path).absolute()) for path in paths}, key=lambda value: (len(Path(value).parts), value)):
        if not any(Path(path).is_relative_to(Path(parent)) for parent in result if Path(parent).is_dir()):
            result.append(path)
    return result


def install_cli(client, python, bin_dir, source_plugin):
    """Keep a shared CLI outside per-install roots so the final uninstall still works."""
    root = state.client_home(client) / 'tao-dev/cli'
    if root.is_symlink() or (root.parent.exists() and root.parent.is_symlink()):
        raise InstallError('CLI storage must not be a symbolic link.')
    if root.exists() and not (root / MARKER).is_file():
        raise InstallError('Existing CLI storage is not owned by tao-dev.')
    bin_dir = bin_dir.expanduser().absolute() if bin_dir else Path.home() / '.local/bin'
    launcher = bin_dir / ('tao.cmd' if os.name == 'nt' else 'tao')
    marker = 'tao-dev managed CLI'
    if launcher.is_symlink() or launcher.exists() and marker not in launcher.read_text():
        raise InstallError(f'Refusing to replace an existing command: {launcher}')
    root.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='.cli-', dir=root.parent))
    backup = root.with_name('.cli-previous')
    if backup.exists():
        shutil.rmtree(stage)
        raise InstallError(f'Previous CLI update needs inspection: {backup}')
    replaced = False
    try:
        copy_plugin(source_plugin, stage / 'plugin')
        (stage / 'plugin' / MARKER).write_text(json.dumps({'schema': 1, 'component': 'cli'}) + '\n')
        if root.exists():
            root.rename(backup)
        (stage / 'plugin').rename(root)
        replaced = True
        entry = root / 'skills/tao-dev/scripts/tao.py'
        if os.name == 'nt':
            text = f'@echo off\r\nrem {marker}\r\n"{python}" -I -B "{entry}" %*\r\n'
        else:
            text = f'#!/bin/sh\n# {marker}\nexec {shlex.quote(str(python))} -I -B {shlex.quote(str(entry))} "$@"\n'
        bin_dir.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix='.tao-', dir=bin_dir)
        try:
            with os.fdopen(descriptor, 'w') as stream:
                stream.write(text)
            Path(temporary).chmod(0o755)
            os.replace(temporary, launcher)
        finally:
            Path(temporary).unlink(missing_ok=True)
    except Exception:
        if replaced:
            shutil.rmtree(root)
        if backup.exists():
            backup.rename(root)
        raise
    else:
        if backup.exists():
            shutil.rmtree(backup, ignore_errors=True)
    finally:
        shutil.rmtree(stage, ignore_errors=True)
    return launcher, root


def ignore_runtime(project):
    """Keep private runtime files out of Git without changing team ignore rules."""
    completed = subprocess.run(['git', '-C', str(project), 'rev-parse', '--git-path', 'info/exclude'],
                               capture_output=True, text=True)
    if completed.returncode:
        return []
    path = Path(completed.stdout.strip())
    if not path.is_absolute():
        path = project / path
    path = path.resolve()
    current = path.read_text() if path.exists() else ''
    pattern = '/.local/tao-dev/'
    if pattern not in current.splitlines():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(current + ('\n' if current and not current.endswith('\n') else '') + pattern + '\n')
        return [str(path)]
    return []


def install(args):
    import install_clients as clients
    clients.validate_scope(args.client, args.scope, args.project)
    if not shutil.which(args.client):
        raise InstallError(f'{args.client} CLI is not on PATH.')
    if not shutil.which('git'):
        raise InstallError('Git is required to manage plugin sources.')
    import runtime
    python = Path(getattr(sys, '_base_executable', sys.executable)).resolve()
    runtime.inspect_python(python)
    run([python, '-I', '-c', 'import venv, ensurepip'], timeout=15)
    identifier = state.install_id(args.client, args.scope, args.project)
    previous = next((row for row in state.records(args.client) if row['id'] == identifier), None)
    spec = source_spec(args, previous)
    wheels = args.wheelhouse or (Path(previous['wheelhouse']) if previous and previous.get('wheelhouse') else None)
    if wheels is not None:
        wheels = wheels.resolve()
        if not wheels.is_dir():
            raise InstallError('--wheelhouse must be an existing directory; no network fallback is used.')
    root = state.managed_root(args.client, args.scope, args.project)
    owned_root(root, identifier)
    files = [str(root)]
    client_root = state.client_home(args.client) / 'tao-dev'
    client_root.mkdir(parents=True, exist_ok=True)
    try:
        with installation_lock(client_root), installation_lock(root):
            with tempfile.TemporaryDirectory(prefix='.incoming-', dir=root) as temporary:
                temporary = Path(temporary)
                origin = materialize(spec, temporary / 'repository')
                if spec['kind'] == 'source':
                    candidate = plugin_root(origin)
                    staged = temporary / 'marketplace'
                    plugin, plugin_id = local_catalog(candidate, staged, args.client, identifier)
                else:
                    plugin, plugin_id = catalog_plugin(origin, args.client)
                runtimes = prepare(plugin, python, root / 'runtime', args.project, wheels)
                snapshot = clients.snapshot_activation(args.client, plugin_id, args.scope, args.project)
                prior_caches = set(snapshot.get('cache_paths', []))
                if previous:
                    prior_caches.add(previous['plugin_path'])
                cache_backups = []
                for index, location in enumerate(sorted(prior_caches)):
                    prior_cache = Path(location)
                    if prior_cache.is_dir():
                        cache_backup = temporary / f'previous-plugin-{index}'
                        copy_plugin(prior_cache, cache_backup)
                        cache_backups.append((prior_cache, cache_backup))
                old = root / '.marketplace-previous'
                target = root / 'marketplace'
                source_changed = False
                old_moved = False
                installed = None
                receipt = None
                try:
                    if spec['kind'] == 'source':
                        # Keep the old source until the installed inventory passes doctor.
                        if old.exists():
                            raise InstallError(f'Previous source update needs inspection: {old}')
                        if target.exists():
                            target.rename(old)
                            old_moved = True
                        staged.rename(target)
                        source_changed = True
                        marketplace = str(target)
                    else:
                        marketplace = spec['location']
                    installed = clients.install_plugin(args.client, marketplace, plugin_id, args.scope, args.project,
                                                       ref=spec.get('ref') if spec['kind'] == 'marketplace' else None,
                                                       python=python)
                    files.extend(installed.get('files', []))
                    cached = Path(installed['plugin_path'])
                    receipt = dict(schema=1, id=identifier, client=args.client, scope=args.scope,
                                   project=None if args.scope == 'user' else str(args.project),
                                   managed_root=str(root), plugin_id=plugin_id,
                                   plugin_path=str(cached), plugin_base=installed['plugin_base'],
                                   python=str(python), runtime_dir=str(root / 'runtime'),
                                   version=installed['version'], source=spec, status='preparing',
                                   wheelhouse=str(wheels) if wheels else None, files=collapse_paths(files))
                    if previous is None:
                        state.save_record(receipt)
                    # The native client may fetch a newer inventory than the staged source.
                    runtimes = prepare(cached, python, root / 'runtime', args.project, wheels)
                    receipt['status'] = 'ready'
                    state.save_record(receipt)
                    checked = doctor(cached, python, args.project)
                    bin_dir = args.bin_dir or (Path(previous['launcher']).parent
                                               if previous and previous.get('launcher') else Path.home() / '.local/bin')
                    launcher = bin_dir.expanduser().absolute() / ('tao.cmd' if os.name == 'nt' else 'tao')
                    cli_root = state.client_home(args.client) / 'tao-dev/cli'
                    files.extend([str(launcher), str(cli_root)])
                    if args.scope != 'user':
                        files.extend(ignore_runtime(args.project))
                    files.append(str(state.record_path(args.client, identifier)))
                    receipt.update(launcher=str(launcher), cli_path=str(cli_root), files=collapse_paths(files))
                    state.save_record(receipt)
                    # This atomic update is the final fallible step of the transaction.
                    install_cli(args.client, python, bin_dir, cached)
                except Exception as failure:
                    rollback_errors = []
                    try:
                        if source_changed:
                            shutil.rmtree(target)
                        if old_moved:
                            old.rename(target)
                        for prior_cache, cache_backup in cache_backups:
                            if prior_cache.exists():
                                shutil.rmtree(prior_cache)
                            prior_cache.parent.mkdir(parents=True, exist_ok=True)
                            cache_backup.rename(prior_cache)
                        attempted = installed['plugin_path'] if installed else getattr(failure, 'plugin_path', None)
                        recovery = clients.restore_activation(snapshot, attempted_plugin_path=attempted)
                        rollback_errors.extend((recovery or {}).get('warnings', []))
                    except Exception as rollback:
                        rollback_errors.append(str(rollback))
                    if previous:
                        state.save_record(previous if not rollback_errors else previous | {'status': 'preparing'})
                    elif receipt:
                        state.save_record(receipt | {'status': 'preparing'})
                    if rollback_errors:
                        raise InstallError(f'{failure}; rollback needs attention: {"; ".join(rollback_errors)}', files) from failure
                    raise
                if old_moved:
                    shutil.rmtree(old, ignore_errors=True)
                warnings = installed.get('warnings', [])
                if previous and previous['plugin_id'] != plugin_id:
                    other = [row for row in state.records(args.client) if row['id'] != identifier]
                    try:
                        clients.remove_activation(args.client, previous['plugin_id'], previous['scope'],
                                                  Path(previous['project'] or args.project),
                                                  keep_plugin=any(row['plugin_id'] == previous['plugin_id'] for row in other))
                    except clients.ClientError as exc:
                        warnings.append(f'New installation is ready; prior activation needs cleanup: {exc}')
                return dict(installation=receipt, doctor=checked, runtimes=runtimes,
                            verification=installed.get('verification', {}),
                            files=receipt['files'], warnings=warnings, usage=guide(receipt))
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        raise InstallError(str(exc), collapse_paths(files + getattr(exc, 'files', []))) from exc


def guide(record):
    invocation = '/tao-dev:tao-dev' if record['client'] == 'claude' else '$tao-dev'
    return [f'Open a new {record["client"]} session in your project.',
            f'{invocation} Plan a small feature for this project and define how to verify it.',
            'No TAO environment variables are required.',
            f'CLI: {record.get("launcher", "tao")} install / uninstall --client {record["client"]}']


def discover(client, project):
    import install_clients as clients
    managed = state.records(client)
    keys = {(row['plugin_id'], row['scope'], row['project']): row for row in managed}
    found = []
    for row in clients.discover(client, project):
        key = (row['plugin_id'], row['scope'], row.get('project'))
        if key in keys:
            keys[key].update({name: row[name] for name in ('plugin_path', 'version', 'enabled') if name in row})
            continue
        row = dict(row, client=client, native=True)
        row['id'] = 'native-' + hashlib.sha256(json.dumps(key).encode()).hexdigest()[:16]
        row['files'] = collapse_paths(row.get('files', [row['plugin_path']]))
        found.append(row)
    return sorted(managed + found, key=lambda row: (row['scope'], row.get('project') or '', row['id']))


def choose(rows, args):
    if args.id:
        selected = next((row for row in rows if row['id'] == args.id), None)
        if selected is None:
            raise InstallError('Installation --id was not found; run uninstall --list again.')
        if args.yes:
            return selected
    else:
        try:
            value = input('Remove which installation? Enter its number, or press Enter to cancel: ').strip()
        except EOFError:
            return None
        if not value:
            return None
        if not value.isdigit() or not 1 <= int(value) <= len(rows):
            raise InstallError('Invalid selection; nothing was removed.')
        selected = rows[int(value) - 1]
    try:
        answer = input(f'Remove {selected["id"]} and its listed owned resources? [y/N] ').strip().lower()
    except EOFError:
        return None
    return selected if answer in ('y', 'yes') else None


def remove_owned(row):
    root = Path(row['managed_root'])
    expected = state.managed_root(row['client'], row['scope'], row.get('project'))
    if root != expected or root.is_symlink():
        raise InstallError('Unsafe installation ownership; no runtime files were removed.')
    if not root.exists():
        return [], []
    marker = root / MARKER
    if not marker.is_file() or marker.is_symlink() or json.loads(marker.read_text()).get('id') != row['id']:
        raise InstallError('Ownership marker does not match; no runtime files were removed.')
    if (root / 'install.lock').exists():
        raise InstallError('Installation is busy; no runtime files were removed.')
    known = {'runtime', 'marketplace', MARKER}
    unknown = [path for path in root.iterdir() if path.name not in known]
    if unknown:
        removed = []
        for path in root.iterdir():
            if path.name not in known or path.name == MARKER:
                continue
            if path.is_symlink() or path.is_file():
                path.unlink()
            else:
                shutil.rmtree(path)
            removed.append(str(path))
        return removed, [f'Preserved unknown files in {root}']
    shutil.rmtree(root)
    return [str(root)], []


def uninstall(args):
    import install_clients as clients
    rows = discover(args.client, args.project)
    if args.format != 'json' or not args.list and not args.yes:
        print_inventory(rows)
    if args.list or not rows:
        return {'installations': rows, 'removed': []}
    selected = choose(rows, args)
    if selected is None:
        return {'installations': rows, 'removed': [], 'cancelled': True}
    others = [row for row in rows if row['id'] != selected['id'] and row['plugin_id'] == selected['plugin_id']]
    same_activation = any(row['project'] == selected.get('project') and
                          row['scope'] in ('project', 'local') and selected['scope'] in ('project', 'local')
                          for row in others) if args.client == 'codex' else False
    if not selected.get('native'):
        # Validate ownership before changing client activation.
        root = state.managed_root(selected['client'], selected['scope'], selected['project'])
        if root.exists():
            owned_root(root, selected['id'])
            if (root / 'install.lock').exists():
                raise InstallError('Installation is busy; nothing was removed.')
    result = clients.remove_activation(args.client, selected['plugin_id'], selected['scope'],
                                       Path(selected.get('project') or args.project),
                                       keep_plugin=bool(others), keep_activation=same_activation)
    removed, warnings = list(result.get('files', [])), list(result.get('warnings', []))
    if not selected.get('native'):
        paths, notices = remove_owned(selected)
        removed.extend(paths)
        warnings.extend(notices)
        receipt_path = state.record_path(args.client, selected['id'])
        receipt_path.unlink(missing_ok=True)
        removed.append(str(receipt_path))
        warnings.append('The shared tao CLI is retained for future install/uninstall commands.')
    else:
        warnings.append('Unrecorded Python runtime locations are retained; their ownership cannot be inferred.')
    return {'installation': selected, 'removed': removed, 'warnings': warnings,
            'shared_plugin_retained': bool(others)}


def print_inventory(rows):
    if not rows:
        print('No tao-dev installations found.')
    for number, row in enumerate(rows, 1):
        print(f'{number}. {row["id"]}: {row["scope"]} | {row.get("project") or "all projects"} | {row.get("version", "unknown")}')
        for path in row.get('files', []):
            print('   ' + path)


def main(argv=None):
    args = arguments(list(sys.argv[1:] if argv is None else argv))
    try:
        result = install(args) if args.command == 'install' else uninstall(args)
        report = dict(tool='tao-dev', command=args.command, status='passed', outputs=result, diagnostics=[])
        code = 0
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        report = dict(tool='tao-dev', command=args.command, status='not_run',
                      outputs={'files': getattr(exc, 'files', [])}, diagnostics=[{'message': str(exc)}])
        code = 2
    if args.format == 'json':
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f'tao {args.command}: {report["status"]}')
        if code:
            print(report['diagnostics'][0]['message'])
            for path in report['outputs']['files']:
                print('  ' + path)
        elif args.command == 'install':
            row = result['installation']
            print(f'{row["client"]} | {row["version"]} | {row["scope"]} | {row["project"] or "all projects"}')
            print('Plugin: ' + row['plugin_path'])
            print('Python: ' + row['python'])
            print('Runtime: ' + row['runtime_dir'])
            print('Doctor: core ready; publication ready')
            print('Written files/directories:')
            for path in result['files']:
                print('  ' + path)
            for line in result['usage']:
                print(line)
        elif result.get('removed'):
            print('Removed or updated:')
            for path in result['removed']:
                print('  ' + path)
        for warning in report['outputs'].get('warnings', []):
            print('Note: ' + warning)
    return code
