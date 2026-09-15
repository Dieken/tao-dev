"""Installation receipts bind native plugin copies to isolated runtimes."""

import importlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "plugins/tao-dev/skills/tao-dev/scripts"


@pytest.fixture
def registry(tmp_path, monkeypatch):
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "codex"))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "claude"))
    monkeypatch.delenv("TAO_PYTHON", raising=False)
    monkeypatch.delenv("TAO_RUNTIME_DIR", raising=False)
    assert importlib.util.find_spec("installed_runtime"), "Installation registry is not implemented"
    return importlib.import_module("installed_runtime")


def receipt(registry, tmp_path, client="codex", scope="user", project=None):
    root = registry.managed_root(client, scope, project)
    base = tmp_path / "cache" / "tao-dev"
    return {"schema": 1, "id": registry.install_id(client, scope, project),
            "client": client, "scope": scope,
            "project": str(project.resolve()) if project is not None else None,
            "managed_root": str(root), "plugin_id": "tao-dev@test",
            "plugin_path": str(base / "1.0"), "plugin_base": str(base),
            "python": sys.executable, "runtime_dir": str(root / "runtime"),
            "version": "1.0", "source": {"kind": "test"}, "status": "ready", "files": []}


def test_receipts_round_trip_without_writing_during_discovery(registry, tmp_path):
    assert registry.records("codex") == []
    assert not (tmp_path / "codex").exists()
    record = receipt(registry, tmp_path)
    record["native"] = {"cache_shared": True}
    path = registry.save_record(record)
    assert path == tmp_path / "codex/tao-dev/installations" / (record["id"] + ".json")
    assert registry.records("codex") == [record]
    assert not list(path.parent.glob(".write-*"))


def test_binding_selects_deepest_eligible_scope_and_survives_cache_upgrade(registry, tmp_path):
    project = tmp_path / "project"
    child = project / "nested"
    entries = [receipt(registry, tmp_path),
               receipt(registry, tmp_path, scope="project", project=project),
               receipt(registry, tmp_path, scope="local", project=project),
               receipt(registry, tmp_path, scope="project", project=child)]
    for record in entries:
        registry.save_record(record)
    scripts = tmp_path / "cache/tao-dev/2.0/skills/tao-dev/scripts"
    assert registry.binding(scripts, child / "src")["id"] == entries[3]["id"]
    assert registry.binding(scripts, project / "src")["id"] == entries[2]["id"]
    assert registry.binding(scripts, tmp_path / "outside")["id"] == entries[0]["id"]
    assert registry.binding(tmp_path / "unrelated/scripts", project) is None


def test_project_binding_does_not_activate_outside_project(registry, tmp_path):
    record = receipt(registry, tmp_path, client="claude", scope="local", project=tmp_path / "project")
    registry.save_record(record)
    scripts = Path(record["plugin_path"]) / "skills/tao-dev/scripts"
    assert registry.binding(scripts, tmp_path / "project/subdir") == record
    assert registry.binding(scripts, tmp_path / "project-other") is None
    record["status"] = "preparing"
    registry.save_record(record)
    assert registry.binding(scripts, tmp_path / "project") is None


@pytest.mark.parametrize("change", [
    {"id": "../escape"}, {"managed_root": "/"}, {"runtime_dir": "/tmp"},
    {"plugin_base": "/"}, {"python": "python3"}, {"project": "/tmp"},
])
def test_unsafe_receipt_cannot_be_saved(registry, tmp_path, change):
    record = receipt(registry, tmp_path) | change
    with pytest.raises(ValueError):
        registry.save_record(record)
    assert registry.records("codex") == []


def test_malformed_and_symlinked_receipts_are_ignored(registry, tmp_path):
    record = receipt(registry, tmp_path)
    path = registry.save_record(record)
    path.write_text("{broken")
    assert registry.binding(Path(record["plugin_path"]), tmp_path) is None
    external = tmp_path / "external.json"
    external.write_text(json.dumps(record))
    path.unlink()
    path.symlink_to(external)
    assert registry.records("codex") == []
    with pytest.raises(ValueError):
        registry.save_record(record)
    assert json.loads(external.read_text()) == record


def test_symlinked_owned_directories_are_rejected(registry, tmp_path):
    record = receipt(registry, tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    home = tmp_path / "codex"
    home.mkdir()
    (home / "tao-dev").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError):
        registry.save_record(record)
    assert registry.records("codex") == []
    assert not list(outside.iterdir())


def test_cache_base_cannot_bind_other_plugins(registry, tmp_path):
    record = receipt(registry, tmp_path)
    record["plugin_base"] = str(tmp_path / "cache")
    with pytest.raises(ValueError):
        registry.save_record(record)


def test_receipt_own_path_and_project_symlinks_are_rejected(registry, tmp_path):
    record = receipt(registry, tmp_path)
    path = registry.save_record(record)
    path.rename(path.with_name("another-installation.json"))
    assert registry.records("codex") == []
    project = tmp_path / "consumer"
    project.mkdir()
    scoped = receipt(registry, tmp_path, scope="local", project=project)
    outside = tmp_path / "outside"
    outside.mkdir()
    (project / ".local").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError):
        registry.save_record(scoped)
    assert not list(outside.iterdir())


def test_runtime_prefers_receipt_over_claude_data_and_keeps_explicit_overrides(registry, tmp_path, monkeypatch):
    import runtime
    record = receipt(registry, tmp_path)
    recorded_python = tmp_path / "recorded-python"
    recorded_python.symlink_to(sys.executable)
    record["python"] = str(recorded_python)
    record.update(plugin_path=str(SCRIPTS.parent.parent.parent), plugin_base=str(SCRIPTS.parent.parent.parent))
    registry.save_record(record)
    monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path / "claude-data"))
    before = dict(os.environ)
    ctx = runtime.context("core")
    assert ctx["root"] == Path(record["runtime_dir"])
    assert ctx["base_python"] == str(recorded_python)
    assert dict(os.environ) == before
    monkeypatch.setenv("TAO_RUNTIME_DIR", str(tmp_path / "explicit"))
    monkeypatch.setenv("TAO_PYTHON", str(tmp_path / "absent-python"))
    with pytest.raises(runtime.RuntimeFailure):
        runtime.context("core")
    monkeypatch.setenv("TAO_PYTHON", sys.executable)
    assert runtime.context("core")["root"] == tmp_path / "explicit"


@pytest.mark.parametrize("project_args", [lambda p: ["--project", str(p)], lambda p: ["--project=" + str(p)]])
def test_cli_binding_uses_project_argument_and_reexecutes_without_tao_variables(registry, tmp_path, project_args):
    project = tmp_path / "consumer"
    project.mkdir()
    plugin = tmp_path / "cache/tao-dev/1.0"
    shutil.copytree(SCRIPTS.parent.parent.parent, plugin, ignore=shutil.ignore_patterns("__pycache__"))
    record = receipt(registry, tmp_path, scope="project", project=project)
    # Prepare at its permanent location: copied venvs cannot be relocated safely.
    managed = Path(record["runtime_dir"])
    env = dict(os.environ) | {"TAO_RUNTIME_DIR": str(managed), "TAO_PYTHON": sys.executable}
    wheels = Path(os.environ.get("TAO_TEST_WHEELHOUSE", SCRIPTS.parents[4] / "tmp/tao/wheels"))
    setup = subprocess.run([sys.executable, str(plugin / "skills/tao-dev/scripts/tao.py"),
                            "setup", "--wheelhouse", str(wheels), "--format", "json"],
                           env=env, capture_output=True, text=True, check=False)
    assert setup.returncode == 0, setup.stdout + setup.stderr
    registry.save_record(record)
    clean_env = dict(os.environ)
    clean_env.pop("TAO_RUNTIME_DIR", None)
    clean_env.pop("TAO_PYTHON", None)
    clean_env["CLAUDE_PLUGIN_DATA"] = str(tmp_path / "wrong-data")
    reuse = subprocess.run([sys.executable, str(plugin / "skills/tao-dev/scripts/tao.py"),
                            "setup", *project_args(project), "--format", "json"],
                           cwd=tmp_path, env=clean_env, capture_output=True, text=True, timeout=30, check=False)
    assert reuse.returncode == 0, reuse.stdout + reuse.stderr
    result = subprocess.run([sys.executable, str(plugin / "skills/tao-dev/scripts/tao.py"),
                             "doctor", *project_args(project), "--format", "json"],
                            cwd=tmp_path, env=clean_env, capture_output=True, text=True, timeout=30, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["outputs"]["runtime"]["data_directory"] == str(managed)
    from test_hooks import project as configure_project
    configure_project(project)
    hook = subprocess.run([sys.executable, str(plugin / "skills/tao-dev/scripts/hook.py")],
                          cwd=project, env=clean_env, input='{"hook_event_name":"PostToolUse"}',
                          capture_output=True, text=True, timeout=30, check=False)
    assert hook.returncode == 0, hook.stdout + hook.stderr
    assert "passed" in json.loads(hook.stdout)["hookSpecificOutput"]["additionalContext"]


def test_shared_cli_routes_across_clients_to_each_native_inventory(registry, tmp_path):
    import installation
    clean = dict(os.environ)
    clean.pop("TAO_RUNTIME_DIR", None)
    clean.pop("TAO_PYTHON", None)
    wheels = Path(os.environ.get("TAO_TEST_WHEELHOUSE", SCRIPTS.parents[4] / "tmp/tao/wheels"))
    installed = []
    for client in ("codex", "claude"):
        project = tmp_path / (client + "-project")
        project.mkdir()
        native = tmp_path / "cache" / client / "tao-dev/1.0"
        shutil.copytree(SCRIPTS.parent.parent.parent, native, ignore=shutil.ignore_patterns("__pycache__"))
        if client == "claude":
            inventory = native / "skills/tao-dev/scripts/requirements.txt"
            inventory.write_text(inventory.read_text() + "\n# Distinct newer dependency inventory\n")
        row = receipt(registry, tmp_path, client=client, scope="project", project=project)
        row.update(plugin_path=str(native), plugin_base=str(native.parent))
        setup = subprocess.run([sys.executable, str(native / "skills/tao-dev/scripts/tao.py"),
                                "setup", "--wheelhouse", str(wheels), "--format", "json"],
                               env=clean | {"TAO_RUNTIME_DIR": row["runtime_dir"], "TAO_PYTHON": sys.executable},
                               capture_output=True, text=True, check=False)
        assert setup.returncode == 0, setup.stdout + setup.stderr
        launcher, shared = installation.install_cli(client, sys.executable, tmp_path / "bin", native)
        row["cli_path"] = str(shared)
        registry.save_record(row)
        installed.append(row)
    # The second client replaced the same command; it must still route to the
    # first client's original package and its different dependency inventory.
    for row in installed:
        result = subprocess.run([str(launcher), "doctor", "--project", row["project"], "--format", "json"],
                                cwd=tmp_path, env=clean, capture_output=True, text=True, timeout=30, check=False)
        assert result.returncode == 0, result.stdout + result.stderr
        assert json.loads(result.stdout)["outputs"]["runtime"]["data_directory"] == row["runtime_dir"]
        reuse = subprocess.run([str(launcher), "setup", "--project", row["project"],
                                "--wheelhouse", str(wheels), "--format", "json"],
                               cwd=tmp_path, env=clean, capture_output=True, text=True, timeout=30, check=False)
        assert reuse.returncode == 0, reuse.stdout + reuse.stderr
        assert (json.loads(reuse.stdout)["outputs"]["runtime"]["python"]
                == json.loads(result.stdout)["outputs"]["runtime"]["python"])
    outside = subprocess.run([str(launcher), "doctor", "--format", "json"],
                             cwd=tmp_path, env=clean, capture_output=True, text=True, timeout=30, check=False)
    assert outside.returncode == 2
    assert "tao install" in outside.stdout
    override = tmp_path / "explicit-missing-runtime"
    explicit = subprocess.run([str(launcher), "doctor", "--project", installed[0]["project"], "--format", "json"],
                              cwd=tmp_path, env=clean | {"TAO_RUNTIME_DIR": str(override)},
                              capture_output=True, text=True, timeout=30, check=False)
    assert explicit.returncode == 2
    assert json.loads(explicit.stdout)["outputs"]["runtime"]["data_directory"] == str(override)
    shutil.rmtree(installed[0]["plugin_path"])
    missing = subprocess.run([str(launcher), "doctor", "--project", installed[0]["project"], "--format", "json"],
                             cwd=tmp_path, env=clean, capture_output=True, text=True, timeout=30, check=False)
    assert missing.returncode == 2
    assert "tao install" in missing.stdout
