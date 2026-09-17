"""Export locked runtime dependencies; this script is not distributed."""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import tomllib


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "plugins/tao-dev/skills/tao-dev/scripts"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    environment = os.environ | {"UV_CACHE_DIR": str(ROOT / "tmp/tao/uv-cache"),
                                "UV_PYTHON_DOWNLOADS": "never"}
    stale = []
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    bounds = re.fullmatch(r">=(\d+)\.(\d+),<(\d+)\.(\d+)", project["requires-python"])
    if bounds is None:
        raise ValueError("Update the runtime policy exporter for the new Python constraint.")
    policy = {"version": project["version"], "python_min": [int(x) for x in bounds.groups()[:2]],
              "python_max": [int(x) for x in bounds.groups()[2:]]}
    policy_path = SCRIPTS / "runtime.json"
    policy_text = json.dumps(policy, indent=2) + "\n"
    if args.check:
        if not policy_path.exists() or policy_path.read_text(encoding="utf-8") != policy_text:
            stale.append("runtime.json")
    else:
        policy_path.write_text(policy_text, encoding="utf-8")
    for name, extras in (("requirements.txt", []),
                         ("requirements-publication.txt", ["--extra", "publication"])):
        command = ["uv", "export", "--no-config", "--locked", "--offline", "--no-dev",
                   "--no-emit-project", "--no-header", "--no-annotate", *extras]
        completed = subprocess.run(command, cwd=ROOT, env=environment,
                                   capture_output=True, text=True, encoding="utf-8", errors="replace", check=True)
        text = ("# Generated from pyproject.toml and uv.lock; do not edit.\n"
                "# Regenerate: uv run --locked python scripts/export_dependencies.py\n"
                + completed.stdout)
        path = SCRIPTS / name
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                stale.append(name)
        else:
            path.write_text(text, encoding="utf-8")
    if stale:
        print("Stale release dependencies: " + ", ".join(stale))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
