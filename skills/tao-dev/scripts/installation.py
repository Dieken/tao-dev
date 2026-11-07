"""Standard-library, project-only skill deployment with owned-tree transactions."""

import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile

from install_clients import PROJECT_SKILLS, destination


SKILL = Path(__file__).resolve().parent.parent
MARKER = '.tao-install.json'
SCHEMA = 'tao.project-skill-install/v1'
IGNORED = {'__pycache__', '.git', '.pytest_cache'}


class InstallError(ValueError):
    pass


def arguments(argv):
    parser = argparse.ArgumentParser(prog='tao', description=__doc__)
    parser.add_argument('command', choices=('install', 'upgrade', 'list', 'uninstall'))
    parser.add_argument('--project', type=Path, required=True, help='Existing project directory; never user scope.')
    parser.add_argument('--client', choices=tuple(PROJECT_SKILLS))
    parser.add_argument('--format', choices=('text', 'json'), default='text')
    parser.add_argument('--source', type=Path, help='Local repository or complete skill directory (install/upgrade only).')
    args = parser.parse_args(argv)
    if args.command != 'list' and not args.client:
        parser.error('--client is required for install, upgrade and uninstall.')
    if args.source is not None and args.command not in ('install', 'upgrade'):
        parser.error('--source is only supported by install and upgrade.')
    return args


def linked(path):
    """Include Windows junctions, including on Python 3.11 without is_junction."""
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return stat.S_ISLNK(info.st_mode) or getattr(info, 'st_reparse_tag', 0) == 0xA0000003


def project_root(path):
    path = Path(path).absolute()
    if linked(path):
        raise InstallError(f'Project directory must not be a symbolic link: {path}')
    if not path.is_dir():
        raise InstallError(f'Project directory does not exist: {path}')
    project = path.resolve()
    if project == Path.home().resolve() or project == Path(project.anchor):
        raise InstallError('Select a project directory, not the home or filesystem root.')
    return project


def safe_path(project, path):
    """Reject symlinks and non-directory ancestors before reads or writes."""
    current = project
    relative = path.relative_to(project)
    for index, component in enumerate(relative.parts):
        current = current / component
        if linked(current):
            raise InstallError(f'Symbolic links are not managed: {current}')
        if index < len(relative.parts) - 1 and current.exists() and not current.is_dir():
            raise InstallError(f'Parent path is not a directory: {current}')
    return path


def tree_inventory(root, *, source=False):
    """Hash all regular files and retain directories/modes to protect user edits."""
    if linked(root) or not root.is_dir():
        raise InstallError(f'Skill must be a regular directory: {root}')
    files, directories = {}, []
    def unreadable(error):
        raise InstallError(f'Cannot inventory skill: {error}') from error

    for parent, names, leaves in os.walk(root, followlinks=False, onerror=unreadable):
        parent = Path(parent)
        if source:
            names[:] = [name for name in names if name not in IGNORED]
        names.sort()
        for name in sorted(names):
            path = parent / name
            if linked(path):
                raise InstallError(f'Symbolic links are not managed: {path}')
            directories.append(path.relative_to(root).as_posix())
        for name in sorted(leaves):
            path = parent / name
            relative = path.relative_to(root).as_posix()
            if relative == MARKER:
                if linked(path):
                    raise InstallError(f'Symbolic links are not managed: {path}')
                continue
            if source and name.endswith(('.pyc', '.pyo')):
                continue
            info = path.lstat()
            if not stat.S_ISREG(info.st_mode):
                raise InstallError(f'Only regular skill files are supported: {path}')
            with path.open('rb') as stream:
                digest = hashlib.file_digest(stream, 'sha256').hexdigest()
            files[relative] = {'sha256': digest, 'mode': stat.S_IMODE(info.st_mode)}
    return {'files': files, 'directories': sorted(directories)}


def source_skill(path):
    path = Path(path).absolute()
    if linked(path):
        raise InstallError(f'Source must not be a symbolic link: {path}')
    for candidate in (path, path / 'skills/tao-dev'):
        if (candidate / 'SKILL.md').is_file() and (candidate / 'scripts/tao.py').is_file():
            safe_path(path, candidate)
            tree_inventory(candidate, source=True)
            return candidate.resolve()
    raise InstallError('Source must contain SKILL.md and scripts/tao.py, directly or under skills/tao-dev.')


def read_record(target, client):
    if not target.is_dir():
        raise InstallError(f'No tao ownership record; refusing to change {target}')
    marker = target / MARKER
    if linked(marker) or not marker.is_file():
        raise InstallError(f'No tao ownership record; refusing to change {target}')
    try:
        record = json.loads(marker.read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise InstallError(f'Invalid ownership record: {marker}') from exc
    if (not isinstance(record, dict) or record.get('schema') != SCHEMA
            or record.get('client') != client or record.get('skill') != 'tao-dev'
            or not isinstance(record.get('inventory'), dict)
            or not isinstance(record['inventory'].get('files'), dict)
            or not isinstance(record['inventory'].get('directories'), list)):
        raise InstallError(f'Invalid ownership record: {marker}')
    return record


def unchanged(target, record):
    if tree_inventory(target) != record['inventory']:
        raise InstallError(f'Managed skill has modified, missing or unowned files: {target}. '
                           'Save your changes elsewhere and restore the installed contents before retrying.')


def remove_owned_tree(path):
    def retry_readonly(function, name, error):
        failure = error[1]
        candidate = Path(name)
        if os.name != 'nt' or not isinstance(failure, PermissionError) or linked(candidate):
            raise failure
        candidate.chmod(candidate.stat().st_mode | stat.S_IWRITE)
        function(name)
    shutil.rmtree(path, onerror=retry_readonly)


@contextmanager
def transaction_directory(project, target):
    created = []
    current = project
    for component in target.parent.relative_to(project).parts:
        current = current / component
        safe_path(project, current)
        if not current.exists():
            current.mkdir()
            created.append(current)
    lock = target.parent / '.tao-dev-install.lock'
    safe_path(project, lock)
    try:
        lock.mkdir()
    except FileExistsError as exc:
        raise InstallError(f'Installation is locked: {lock}. Remove only after confirming no installer is running.') from exc
    work = None
    failed = False
    try:
        work = Path(tempfile.mkdtemp(prefix='.tao-dev-', dir=target.parent))
        yield work
    except BaseException:
        failed = True
        raise
    finally:
        # If even rollback failed, retain the old tree rather than deleting the
        # only recoverable copy. Ordinary copy/swap failures leave no staging.
        try:
            recovery = work is not None and (work / 'previous').exists() and not target.exists()
            if work is not None and not (failed and recovery):
                try:
                    remove_owned_tree(work)
                except OSError as error:
                    state = 'failed' if failed else 'committed'
                    raise InstallError(f'Installation operation {state}; cleanup incomplete at {work}: {error}. '
                                       'Inspect remaining files before removing that staging directory.') from error
        finally:
            try:
                lock.rmdir()
            finally:
                for directory in reversed(created):
                    try:
                        directory.rmdir()
                    except OSError:
                        pass  # Successful installs or retained staging occupy this parent.


def stage_skill(source, staged, client):
    inventory = tree_inventory(source, source=True)
    staged.mkdir()
    for directory in inventory['directories']:
        (staged / directory).mkdir(parents=True, exist_ok=True)
    for relative in inventory['files']:
        shutil.copy2(source / relative, staged / relative, follow_symlinks=False)
    if tree_inventory(staged) != inventory:
        raise InstallError('Source changed while copying; existing installation is unchanged.')
    record = {'schema': SCHEMA, 'skill': 'tao-dev', 'client': client,
              'inventory': inventory}
    (staged / MARKER).write_text(json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def deploy(args):
    project = project_root(args.project)
    target = safe_path(project, destination(project, args.client))
    source = source_skill(args.source if args.source is not None else SKILL)
    if source != target and (source.is_relative_to(target) or target.is_relative_to(source)):
        raise InstallError('Source and destination must not contain one another.')
    if args.command == 'upgrade' and not target.exists():
        raise InstallError(f'No project installation to upgrade: {target}')
    if target.exists():
        unchanged(target, read_record(target, args.client))
    with transaction_directory(project, target) as work:
        staged, previous = work / 'new', work / 'previous'
        stage_skill(source, staged, args.client)
        safe_path(project, target)
        had_previous = target.exists()
        if had_previous:
            unchanged(target, read_record(target, args.client))
            target.rename(previous)
        try:
            staged.rename(target)
        except BaseException as exc:
            if had_previous:
                try:
                    previous.rename(target)
                except OSError as rollback:
                    raise InstallError(f'Update failed ({exc}); rollback failed ({rollback}). '
                                       f'Previous installation is retained at {previous}.') from rollback
            raise
    return {'client': args.client, 'project': str(project), 'path': str(target),
            'state': 'installed', 'source': str(source)}


def inventory(args):
    project = project_root(args.project)
    rows = []
    for client in ([args.client] if args.client else PROJECT_SKILLS):
        target = destination(project, client)
        try:
            safe_path(project, target)
            if not target.exists():
                continue
            record = read_record(target, client)
            try:
                unchanged(target, record)
                state = 'installed'
            except InstallError:
                state = 'modified'
            rows.append({'client': client, 'path': str(target), 'state': state})
        except InstallError as exc:
            rows.append({'client': client, 'path': str(target), 'state': 'unmanaged', 'reason': str(exc)})
    return {'project': str(project), 'installations': rows}


def uninstall(args):
    project = project_root(args.project)
    target = safe_path(project, destination(project, args.client))
    if not target.exists():
        raise InstallError(f'No project installation to uninstall: {target}')
    unchanged(target, read_record(target, args.client))
    with transaction_directory(project, target) as work:
        safe_path(project, target)
        unchanged(target, read_record(target, args.client))
        target.rename(work / 'previous')
    return {'client': args.client, 'project': str(project), 'path': str(target), 'state': 'removed'}


def main(argv=None):
    args = arguments(list(sys.argv[1:] if argv is None else argv))
    try:
        result = (inventory(args) if args.command == 'list' else
                  uninstall(args) if args.command == 'uninstall' else deploy(args))
        report = {'tool': 'tao-dev', 'command': args.command, 'status': 'passed',
                  'outputs': result, 'diagnostics': []}
        code = 0
    except (OSError, ValueError) as exc:
        report = {'tool': 'tao-dev', 'command': args.command, 'status': 'failed',
                  'outputs': {}, 'diagnostics': [{'severity': 'error', 'message': str(exc)}]}
        code = 2
    if args.format == 'json':
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif code:
        print(report['diagnostics'][0]['message'], file=sys.stderr)
    else:
        print(json.dumps(report['outputs'], ensure_ascii=False, indent=2))
    return code
