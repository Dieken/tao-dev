"""Exercise native client install, disable, update and removal without a model."""

import argparse
import json
from pathlib import Path
import subprocess

import isolated_codex
from clients import global_configuration, prepare


def run(workspace, *, codex_legacy=False):
    if workspace.exists() and any(workspace.iterdir()):
        raise RuntimeError('Lifecycle acceptance requires a fresh workspace.')
    if workspace.is_relative_to(isolated_codex.ROOT):
        raise RuntimeError('Use an independent temporary workspace.')
    inside = workspace / 'codex/inside'
    plugin = prepare(inside, 'codex', native_plugin=True, codex_legacy=codex_legacy)
    cache = isolated_codex.configure(workspace, inside, plugin)
    initial = isolated_codex.check_boundary(workspace, inside)
    initial_hook = isolated_codex.trust_test_hook(workspace, inside, plugin) if codex_legacy else None
    config = inside / '.codex/config.toml'
    enabled = config.read_text()
    config.write_text(enabled.replace('enabled = true', 'enabled = false'))
    disabled = isolated_codex.skills(workspace, [inside, workspace / 'codex/outside'])
    if any(disabled.values()):
        raise RuntimeError('Disabled plugin still exposes a native skill.')
    if codex_legacy and any(row['hooks'] for row in isolated_codex.hook_inventory(workspace, inside)):
        raise RuntimeError('Disabled plugin still exposes a hook.')
    config.write_text(enabled)
    isolated_codex.check_boundary(workspace, inside)
    manifest = plugin / ('.codex-plugin/plugin.json' if codex_legacy else 'plugin.json')
    value = json.loads(manifest.read_text())
    value['version'] = '0.2.3'
    manifest.write_text(json.dumps(value))
    skill = plugin / 'skills/tao-dev/SKILL.md'
    skill.write_text(skill.read_text().replace('description: ', 'description: Acceptance update marker. ', 1))
    if codex_legacy:
        hooks_file = plugin / 'com.openai/hooks/hooks.json'
        definition = json.loads(hooks_file.read_text())
        definition['hooks']['PostToolUse'][0]['hooks'][0]['timeout'] = 34
        hooks_file.write_text(json.dumps(definition))
    state_config = workspace / 'client-state/config.toml'
    default_disabled = state_config.read_text()
    updated = subprocess.run(['codex', 'plugin', 'add', isolated_codex.PLUGIN_ID, '--json'],
                             cwd=inside, env=isolated_codex.environment(workspace),
                             capture_output=True, text=True, timeout=45, check=True)
    state_config.write_text(default_disabled)
    update_result = json.loads(updated.stdout)
    latest = isolated_codex.check_boundary(workspace, inside)
    found = latest[str(inside)][0]
    if 'Acceptance update marker.' not in found['description'] or '/0.2.3/' not in found['path']:
        raise RuntimeError('Fresh native discovery still exposes the old plugin.')
    updated_hooks = isolated_codex.hook_inventory(workspace, inside) if codex_legacy else []
    if codex_legacy:
        hooks = [hook for row in updated_hooks for hook in row['hooks']]
        if (len(hooks) != 1 or '/0.2.3/' not in hooks[0]['sourcePath'] or
                hooks[0]['currentHash'] == initial_hook['currentHash'] or hooks[0]['trustStatus'] == 'trusted'):
            raise RuntimeError('Updated hook must use the new cache and require fresh trust.')
    removed = subprocess.run(['codex', 'plugin', 'remove', isolated_codex.PLUGIN_ID, '--json'],
                             cwd=inside, env=isolated_codex.environment(workspace),
                             capture_output=True, text=True, timeout=45, check=True)
    after_removal = isolated_codex.skills(workspace, [inside, workspace / 'codex/outside'])
    if any(after_removal.values()):
        raise RuntimeError('Removed plugin still exposes a native skill.')
    if codex_legacy and any(row['hooks'] for row in isolated_codex.hook_inventory(workspace, inside)):
        raise RuntimeError('Removed plugin still exposes a hook.')
    return {'initial_cache': str(cache), 'initial_discovery': initial,
            'disabled_discovery': disabled, 'update': update_result,
            'updated_discovery': latest, 'updated_hooks': updated_hooks, 'removal': json.loads(removed.stdout),
            'removed_discovery': after_removal, 'model_called': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--codex-legacy', action='store_true')
    parser.add_argument('--client', choices=['codex', 'claude'], default='codex')
    parser.add_argument('--claude-scope', choices=['user', 'project', 'local'])
    args = parser.parse_args()
    if (args.client == 'claude') != bool(args.claude_scope) or args.client == 'claude' and args.codex_legacy:
        parser.error('Claude lifecycle probes require --claude-scope and cannot use --codex-legacy.')
    before = global_configuration()
    result = {}
    try:
        if args.client == 'claude':
            from isolated_claude import lifecycle
            result = lifecycle(args.workspace.resolve(), args.claude_scope)
        else:
            result = run(args.workspace.resolve(), codex_legacy=args.codex_legacy)
    finally:
        after = global_configuration()
        result['global_configuration_unchanged'] = before == after
        result['changed_global_files'] = [p for p in before if before[p] != after[p]]
        print(json.dumps(result, indent=2))
    return 0 if before == after else 1


if __name__ == '__main__':
    raise SystemExit(main())
