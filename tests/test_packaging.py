"""Complete installation catalogs must resolve to self-contained plugins."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_github_catalogs_resolve_one_complete_compatible_source():
    codex = json.loads((ROOT / '.agents/plugins/marketplace.json').read_text())
    claude = json.loads((ROOT / '.claude-plugin/marketplace.json').read_text())
    assert codex['name'] == claude['name'] == 'tao-dev'
    codex_entry, = codex['plugins']
    claude_entry, = claude['plugins']
    plugin = (ROOT / codex_entry['source']['path']).resolve()
    assert plugin == (ROOT / claude_entry['source']).resolve()
    # Codex 0.154.0 skips hooks when a portable root manifest takes precedence.
    assert not (plugin / 'plugin.json').exists()
    manifest = json.loads((plugin / '.codex-plugin/plugin.json').read_text())
    claude_manifest = json.loads((plugin / '.claude-plugin/plugin.json').read_text())
    for key in ('name', 'version', 'description'):
        assert manifest[key] == claude_manifest[key]
    hooks = json.loads((plugin / manifest['hooks']).read_text())
    assert hooks['hooks']['PostToolUse']
    assert (plugin / 'skills/tao-dev/scripts/tao.py').is_file()


@pytest.mark.parametrize('package_format', ['public', 'codex-legacy'])
def test_installation_catalog_resolves_complete_plugin(tmp_path, package_format):
    output = tmp_path / 'marketplace with spaces'
    command = [sys.executable, str(ROOT / 'scripts/package_plugin.py'),
               '--format', package_format, '--marketplace', '--output', str(output)]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report['installed'] is False
    catalog_path = output / ('.agents/plugins/marketplace.json' if package_format == 'codex-legacy'
                             else '.claude-plugin/marketplace.json')
    catalog = json.loads(catalog_path.read_text())
    assert catalog['name'] == 'tao-dev-local'
    entry, = catalog['plugins']
    relative = entry['source']['path'] if package_format == 'codex-legacy' else entry['source']
    plugin = (output / relative).resolve()
    assert plugin.is_relative_to(output)
    assert plugin.name == entry['name'] == 'tao-dev'
    folders = ('skills', 'com.openai') if package_format == 'codex-legacy' else (
        'skills', 'agents', 'commands', 'hooks', '.claude-plugin')
    for folder in folders:
        source = ROOT / 'plugins/tao-dev' / folder
        for path in source.rglob('*'):
            if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc':
                assert (plugin / path.relative_to(ROOT / 'plugins/tao-dev')).read_bytes() == path.read_bytes()
    assert not list(plugin.rglob('__pycache__'))
    assert not (plugin / 'docs').exists()
    manifest = plugin / ('.codex-plugin/plugin.json' if package_format == 'codex-legacy'
                         else '.claude-plugin/plugin.json')
    assert json.loads(manifest.read_text())['name'] == 'tao-dev'
    if package_format == 'public':
        portable = json.loads((plugin / 'plugin.json').read_text())
        assert portable['$schema'] == 'https://agent-plugins.org/schemas/1.0.0/plugin.schema.json'
        assert (plugin / portable['extensions']['com.openai']['hooks']).is_file()
        assert not (plugin / '.codex-plugin').exists()
    previous = catalog_path.read_bytes()
    repeated = subprocess.run(command, capture_output=True, text=True, check=False)
    assert repeated.returncode != 0
    assert catalog_path.read_bytes() == previous
