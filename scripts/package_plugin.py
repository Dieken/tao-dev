"""Create a runtime-only plugin directory without installing or registering it."""

import argparse
import json
import shutil
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / 'plugins/tao-dev'


def build(output, *, codex_legacy=False):
    output = output.resolve()
    if output.is_relative_to(SOURCE.resolve()) or output.exists():
        raise ValueError('Package output must be new and outside the source plugin.')
    if any(path.is_symlink() for path in SOURCE.rglob('*')):
        raise ValueError('Package sources must not contain symbolic links.')
    manifest = json.loads((SOURCE / '.codex-plugin/plugin.json').read_text(encoding='utf-8'))
    output.mkdir(parents=True)
    names = ('skills', 'com.openai', '.codex-plugin') if codex_legacy else tuple(
        p.name for p in SOURCE.iterdir() if p.name != '.codex-plugin')
    for name in names:
        source = SOURCE / name
        if source.is_dir():
            shutil.copytree(source, output / name, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        else:
            shutil.copy2(source, output / name)
    if not codex_legacy:
        portable = {'$schema': 'https://agent-plugins.org/schemas/1.0.0/plugin.schema.json',
                    **{key: manifest[key] for key in ('name', 'version', 'description')},
                    'extensions': {'com.openai': {'hooks': manifest['hooks']}}}
        (output / 'plugin.json').write_text(json.dumps(portable, indent=2) + '\n', encoding='utf-8', newline='\n')
    return output


def build_marketplace(output, *, codex_legacy=False):
    output = output.resolve()
    if output.is_relative_to(SOURCE.resolve()) or output.exists():
        raise ValueError('Marketplace output must be new and outside the source plugin.')
    plugin = build(output / 'plugins/tao-dev', codex_legacy=codex_legacy)
    if codex_legacy:
        catalog = {'name': 'tao-dev-local', 'plugins': [{
            'name': 'tao-dev', 'source': {'source': 'local', 'path': './plugins/tao-dev'},
            'policy': {'installation': 'AVAILABLE', 'authentication': 'ON_INSTALL'},
            'category': 'Productivity'}]}
        path = output / '.agents/plugins/marketplace.json'
    else:
        catalog = {'name': 'tao-dev-local', 'owner': {'name': 'tao-dev'},
                   'plugins': [{'name': 'tao-dev', 'source': './plugins/tao-dev'}]}
        path = output / '.claude-plugin/marketplace.json'
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(catalog, indent=2) + '\n', encoding='utf-8', newline='\n')
    return plugin


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--format', choices=['public', 'codex-legacy'], default='public')
    parser.add_argument('--marketplace', action='store_true',
                        help='Wrap the package in a local marketplace for the selected client format.')
    args = parser.parse_args()
    builder = build_marketplace if args.marketplace else build
    plugin = builder(args.output, codex_legacy=args.format == 'codex-legacy')
    print(json.dumps({'path': str(args.output.resolve()), 'plugin_path': str(plugin),
                      'format': args.format, 'installed': False}))


if __name__ == '__main__':
    main()
