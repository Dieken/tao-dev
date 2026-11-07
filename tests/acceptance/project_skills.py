"""Project-only installation and non-billable native discovery acceptance."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
import time

ROOT = Path(__file__).resolve().parents[2]
ENTRY = ROOT / "skills/tao-dev/scripts/tao.py"
CLIENT_PATHS = {
    "claude": ".claude/skills/tao-dev",
    "codex": ".agents/skills/tao-dev",
    "cursor": ".cursor/skills/tao-dev",
    "kiro": ".kiro/skills/tao-dev",
}


def isolated_environment(workspace):
    """Never inherit credentials, client settings, or the real home directory."""
    home = workspace / "home"
    home.mkdir()
    environment = {key: os.environ[key] for key in (
        "PATH", "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT",
    ) if key in os.environ}
    environment.update({
        "HOME": str(home), "USERPROFILE": str(home),
        "CODEX_HOME": str(home / ".codex"),
        "XDG_CONFIG_HOME": str(home / ".config"),
        "XDG_DATA_HOME": str(home / ".local/share"),
        "XDG_CACHE_HOME": str(home / ".cache"),
        "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
        "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1",
    })
    for name in ("CODEX_HOME", "XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME"):
        Path(environment[name]).mkdir(parents=True, exist_ok=True)
    temporary = workspace / "tmp"
    temporary.mkdir()
    environment.update(TMPDIR=str(temporary), TMP=str(temporary), TEMP=str(temporary))
    return environment


def snapshot(directory):
    return {
        str(path.relative_to(directory)): hashlib.sha256(path.read_bytes()).hexdigest()
        if path.is_file() else None
        for path in sorted(directory.rglob("*"))
    }


def invoke(action, project, client, environment):
    result = subprocess.run(
        [sys.executable, "-I", "-S", "-B", str(ENTRY), action,
         "--project", str(project), "--client", client, "--format", "json"],
        cwd=project, env=environment, capture_output=True, text=True,
        encoding="utf-8", timeout=30, check=False,
    )
    if result.returncode:
        raise RuntimeError(f"{client} {action} failed: {result.stdout}\n{result.stderr}")
    return json.loads(result.stdout)


def _stop(process):
    """Reap the read-only inspector, without signalling an exited process group."""
    process.terminate()
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=3)


def discover_codex(projects, environment, *, timeout=20):
    """Only initialize and skills/list; no threads, turns, auth, or model calls."""
    if not 0 < timeout <= 60:
        raise ValueError("Discovery timeout must be greater than zero and at most 60 seconds")
    executable = shutil.which("codex")
    if executable is None:
        raise RuntimeError("Codex CLI is not installed; native discovery was not performed")
    projects = [path.resolve() for path in projects]
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as errors:
        process = subprocess.Popen(
            [executable, "app-server"], cwd=projects[0], env=environment,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=errors,
            text=True, encoding="utf-8",
        )
        responses = queue.Queue()

        def collect():
            try:
                for line in process.stdout:
                    responses.put(line)
            finally:
                responses.put(None)

        reader = threading.Thread(target=collect, daemon=True)
        reader.start()
        deadline = time.monotonic() + timeout

        def send(payload):
            process.stdin.write(json.dumps(payload) + "\n")
            process.stdin.flush()

        def receive(identity):
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise RuntimeError("Codex skills/list timed out")
                try:
                    line = responses.get(timeout=remaining)
                except queue.Empty as exc:
                    raise RuntimeError("Codex skills/list timed out") from exc
                if line is None:
                    raise RuntimeError("Codex app-server exited before responding")
                value = json.loads(line)
                if value.get("id") != identity:
                    continue
                if "error" in value:
                    raise RuntimeError(f"Codex discovery failed: {value['error']}")
                return value["result"]

        try:
            send({"id": 1, "method": "initialize", "params": {
                "clientInfo": {"name": "tao-acceptance", "version": "1.0"},
                "capabilities": {"experimentalApi": True},
            }})
            receive(1)
            send({"method": "initialized"})
            send({"id": 2, "method": "skills/list", "params": {
                "cwds": [str(path) for path in projects], "forceReload": True,
            }})
            result = receive(2)
        finally:
            _stop(process)
            process.stdin.close()
            reader.join(timeout=3)
            if reader.is_alive():
                raise RuntimeError("Codex discovery output reader did not stop")
            process.stdout.close()
    rows = {}
    for row in result["data"]:
        if row.get("errors"):
            raise RuntimeError(f"Codex skill scan reported errors: {row['errors']}")
        cwd = Path(row["cwd"]).resolve()
        if cwd in rows:
            raise RuntimeError(f"Codex returned duplicate skill results for {cwd}")
        rows[cwd] = row["skills"]
    if set(rows) != set(projects):
        raise RuntimeError("Codex omitted or added a requested project")
    return rows


def assert_discovery(rows, inside, outside, *, installed):
    expected = inside / CLIENT_PATHS["codex"] / "SKILL.md"
    found = [skill for skill in rows[inside] if skill["name"] == "tao-dev"]
    if installed:
        if len(found) != 1 or not found[0].get("enabled"):
            raise RuntimeError("Codex did not discover exactly one enabled project tao-dev skill")
        if Path(found[0]["path"]).resolve() != expected.resolve():
            raise RuntimeError("Codex discovered tao-dev from a different location")
    elif found:
        raise RuntimeError("Codex still discovered tao-dev after uninstall")
    if any(skill["name"] == "tao-dev" for skill in rows[outside]):
        raise RuntimeError("Codex discovered tao-dev in the untouched project")


def run(client, *, native=False):
    if client not in CLIENT_PATHS:
        raise ValueError(f"Unsupported client: {client}")
    if native and client != "codex":
        raise ValueError("Native discovery acceptance is implemented only for Codex")
    with tempfile.TemporaryDirectory(prefix="tao-project-skill-") as temporary:
        workspace = Path(temporary).resolve()
        environment = isolated_environment(workspace)
        inside, outside = workspace / "inside", workspace / "outside"
        for project in (inside, outside):
            project.mkdir()
            (project / ".git").mkdir()
            (project / "docs").mkdir()
            (project / "docs/keep.md").write_text("User project knowledge.\n", encoding="utf-8")
        destination = inside / CLIENT_PATHS[client]
        sibling = destination.parent / "user-skill"
        sibling.mkdir(parents=True)
        user_skill = "---\nname: user-skill\ndescription: User-owned local skill.\n---\n\nUser-owned skill.\n"
        (sibling / "SKILL.md").write_text(user_skill, encoding="utf-8")
        home_before = snapshot(workspace / "home")
        outside_before = snapshot(outside)
        source = (ROOT / "skills/tao-dev/SKILL.md").read_bytes()
        invoke("install", inside, client, environment)
        if (destination / "SKILL.md").read_bytes() != source:
            raise RuntimeError("Installed skill differs from the source")
        installed_before = snapshot(destination)
        for _ in range(2):
            invoke("upgrade", inside, client, environment)
        if snapshot(destination) != installed_before:
            raise RuntimeError("Repeated upgrade changed the installed skill")
        listing = invoke("list", inside, client, environment)
        rows = listing["outputs"]["installations"]
        if len(rows) != 1 or rows[0]["client"] != client or rows[0]["state"] != "installed":
            raise RuntimeError("List did not report the installed project skill")
        if snapshot(workspace / "home") != home_before:
            raise RuntimeError("Installation changed the isolated home directory")
        if native:
            assert_discovery(discover_codex([inside, outside], environment), inside, outside, installed=True)
        invoke("uninstall", inside, client, environment)
        if destination.exists():
            raise RuntimeError("Uninstall left the managed skill behind")
        if (inside / "docs/keep.md").read_text(encoding="utf-8") != "User project knowledge.\n":
            raise RuntimeError("Uninstall changed project knowledge")
        if (sibling / "SKILL.md").read_text(encoding="utf-8") != user_skill:
            raise RuntimeError("Uninstall changed an unmanaged skill")
        if snapshot(outside) != outside_before:
            raise RuntimeError("Lifecycle changed the untouched project")
        if not native and snapshot(workspace / "home") != home_before:
            raise RuntimeError("Lifecycle changed the isolated home directory")
        if invoke("list", inside, client, environment)["outputs"]["installations"]:
            raise RuntimeError("List still reported the uninstalled project skill")
        if native:
            assert_discovery(discover_codex([inside, outside], environment), inside, outside, installed=False)
    return {"client": client, "lifecycle": "passed", "native_discovery": "passed" if native else "not_run"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--client", choices=tuple(CLIENT_PATHS), required=True)
    parser.add_argument("--native", action="store_true", help="Inspect Codex skills/list without invoking a model")
    args = parser.parse_args()
    if args.native and args.client != "codex":
        parser.error("--native supports only --client codex")
    print(json.dumps(run(args.client, native=args.native)))


if __name__ == "__main__":
    main()
