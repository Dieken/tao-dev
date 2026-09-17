"""Native adapter boundaries, with all client state isolated from personal data."""
import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / 'plugins/tao-dev/skills/tao-dev/scripts'
spec = importlib.util.spec_from_file_location('install_clients', SCRIPTS / 'install_clients.py')
clients = importlib.util.module_from_spec(spec)
if spec.loader:
    spec.loader.exec_module(clients)


@pytest.fixture
def state(tmp_path, monkeypatch):
    for variable, name in [('CODEX_HOME', 'codex'), ('CLAUDE_CONFIG_DIR', 'claude'),
                           ('XDG_CONFIG_HOME', 'xdg'), ('GIT_CONFIG_GLOBAL', 'gitconfig')]:
        monkeypatch.setenv(variable, str(tmp_path / name))
    project = tmp_path / 'project'
    project.mkdir()
    return tmp_path, project


def cache(root, marketplace='custom'):
    plugin = root / 'codex/plugins/cache' / marketplace / 'tao-dev/1.2.3'
    (plugin / '.codex-plugin').mkdir(parents=True)
    (plugin / '.codex-plugin/plugin.json').write_text(json.dumps({'name': 'tao-dev', 'version': '1.2.3'}), encoding='utf-8')
    return plugin


def test_discover_codex_only_enabled_scopes_and_arbitrary_marketplace(state):
    root, project = state
    plugin = cache(root)
    other = root / 'other'
    (other / '.codex').mkdir(parents=True)
    (project / '.codex').mkdir()
    (root / 'codex/config.toml').write_text('[plugins."tao-dev@custom"]\nenabled=false\n[projects.' + json.dumps(str(other)) + ']\ntrust_level="trusted"\n', encoding='utf-8')
    for folder in (project, other):
        (folder / '.codex/config.toml').write_text('[plugins."tao-dev@custom"]\nenabled=true\n[plugins."unrelated@custom"]\nenabled=true\n', encoding='utf-8')
    rows = clients.discover('codex', project)
    assert len(rows) == 2
    assert {row['project'] for row in rows} == {str(project), str(other)}
    assert {row['plugin_path'] for row in rows} == {str(plugin)}


def test_claude_discovery_preserves_all_native_scopes(state):
    root, project = state
    data = root / 'claude/plugins'
    data.mkdir(parents=True)
    (data / 'installed_plugins.json').write_text(json.dumps({'plugins': {
        'tao-dev@anything': [{'scope': 'local', 'projectPath': str(project), 'installPath': str(root/'cache'), 'version': '1'},
                             {'scope': 'user', 'installPath': str(root/'cache'), 'version': '1'}],
        'not-tao-dev@anything': [{'scope': 'user', 'installPath': '/unused'}]}}), encoding='utf-8')
    rows = clients.discover('claude', project)
    assert [row['scope'] for row in rows] == ['local', 'user']
    assert rows[1]['project'] is None


def test_codex_local_is_project_alias_even_with_tracked_config(state):
    root, project = state
    subprocess.run(['git', 'init', '-q', str(project)], check=True)
    (project / '.codex').mkdir()
    target = project / '.codex/config.toml'
    target.write_text('# team config\n', encoding='utf-8')
    subprocess.run(['git', '-C', str(project), 'add', '.codex/config.toml'], check=True)
    assert clients.validate_scope('codex', 'local', project) == 'project'
    assert target.read_text(encoding='utf-8') == '# team config\n'
    assert clients.validate_scope('claude', 'local', project) == 'local'


def test_codex_project_install_preserves_prior_user_activation(state, monkeypatch):
    root, project = state
    plugin = cache(root)
    (root / 'codex/config.toml').write_text('[plugins."tao-dev@custom"]\nenabled=true\n', encoding='utf-8')
    edits = []
    monkeypatch.setattr(clients, '_run', lambda *a, **kw: {'installedPath': str(plugin), 'marketplaceName': 'custom'})
    monkeypatch.setattr(clients, '_write_config', lambda path, values, **kw: edits.append((path, values)))
    monkeypatch.setattr(clients, '_trust_hook', lambda *a: [])
    monkeypatch.setattr(clients, '_verify_skills', lambda *a: {})
    result = clients.install_plugin('codex', 'owner/repo', 'tao-dev@custom', 'project', project)
    assert result['plugin_path'] == str(plugin)
    assert not any(value is False for path, values in edits for key, value in values if 'enabled' in key)


def test_codex_scope_removal_keeps_shared_cache_and_unrelated_config(state, monkeypatch):
    root, project = state
    cache(root)
    (root / 'codex/config.toml').write_text('[plugins."tao-dev@custom"]\nenabled=true\n', encoding='utf-8')
    (project / '.codex').mkdir()
    (project / '.codex/config.toml').write_text('[plugins."tao-dev@custom"]\nenabled=true\n', encoding='utf-8')
    edits = []
    monkeypatch.setattr(clients, '_write_config', lambda path, values, **kw: edits.append((path, values)))
    monkeypatch.setattr(clients, '_run', lambda *a, **kw: pytest.fail('Must preserve shared cache'))
    clients.remove_activation('codex', 'tao-dev@custom', 'user', project)
    assert edits == [(root/'codex/config.toml', [('plugins."tao-dev@custom".enabled', False)])]


def test_keep_activation_preserves_same_project_key(state, monkeypatch):
    _, project = state
    monkeypatch.setattr(clients, '_run', lambda *a, **kw: pytest.fail('Shared activation must remain'))
    monkeypatch.setattr(clients, '_write_config', lambda *a, **kw: pytest.fail('Shared activation must remain'))
    assert clients.remove_activation('codex', 'tao-dev@custom', 'local', project, keep_plugin=True, keep_activation=True)['files'] == []


def test_hook_trust_rejects_other_command(state, monkeypatch):
    root, project = state
    plugin = cache(root)
    hook = {'pluginId': 'tao-dev@custom', 'sourcePath': str(plugin/'com.openai/hooks/hooks.json'),
            'command': 'sh /unrelated hook', 'key': 'owned', 'currentHash': 'sha256:abc',
            'eventName': 'postToolUse', 'handlerType': 'command', 'matcher': 'Write|Edit|apply_patch',
            'timeoutSec': 35, 'enabled': True, 'isManaged': False}
    monkeypatch.setattr(clients, '_rpc', lambda *a, **kw: {'data': [{'cwd': str(project), 'hooks': [hook], 'errors': [], 'warnings': []}]})
    monkeypatch.setattr(clients, '_write_config', lambda *a, **kw: pytest.fail('Unreviewed hook must not be trusted'))
    with pytest.raises(ValueError, match='hook'):
        clients._trust_hook(project, 'tao-dev@custom', plugin)


def test_hook_trust_accepts_the_reported_path_spelling(state, monkeypatch):
    root, project = state
    plugin = cache(root)
    script = plugin / 'skills/tao-dev/scripts/hook.py'
    script.parent.mkdir(parents=True)
    script.write_text('', encoding='utf-8')
    # Codex substitutes ${PLUGIN_ROOT} in place, so the command keeps the
    # portable tail's separators instead of the platform's own spelling. The
    # duplicated separator stands in for the mixed separators a Windows
    # installation reports, which no POSIX path can reproduce.
    hook = {'pluginId': 'tao-dev@custom', 'sourcePath': str(plugin/'com.openai/hooks/hooks.json'),
            'command': f'python3 -I -B "{plugin}//skills/tao-dev/scripts/hook.py"',
            'key': 'tao-dev@custom:com.openai/hooks/hooks.json:post_tool_use:0:0',
            'currentHash': 'sha256:abc', 'eventName': 'postToolUse', 'handlerType': 'command',
            'matcher': 'Write|Edit|apply_patch', 'timeoutSec': 35, 'enabled': True, 'isManaged': False}
    calls = []

    def listed(method, params, cwd, **options):
        calls.append(method)
        trusted = dict(hook, trustStatus='trusted' if len(calls) > 1 else 'untrusted')
        return {'data': [{'cwd': str(project), 'hooks': [trusted], 'errors': [], 'warnings': []}]}

    edits = []
    monkeypatch.setattr(clients, '_rpc', listed)
    monkeypatch.setattr(clients, '_write_config', lambda path, values: edits.append((path, values)))
    config = clients._home('codex') / 'config.toml'
    assert clients._trust_hook(project, 'tao-dev@custom', plugin) == [str(config)]
    assert edits == [(config, [(clients._key('hooks', 'state', hook['key'], 'trusted_hash'), 'sha256:abc')])]


@pytest.mark.parametrize('client', ['claude', 'codex'])
def test_complete_install_binds_hook_to_exact_python(state, client):
    root, _ = state
    plugin = root / 'plugin with spaces'
    source = SCRIPTS.parents[2]
    import shutil
    shutil.copytree(source, plugin)
    python = root / 'Python Runtime/python3'
    clients._bind_hook(client, plugin, python)
    relative = 'hooks/hooks.json' if client == 'claude' else 'com.openai/hooks/hooks.json'
    hook = json.loads((plugin / relative).read_text(encoding='utf-8'))['hooks']['PostToolUse'][0]['hooks'][0]
    script = plugin / 'skills/tao-dev/scripts/hook.py'
    if client == 'claude':
        assert hook['command'] == str(python)
        assert hook['args'] == ['-I', '-B', str(script)]
    else:
        assert hook['command'] == clients._command_line([python, '-I', '-B', script])


def test_complete_install_refuses_extra_hook_behavior(state):
    root, _ = state
    plugin = root / 'plugin'
    import shutil
    shutil.copytree(SCRIPTS.parents[2], plugin)
    path = plugin / 'com.openai/hooks/hooks.json'
    definition = json.loads(path.read_text(encoding='utf-8'))
    definition['hooks']['PostToolUse'][0]['hooks'][0]['async'] = True
    path.write_text(json.dumps(definition), encoding='utf-8')
    with pytest.raises(clients.ClientError, match='unexpected'):
        clients._bind_hook('codex', plugin, root / 'python3')


def test_codex_native_add_failure_restores_user_boundary(state, monkeypatch):
    root, project = state
    cache(root)
    edits = []
    def native(args, *a, **kw):
        if args[1:3] == ['plugin', 'add']:
            raise clients.ClientError('partial native add failure')
        return {}
    monkeypatch.setattr(clients, '_run', native)
    monkeypatch.setattr(clients, '_write_config', lambda path, values, **kw: edits.append((path, values)))
    with pytest.raises(ValueError, match='partial'):
        clients.install_plugin('codex', 'owner/repo', 'tao-dev@custom', 'project', project)
    assert edits[-1] == (root/'codex/config.toml', [('plugins."tao-dev@custom".enabled', False)])


def test_discovery_does_not_follow_marketplace_cache_symlink(state):
    root, project = state
    plugin = cache(root)
    outside = root / 'outside-cache'
    (root / 'codex/plugins/cache/custom').rename(outside)
    (root / 'codex/plugins/cache/custom').symlink_to(outside, target_is_directory=True)
    (root / 'codex/config.toml').write_text('[plugins."tao-dev@custom"]\nenabled=true\n', encoding='utf-8')
    assert clients.discover('codex', project) == []


def native_enabled():
    import os
    return os.environ.get('TAO_TEST_NATIVE_CLIENTS') == '1'


@pytest.mark.skipif(not native_enabled(), reason='Set TAO_TEST_NATIVE_CLIENTS=1 for isolated installed-CLI probes')
def test_native_toml_editor_preserves_comments_and_deletes_only_selected_key(state):
    root, project = state
    config = project / '.codex/config.toml'
    config.parent.mkdir()
    original = '# team comment\ncustom = """multiline\ntext"""\n[plugins."other@catalog"]\nenabled=true\n'
    config.write_text(original, encoding='utf-8')
    clients._write_config(config, [('plugins."tao-dev@catalog".enabled', True)])
    assert '# team comment' in config.read_text(encoding='utf-8')
    clients._write_config(config, [('plugins."tao-dev@catalog"', None)])
    parsed = clients._config(config)
    assert parsed == {'custom': 'multiline\ntext', 'plugins': {'other@catalog': {'enabled': True}}}
    assert list(config.parent.iterdir()) == [config]


@pytest.mark.skipif(not native_enabled(), reason='Set TAO_TEST_NATIVE_CLIENTS=1 for isolated installed-CLI probes')
@pytest.mark.parametrize('client', ['claude', 'codex'])
def test_native_install_repeat_shared_scope_removal_and_outside_boundary(state, client):
    root, project = state
    outside = root / 'outside'
    outside.mkdir()
    source = SCRIPTS.parents[4]
    plugin_id = 'tao-dev@tao-dev'
    result = clients.install_plugin(client, str(source), plugin_id, 'project', project)
    cached = Path(result['plugin_path'])
    assert cached.is_relative_to(root)
    def active(folder):
        if client == 'codex':
            rows = clients._rpc('skills/list', {'cwds': [str(folder)], 'forceReload': True}, folder)['data']
            return any(skill.get('pluginId') == plugin_id and skill.get('enabled')
                       for row in rows for skill in row['skills'])
        return any(row['id'] == plugin_id and row['enabled'] for row in clients._run(['claude', 'plugin', 'list', '--json'], folder))
    assert active(project)
    assert not active(outside)
    again = clients.install_plugin(client, str(source), plugin_id, 'project', project)
    assert again['plugin_path'] == result['plugin_path']
    assert not active(outside)
    clients.install_plugin(client, str(source), plugin_id, 'user', project)
    assert active(outside)
    # Installing project again must preserve a separately enabled user scope.
    clients.install_plugin(client, str(source), plugin_id, 'project', project)
    assert active(outside)
    clients.remove_activation(client, plugin_id, 'user', project)
    assert cached.is_dir()
    assert active(project)
    assert not active(outside)
    clients.remove_activation(client, plugin_id, 'project', project)
    assert clients.discover(client, project) == []
    assert not active(project)


@pytest.mark.parametrize('manifest', ['plugin.json', '.claude-plugin/plugin.json'])
def test_discovery_accepts_previous_native_manifest_formats(state, manifest):
    root, project = state
    plugin = cache(root)
    current = plugin / '.codex-plugin/plugin.json'
    target = plugin / manifest
    target.parent.mkdir(exist_ok=True)
    current.rename(target)
    (root / 'codex/config.toml').write_text('[plugins."tao-dev@custom"]\nenabled=true\n', encoding='utf-8')
    assert clients.discover('codex', project)[0]['plugin_path'] == str(plugin)


@pytest.mark.parametrize('client', ['claude', 'codex'])
def test_source_conflict_is_rejected_before_native_update(state, monkeypatch, client):
    root, project = state
    if client == 'claude':
        (root / 'claude/plugins').mkdir(parents=True)
        (root / 'claude/plugins/known_marketplaces.json').write_text(json.dumps({'custom': {'source': {'source': 'directory', 'path': str(root/'old')}}}), encoding='utf-8')
    else:
        (root / 'codex').mkdir()
        (root / 'codex/config.toml').write_text('[marketplaces.custom]\nsource_type="local"\nsource=' + json.dumps(str(root/'old')) + '\n', encoding='utf-8')
    monkeypatch.setattr(clients, '_run', lambda *a, **kw: pytest.fail('Conflicting source must not be refreshed'))
    with pytest.raises(ValueError, match='different source'):
        clients.install_plugin(client, str(root/'new'), 'tao-dev@custom', 'project', project)


def test_failed_native_command_reports_partial_config_write(state, monkeypatch):
    root, project = state
    def native(*a, **kw):
        (root / 'codex/config.toml').write_text('[marketplaces.custom]\nsource_type="local"\nsource="/partial"\n', encoding='utf-8')
        raise clients.ClientError('partial catalog failure')
    monkeypatch.setattr(clients, '_run', native)
    with pytest.raises(clients.ClientError) as failure:
        clients.install_plugin('codex', '/source', 'tao-dev@custom', 'project', project)
    assert str(root/'codex/config.toml') in failure.value.files


@pytest.mark.parametrize('client', ['claude', 'codex'])
def test_ref_uses_native_marketplace_syntax(state, monkeypatch, client):
    root, project = state
    calls = []
    def native(args, *a, **kw):
        calls.append(args)
        raise clients.ClientError('stop after recording native arguments')
    monkeypatch.setattr(clients, '_run', native)
    source = 'https://github.com/example/catalog.git'
    with pytest.raises(ValueError, match='recording'):
        clients.install_plugin(client, source, 'tao-dev@custom', 'project', project, ref='release')
    if client == 'codex':
        assert calls[0][4:7] == [source, '--ref', 'release']
    else:
        assert calls[0][4] == source + '#release'


def test_disabled_user_cache_is_discovered_without_project_reference(state):
    root, project = state
    cache(root)
    (root / 'codex/config.toml').write_text('[plugins."tao-dev@custom"]\nenabled=false\n', encoding='utf-8')
    rows = clients.discover('codex', project)
    assert len(rows) == 1
    assert rows[0]['scope'] == 'user'
    assert rows[0]['enabled'] is False


def test_disabled_project_is_discovered_and_keeps_cache_on_user_removal(state, monkeypatch):
    root, project = state
    cache(root)
    (root / 'codex/config.toml').write_text('[plugins."tao-dev@custom"]\nenabled=true\n', encoding='utf-8')
    (project / '.codex').mkdir()
    (project / '.codex/config.toml').write_text('[plugins."tao-dev@custom"]\nenabled=false\n', encoding='utf-8')
    rows = clients.discover('codex', project)
    assert len(rows) == 2
    assert [row['enabled'] for row in rows] == [True, False]
    monkeypatch.setattr(clients, '_write_config', lambda *a, **kw: None)
    monkeypatch.setattr(clients, '_run', lambda *a, **kw: pytest.fail('Disabled project still references cache'))
    clients.remove_activation('codex', 'tao-dev@custom', 'user', project)
    (root / 'codex/config.toml').write_text('[plugins."tao-dev@custom"]\nenabled=false\n', encoding='utf-8')
    assert [row['scope'] for row in clients.discover('codex', project)] == ['project']


def test_deleted_claude_project_uninstall_only_removes_exact_registry_row(state, monkeypatch):
    root, project = state
    deleted = root / 'deleted-project'
    registry = root / 'claude/plugins/installed_plugins.json'
    registry.parent.mkdir(parents=True)
    plugin = root / 'claude/plugins/cache/custom/tao-dev/1'
    plugin.mkdir(parents=True)
    removed = {'scope': 'project', 'projectPath': str(deleted), 'installPath': str(plugin), 'version': '1'}
    retained = {'scope': 'project', 'projectPath': str(project), 'installPath': str(plugin), 'version': '1'}
    registry.write_text(json.dumps({'version': 2, 'plugins': {'tao-dev@custom': [removed, retained], 'other@custom': []}}), encoding='utf-8')
    monkeypatch.setattr(clients, '_run', lambda *a, **kw: pytest.fail('Cannot uninstall stale scope from another cwd'))
    clients.remove_activation('claude', 'tao-dev@custom', 'project', deleted)
    assert not deleted.exists()
    assert clients._read_json(registry) == {'version': 2, 'plugins': {'tao-dev@custom': [retained], 'other@custom': []}}
    assert plugin.is_dir()


def test_deleted_codex_project_uninstall_does_not_recreate_it_or_remove_shared_cache(state, monkeypatch):
    root, project = state
    plugin = cache(root)
    deleted = root / 'deleted-project'
    (root / 'codex/config.toml').write_text('[plugins."tao-dev@custom"]\nenabled=true\n', encoding='utf-8')
    monkeypatch.setattr(clients, '_run', lambda *a, **kw: pytest.fail('User scope still shares cache'))
    monkeypatch.setattr(clients, '_write_config', lambda *a, **kw: pytest.fail('Missing config must not be recreated'))
    clients.remove_activation('codex', 'tao-dev@custom', 'project', deleted)
    assert not deleted.exists()
    assert plugin.is_dir()


def test_late_install_error_exposes_attempted_cache(state, monkeypatch):
    root, project = state
    plugin = cache(root)
    monkeypatch.setattr(clients, '_run', lambda *a, **kw: {'installedPath': str(plugin), 'marketplaceName': 'custom'})
    monkeypatch.setattr(clients, '_write_config', lambda *a, **kw: None)
    def reject(*a):
        raise clients.ClientError('hook verification failed')
    monkeypatch.setattr(clients, '_trust_hook', reject)
    with pytest.raises(clients.ClientError) as failure:
        clients.install_plugin('codex', 'owner/repo', 'tao-dev@custom', 'project', project)
    assert failure.value.plugin_path == str(plugin)


@pytest.mark.skipif(not native_enabled(), reason='Set TAO_TEST_NATIVE_CLIENTS=1 for isolated installed-CLI probes')
@pytest.mark.parametrize('client', ['claude', 'codex'])
def test_native_failed_upgrade_rollback_restores_prior_cache_and_activation(state, client):
    import shutil
    root, project = state
    source = root / 'catalog'
    plugin_source = source / 'plugin'
    shutil.copytree(SCRIPTS.parents[2], plugin_source, ignore=shutil.ignore_patterns('__pycache__'))
    (source / '.agents/plugins').mkdir(parents=True)
    (source / '.claude-plugin').mkdir()
    (source / '.agents/plugins/marketplace.json').write_text(json.dumps({
        'name': 'rollback-test', 'plugins': [{'name': 'tao-dev', 'source': {'source': 'local', 'path': './plugin'},
                                           'policy': {'installation': 'AVAILABLE', 'authentication': 'ON_INSTALL'},
                                           'category': 'Productivity'}]}), encoding='utf-8')
    (source / '.claude-plugin/marketplace.json').write_text(json.dumps({
        'name': 'rollback-test', 'owner': {'name': 'Test'}, 'plugins': [{'name': 'tao-dev', 'source': './plugin'}]}), encoding='utf-8')
    def version(value):
        for name in ('.codex-plugin/plugin.json', '.claude-plugin/plugin.json'):
            manifest = plugin_source / name
            data = json.loads(manifest.read_text(encoding='utf-8'))
            data['version'] = value
            manifest.write_text(json.dumps(data), encoding='utf-8')
    plugin_id = 'tao-dev@rollback-test'
    version('1.0.0')
    before = clients.install_plugin(client, str(source), plugin_id, 'project', project)
    snapshot = clients.snapshot_activation(client, plugin_id, 'project', project)
    previous_cache = Path(before['plugin_path'])
    backup = root / 'previous-cache'
    shutil.copytree(previous_cache, backup)
    version('2.0.0')
    attempted = clients.install_plugin(client, str(source), plugin_id, 'project', project)
    assert attempted['version'] == '2.0.0'
    # Caller restores old source/cache bytes before the adapter restores keys.
    version('1.0.0')
    if previous_cache.exists():
        shutil.rmtree(previous_cache)
    shutil.copytree(backup, previous_cache)
    unrelated = root / client / ('config.toml' if client == 'codex' else 'settings.json')
    if client == 'codex':
        clients._write_config(unrelated, [('test_preserve', 'unrelated')])
    else:
        data = clients._read_json(unrelated)
        data['test_preserve'] = 'unrelated'
        unrelated.write_text(json.dumps(data), encoding='utf-8')
    clients.restore_activation(snapshot, attempted_plugin_path=attempted['plugin_path'])
    assert previous_cache.is_dir()
    assert not Path(attempted['plugin_path']).exists()
    rows = clients.discover(client, project)
    assert len(rows) == 1
    assert rows[0]['plugin_path'] == str(previous_cache)
    if client == 'codex':
        clients._verify_skills(project, plugin_id, previous_cache)
        assert clients._config(unrelated)['test_preserve'] == 'unrelated'
    else:
        native = clients._run(['claude', 'plugin', 'list', '--json'], project)
        assert native[0]['enabled'] is True
        assert native[0]['installPath'] == str(previous_cache)
        assert clients._read_json(unrelated)['test_preserve'] == 'unrelated'


def test_deleted_codex_project_final_removal_uses_existing_neutral_cwd(state, monkeypatch):
    root, project = state
    deleted = root / 'deleted'
    cache(root)
    (root / 'codex/config.toml').write_text('[plugins."tao-dev@custom"]\nenabled=true\n', encoding='utf-8')
    monkeypatch.setattr(clients, '_write_config', lambda *a, **kw: None)
    seen = []
    def native(args, cwd, **kwargs):
        assert Path(cwd).is_dir()
        assert Path(cwd) != project
        seen.append(args)
        return {}
    monkeypatch.setattr(clients, '_run', native)
    clients.remove_activation('codex', 'tao-dev@custom', 'user', deleted)
    assert seen == [['codex', 'plugin', 'remove', 'tao-dev@custom', '--json']]
    assert not deleted.exists()


def test_rollback_without_native_mutation_does_not_report_problem(state):
    root, project = state
    snapshot = clients.snapshot_activation('codex', 'tao-dev@custom', 'project', project)
    restored = clients.restore_activation(snapshot)
    assert restored == {'files': [], 'warnings': []}


@pytest.mark.parametrize('client', ['claude', 'codex'])
def test_uninstall_after_registration_rollback_is_idempotent(state, monkeypatch, client):
    root, project = state
    monkeypatch.setattr(clients, '_run', lambda *a, **kw: pytest.fail('No selected native registration remains'))
    monkeypatch.setattr(clients, '_write_config', lambda *a, **kw: None)
    clients.remove_activation(client, 'tao-dev@custom', 'project', project)
    clients.remove_activation(client, 'tao-dev@custom', 'project', project)


def test_missing_claude_registration_still_cleans_only_selected_settings_key(state, monkeypatch):
    root, project = state
    config = project / '.claude/settings.json'
    config.parent.mkdir()
    config.write_text(json.dumps({'enabledPlugins': {'tao-dev@custom': True, 'other@catalog': True}, 'unrelated': 5}), encoding='utf-8')
    monkeypatch.setattr(clients, '_run', lambda *a, **kw: pytest.fail('Registry already removed'))
    clients.remove_activation('claude', 'tao-dev@custom', 'project', project)
    assert clients._read_json(config) == {'enabledPlugins': {'other@catalog': True}, 'unrelated': 5}
