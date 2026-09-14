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
