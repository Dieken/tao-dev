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
from tao_messages import Message, configured_locale, diagnostic


def feedback(message, event="PostToolUse"):
    # Claude/Codex use nested hookSpecificOutput; Cursor postToolUse uses
    # additional_context at the top level.
    if event == "postToolUse":
        return {"additional_context": message}
    return {"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": message}}


def run(payload):
    event = payload.get("hook_event_name")
    if event not in ("PostToolUse", "postToolUse"):
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
    locale = project.diagnostic_locale or project.locale

    def display(message):
        return diagnostic(message, locale)['message']
    deadline = time.monotonic() + project.hook_timeout
    scripts = Path(__file__).resolve().parents[1]
    inputs = project.sources() + list(project.output("retired").glob("*.jsonl"))
    inputs += [project.root / ".tao/config.toml"]
    for path in inputs:
        contained(project.root, path)
    inputs += list(scripts.rglob("*.py")) + list((scripts.parent / "assets").rglob("*.json"))
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
                    return feedback(display("tao docs not_run: input scan exceeded the hook budget; run explicit verification."), event)
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
        if isinstance(previous, dict) and previous.get("fingerprint") == fingerprint and isinstance(previous.get("message"), str):
            return feedback(display(Message('tao docs feedback (unchanged inputs): {arg0}', previous['message'])), event)
        command = [sys.executable, str(scripts / "tao.py"), "--project", str(project.root), "verify", "--only", "docs", "--format", "json"]
        try:
            completed = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=max(0.001, deadline - time.monotonic()))
            report = json.loads(completed.stdout)
            details = "; ".join(f"{d.get('path', '')}:{d.get('line', 1)} {d['rule_id']}: {d['message']}" for d in report["diagnostics"][:8])
            message = display(Message('{arg0} (docs only, partial; not delivery acceptance). {arg1}', report['status'], details))[:3000]
        except subprocess.TimeoutExpired:
            return feedback(display("tao docs not_run: hook time budget exceeded; run explicit verification with an appropriate budget."), event)
        except (ValueError, KeyError):
            return feedback(display("tao docs not_run: validator could not return a report; check its Python dependencies with the trusted entry point."), event)
        text = json.dumps({"fingerprint": fingerprint, "message": message}, ensure_ascii=False) + "\n"
        if before is None:
            create_file(project.root, cache, text)
        else:
            replace_file(project.root, cache, text, before)
        return feedback(display(Message('tao docs feedback: {arg0}', message)), event)


def main():
    event = "PostToolUse"
    try:
        payload = json.loads(sys.stdin.read(1_000_001))
        if not isinstance(payload, dict):
            raise ValueError("Expected a hook event object.")
        event = payload.get("hook_event_name") or event
        response = run(payload)
    except (OSError, ValueError) as exc:
        response = feedback('tao docs not_run: ' + diagnostic(exc, configured_locale())['message'],
                            event if event in ("PostToolUse", "postToolUse") else "PostToolUse")
    print(json.dumps(response, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
