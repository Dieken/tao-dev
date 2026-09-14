"""Export locked runtime dependencies; this script is not distributed."""

import argparse
import os
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "plugins/tao-dev/skills/tao-dev/scripts"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    environment = os.environ | {"UV_CACHE_DIR": str(ROOT / "tmp/tao/uv-cache"),
                                "UV_PYTHON_DOWNLOADS": "never"}
    stale = []
    for name, extras in (("requirements.txt", []),
                         ("requirements-publication.txt", ["--extra", "publication"])):
        command = ["uv", "export", "--no-config", "--locked", "--offline", "--no-dev",
                   "--no-emit-project", "--no-header", "--no-annotate", *extras]
        completed = subprocess.run(command, cwd=ROOT, env=environment,
                                   capture_output=True, text=True, check=True)
        text = ("# Generated from pyproject.toml and uv.lock; do not edit.\n"
                "# Regenerate: uv run --locked python scripts/export_dependencies.py\n"
                + completed.stdout)
        path = SCRIPTS / name
        if args.check:
            if not path.exists() or path.read_text() != text:
                stale.append(name)
        else:
            path.write_text(text, encoding="utf-8")
    if stale:
        print("Stale release dependencies: " + ", ".join(stale))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
