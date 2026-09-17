"""Installer contracts: source snapshots, selection, ownership and reporting."""

import json
from pathlib import Path
import subprocess
import sys

import pytest

import installation as install
import installed_runtime as state


@pytest.mark.parametrize('scope', ['repo', 'project', 'local'])
def test_codex_scope_aliases_have_one_identity(scope, tmp_path):
    args = install.arguments(['install', '--client', 'codex', '--scope', scope, '--project', str(tmp_path)])
    assert args.scope == 'project'
    assert state.install_id('codex', args.scope, tmp_path) == state.install_id('codex', 'project', tmp_path)


def test_automatic_uninstall_requires_one_explicit_id():
    with pytest.raises(SystemExit):
        install.arguments(['uninstall', '--client', 'claude', '--yes'])


def test_source_modes_are_exclusive():
    with pytest.raises(SystemExit):
        install.arguments(['install', '--client', 'codex', '--source', '.', '--marketplace', 'a/b'])


def test_dependency_preparation_invokes_one_complete_setup(monkeypatch, tmp_path):
    calls = []
    report = {'status': 'passed', 'outputs': {'runtime': {
        'state': 'ready', 'mode': 'core',
        'publication': {'state': 'ready', 'mode': 'publication'},
    }}}

    def run(argv, **_kwargs):
        calls.append([str(value) for value in argv])
        return json.dumps(report)

    monkeypatch.setattr(install, 'run', run)
    prepared = install.prepare(install.PLUGIN, Path(sys.executable), tmp_path / 'runtime', tmp_path, None)
    assert len(calls) == 1
    assert '--publication' not in calls[0]
    assert calls[0][calls[0].index('--timeout') + 1] == '300'
    assert [item['mode'] for item in prepared] == ['core', 'publication']
    assert 'publication' not in prepared[0]


def test_empty_selection_and_eof_do_not_delete(monkeypatch):
    args = install.arguments(['uninstall', '--client', 'codex'])
    monkeypatch.setattr('builtins.input', lambda *_: '')
    assert install.choose([{'id': 'x'}], args) is None
    def eof(*_):
        raise EOFError
    monkeypatch.setattr('builtins.input', eof)
    assert install.choose([{'id': 'x'}], args) is None


def test_changed_local_content_gets_new_native_cache_version(tmp_path):
    source = tmp_path / 'source'
    install.copy_plugin(install.PLUGIN, source)
    one, _ = install.local_catalog(source, tmp_path / 'one', 'codex', 'test')
    two, _ = install.local_catalog(source, tmp_path / 'two', 'codex', 'test')
    path = '.codex-plugin/plugin.json'
    assert json.loads((one / path).read_text(encoding='utf-8'))['version'] == json.loads((two / path).read_text(encoding='utf-8'))['version']
    (source / 'skills/tao-dev/SKILL.md').write_text('changed local work directory', encoding='utf-8')
    three, _ = install.local_catalog(source, tmp_path / 'three', 'codex', 'test')
    assert json.loads((one / path).read_text(encoding='utf-8'))['version'] != json.loads((three / path).read_text(encoding='utf-8'))['version']


def test_sources_cannot_escape_catalog_or_follow_links(tmp_path):
    marketplace = tmp_path / 'market'
    (marketplace / '.agents/plugins').mkdir(parents=True)
    (marketplace / '.agents/plugins/marketplace.json').write_text(json.dumps({
        'name': 'bad', 'plugins': [{'name': 'tao-dev', 'source': '../outside'}]}), encoding='utf-8')
    with pytest.raises(install.InstallError, match='inside'):
        install.catalog_plugin(marketplace, 'codex')
    (marketplace / 'link').symlink_to(tmp_path)
    with pytest.raises(install.InstallError, match='symbolic'):
        install.copy_plugin(marketplace, tmp_path / 'copy')


def test_owned_root_never_replaces_existing_user_directory(tmp_path):
    root = tmp_path / 'existing'
    root.mkdir()
    (root / 'notes.txt').write_text('mine', encoding='utf-8')
    with pytest.raises(install.InstallError, match='ownership'):
        install.owned_root(root, 'test')
    assert (root / 'notes.txt').read_text(encoding='utf-8') == 'mine'


def test_removal_preserves_unknown_files_and_external_symlink_targets(tmp_path, monkeypatch):
    monkeypatch.setenv('CODEX_HOME', str(tmp_path / 'codex'))
    identifier = state.install_id('codex', 'project', tmp_path)
    root = state.managed_root('codex', 'project', tmp_path)
    install.owned_root(root, identifier)
    (root / 'runtime').mkdir()
    outside = tmp_path / 'precious'
    outside.mkdir()
    (outside / 'notes').write_text('mine', encoding='utf-8')
    (root / 'runtime/link').symlink_to(outside)
    (root / 'notes.txt').write_text('keep this unknown file', encoding='utf-8')
    paths, warnings = install.remove_owned({'id': identifier, 'client': 'codex', 'scope': 'project',
                                            'project': str(tmp_path), 'managed_root': str(root)})
    assert paths == [str(root / 'runtime')]
    assert warnings and (root / 'notes.txt').is_file() and (outside / 'notes').read_text(encoding='utf-8') == 'mine'


def test_report_collapses_fully_owned_directory(tmp_path):
    owned = tmp_path / 'runtime'
    owned.mkdir()
    shared = tmp_path / 'config.toml'
    assert set(install.collapse_paths([str(owned), str(owned / 'a/b'), str(shared)])) == {str(owned), str(shared)}


def test_shared_cli_binding_uses_current_installation(tmp_path, monkeypatch):
    monkeypatch.setenv('CODEX_HOME', str(tmp_path / 'codex'))
    monkeypatch.setenv('TAO_CLI_DIR', str(tmp_path / 'shared'))
    identifier = state.install_id('codex', 'user', None)
    owned = state.managed_root('codex', 'user', None)
    plugin = tmp_path / 'codex/plugins/cache/test/tao-dev/1.0.0'
    cli = state.cli_root()
    row = dict(schema=1, id=identifier, client='codex', scope='user', project=None,
               managed_root=str(owned), plugin_id='tao-dev@test', plugin_path=str(plugin),
               plugin_base=str(plugin.parent), python=sys.executable, runtime_dir=str(owned / 'runtime'),
               version='1.0.0', source={}, status='ready', files=[], cli_path=str(cli))
    state.save_record(row)
    assert state.binding(cli / 'skills/tao-dev/scripts', tmp_path)['id'] == identifier


@pytest.mark.parametrize('failure_stage', ['prepare', 'doctor', 'cli'])
@pytest.mark.parametrize('managed', [True, False])
def test_failed_upgrade_restores_source_cache_receipt_and_cli(tmp_path, monkeypatch, failure_stage, managed):
    import install_clients as clients
    import runtime
    monkeypatch.setenv('CODEX_HOME', str(tmp_path / 'codex'))
    monkeypatch.setenv('TAO_CLI_DIR', str(tmp_path / 'shared'))
    args = install.arguments(['install', '--client', 'codex', '--scope', 'project',
                              '--project', str(tmp_path), '--source', str(install.PLUGIN),
                              '--bin-dir', str(tmp_path / 'bin')])
    identifier = state.install_id('codex', 'project', tmp_path)
    root = state.managed_root('codex', 'project', tmp_path)
    install.owned_root(root, identifier)
    _, plugin_id = install.local_catalog(install.PLUGIN, root / 'marketplace', 'codex', identifier)
    (root / 'marketplace/old-source').write_text('previous source', encoding='utf-8')
    base = tmp_path / 'codex/plugins/cache' / plugin_id.split('@')[1] / 'tao-dev'
    old_cache, new_cache = base / 'old', base / 'new'
    install.copy_plugin(install.PLUGIN, old_cache)
    launcher, cli = install.install_cli(Path(sys.executable), tmp_path / 'bin', old_cache)
    old_launcher = launcher.read_bytes()
    (cli / 'old-cli').write_text('previous CLI', encoding='utf-8')
    previous = dict(schema=1, id=identifier, client='codex', scope='project', project=str(tmp_path),
                    managed_root=str(root), plugin_id=plugin_id, plugin_path=str(old_cache),
                    plugin_base=str(base), python=sys.executable, runtime_dir=str(root / 'runtime'),
                    version='old', source={'kind': 'source', 'location': str(install.PLUGIN)}, status='ready',
                    files=[], launcher=str(launcher), cli_path=str(cli))
    if managed:
        state.save_record(previous)
    monkeypatch.setattr(runtime, 'inspect_python', lambda *_: None)
    monkeypatch.setattr(install.shutil, 'which', lambda name: name)
    monkeypatch.setattr(install, 'run', lambda *_args, **_kwargs: '')
    monkeypatch.setattr(clients, 'snapshot_activation', lambda *_: {'previous': True, 'cache_paths': [str(old_cache)]}, raising=False)
    restored = []
    def restore(snapshot, **kwargs):
        assert (root / 'marketplace/old-source').read_text(encoding='utf-8') == 'previous source'
        assert (old_cache / 'skills/tao-dev/scripts/tao.py').is_file()
        restored.append((snapshot, kwargs))
    monkeypatch.setattr(clients, 'restore_activation', restore, raising=False)
    def native(*_args, **_kwargs):
        install.shutil.rmtree(old_cache)  # Native upgrade can retire an old cache.
        install.copy_plugin(install.PLUGIN, new_cache)
        return dict(plugin_path=str(new_cache), plugin_base=str(base), version='new', files=[])
    monkeypatch.setattr(clients, 'install_plugin', native)
    calls = []
    def prepare(*_args):
        calls.append(True)
        if failure_stage == 'prepare' and len(calls) == 2:
            raise install.InstallError('injected prepare failure')
        return []
    monkeypatch.setattr(install, 'prepare', prepare)
    def fail(*_args):
        raise install.InstallError('injected failure')
    monkeypatch.setattr(install, 'doctor', fail if failure_stage == 'doctor' else lambda *_: {})
    if failure_stage == 'cli':
        monkeypatch.setattr(install, 'install_cli', fail)
    with pytest.raises(install.InstallError, match='injected'):
        install.install(args)
    assert restored and restored[0][1]['attempted_plugin_path'] == str(new_cache)
    if managed:
        assert state.records('codex') == [previous]
    else:
        assert state.records('codex')[0]['status'] == 'preparing'
    assert (root / 'marketplace/old-source').read_text(encoding='utf-8') == 'previous source'
    assert not (root / '.marketplace-previous').exists()
    assert launcher.read_bytes() == old_launcher and (cli / 'old-cli').is_file()


def test_launcher_write_failure_keeps_previous_shared_cli(tmp_path, monkeypatch):
    monkeypatch.setenv('TAO_CLI_DIR', str(tmp_path / 'shared'))
    launcher, cli = install.install_cli(Path(sys.executable), tmp_path / 'bin', install.PLUGIN)
    # The rollback is only reachable when the launcher content actually changes.
    with launcher.open('a', encoding='utf-8', newline='') as stream:
        stream.write('# stale\n')
    original = launcher.read_bytes()
    (cli / 'previous').write_text('keep', encoding='utf-8')
    def fail(*_args):
        raise OSError('injected launcher failure')
    monkeypatch.setattr(install.os, 'replace', fail)
    with pytest.raises(OSError, match='injected'):
        install.install_cli(Path(sys.executable), tmp_path / 'bin', install.PLUGIN)
    assert launcher.read_bytes() == original and (cli / 'previous').read_text(encoding='utf-8') == 'keep'


def receipt(tmp_path, monkeypatch):
    home = tmp_path / 'client'
    project = tmp_path / 'project'
    monkeypatch.setenv('CLAUDE_CONFIG_DIR', str(home))
    identifier = 'claude-local-abcdef0123456789'
    cache = home / 'plugins/cache' / f'tao-dev-{identifier}' / 'tao-dev'
    return {
        'id': identifier, 'client': 'claude', 'scope': 'local', 'project': str(project),
        'plugin_id': f'tao-dev@tao-dev-{identifier}', 'version': '0.5.0',
        'managed_root': str(project / '.local/tao-dev/claude/local'),
        'plugin_path': str(cache / '0.5.0'), 'plugin_base': str(cache),
        'cli_path': str(tmp_path / 'shared/cli'), 'launcher': str(tmp_path / 'bin/tao'),
        'files': [str(home / 'plugins/installed_plugins.json'),
                  str(home / 'plugins/known_marketplaces.json'),
                  str(tmp_path / 'shared/cli'), str(tmp_path / 'bin/tao'),
                  str(home / f'tao-dev/installations/{identifier}.json'),
                  str(project / '.claude/settings.local.json'), str(cache),
                  str(project / '.git/info/exclude'),
                  str(project / '.local/tao-dev/claude/local')],
    }


def test_planned_actions_separate_owned_edited_and_retained_paths(tmp_path, monkeypatch):
    row = receipt(tmp_path, monkeypatch)
    actions = install.planned_actions(row, [row])
    assert [actions[path] for path in row['files']] == [
        'modify', 'keep', 'keep', 'keep', 'delete', 'modify', 'client', 'keep', 'delete']
    shared = dict(row, id='claude-project-0123456789abcdef')
    assert install.planned_actions(row, [row, shared])[row['plugin_base']] == 'keep'


def test_inventory_annotates_every_listed_path_with_a_legend(tmp_path, monkeypatch, capsys):
    row = receipt(tmp_path, monkeypatch)
    row['file_actions'] = install.planned_actions(row, [row])
    install.print_inventory([row])
    printed = capsys.readouterr().out
    assert all(f'{path}  [{action}]' in printed for path, action in row['file_actions'].items())
    assert printed.rstrip().splitlines()[-1].startswith('Removal legend: delete = ')


def test_cancelled_removal_is_reported_as_cancelled(tmp_path, monkeypatch, capsys):
    row = receipt(tmp_path, monkeypatch)
    monkeypatch.setattr(install, 'discover', lambda *_args: [row])
    monkeypatch.setattr('builtins.input', lambda *_args: '')
    code = install.main(['uninstall', '--client', 'claude', '--project', str(tmp_path)])
    printed = capsys.readouterr().out
    assert code == 0
    assert 'tao uninstall: cancelled' in printed
    assert 'Removed or updated' not in printed


def test_child_diagnostic_survives_the_installer_layer():
    report = {'status': 'not_run', 'outputs': {},
              'diagnostics': [{'message': 'Preparation exceeded its time limit; raise --timeout.'}]}
    completed = subprocess.CompletedProcess([], 2, json.dumps(report), None)
    assert install.detail(completed) == report['diagnostics'][0]['message']
    assert install.detail(subprocess.CompletedProcess([], 2, 'plain', 'stderr text')) == 'stderr text'


def test_unchanged_launcher_is_not_rewritten_during_an_upgrade(tmp_path, monkeypatch):
    monkeypatch.setenv('TAO_CLI_DIR', str(tmp_path / 'shared'))
    launcher, _cli = install.install_cli(Path(sys.executable), tmp_path / 'bin', install.PLUGIN)
    before = launcher.stat().st_mtime_ns, launcher.read_bytes()
    def refuse(*_args, **_kwargs):
        raise AssertionError('a running launcher must not be replaced without a change')
    monkeypatch.setattr(install.tempfile, 'mkstemp', refuse)
    install.install_cli(Path(sys.executable), tmp_path / 'bin', install.PLUGIN)
    assert (launcher.stat().st_mtime_ns, launcher.read_bytes()) == before


def stored(tmp_path, scope='project', project=None):
    identifier = state.install_id('codex', scope, project)
    root = state.managed_root('codex', scope, project)
    base = tmp_path / 'cache/tao-dev'
    return dict(schema=1, id=identifier, client='codex', scope=scope,
                project=str(project) if project else None, managed_root=str(root),
                plugin_id='tao-dev@test', plugin_path=str(base / '1.0'), plugin_base=str(base),
                python=sys.executable, runtime_dir=str(root / 'runtime'), version='1.0',
                source={'kind': 'source', 'location': str(tmp_path / 'origin')}, status='ready', files=[])


def test_upgrade_renews_a_recorded_installation_and_never_creates_one(tmp_path, monkeypatch):
    monkeypatch.setenv('CODEX_HOME', str(tmp_path / 'codex'))
    project = tmp_path / 'work'
    project.mkdir()
    args = install.arguments(['upgrade', '--client', 'codex', '--project', str(tmp_path)])
    with pytest.raises(install.InstallError, match='tao list'):
        install.upgrade(args)
    state.save_record(stored(tmp_path, 'project', project))
    captured = []
    def record_args(selected):
        captured.append(selected)
        return {'installation': {}}
    monkeypatch.setattr(install, 'install', record_args)
    install.upgrade(args)
    assert captured[0].scope == 'project' and captured[0].project == project
    assert captured[0].source is None and captured[0].marketplace is None and captured[0].bin_dir is None
    state.save_record(stored(tmp_path, 'user'))
    with pytest.raises(install.InstallError, match='--id'):
        install.upgrade(args)
    install.upgrade(install.arguments(['upgrade', '--client', 'codex', '--project', str(tmp_path),
                                       '--id', state.install_id('codex', 'user', None)]))
    assert captured[1].scope == 'user' and captured[1].project == tmp_path


def test_list_reports_installations_without_offering_removal(tmp_path, monkeypatch, capsys):
    row = receipt(tmp_path, monkeypatch)
    monkeypatch.setattr(install, 'discover', lambda *_args: [row])
    monkeypatch.setattr('builtins.input', lambda *_args: pytest.fail('list must not prompt'))
    code = install.main(['list', '--client', 'claude', '--project', str(tmp_path)])
    printed = capsys.readouterr().out
    assert code == 0 and 'tao list: passed' in printed
    assert f"{row['files'][0]}  [modify]" in printed and 'Removal legend: ' in printed


def test_shared_cli_lives_outside_every_client_home(tmp_path, monkeypatch):
    monkeypatch.setenv('CODEX_HOME', str(tmp_path / 'codex'))
    monkeypatch.setenv('CLAUDE_CONFIG_DIR', str(tmp_path / 'claude'))
    monkeypatch.setenv('TAO_CLI_DIR', str(tmp_path / 'shared'))
    launcher, root = install.install_cli(Path(sys.executable), tmp_path / 'bin', install.PLUGIN)
    assert root == (tmp_path / 'shared/cli').resolve()
    assert not (tmp_path / 'claude/tao-dev').exists() and not (tmp_path / 'codex/tao-dev').exists()
    assert str(root) in launcher.read_text(encoding='utf-8')
    assert state.shared_cli(root / 'skills/tao-dev/scripts')

