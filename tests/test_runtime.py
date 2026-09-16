"""Exercise preparation with real locked wheels and an empty Python environment."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tomllib

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "plugins/tao-dev/skills/tao-dev/scripts"
WHEELS = Path(os.environ.get("TAO_TEST_WHEELHOUSE", ROOT / "tmp/tao/wheels"))


@pytest.fixture(scope="module")
def bare_python(tmp_path_factory):
    root = tmp_path_factory.mktemp("bare python 中文")
    subprocess.run([sys.executable, "-m", "venv", str(root)], check=True)
    return root / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def invoke(python, data, *args, scripts=SCRIPTS, cwd=None, extra=None):
    env = os.environ | {"TAO_RUNTIME_DIR": str(data), "TAO_PYTHON": str(python)}
    if extra:
        env.update(extra)
    return subprocess.run([str(python), str(scripts / "tao.py"), *args, "--format", "json"],
                          cwd=cwd or data.parent, env=env, capture_output=True, text=True)


def prepare(python, data, *args, scripts=SCRIPTS):
    assert WHEELS.is_dir(), "Prepare locked wheels using tests/acceptance/runtime.py --download."
    completed = invoke(python, data, "env", "prepare", "--wheelhouse", str(WHEELS), *args, scripts=scripts)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    return json.loads(completed.stdout)["outputs"]["runtime"]


def test_doctor_without_dependencies_is_structured_and_read_only(bare_python, tmp_path):
    data = tmp_path / "data"
    completed = invoke(bare_python, data, "doctor")
    assert completed.returncode == 2
    report = json.loads(completed.stdout)
    assert report["tool_version"] == tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    assert report["diagnostics"][0]["rule_id"] == "TAO-RUNTIME-002"
    assert report["outputs"]["runtime"]["state"] == "missing"
    joined = subprocess.run([str(bare_python), str(SCRIPTS / "tao.py"), "doctor", "--format=json"],
                            env=os.environ | {"TAO_RUNTIME_DIR": str(data), "TAO_PYTHON": str(bare_python)},
                            capture_output=True, text=True)
    assert json.loads(joined.stdout)["tool_version"] == report["tool_version"]
    assert not data.exists()


def test_offline_preparation_runs_without_uv_and_does_not_modify_base(bare_python, tmp_path):
    before = subprocess.check_output([str(bare_python), "-m", "pip", "list", "--format", "json"])
    data = tmp_path / "runtime data"
    info = prepare(bare_python, data)
    assert info["mode"] == "core"
    assert Path(info["python"]).is_file()
    assert info["publication"]["state"] == "ready"
    assert Path(info["publication"]["python"]).is_file()
    report = invoke(bare_python, data, "id", "new", "REQ", "--project", str(tmp_path), extra={"PATH": ""})
    assert report.returncode == 0, report.stdout + report.stderr
    assert json.loads(report.stdout)["outputs"]["id"].startswith("REQ_")
    assert invoke(bare_python, data, "doctor", extra={"PATH": ""}).returncode == 0
    after = subprocess.check_output([str(bare_python), "-m", "pip", "list", "--format", "json"])
    assert before == after
    assert prepare(bare_python, data)["python"] == info["python"]


def test_failed_complete_setup_keeps_existing_core_and_does_not_implicitly_install(bare_python, tmp_path):
    scripts = tmp_path / "plugin/scripts"
    shutil.copytree(SCRIPTS, scripts, ignore=shutil.ignore_patterns("__pycache__"))
    data = tmp_path / "data"
    info = prepare(bare_python, data, scripts=scripts)
    requirements = scripts / "requirements-publication.txt"
    requirements.write_text(requirements.read_text() + "\n# New publication inventory\n")
    empty = tmp_path / "empty-wheels"
    empty.mkdir()
    failed = invoke(bare_python, data, "env", "prepare", "--wheelhouse", str(empty), scripts=scripts)
    assert failed.returncode == 2
    assert json.loads(failed.stdout)["status"] == "not_run"
    assert Path(info["python"]).is_file()
    core = subprocess.run([info["python"], "-I", "-c", "import markdown_it, yaml"],
                          capture_output=True, text=True)
    assert core.returncode == 0, core.stdout + core.stderr
    before = sorted(str(p.relative_to(data)) for p in data.rglob("*"))
    missing = invoke(bare_python, data, "docs", "build", "--project", str(tmp_path), scripts=scripts)
    assert missing.returncode == 2
    assert "publication" in missing.stdout
    assert sorted(str(p.relative_to(data)) for p in data.rglob("*")) == before


def test_env_prepare_rejects_removed_publication_option(bare_python, tmp_path):
    completed = invoke(bare_python, tmp_path / "data", "env", "prepare", "--publication")
    assert completed.returncode == 2
    assert "unrecognized arguments: --publication" in completed.stderr


def test_changed_dependencies_use_another_environment_and_preserve_old(bare_python, tmp_path):
    scripts = tmp_path / "plugin/scripts"
    shutil.copytree(SCRIPTS, scripts, ignore=shutil.ignore_patterns("__pycache__"))
    data = tmp_path / "data"
    first = prepare(bare_python, data, scripts=scripts)
    requirements = scripts / "requirements.txt"
    requirements.write_text(requirements.read_text() + "\n# New release inventory\n")
    second = prepare(bare_python, data, scripts=scripts)
    assert first["python"] != second["python"]
    assert Path(first["python"]).is_file()


def test_readonly_plugin_and_claude_data_location(bare_python, tmp_path):
    plugin = tmp_path / "readonly plugin"
    shutil.copytree(SCRIPTS, plugin, ignore=shutil.ignore_patterns("__pycache__"))
    for path in plugin.rglob("*"):
        path.chmod(0o555 if path.is_dir() else 0o444)
    data = tmp_path / "claude data"
    env = os.environ | {"CLAUDE_PLUGIN_DATA": str(data), "TAO_PYTHON": str(bare_python)}
    env.pop("TAO_RUNTIME_DIR", None)
    completed = subprocess.run([str(bare_python), str(plugin / "tao.py"), "env", "prepare", "--wheelhouse", str(WHEELS), "--format", "json"],
                               env=env, capture_output=True, text=True)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    runtime = json.loads(completed.stdout)["outputs"]["runtime"]
    selected = Path(runtime["python"])
    assert selected.is_relative_to(data)
    assert Path(runtime["publication"]["python"]).is_relative_to(data)
    assert not list(plugin.rglob("__pycache__"))


def test_concurrent_preparation_publishes_one_complete_environment(bare_python, tmp_path):
    data = tmp_path / "data"
    env = os.environ | {"TAO_RUNTIME_DIR": str(data), "TAO_PYTHON": str(bare_python)}
    argv = [str(bare_python), str(SCRIPTS / "tao.py"), "env", "prepare", "--wheelhouse", str(WHEELS), "--format", "json"]
    processes = [subprocess.Popen(argv, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(2)]
    outputs = [process.communicate(timeout=60) for process in processes]
    assert all(p.returncode == 0 for p in processes), outputs
    reports = [json.loads(stdout)["outputs"]["runtime"] for stdout, _ in outputs]
    selected = [report["python"] for report in reports]
    assert selected[0] == selected[1]
    assert reports[0]["publication"]["python"] == reports[1]["publication"]["python"]
    assert len(list(data.rglob("ready.json"))) == 2
    assert not list(data.rglob("prepare.lock"))


def test_corrupt_environment_requires_explicit_repair(bare_python, tmp_path):
    data = tmp_path / "data"
    first = prepare(bare_python, data)
    marker = Path(first["python"]).parent.parent / "ready.json"
    marker.write_text("{}")
    broken = invoke(bare_python, data, "doctor")
    assert broken.returncode == 2
    assert json.loads(broken.stdout)["outputs"]["runtime"]["state"] == "broken"
    second = prepare(bare_python, data)
    assert first["python"] != second["python"]
    assert Path(first["python"]).is_file()


def test_explicit_missing_interpreter_never_falls_back(bare_python, tmp_path):
    data = tmp_path / "data"
    completed = invoke(bare_python, data, "env", "prepare", extra={"TAO_PYTHON": str(tmp_path / "absent")})
    assert completed.returncode == 2
    assert json.loads(completed.stdout)["diagnostics"][0]["rule_id"] == "TAO-RUNTIME-001"
    assert not data.exists()


def test_symlinked_runtime_slot_never_writes_outside_data(bare_python, tmp_path):
    data, outside = tmp_path / "data", tmp_path / "outside"
    data.mkdir()
    outside.mkdir()
    (data / "runtimes").symlink_to(outside, target_is_directory=True)
    failed = invoke(bare_python, data, "env", "prepare", "--wheelhouse", str(WHEELS))
    assert failed.returncode == 2
    assert list(outside.iterdir()) == []


def test_readonly_release_copy_builds_book_without_uv(tmp_path, tool_runtime):
    from test_publication import project
    plugin = tmp_path / "独立 plugin"
    shutil.copytree(SCRIPTS.parent, plugin, ignore=shutil.ignore_patterns("__pycache__"))
    for path in plugin.rglob("*"):
        path.chmod(0o555 if path.is_dir() else 0o444)
    root = tmp_path / "consumer"
    root.mkdir()
    project(root)
    result = invoke(sys.executable, tool_runtime, "docs", "build", "--project", str(root),
                    scripts=plugin / "scripts", cwd=root, extra={"PATH": ""})
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert (root / report["outputs"]["directory"] / "docs/spec.html").is_file()
    assert not list(plugin.rglob("__pycache__"))


def test_failed_interpreter_probe_reports_exit_failure_before_decoding(monkeypatch):
    import importlib.util
    spec = importlib.util.spec_from_file_location('runtime_probe_test', SCRIPTS / 'runtime.py')
    runtime = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runtime)
    monkeypatch.setattr(runtime.subprocess, 'run', lambda *a, **kw: subprocess.CompletedProcess(a[0], 1, '', ''))
    with pytest.raises(runtime.RuntimeFailure, match='Interpreter probe failed'):
        runtime.inspect_python('/unavailable/python')
