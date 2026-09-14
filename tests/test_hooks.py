import json
from pathlib import Path
import subprocess
import sys

from taolib.documents import ASSETS
from test_documents import spec


HOOK = ASSETS.parent / "scripts/hook.py"


def invoke(root, event="PostToolUse"):
    return subprocess.run([sys.executable, str(HOOK)], cwd=root, input=json.dumps({"hook_event_name": event, "cwd": str(root), "tool_name": "Write", "tool_input": {"file_path": str(root / "docs/spec.md")}}), capture_output=True, text=True)


def project(root):
    (root / ".tao").mkdir()
    (root / ".tao/config.toml").write_text('version = 1\n')
    (root / "docs").mkdir()
    (root / "docs/spec.md").write_text(spec(), encoding="utf-8")


def test_hook_checks_docs_then_reuses_only_identical_inputs(tmp_path):
    project(tmp_path)
    first = invoke(tmp_path)
    assert first.returncode == 0, first.stderr
    first_report = json.loads(first.stdout)
    assert "passed" in first_report["hookSpecificOutput"]["additionalContext"]
    second = json.loads(invoke(tmp_path).stdout)
    assert "unchanged inputs" in second["hookSpecificOutput"]["additionalContext"]
    (tmp_path / "docs/spec.md").write_text("# Broken metadata\n")
    third = json.loads(invoke(tmp_path).stdout)
    assert "TAO-DOC-001" in third["hookSpecificOutput"]["additionalContext"]
    assert "unchanged inputs" not in third["hookSpecificOutput"]["additionalContext"]


def test_disabled_or_unconfigured_hook_has_no_side_effects(tmp_path):
    assert json.loads(invoke(tmp_path).stdout) == {}
    project(tmp_path)
    (tmp_path / ".tao/config.toml").write_text('version = 1\n[hooks]\ndocs_enabled = false\n')
    assert json.loads(invoke(tmp_path).stdout) == {}
    assert not (tmp_path / "tmp").exists()


def test_hook_ignores_unrelated_events(tmp_path):
    project(tmp_path)
    assert json.loads(invoke(tmp_path, "SessionStart").stdout) == {}
    assert not (tmp_path / "tmp").exists()


def test_timeout_never_creates_a_pass_cache(tmp_path):
    import shutil
    project(tmp_path)
    (tmp_path / ".tao/config.toml").write_text('version = 1\n[hooks]\ntimeout_seconds = 1\n')
    package = tmp_path / "test-runtime"
    shutil.copytree(ASSETS.parent, package, ignore=shutil.ignore_patterns("__pycache__"))
    (package / "scripts/tao.py").write_text('import time\ntime.sleep(5)\n')
    completed = subprocess.run([sys.executable, str(package / "scripts/hook.py")], cwd=tmp_path,
                               input='{"hook_event_name":"PostToolUse"}', capture_output=True, text=True, timeout=4)
    assert "not_run" in json.loads(completed.stdout)["hookSpecificOutput"]["additionalContext"]
    assert not (tmp_path / "tmp/tao/cache/hook.json").exists()


def test_hook_refuses_an_escaping_managed_source(tmp_path):
    project(tmp_path)
    outside = tmp_path.parent / (tmp_path.name + "-outside.md")
    outside.write_text(spec())
    (tmp_path / "docs/escape.md").symlink_to(outside)
    assert "not_run" in json.loads(invoke(tmp_path).stdout)["hookSpecificOutput"]["additionalContext"]


def test_hook_without_python_packages_is_quiet_outside_and_diagnostic_inside(tmp_path):
    import os
    python = tmp_path / "bare" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    subprocess.run([sys.executable, "-m", "venv", str(python.parent.parent)], check=True)
    data = tmp_path / "unprepared-data"
    env = os.environ | {"TAO_RUNTIME_DIR": str(data), "TAO_PYTHON": str(python)}
    def call():
        return subprocess.run([str(python), str(HOOK)], cwd=tmp_path, env=env,
                              input='{"hook_event_name":"PostToolUse"}', capture_output=True, text=True)
    outside = call()
    assert outside.returncode == 0, outside.stderr
    assert json.loads(outside.stdout) == {}
    project(tmp_path)
    inside = call()
    assert inside.returncode == 0, inside.stderr
    assert "not_run" in json.loads(inside.stdout)["hookSpecificOutput"]["additionalContext"]
    assert not data.exists()
    assert not (tmp_path / "tmp").exists()


def test_shell_hook_without_python_is_quiet_outside_and_explains_inside(tmp_path):
    import os
    import shutil
    shell = shutil.which("sh")
    if shell is None:
        import pytest
        pytest.skip("POSIX shell unavailable; this test does not validate PowerShell.")
    env = os.environ | {"PATH": "", "TAO_PYTHON": str(tmp_path / "absent")}
    argv = [shell, str(HOOK.parent / "tao-launch.sh"), "hook"]
    outside = subprocess.run(argv, cwd=tmp_path, env=env, capture_output=True, text=True)
    assert outside.returncode == 0, outside.stderr
    assert json.loads(outside.stdout) == {}
    project(tmp_path)
    inside = subprocess.run(argv, cwd=tmp_path, env=env, capture_output=True, text=True)
    assert inside.returncode == 0, inside.stderr
    assert "Python" in json.loads(inside.stdout)["hookSpecificOutput"]["additionalContext"]
    assert not (tmp_path / "tmp").exists()


def test_incomplete_hook_cache_is_rebuilt(tmp_path):
    project(tmp_path)
    assert invoke(tmp_path).returncode == 0
    cache = tmp_path / 'tmp/tao/cache/hook.json'
    saved = json.loads(cache.read_text())
    saved.pop('message')
    cache.write_text(json.dumps(saved))
    observed = invoke(tmp_path)
    assert observed.returncode == 0, observed.stderr
    assert 'passed' in json.loads(observed.stdout)['hookSpecificOutput']['additionalContext']
    assert 'message' in json.loads(cache.read_text())
