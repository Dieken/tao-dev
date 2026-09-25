"""Prepare real isolated tool environments for entry-point regression tests."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

PREPARE_TIMEOUT = 300


@pytest.fixture(scope="session", autouse=True)
def tool_runtime(tmp_path_factory):
    root = Path(__file__).resolve().parents[1]
    data = tmp_path_factory.mktemp("tao-runtime")
    wheels = Path(os.environ.get("TAO_TEST_WHEELHOUSE", root / "tmp/tao/wheels"))
    if not wheels.is_dir():
        pytest.fail("Prepare locked wheels first: uv run --locked --extra publication python tests/acceptance/runtime.py --download")
    previous = {key: os.environ.get(key) for key in ("TAO_RUNTIME_DIR", "TAO_PYTHON")}
    os.environ.update(TAO_RUNTIME_DIR=str(data), TAO_PYTHON=sys.executable)
    try:
        entry = root / "plugins/tao-dev/skills/tao-dev/scripts/tao.py"
        # The CLI owns the preparation budget; keep the parent alive for the
        # same startup and final-reporting margin used by installations.
        completed = subprocess.run([sys.executable, str(entry), "env", "prepare",
                                    "--wheelhouse", str(wheels), "--format", "json",
                                    "--timeout", str(PREPARE_TIMEOUT)],
                                   capture_output=True, text=True, encoding='utf-8',
                                   timeout=PREPARE_TIMEOUT + 60, check=False)
        assert completed.returncode == 0, completed.stdout + completed.stderr
        yield data
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
