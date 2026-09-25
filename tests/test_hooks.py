import json
import subprocess
import sys

from taolib.documents import ASSETS
from test_documents import spec

HOOK = ASSETS.parent / "scripts/hook.py"


def invoke(root, event="PostToolUse"):
    return subprocess.run([sys.executable, str(HOOK)], cwd=root, input=json.dumps({"hook_event_name": event, "cwd": str(root), "tool_name": "Write", "tool_input": {"file_path": str(root / "docs/spec.md")}}), capture_output=True, text=True, encoding="utf-8")


def project(root):
    (root / ".tao").mkdir()
    (root / ".tao/config.toml").write_text('version = 1\n', encoding="utf-8")
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
    (tmp_path / "docs/spec.md").write_text("# Broken metadata\n", encoding="utf-8")
    third = json.loads(invoke(tmp_path).stdout)
    assert "TAO-DOC-001" in third["hookSpecificOutput"]["additionalContext"]
    assert "unchanged inputs" not in third["hookSpecificOutput"]["additionalContext"]


def test_disabled_or_unconfigured_hook_has_no_side_effects(tmp_path):
    assert json.loads(invoke(tmp_path).stdout) == {}
    project(tmp_path)
    (tmp_path / ".tao/config.toml").write_text('version = 1\n[hooks]\ndocs_enabled = false\n', encoding="utf-8")
    assert json.loads(invoke(tmp_path).stdout) == {}
    assert not (tmp_path / "tmp").exists()


def test_hook_ignores_unrelated_events(tmp_path):
    project(tmp_path)
    assert json.loads(invoke(tmp_path, "SessionStart").stdout) == {}
    assert not (tmp_path / "tmp").exists()


def test_timeout_never_creates_a_pass_cache(tmp_path):
    import shutil
    project(tmp_path)
    (tmp_path / ".tao/config.toml").write_text('version = 1\n[hooks]\ntimeout_seconds = 1\n', encoding="utf-8")
    package = tmp_path / "test-runtime"
    shutil.copytree(ASSETS.parent, package, ignore=shutil.ignore_patterns("__pycache__"))
    (package / "scripts/tao.py").write_text('import time\ntime.sleep(5)\n', encoding="utf-8")
    completed = subprocess.run([sys.executable, str(package / "scripts/hook.py")], cwd=tmp_path,
                               input='{"hook_event_name":"PostToolUse"}', capture_output=True, text=True, timeout=4, encoding="utf-8")
    assert "not_run" in json.loads(completed.stdout)["hookSpecificOutput"]["additionalContext"]
    assert not (tmp_path / "tmp/tao/cache/hook.json").exists()


def test_hook_refuses_an_escaping_managed_source(tmp_path):
    project(tmp_path)
    outside = tmp_path.parent / (tmp_path.name + "-outside.md")
    outside.write_text(spec(), encoding="utf-8")
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
                              input='{"hook_event_name":"PostToolUse"}', capture_output=True, text=True, encoding="utf-8")
    outside = call()
    assert outside.returncode == 0, outside.stderr
    assert json.loads(outside.stdout) == {}
    project(tmp_path)
    inside = call()
    assert inside.returncode == 0, inside.stderr
    assert "not_run" in json.loads(inside.stdout)["hookSpecificOutput"]["additionalContext"]
    assert not data.exists()
    assert not (tmp_path / "tmp").exists()


def test_static_client_hooks_invoke_python_without_platform_launchers():
    plugin = HOOK.parents[3]
    claude = json.loads((plugin / "hooks/hooks.json").read_text(encoding="utf-8"))["hooks"]["PostToolUse"][0]["hooks"][0]
    codex = json.loads((plugin / "com.openai/hooks/hooks.json").read_text(encoding="utf-8"))["hooks"]["PostToolUse"][0]["hooks"][0]
    cursor = json.loads((plugin / "com.cursor/hooks/hooks.json").read_text(encoding="utf-8"))["hooks"]["postToolUse"][0]
    assert claude["command"] == "python3"
    assert claude["args"] == ["-I", "-B", "${CLAUDE_PLUGIN_ROOT}/skills/tao-dev/scripts/hook.py"]
    assert codex["command"] == 'python3 -I -B "${PLUGIN_ROOT}/skills/tao-dev/scripts/hook.py"'
    assert cursor["command"] == 'python3 -I -B "${CURSOR_PLUGIN_ROOT}/skills/tao-dev/scripts/hook.py"'
    assert cursor["matcher"] == "Write"
    assert not (HOOK.parent / "tao-launch.sh").exists()
    assert not (HOOK.parent / "tao-launch.ps1").exists()


def test_cursor_hook_event_uses_additional_context(tmp_path):
    project(tmp_path)
    completed = invoke(tmp_path, "postToolUse")
    assert completed.returncode == 0, completed.stderr
    report = json.loads(completed.stdout)
    assert "passed" in report["additional_context"]
    assert "hookSpecificOutput" not in report


def test_incomplete_hook_cache_is_rebuilt(tmp_path):
    project(tmp_path)
    assert invoke(tmp_path).returncode == 0
    cache = tmp_path / 'tmp/tao/cache/hook.json'
    saved = json.loads(cache.read_text(encoding="utf-8"))
    saved.pop('message')
    cache.write_text(json.dumps(saved), encoding="utf-8")
    observed = invoke(tmp_path)
    assert observed.returncode == 0, observed.stderr
    assert 'passed' in json.loads(observed.stdout)['hookSpecificOutput']['additionalContext']
    assert 'message' in json.loads(cache.read_text(encoding="utf-8"))


def test_kiro_hook_uses_plain_text_and_empty_noop(tmp_path):
    script = HOOK
    outside = subprocess.run([sys.executable, '-I', '-B', str(script), '--host', 'kiro'], cwd=tmp_path,
                             input='{}', capture_output=True, text=True, encoding='utf-8', check=False)
    assert outside.returncode == 0 and outside.stdout == ''
    (tmp_path / '.tao').mkdir()
    (tmp_path / '.tao/config.toml').write_text('', encoding='utf-8')
    inside = subprocess.run([sys.executable, '-I', '-B', str(script), '--host', 'kiro'], cwd=tmp_path,
                            input='{}', capture_output=True, text=True, encoding='utf-8')
    assert inside.returncode == 0
    assert 'not_run' in inside.stdout
    assert not inside.stdout.startswith('{')
