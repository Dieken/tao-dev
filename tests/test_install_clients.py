"""Native adapter boundaries, with all client state isolated from personal data."""
import importlib.util
import json
import subprocess
import sys
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
                           ('CURSOR_CONFIG_DIR', 'cursor'), ('KIRO_HOME', 'kiro'),
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


@pytest.mark.parametrize('initially_enabled', [True, False])
def test_claude_local_upgrade_uses_native_activation_state(state, monkeypatch, initially_enabled):
    root, project = state
    plugin_id = 'tao-dev@custom'
    home = root / 'claude'
    cache = home / 'plugins/cache/custom/tao-dev/1.2.3'
    cache.mkdir(parents=True)
    registry = home / 'plugins/installed_plugins.json'
    registry.write_text(json.dumps({'plugins': {plugin_id: [{
        'scope': 'local', 'projectPath': str(project),
        'installPath': str(cache), 'version': '1.2.3'}]}}), encoding='utf-8')
    (home / 'plugins/known_marketplaces.json').write_text(json.dumps({
        'custom': {'source': {'source': 'directory', 'path': str(root / 'source')}}
    }), encoding='utf-8')
    commands = []
    enabled = initially_enabled

    def native(args, cwd, **kwargs):
        nonlocal enabled
        commands.append(args)
        if args[1:3] == ['plugin', 'enable']:
            assert not enabled, 'Claude rejects enable when local scope is already enabled'
            enabled = True
        if args[1:3] == ['plugin', 'list']:
            return [{'id': plugin_id, 'scope': 'local', 'projectPath': str(root / 'other'),
                     'enabled': True},
                    {'id': plugin_id, 'scope': 'local', 'projectPath': str(project),
                     'enabled': enabled}]
        if args[1:3] == ['plugin', 'details']:
            return 'Skills (1)\nHooks (1)'
        return ''

    monkeypatch.setattr(clients, '_run', native)
    result = clients.install_plugin('claude', str(root / 'source'), plugin_id, 'local', project)
    assert result['verification']['native_plugin_enabled']
    assert [args[1:3] for args in commands].count(['plugin', 'enable']) == (0 if initially_enabled else 1)


def test_codex_local_is_project_alias_even_with_tracked_config(state):
    root, project = state
    subprocess.run(['git', 'init', '-q', str(project)], check=True)
    (project / '.codex').mkdir()
    target = project / '.codex/config.toml'
    target.write_text('# team config\n', encoding='utf-8')
    subprocess.run(['git', '-C', str(project), 'add', '.codex/config.toml'], check=True)
    assert clients.validate_scope('codex', 'local', project) == 'project'
    assert clients.validate_scope('cursor', 'local', project) == 'project'
    assert target.read_text(encoding='utf-8') == '# team config\n'
    assert clients.validate_scope('claude', 'local', project) == 'local'


def _cursor_marketplace(root):
    import sys
    marketplace = root / 'marketplace'
    plugin = marketplace / 'plugins/tao-dev'
    (plugin / '.cursor-plugin').mkdir(parents=True)
    (plugin / 'com.cursor/hooks').mkdir(parents=True)
    (plugin / 'com.cursor/agents').mkdir(parents=True)
    (plugin / 'com.cursor/commands').mkdir(parents=True)
    (plugin / 'skills/tao-dev/scripts').mkdir(parents=True)
    (plugin / '.cursor-plugin/plugin.json').write_text(
        json.dumps({'name': 'tao-dev', 'version': '1.2.3', 'description': 'test',
                    'skills': './skills/', 'hooks': './com.cursor/hooks/hooks.json',
                    'agents': './com.cursor/agents/', 'commands': './com.cursor/commands/'}),
        encoding='utf-8')
    (plugin / 'com.cursor/hooks/hooks.json').write_text(json.dumps({
        'version': 1,
        'hooks': {'postToolUse': [{'command': 'python3 -I -B "${CURSOR_PLUGIN_ROOT}/skills/tao-dev/scripts/hook.py"',
                                   'matcher': 'Write|Edit', 'timeout': 35}]}
    }), encoding='utf-8')
    (plugin / 'skills/tao-dev/scripts/hook.py').write_text('print("ok")\n', encoding='utf-8')
    (marketplace / '.cursor-plugin').mkdir(parents=True)
    (marketplace / '.cursor-plugin/marketplace.json').write_text(json.dumps({
        'name': 'custom', 'owner': {'name': 'tao-dev'},
        'plugins': [{'name': 'tao-dev', 'source': './plugins/tao-dev'}]
    }), encoding='utf-8')
    return marketplace, Path(sys.executable)


def test_cursor_user_install_publishes_local_plugin(state):
    root, project = state
    marketplace, python = _cursor_marketplace(root)
    result = clients.install_plugin('cursor', str(marketplace), 'tao-dev@custom', 'user', project, python=python)
    local = root / 'cursor/plugins/local/tao-dev'
    assert Path(result['plugin_path']) == local
    assert (local / '.tao-owned.json').is_file()
    assert (local / '.cursor-plugin/plugin.json').is_file()
    hook = json.loads((local / 'com.cursor/hooks/hooks.json').read_text(encoding='utf-8'))
    command = hook['hooks']['postToolUse'][0]['command']
    assert 'CURSOR_PLUGIN_ROOT' not in command
    assert str(local / 'skills/tao-dev/scripts/hook.py') in command
    rows = clients.discover('cursor', project)
    assert any(row['scope'] == 'user' and row['plugin_path'] == str(local) for row in rows)


def test_cursor_project_install_writes_settings(state):
    root, project = state
    marketplace, python = _cursor_marketplace(root)
    result = clients.install_plugin('cursor', str(marketplace), 'tao-dev@custom', 'local', project, python=python)
    assert result['version'] == '1.2.3'
    settings = json.loads((project / '.cursor/settings.json').read_text(encoding='utf-8'))
    assert settings['plugins']['custom/tao-dev']['enabled'] is True
    assert not (root / 'cursor/plugins/local/tao-dev').exists()
    rows = clients.discover('cursor', project)
    assert any(row['scope'] == 'project' and row['project'] == str(project) for row in rows)
    clients.remove_activation('cursor', 'tao-dev@custom', 'project', project)
    assert not (project / '.cursor/settings.json').exists()


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
    relative = 'com.anthropic/hooks/hooks.json' if client == 'claude' else 'com.openai/hooks/hooks.json'
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


def _require_native(*clients_needed):
    import native_clients
    for client in clients_needed:
        native_clients.require_cli(client)


def test_config_editor_stages_existing_config_after_startup(state, monkeypatch):
    _, project = state
    config = project / 'config.toml'
    config.write_text('# preserved\n', encoding='utf-8')

    def edit(method, params, cwd, *, home):
        target = Path(params['filePath'])
        assert method == 'config/batchWrite'
        assert target == Path(cwd) / 'config.toml'
        assert home == target.parent
        assert target.read_text(encoding='utf-8') == '# preserved\n'
        target.write_text('# preserved\nenabled = true\n', encoding='utf-8')

    monkeypatch.setattr(clients, '_rpc', edit)
    clients._write_config(config, [('enabled', True)])
    assert config.read_text(encoding='utf-8') == '# preserved\nenabled = true\n'


def test_native_toml_editor_preserves_comments_and_deletes_only_selected_key(state):
    _require_native('codex')
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


@pytest.mark.parametrize(('client', 'scope'), [('claude', 'project'), ('claude', 'local'),
                                                  ('codex', 'project'), ('cursor', 'project'),
                                                  ('kiro', 'project')])
def test_native_install_repeat_shared_scope_removal_and_outside_boundary(state, client, scope):
    _require_native(client)
    root, project = state
    outside = root / 'outside'
    outside.mkdir()
    source = SCRIPTS.parents[4]
    plugin_id = 'tao-dev@tao-dev'
    options = {'python': Path(sys.executable)} if client == 'kiro' else {}
    result = clients.install_plugin(client, str(source), plugin_id, scope, project, **options)
    cached = Path(result['plugin_path'])
    assert cached.is_relative_to(root)

    def active(folder):
        if client == 'codex':
            rows = clients._rpc('skills/list', {'cwds': [str(folder)], 'forceReload': True}, folder)['data']
            return any(skill.get('pluginId') == plugin_id and skill.get('enabled')
                       for row in rows for skill in row['skills'])
        if client in ('cursor', 'kiro'):
            return any(row['plugin_id'] == plugin_id and row['enabled'] and row['scope'] in ('user', 'project')
                       for row in clients.discover(client, folder)
                       if row['scope'] == 'user' or row['project'] == str(folder))
        return any(row['id'] == plugin_id and row['enabled']
                   for row in clients._run(['claude', 'plugin', 'list', '--json'], folder))

    assert active(project)
    assert not active(outside)
    again = clients.install_plugin(client, str(source), plugin_id, scope, project, **options)
    assert again['plugin_path'] == result['plugin_path']
    assert not active(outside)
    clients.install_plugin(client, str(source), plugin_id, 'user', project, **options)
    assert active(outside)
    # Installing project again must preserve a separately enabled user scope.
    clients.install_plugin(client, str(source), plugin_id, scope, project, **options)
    assert active(outside)
    clients.remove_activation(client, plugin_id, 'user', project)
    assert cached.is_dir()
    assert active(project)
    assert not active(outside)
    clients.remove_activation(client, plugin_id, scope, project)
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


def test_registered_source_is_recognized_through_another_spelling(state):
    root, _ = state
    source = root / 'catalog'
    source.mkdir()
    # A client records its own canonical spelling of the same directory.
    recorded = root / 'recorded-catalog'
    recorded.symlink_to(source, target_is_directory=True)
    clients._check_codex_source({'source_type': 'local', 'source': str(recorded)}, str(source))
    clients._check_claude_source({'source': {'source': 'directory', 'path': str(recorded)}}, str(source), None)
    with pytest.raises(clients.ClientError, match='different source'):
        clients._check_codex_source({'source_type': 'local', 'source': str(root)}, str(source))


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


@pytest.mark.parametrize('client', ['claude', 'codex', 'cursor', 'kiro'])
def test_native_failed_upgrade_rollback_restores_prior_cache_and_activation(state, client):
    _require_native(client)
    import shutil
    root, project = state
    source = root / 'catalog'
    plugin_source = source / 'plugin'
    shutil.copytree(SCRIPTS.parents[2], plugin_source, ignore=shutil.ignore_patterns('__pycache__'))
    (source / '.agents/plugins').mkdir(parents=True)
    (source / '.claude-plugin').mkdir()
    (source / '.cursor-plugin').mkdir()
    (source / '.agents/plugins/marketplace.json').write_text(json.dumps({
        'name': 'rollback-test', 'plugins': [{'name': 'tao-dev', 'source': {'source': 'local', 'path': './plugin'},
                                           'policy': {'installation': 'AVAILABLE', 'authentication': 'ON_INSTALL'},
                                           'category': 'Productivity'}]}), encoding='utf-8')
    (source / '.claude-plugin/marketplace.json').write_text(json.dumps({
        'name': 'rollback-test', 'owner': {'name': 'Test'}, 'plugins': [{'name': 'tao-dev', 'source': './plugin'}]}), encoding='utf-8')
    (source / '.cursor-plugin/marketplace.json').write_text(json.dumps({
        'name': 'rollback-test', 'owner': {'name': 'Test'}, 'plugins': [{'name': 'tao-dev', 'source': './plugin'}]}), encoding='utf-8')
    def version(value):
        for name in ('.codex-plugin/plugin.json', '.claude-plugin/plugin.json', '.cursor-plugin/plugin.json'):
            manifest = plugin_source / name
            if not manifest.is_file():
                continue
            data = json.loads(manifest.read_text(encoding='utf-8'))
            data['version'] = value
            manifest.write_text(json.dumps(data), encoding='utf-8')
    plugin_id = 'tao-dev@rollback-test'
    version('1.0.0')
    options = {'python': Path(sys.executable)} if client == 'kiro' else {}
    before = clients.install_plugin(client, str(source), plugin_id, 'project', project, **options)
    snapshot = clients.snapshot_activation(client, plugin_id, 'project', project)
    previous_cache = Path(before['plugin_path'])
    backup = root / 'previous-cache'
    shutil.copytree(previous_cache, backup)
    version('2.0.0')
    attempted = clients.install_plugin(client, str(source), plugin_id, 'project', project, **options)
    assert attempted['version'] == '2.0.0'
    # Caller restores old source/cache bytes before the adapter restores keys.
    version('1.0.0')
    if previous_cache.exists():
        shutil.rmtree(previous_cache)
    shutil.copytree(backup, previous_cache)
    if client == 'codex':
        unrelated = root / 'codex' / 'config.toml'
        clients._write_config(unrelated, [('test_preserve', 'unrelated')])
    elif client == 'claude':
        unrelated = root / 'claude' / 'settings.json'
        data = clients._read_json(unrelated)
        data['test_preserve'] = 'unrelated'
        unrelated.write_text(json.dumps(data), encoding='utf-8')
    elif client == 'cursor':
        unrelated = project / '.cursor/settings.json'
        data = clients._read_json(unrelated)
        data['test_preserve'] = 'unrelated'
        unrelated.write_text(json.dumps(data), encoding='utf-8')
    else:
        unrelated = project / '.kiro/unrelated.json'
        unrelated.parent.mkdir(exist_ok=True)
        unrelated.write_text(json.dumps({'test_preserve': 'unrelated'}), encoding='utf-8')
    clients.restore_activation(snapshot, attempted_plugin_path=attempted['plugin_path'])
    assert previous_cache.is_dir()
    assert not Path(attempted['plugin_path']).exists()
    rows = clients.discover(client, project)
    assert len(rows) == 1
    assert rows[0]['plugin_path'] == str(previous_cache)
    if client == 'codex':
        clients._verify_skills(project, plugin_id, previous_cache)
        assert clients._config(unrelated)['test_preserve'] == 'unrelated'
    elif client == 'claude':
        native = clients._run(['claude', 'plugin', 'list', '--json'], project)
        assert native[0]['enabled'] is True
        assert native[0]['installPath'] == str(previous_cache)
        assert clients._read_json(unrelated)['test_preserve'] == 'unrelated'
    elif client == 'cursor':
        assert clients._read_json(unrelated)['test_preserve'] == 'unrelated'
        assert clients._read_json(unrelated)['plugins']['rollback-test/tao-dev']['enabled'] is True
    else:
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


@pytest.mark.parametrize('scope', ['user', 'project', 'local'])
def test_kiro_v3_file_install_discover_and_remove(state, scope):
    root, project = state
    source = SCRIPTS.parents[4]
    result = clients.install_plugin('kiro', str(source), 'tao-dev@tao-dev', scope, project,
                                    python=Path(sys.executable))
    normalized = 'project' if scope == 'local' else scope
    base = root / 'kiro' if normalized == 'user' else project / '.kiro'
    skill = base / 'skills/tao-dev'
    hook = base / 'hooks/tao-dev.json'
    assert Path(result['plugin_path']).is_dir()
    assert (skill / 'SKILL.md').is_file()
    definition = json.loads(hook.read_text(encoding='utf-8'))
    command = definition['hooks'][0]['action']['command']
    assert definition['version'] == 'v1'
    assert definition['hooks'][0]['trigger'] == 'PostToolUse'
    assert '--host kiro' in command
    rows = clients.discover('kiro', project)
    assert any(row['scope'] == normalized and row['enabled'] for row in rows)
    clients.remove_activation('kiro', 'tao-dev@tao-dev', normalized, project)
    assert not skill.exists() and not hook.exists()


def test_kiro_refuses_unmanaged_skill(state):
    root, project = state
    skill = root / 'kiro/skills/tao-dev'
    skill.mkdir(parents=True)
    (skill / 'SKILL.md').write_text('mine', encoding='utf-8')
    with pytest.raises(clients.ClientError, match='unmanaged Kiro skill'):
        clients.install_plugin('kiro', str(SCRIPTS.parents[4]), 'tao-dev@tao-dev', 'user', project,
                               python=Path(sys.executable))
    assert (skill / 'SKILL.md').read_text(encoding='utf-8') == 'mine'


def test_kiro_rejects_symlinked_project_root(state):
    root, project = state
    outside = root / 'outside-kiro'
    outside.mkdir()
    (project / '.kiro').symlink_to(outside, target_is_directory=True)
    with pytest.raises(clients.ClientError, match='symlinked Kiro activation'):
        clients.install_plugin('kiro', str(SCRIPTS.parents[4]), 'tao-dev@tao-dev', 'project', project,
                               python=Path(sys.executable))
    assert not list(outside.iterdir())


def test_kiro_modified_skill_is_not_overwritten(state):
    _, project = state
    result = clients.install_plugin('kiro', str(SCRIPTS.parents[4]), 'tao-dev@tao-dev', 'user', project,
                                    python=Path(sys.executable))
    skill = Path(result['activation']['skill'])
    (skill / 'SKILL.md').write_text('user change', encoding='utf-8')
    with pytest.raises(clients.ClientError, match='modified Kiro skill'):
        clients.install_plugin('kiro', str(SCRIPTS.parents[4]), 'tao-dev@tao-dev', 'user', project,
                               python=Path(sys.executable))
    assert (skill / 'SKILL.md').read_text(encoding='utf-8') == 'user change'


def test_kiro_uninstall_removes_hook_when_skill_is_missing(state):
    _, project = state
    result = clients.install_plugin('kiro', str(SCRIPTS.parents[4]), 'tao-dev@tao-dev', 'user', project,
                                    python=Path(sys.executable))
    skill = Path(result['activation']['skill'])
    hook = Path(result['activation']['hook'])
    import shutil
    shutil.rmtree(skill)
    clients.remove_activation('kiro', 'tao-dev@tao-dev', 'user', project,
                              activation=result['activation'])
    assert not hook.exists()


def test_kiro_restore_includes_private_git_exclude(state):
    _, project = state
    subprocess.run(['git', '-C', str(project), 'init', '-q'], check=True)
    exclude = project / '.git/info/exclude'
    before = exclude.read_bytes()
    snapshot = clients.snapshot_activation('kiro', 'tao-dev@tao-dev', 'project', project)
    result = clients.install_plugin('kiro', str(SCRIPTS.parents[4]), 'tao-dev@tao-dev', 'project', project,
                                    python=Path(sys.executable))
    assert exclude.read_bytes() != before
    clients.restore_activation(snapshot, attempted_plugin_path=result['plugin_path'])
    assert exclude.read_bytes() == before


def test_kiro_rejects_symlinked_cache_ancestor(state):
    root, project = state
    outside = root / 'outside-cache'
    outside.mkdir()
    home = root / 'kiro'
    home.mkdir()
    (home / 'plugins').symlink_to(outside, target_is_directory=True)
    with pytest.raises(clients.ClientError, match='symlinked Kiro plugin cache'):
        clients.install_plugin('kiro', str(SCRIPTS.parents[4]), 'tao-dev@tao-dev', 'user', project,
                               python=Path(sys.executable))
    assert not list(outside.iterdir())


def test_kiro_uninstall_preserves_foreign_cache_content(state):
    root, project = state
    result = clients.install_plugin('kiro', str(SCRIPTS.parents[4]), 'tao-dev@tao-dev', 'user', project,
                                    python=Path(sys.executable))
    base = Path(result['plugin_base'])
    foreign = base / 'foreign/keep.txt'
    foreign.parent.mkdir()
    foreign.write_text('mine', encoding='utf-8')
    clients.remove_activation('kiro', 'tao-dev@tao-dev', 'user', project,
                              activation=result['activation'])
    assert foreign.read_text(encoding='utf-8') == 'mine'


def test_kiro_cache_owner_symlink_never_authorizes_replacement(state):
    root, project = state
    result = clients.install_plugin('kiro', str(SCRIPTS.parents[4]), 'tao-dev@tao-dev', 'user', project,
                                    python=Path(sys.executable))
    cached = Path(result['plugin_path'])
    owner = cached / '.tao-owned.json'
    external = root / 'fake-owner.json'
    external.write_text(json.dumps({'component': 'kiro-cache', 'plugin_id': 'tao-dev@tao-dev'}), encoding='utf-8')
    owner.unlink()
    owner.symlink_to(external)
    valuable = cached / 'valuable.txt'
    valuable.write_text('mine', encoding='utf-8')
    with pytest.raises(clients.ClientError, match='unmanaged Kiro plugin cache'):
        clients.install_plugin('kiro', str(SCRIPTS.parents[4]), 'tao-dev@tao-dev', 'user', project,
                               python=Path(sys.executable))
    assert valuable.read_text(encoding='utf-8') == 'mine'


def test_kiro_uninstall_rejects_cache_ancestor_replaced_by_symlink(state):
    root, project = state
    result = clients.install_plugin('kiro', str(SCRIPTS.parents[4]), 'tao-dev@tao-dev', 'user', project,
                                    python=Path(sys.executable))
    plugins = root / 'kiro/plugins'
    outside = root / 'moved-plugins'
    plugins.rename(outside)
    plugins.symlink_to(outside, target_is_directory=True)
    with pytest.raises(clients.ClientError, match='symlinked Kiro plugin cache'):
        clients.remove_activation('kiro', 'tao-dev@tao-dev', 'user', project,
                                  activation=result['activation'])
    assert Path(result['activation']['skill']).exists()


def test_kiro_uninstall_ignores_malformed_foreign_cache_marker(state):
    _, project = state
    result = clients.install_plugin('kiro', str(SCRIPTS.parents[4]), 'tao-dev@tao-dev', 'user', project,
                                    python=Path(sys.executable))
    base = Path(result['plugin_base'])
    foreign = base / 'foreign'
    foreign.mkdir()
    (foreign / '.tao-owned.json').write_text('{broken', encoding='utf-8')
    (foreign / 'keep.txt').write_text('mine', encoding='utf-8')
    clients.remove_activation('kiro', 'tao-dev@tao-dev', 'user', project,
                              activation=result['activation'])
    assert (foreign / 'keep.txt').read_text(encoding='utf-8') == 'mine'
    assert not Path(result['activation']['skill']).exists()


def test_kiro_snapshot_rejects_internal_symlink_without_change(state):
    root, project = state
    skill = root / 'kiro/skills/tao-dev'
    skill.mkdir(parents=True)
    target = root / 'keep.txt'
    target.write_text('mine', encoding='utf-8')
    link = skill / 'linked.txt'
    link.symlink_to(target)
    with pytest.raises(clients.ClientError, match='snapshot symlinked Kiro activation'):
        clients.snapshot_activation('kiro', 'tao-dev@tao-dev', 'user', project)
    assert link.is_symlink() and target.read_text(encoding='utf-8') == 'mine'
