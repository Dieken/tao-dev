#!/usr/bin/env python3
"""Bounded PostToolUse feedback; never runs a model or a project command."""

import hashlib
from importlib.metadata import PackageNotFoundError, version
import json
from pathlib import Path
import subprocess
import sys
import time

from taolib.project import ConfigurationError, Project, contained, mutation_lock, create_file, replace_file


def feedback(message):
    return {"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": message}}


def run(payload):
    if payload.get("hook_event_name") != "PostToolUse":
        return {}
    # The host's working directory determines scope; untrusted tool input
    # never selects the project or becomes an executable command.
    try:
        project = Project()
    except ConfigurationError:
        if not any((p / ".tao/config.toml").is_file() for p in [Path.cwd(), *Path.cwd().parents]):
            return {}
        raise
    if not project.hook_enabled:
        return {}
    deadline = time.monotonic() + project.hook_timeout
    scripts = Path(__file__).resolve().parent
    inputs = project.sources() + list(project.output("retired").glob("*.jsonl"))
    inputs += [project.root / ".tao/config.toml"]
    for path in inputs:
        contained(project.root, path)
    inputs += list(scripts.rglob("*.py")) + [scripts.parent / "assets/document-profiles.json"]
    digest = hashlib.sha256()
    digest.update(sys.version.encode())
    for dependency in ("markdown-it-py", "PyYAML"):
        try:
            digest.update(version(dependency).encode())
        except PackageNotFoundError:
            digest.update(b"missing")
    for path in sorted(set(inputs)):
        digest.update(str(path).encode() + b"\0")
        with path.open("rb") as stream:
            while chunk := stream.read(131072):
                if time.monotonic() >= deadline:
                    return feedback("tao docs not_run: input scan exceeded the hook budget; run explicit verification.")
                digest.update(chunk)
        digest.update(b"\0")
    fingerprint = digest.hexdigest()
    cache = project.output("temporary", "cache/hook.json")
    with mutation_lock(project):
        before = cache.read_bytes() if cache.exists() else None
        try:
            previous = json.loads(before) if before else {}
        except (ValueError, TypeError):
            previous = {}
        if previous.get("fingerprint") == fingerprint:
            return feedback("tao docs feedback (unchanged inputs): " + previous["message"])
        command = [sys.executable, str(scripts / "tao.py"), "--project", str(project.root), "verify", "--only", "docs", "--format", "json"]
        try:
            completed = subprocess.run(command, capture_output=True, text=True, timeout=max(0.001, deadline - time.monotonic()))
            report = json.loads(completed.stdout)
            details = "; ".join(f"{d.get('path', '')}:{d.get('line', 1)} {d['rule_id']}: {d['message']}" for d in report["diagnostics"][:8])
            message = f"{report['status']} (docs only, partial; not delivery acceptance). {details}"[:3000]
        except subprocess.TimeoutExpired:
            return feedback("tao docs not_run: hook time budget exceeded; run explicit verification with an appropriate budget.")
        except (ValueError, KeyError):
            return feedback("tao docs not_run: validator could not return a report; check its Python dependencies with the trusted entry point.")
        text = json.dumps({"fingerprint": fingerprint, "message": message}, ensure_ascii=False) + "\n"
        if before is None:
            create_file(project.root, cache, text)
        else:
            replace_file(project.root, cache, text, before)
        return feedback("tao docs feedback: " + message)


def main():
    try:
        payload = json.loads(sys.stdin.read(1_000_001))
        if not isinstance(payload, dict):
            raise ValueError("Expected a hook event object.")
        response = run(payload)
    except (OSError, ValueError) as exc:
        response = feedback(f"tao docs not_run: {exc}")
    print(json.dumps(response, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
