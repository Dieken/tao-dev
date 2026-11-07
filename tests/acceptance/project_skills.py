"""Project-only complete skill copy and opt-in non-billable native discovery."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import queue
import shutil
import subprocess
import tempfile
import threading
import time

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "skills/tao-dev"
CLIENT_PATHS = {
    "claude": ".claude/skills/tao-dev",
    "codex": ".agents/skills/tao-dev",
    "cursor": ".agents/skills/tao-dev",
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


def snapshot(directory, *, ignore_bytecode=False):
    return {
        path.relative_to(directory).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        if path.is_file() else None
        for path in sorted(directory.rglob("*"))
        if not ignore_bytecode or not any(
            part == "__pycache__" or part.endswith(".pyc")
            for part in path.relative_to(directory).parts
        )
    }


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


def assert_discovery(rows, inside, outside, *, copied):
    expected = inside / CLIENT_PATHS["codex"] / "SKILL.md"
    found = [skill for skill in rows[inside] if skill["name"] == "tao-dev"]
    if copied:
        if len(found) != 1 or not found[0].get("enabled"):
            raise RuntimeError("Codex did not discover exactly one enabled project tao-dev skill")
        if Path(found[0]["path"]).resolve() != expected.resolve():
            raise RuntimeError("Codex discovered tao-dev from a different location")
    elif found:
        raise RuntimeError("Codex still discovered tao-dev after removing the copied skill")
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
        inside_before = snapshot(inside)
        home_before = snapshot(workspace / "home")
        outside_before = snapshot(outside)
        source_before = snapshot(SOURCE, ignore_bytecode=True)
        for resource in ("SKILL.md", "references", "assets", "scripts/tao.py",
                         "scripts/requirements.txt", "scripts/requirements-publication.txt"):
            if resource not in source_before:
                raise RuntimeError(f"Source skill is missing {resource}")
        shutil.copytree(SOURCE, destination, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        if snapshot(destination) != source_before:
            raise RuntimeError("Copied skill differs from the complete source bundle")
        if snapshot(workspace / "home") != home_before:
            raise RuntimeError("Copying the skill changed the isolated home directory")
        if native:
            assert_discovery(discover_codex([inside, outside], environment), inside, outside, copied=True)
        home_before_removal = snapshot(workspace / "home")
        shutil.rmtree(destination)
        if destination.exists():
            raise RuntimeError("Removing the copied skill left files behind")
        if snapshot(workspace / "home") != home_before_removal:
            raise RuntimeError("Removing the copied skill changed the isolated home directory")
        if native:
            assert_discovery(discover_codex([inside, outside], environment), inside, outside, copied=False)
        if snapshot(inside) != inside_before:
            raise RuntimeError("Copy acceptance changed project knowledge or neighboring files")
        if snapshot(outside) != outside_before:
            raise RuntimeError("Copy acceptance changed the untouched project")
        if not native and snapshot(workspace / "home") != home_before:
            raise RuntimeError("Copy acceptance changed the isolated home directory")
        if snapshot(SOURCE, ignore_bytecode=True) != source_before:
            raise RuntimeError("Copy acceptance changed the source skill")
    return {"client": client, "copy": "passed", "native_discovery": "passed" if native else "not_run"}


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
