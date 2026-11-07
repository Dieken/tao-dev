"""Build a self-contained skill directory without registering it with a client."""

import argparse
import json
from pathlib import Path
import shutil
import tempfile

SOURCE = Path(__file__).resolve().parents[1] / "skills/tao-dev"


def build(output):
    output = Path(output).absolute()
    if output.is_symlink() or output.exists() or output.resolve().is_relative_to(SOURCE.resolve()):
        raise ValueError("Package output must be new and outside the source skill.")
    if any(path.is_symlink() for path in SOURCE.rglob("*")):
        raise ValueError("Skill package sources must not contain symbolic links.")
    if not (SOURCE / "SKILL.md").is_file():
        raise ValueError("Skill entry point is missing.")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".tao-package-", dir=output.parent) as temporary:
        staged = Path(temporary) / "tao-dev"
        shutil.copytree(SOURCE, staged, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        # Reserve the output before moving files so an existing destination is
        # never overwritten, even if another process created it during copying.
        output.mkdir()
        try:
            for path in staged.iterdir():
                path.rename(output / path.name)
        except BaseException:
            shutil.rmtree(output)
            raise
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        path = build(args.output)
    except (OSError, ValueError) as error:
        parser.exit(2, f"{error}\n")
    print(json.dumps({"path": str(path), "installed": False}))


if __name__ == "__main__":
    main()
