"""Create a runtime-only plugin directory without installing or registering it."""

import argparse
import json
from pathlib import Path
import shutil

SOURCE = Path(__file__).resolve().parents[1] / 'plugins/tao-dev'


def build(output, *, codex_legacy=False):
    output = output.resolve()
    if output.is_relative_to(SOURCE.resolve()) or output.exists():
        raise ValueError('Package output must be new and outside the source plugin.')
    if any(path.is_symlink() for path in SOURCE.rglob('*')):
        raise ValueError('Package sources must not contain symbolic links.')
    manifest = json.loads((SOURCE / 'plugin.json').read_text())
    output.mkdir(parents=True)
    names = ('skills', 'com.openai') if codex_legacy else tuple(p.name for p in SOURCE.iterdir())
    for name in names:
        source = SOURCE / name
        if source.is_dir():
            shutil.copytree(source, output / name, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        else:
            shutil.copy2(source, output / name)
    if codex_legacy:
        compatibility = {key: manifest[key] for key in ('name', 'version', 'description')}
        compatibility['hooks'] = manifest['extensions']['com.openai']['hooks']
        target = output / '.codex-plugin'
        target.mkdir()
        (target / 'plugin.json').write_text(json.dumps(compatibility, indent=2) + '\n')
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--format', choices=['public', 'codex-legacy'], default='public')
    args = parser.parse_args()
    output = build(args.output, codex_legacy=args.format == 'codex-legacy')
    print(json.dumps({'path': str(output), 'format': args.format, 'installed': False}))


if __name__ == '__main__':
    main()
