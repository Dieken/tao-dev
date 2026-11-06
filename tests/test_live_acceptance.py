import json
import os
import signal
import subprocess
import sys
from pathlib import Path

import pytest

import native_clients
from acceptance.limits import model_timeout
from acceptance.commands import cli_executable
from acceptance.isolated_claude import access_environment

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
CLAUDE_PREFLIGHT_TIMEOUT = 60
_PREFLIGHT_UNCHECKED = object()
_CLAUDE_PREFLIGHT_RESULT = _PREFLIGHT_UNCHECKED


def _terminate(process, *, force=False):
    if os.name == "posix":
        try:
            os.killpg(process.pid, signal.SIGKILL if force else signal.SIGTERM)
        except ProcessLookupError:
            pass
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
            # Leave time for the adapter's ten-second model-group cleanup and
            # credential/log finalizers before escalating against the adapter.
            stdout, stderr = process.communicate(timeout=15)
        except subprocess.TimeoutExpired:
            _terminate(process, force=True)
            stdout, stderr = process.communicate(timeout=10)
        pytest.fail(
            f"Acceptance process timed out after {timeout}s.\n"
            f"stdout:\n{stdout}\nstderr:\n{stderr}"
        )
    try:
        report = json.loads(stdout)
    except (TypeError, json.JSONDecodeError):
        report = None
    if (process.returncode == 2 and isinstance(report, dict)
            and report.get('status') == 'blocked'
            and report.get('reason') in {
                'Existing access token cannot cover this probe; no refresh or login attempted.',
                'Existing Codex access token cannot cover this probe; no refresh or login attempted.',
            }):
        pytest.skip(report['reason'])
    assert process.returncode == 0, (
        f"Acceptance process failed with exit code {process.returncode}.\n"
        f"stdout:\n{stdout}\nstderr:\n{stderr}"
    )


def _probe_claude_result(result):
    """Accept only a successful response; report route errors without text."""
    if result.returncode == 0 and result.stdout.strip():
        return None
    if "unrecognized_model" in result.stderr:
        return "Configured Claude model route is not recognized by the CLI."
    return "Claude model route did not return a response during preflight."


def _claude_preflight_reason(workspace):
    global _CLAUDE_PREFLIGHT_RESULT
    if _CLAUDE_PREFLIGHT_RESULT is not _PREFLIGHT_UNCHECKED:
        return _CLAUDE_PREFLIGHT_RESULT
    workspace = Path(workspace)
    workspace.mkdir(parents=True, exist_ok=True)
    try:
        with access_environment(workspace, CLAUDE_PREFLIGHT_TIMEOUT) as (environment, _):
            try:
                result = subprocess.run(
                    [cli_executable("claude"), "-p", "--no-session-persistence",
                     "--output-format", "text", "--effort", "low",
                     "--max-budget-usd", "0.05", "Reply with OK."],
                    cwd=workspace,
                    env=environment,
                    stdin=subprocess.DEVNULL,
                    capture_output=True,
                    text=True,
                    timeout=CLAUDE_PREFLIGHT_TIMEOUT,
                    check=False,
                    encoding="utf-8",
                )
            except subprocess.TimeoutExpired:
                _CLAUDE_PREFLIGHT_RESULT = (
                    "Claude model route did not respond within the 60-second preflight."
                )
                return _CLAUDE_PREFLIGHT_RESULT
        _CLAUDE_PREFLIGHT_RESULT = _probe_claude_result(result)
    except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as exc:
        _CLAUDE_PREFLIGHT_RESULT = str(exc)
    return _CLAUDE_PREFLIGHT_RESULT


def _require_model_session(client, *, preflight_dir=None):
    if os.name != "posix":
        pytest.skip("This authenticated acceptance adapter is POSIX-only.")
    native_clients.require_session(client)
    if client == "claude":
        if preflight_dir is None:
            raise ValueError("Claude model readiness requires an isolated preflight directory.")
        reason = _claude_preflight_reason(preflight_dir)
        if reason:
            pytest.skip(reason)


def _require_cli(client):
    native_clients.require_cli(client)


@pytest.mark.parametrize(
    "case, scope, extra", CLAUDE_CASES, ids=[case for case, _, _ in CLAUDE_CASES]
)
def test_documented_claude_acceptance(case, scope, extra, tmp_path):
    _require_model_session("claude", preflight_dir=tmp_path / "claude-preflight")
    timeout = model_timeout()
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
        str(timeout),
    ]
    _run(arguments, timeout=timeout + 120, environment=os.environ.copy())


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
    timeout = model_timeout()
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
        str(timeout),
    ]
    _run(arguments, timeout=timeout + 120, environment=os.environ.copy())


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
    _require_model_session(client, preflight_dir=tmp_path / "claude-preflight")
    timeout = model_timeout()
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
            str(timeout),
        ],
        timeout=timeout + 120,
        environment=environment,
    )


def test_claude_preflight_rejects_unrecognized_model_without_echoing_output():
    from types import SimpleNamespace

    reason = _probe_claude_result(SimpleNamespace(
        returncode=1,
        stdout="private response text",
        stderr='[claude-code:unrecognized_model] {"model":"private-model"}',
    ))

    assert reason == "Configured Claude model route is not recognized by the CLI."
    assert "private" not in reason


def test_claude_preflight_accepts_a_successful_response():
    from types import SimpleNamespace

    assert _probe_claude_result(SimpleNamespace(
        returncode=0, stdout="OK", stderr="",
    )) is None
