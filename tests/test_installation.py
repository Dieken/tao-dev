"""Project-only installation, ownership protection and transactional replacement."""

import json
from pathlib import Path

import pytest

import installation as install
from install_clients import PROJECT_SKILLS, destination


@pytest.fixture
def source(tmp_path):
    root = tmp_path / 'source'
    (root / 'scripts').mkdir(parents=True)
    (root / 'SKILL.md').write_text('---\nname: tao-dev\ndescription: Test skill\n---\n', encoding='utf-8')
    (root / 'scripts/tao.py').write_text('# entry\n', encoding='utf-8')
    return root


@pytest.fixture
def project(tmp_path):
    root = tmp_path / 'project'
    root.mkdir()
    return root


def args(command, project, source=None, client='codex'):
    argv = [command, '--project', str(project), '--client', client]
    if source is not None:
        argv.extend(['--source', str(source)])
    return install.arguments(argv)


def snapshot(root):
    return {path.relative_to(root).as_posix(): path.read_bytes()
            for path in root.rglob('*') if path.is_file()}


def link(target, source, *, directory=False):
    try:
        target.symlink_to(source, target_is_directory=directory)
    except OSError as exc:
        pytest.skip(f'Symbolic links unavailable: {exc}')


@pytest.mark.parametrize('client', PROJECT_SKILLS)
def test_project_lifecycle_is_deterministic_and_preserves_documents(project, source, client):
    (project / 'docs').mkdir()
    (project / 'docs/plan.md').write_text('User plan', encoding='utf-8')
    install.deploy(args('install', project, source, client))
    target = destination(project, client)
    before = snapshot(target)
    for _ in range(2):
        install.deploy(args('upgrade', project, source, client))
        assert snapshot(target) == before
    assert install.inventory(args('list', project, client=client))['installations'] == [
        {'client': client, 'path': str(target), 'state': 'installed'}]
    install.uninstall(args('uninstall', project, client=client))
    assert not target.exists()
    assert (project / 'docs/plan.md').read_text(encoding='utf-8') == 'User plan'
    assert not list(target.parent.glob('.tao-dev-*'))


def test_upgrade_replaces_removed_and_added_files(project, source):
    (source / 'old').write_text('old', encoding='utf-8')
    install.deploy(args('install', project, source))
    (source / 'old').unlink()
    (source / 'new').write_text('new', encoding='utf-8')
    install.deploy(args('upgrade', project, source))
    target = destination(project, 'codex')
    assert not (target / 'old').exists()
    assert (target / 'new').read_text(encoding='utf-8') == 'new'


@pytest.mark.parametrize('change', ['modified', 'added', 'missing', 'directory'])
@pytest.mark.parametrize('command', ['install', 'upgrade', 'uninstall'])
def test_user_modifications_block_all_destructive_operations(project, source, change, command):
    install.deploy(args('install', project, source))
    target = destination(project, 'codex')
    if change == 'modified':
        (target / 'SKILL.md').write_text('User instructions', encoding='utf-8')
    elif change == 'added':
        (target / 'notes.txt').write_text('User notes', encoding='utf-8')
    elif change == 'missing':
        (target / 'SKILL.md').unlink()
    else:
        (target / 'user-directory').mkdir()
    before = snapshot(target)
    operation = install.uninstall if command == 'uninstall' else install.deploy
    with pytest.raises(install.InstallError, match='modified, missing or unowned'):
        operation(args(command, project, source if command != 'uninstall' else None))
    assert snapshot(target) == before
    assert install.inventory(args('list', project))['installations'][0]['state'] == 'modified'


@pytest.mark.parametrize('marker', [None, '{}', 'not json'])
def test_unowned_target_is_never_adopted(project, source, marker):
    target = destination(project, 'codex')
    target.mkdir(parents=True)
    if marker is not None:
        (target / install.MARKER).write_text(marker, encoding='utf-8')
    before = snapshot(target)
    with pytest.raises(install.InstallError, match='ownership'):
        install.deploy(args('install', project, source))
    assert snapshot(target) == before
    assert install.inventory(args('list', project))['installations'][0]['state'] == 'unmanaged'


@pytest.mark.parametrize('position', ['client', 'skills', 'target', 'file', 'marker'])
def test_symlinks_never_write_outside_project(project, source, tmp_path, position):
    outside = tmp_path / 'outside'
    outside.mkdir()
    (outside / 'precious').write_text('keep', encoding='utf-8')
    target = destination(project, 'codex')
    if position in ('file', 'marker'):
        install.deploy(args('install', project, source))
        path = target / ('SKILL.md' if position == 'file' else install.MARKER)
        path.unlink()
        link(path, outside / 'precious')
    else:
        path = {'client': project / '.agents', 'skills': target.parent, 'target': target}[position]
        path.parent.mkdir(parents=True, exist_ok=True)
        link(path, outside, directory=True)
    with pytest.raises(install.InstallError):
        install.deploy(args('install', project, source))
    assert snapshot(outside) == {'precious': b'keep'}


def test_source_symlink_is_rejected_before_project_changes(project, source, tmp_path):
    link(source / 'unsafe', tmp_path, directory=True)
    with pytest.raises(install.InstallError, match='Symbolic'):
        install.deploy(args('install', project, source))
    assert list(project.iterdir()) == []


@pytest.mark.parametrize('failure', ['copy', 'swap'])
def test_failed_upgrade_restores_exact_previous_install(project, source, monkeypatch, failure):
    install.deploy(args('install', project, source))
    target = destination(project, 'codex')
    before = snapshot(target)
    (source / 'SKILL.md').write_text('New release', encoding='utf-8')
    if failure == 'copy':
        def fail_copy(*_args, **_kwargs):
            raise OSError('Injected copy failure')
        monkeypatch.setattr(install.shutil, 'copy2', fail_copy)
    else:
        rename = Path.rename
        def fail_swap(self, other):
            if self.name == 'new':
                raise OSError('Injected swap failure')
            return rename(self, other)
        monkeypatch.setattr(Path, 'rename', fail_swap)
    with pytest.raises(OSError, match='Injected'):
        install.deploy(args('upgrade', project, source))
    assert snapshot(target) == before
    assert not list(target.parent.glob('.tao-dev-*'))


def test_failed_first_install_leaves_no_partial_destination(project, source, monkeypatch):
    def fail_copy(*_args, **_kwargs):
        raise OSError('Injected copy failure')
    monkeypatch.setattr(install.shutil, 'copy2', fail_copy)
    with pytest.raises(OSError, match='Injected'):
        install.deploy(args('install', project, source))
    assert list(project.iterdir()) == []


def test_lock_blocks_concurrent_writer_without_touching_existing_skill(project, source):
    install.deploy(args('install', project, source))
    target = destination(project, 'codex')
    before = snapshot(target)
    lock = target.parent / '.tao-dev-install.lock'
    lock.mkdir()
    with pytest.raises(install.InstallError, match='locked'):
        install.deploy(args('upgrade', project, source))
    assert snapshot(target) == before and lock.is_dir()


def test_list_is_read_only_and_scoped_to_explicit_project(project, source, tmp_path):
    other = tmp_path / 'other'
    other.mkdir()
    install.deploy(args('install', project, source))
    assert install.inventory(args('list', other))['installations'] == []
    assert list(other.iterdir()) == []


@pytest.mark.parametrize('option', ['--scope=user', '--all', '--yes', '--marketplace=a/b'])
def test_legacy_install_options_are_rejected(project, option):
    with pytest.raises(SystemExit):
        install.arguments(['install', '--project', str(project), '--client', 'codex', option])


def test_project_and_mutation_client_are_required():
    with pytest.raises(SystemExit):
        install.arguments(['install', '--client', 'codex'])
    with pytest.raises(SystemExit):
        install.arguments(['install', '--project', '.'])


def test_repository_source_resolves_only_new_skill_layout(project, source, tmp_path):
    repo = tmp_path / 'repository'
    (repo / 'skills').mkdir(parents=True)
    source.rename(repo / 'skills/tao-dev')
    install.deploy(args('install', project, repo))
    assert (destination(project, 'codex') / 'SKILL.md').is_file()


def test_metadata_is_project_local_and_portable(project, source):
    install.deploy(args('install', project, source))
    record = json.loads((destination(project, 'codex') / install.MARKER).read_text(encoding='utf-8'))
    assert record['schema'] == install.SCHEMA
    assert str(project) not in json.dumps(record)
    assert str(source) not in json.dumps(record)


def test_self_upgrade_excludes_ownership_record_from_payload(project, source):
    install.deploy(args('install', project, source))
    target = destination(project, 'codex')
    before = snapshot(target)
    install.deploy(args('upgrade', project, target))
    assert snapshot(target) == before


def test_destination_inside_source_is_rejected_without_writes(source):
    before = snapshot(source)
    with pytest.raises(install.InstallError, match='contain one another'):
        install.deploy(args('install', source, source))
    assert snapshot(source) == before
    assert not (source / '.agents').exists()


def test_failed_rollback_retains_old_tree_and_reports_recovery_path(project, source, monkeypatch):
    install.deploy(args('install', project, source))
    target = destination(project, 'codex')
    before = snapshot(target)
    rename = Path.rename
    def fail_replacement_and_restore(self, other):
        if self.name in ('new', 'previous'):
            raise OSError('Injected rename failure')
        return rename(self, other)
    monkeypatch.setattr(Path, 'rename', fail_replacement_and_restore)
    with pytest.raises(install.InstallError, match='Previous installation is retained at'):
        install.deploy(args('upgrade', project, source))
    recovery = list(target.parent.glob('.tao-dev-*/previous'))
    assert len(recovery) == 1
    assert snapshot(recovery[0]) == before
    assert not (target.parent / '.tao-dev-install.lock').exists()


def test_cleanup_failure_releases_lock_and_reports_committed_state(project, source, monkeypatch):
    def denied(_path):
        raise PermissionError("Injected cleanup denial")
    monkeypatch.setattr(install, "remove_owned_tree", denied)
    with pytest.raises(install.InstallError, match="committed; cleanup incomplete"):
        install.deploy(args("install", project, source))
    target = destination(project, "codex")
    assert not (target.parent / ".tao-dev-install.lock").exists()
    assert install.inventory(args("list", project))["installations"][0]["state"] == "installed"
    assert (target / "SKILL.md").read_bytes() == (source / "SKILL.md").read_bytes()


def test_readonly_owned_files_can_be_upgraded_and_uninstalled(project, source):
    entry = source / "SKILL.md"
    mode = entry.stat().st_mode
    entry.chmod(0o444)
    try:
        install.deploy(args("install", project, source))
        install.deploy(args("upgrade", project, source))
        install.uninstall(args("uninstall", project))
    finally:
        entry.chmod(mode)
    target = destination(project, "codex")
    assert not target.exists()
    assert not list(target.parent.glob(".tao-dev-*"))
