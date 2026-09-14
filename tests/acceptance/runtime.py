"""Prepare hash-verified wheels explicitly; normal tests never download."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "plugins/tao-dev/skills/tao-dev/scripts"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--download", action="store_true", required=True)
    args = parser.parse_args()
    temporary = ROOT / "tmp/tao"
    temporary.mkdir(parents=True, exist_ok=True)
    wheels = temporary / "wheels"
    log = temporary / "wheel-download.log"
    environment = {k: v for k, v in os.environ.items() if not k.startswith("PIP_")}
    environment["PIP_CONFIG_FILE"] = os.devnull
    with tempfile.TemporaryDirectory(prefix="wheel-preparation-", dir=temporary) as work:
        python = Path(work) / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        commands = [
            [sys.executable, "-I", "-m", "venv", work],
            [str(python), "-I", "-m", "pip", "download", "--disable-pip-version-check",
             "--dest", str(wheels), "--require-hashes", "--only-binary=:all:",
             "--index-url", "https://pypi.org/simple", "-r", str(SCRIPTS / "requirements-publication.txt")],
        ]
        with log.open("w") as output:
            for argv in commands:
                completed = subprocess.run(argv, env=environment, stdout=output, stderr=subprocess.STDOUT, timeout=180)
                if completed.returncode:
                    print(f"Wheel preparation failed; inspect {log.relative_to(ROOT)}")
                    return 2
    print(json.dumps({"wheelhouse": str(wheels), "files": len(list(wheels.glob('*.whl')))}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
