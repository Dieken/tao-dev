import os
import signal
import subprocess
import sys
from pathlib import Path

import pytest

import native_clients

ROOT = Path(__file__).resolve().parents[1]
CLIENT_ACCEPTANCE = ROOT / "tests/acceptance/clients.py"
LIFECYCLE_ACCEPTANCE = ROOT / "tests/acceptance/lifecycle.py"


# These are the documented long-running Claude/Codex acceptance flows.  They
# are pytest tests so the normal readiness guards make them skip, rather than
# making a credential-free CI run fail with a blocked acceptance exit code.
CLAUDE_CASES = (
    ("recover", "project", ("--disable-hooks",)),
    ("plan", "local", ()),
    ("routing", "local", ()),
)
CODEX_CASES = (
    ("write", ("--trust-test-hook",)),
    ("recover", ("--trust-test-hook", "--disable-hooks")),
    ("routing", ()),
)


def _terminate(process):
    if os.name == "posix":
        os.killpg(process.pid, signal.SIGTERM)
    else:
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            capture_output=True,
            timeout=5,
            check=False,
        )


def _run(arguments, *, timeout, environment=None):
    process = subprocess.Popen(
        [sys.executable, *arguments],
        cwd=ROOT,
        env=environment,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
        encoding="utf-8",
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        _terminate(process)
        try:
            stdout, stderr = process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            _terminate(process)
            stdout, stderr = process.communicate(timeout=10)
        pytest.fail(
            f"Acceptance process timed out after {timeout}s.\n"
            f"stdout:\n{stdout}\nstderr:\n{stderr}"
        )
    assert process.returncode == 0, (
        f"Acceptance process failed with exit code {process.returncode}.\n"
        f"stdout:\n{stdout}\nstderr:\n{stderr}"
    )


def _require_model_session(client):
    if os.name != "posix":
        pytest.skip("This authenticated acceptance adapter is POSIX-only.")
    native_clients.require_session(client)


def _require_cli(client):
    native_clients.require_cli(client)


@pytest.mark.parametrize(
    "case, scope, extra", CLAUDE_CASES, ids=[case for case, _, _ in CLAUDE_CASES]
)
def test_documented_claude_acceptance(case, scope, extra, tmp_path):
    _require_model_session("claude")
    workspace = tmp_path / f"claude-{case}"
    arguments = [
        str(CLIENT_ACCEPTANCE),
        "--client",
        "claude",
        "--case",
        case,
        "--claude-scope",
        scope,
        "--reuse-claude-auth",
        *extra,
        "--workspace",
        str(workspace),
        "--timeout",
        "600",
    ]
    _run(arguments, timeout=720, environment=os.environ.copy())


def test_documented_claude_lifecycle_acceptance(tmp_path):
    _require_cli("claude")
    workspace = tmp_path / "claude-lifecycle"
    _run(
        [
            str(LIFECYCLE_ACCEPTANCE),
            "--client",
            "claude",
            "--claude-scope",
            "user",
            "--workspace",
            str(workspace),
        ],
        timeout=720,
        environment=os.environ.copy(),
    )


@pytest.mark.parametrize(
    "case, extra", CODEX_CASES, ids=[case for case, _ in CODEX_CASES]
)
def test_documented_codex_acceptance(case, extra, tmp_path):
    _require_model_session("codex")
    workspace = tmp_path / f"codex-{case}"
    arguments = [
        str(CLIENT_ACCEPTANCE),
        "--client",
        "codex",
        "--case",
        case,
        "--isolated-codex",
        "--reuse-codex-auth",
        "--codex-legacy",
        *extra,
        "--workspace",
        str(workspace),
        "--timeout",
        "600",
    ]
    _run(arguments, timeout=720, environment=os.environ.copy())


def test_documented_codex_lifecycle_acceptance(tmp_path):
    _require_cli("codex")
    workspace = tmp_path / "codex-lifecycle"
    _run(
        [
            str(LIFECYCLE_ACCEPTANCE),
            "--codex-legacy",
            "--workspace",
            str(workspace),
        ],
        timeout=720,
        environment=os.environ.copy(),
    )


@pytest.mark.parametrize("client", ("claude", "codex"))
def test_documented_behavior_acceptance(client, tmp_path):
    _require_model_session(client)
    workspace = tmp_path / f"{client}-behavior"
    environment = os.environ.copy()
    existing = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = str(ROOT / "tests") + (
        os.pathsep + existing if existing else ""
    )
    _run(
        [
            "-m",
            "acceptance.behavior_live",
            "--client",
            client,
            "--workspace",
            str(workspace),
            "--timeout",
            "600",
        ],
        timeout=720,
        environment=environment,
    )
