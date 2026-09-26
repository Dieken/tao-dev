"""Opt-in real multi-turn behavior acceptance for Claude Code and Codex."""

import argparse
import json
import os
import subprocess
import sys
import time
from contextlib import nullcontext
from dataclasses import replace
from pathlib import Path

from acceptance.behavior_contract import load_catalog
from acceptance.behavior_runner import SubprocessExecutor, run_scenario
from acceptance.behavior_trace import FILE_EVENTS
from acceptance.clients import global_configuration, prepare

ROOT = Path(__file__).resolve().parents[2]


def _question(text):
    return "?" in text or "？" in text


def assess_material_interaction(run):
    """Check the deterministic interaction envelope around a material unknown."""
    if run.status != "recorded" or not run.trace.complete:
        return {
            "status": "blocked",
            "reason": run.reason or "multi-turn telemetry is incomplete",
            "confidence": 0.0,
        }
    first_messages = [
        event for event in run.trace.events
        if event.turn == 1 and event.kind == "message.assistant"
    ]
    writes = [
        event.data.get("path", "") for event in run.trace.events
        if event.turn == 1 and event.kind in FILE_EVENTS
    ]
    repeated = sum(
        _question(event.data.get("text", ""))
        for event in run.trace.events
        if event.turn > 1 and event.kind == "message.assistant"
    )
    later_writes = [
        event.data.get("path", "") for event in run.trace.events
        if event.turn > 1 and event.kind in FILE_EVENTS
    ]
    asked = any(_question(event.data.get("text", "")) for event in first_messages)
    has_second_turn = any(event.turn == 2 for event in run.trace.events)
    passed = asked and not writes and repeated == 0 and has_second_turn
    return {
        "status": "passed" if passed else "failed",
        "confidence": 1.0,
        "asked_before_writing": asked and not writes,
        "writes_before_reply": writes,
        "writes_after_reply": later_writes,
        "repeated_questions": repeated,
        "same_session": run.session_id is not None,
        "turns": max((event.turn for event in run.trace.events), default=0),
    }


def summarize_usage(log_paths, client):
    """Aggregate only usage and cost fields emitted by the real client."""
    summary = {
        "model": None,
        "input_tokens": 0,
        "cached_input_tokens": 0,
        "output_tokens": 0,
        "reasoning_output_tokens": 0,
        "estimated_usd": 0.0 if client == "claude" else None,
        "billed_usd": None,
    }
    for path in log_paths:
        for line in Path(path).read_text(errors="replace", encoding='utf-8').splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if (client == "claude" and event.get("type") == "system"
                    and event.get("subtype") == "init"):
                summary["model"] = event.get("model")
            if client == "claude" and event.get("type") == "result":
                usage = event.get("usage") or {}
                summary["estimated_usd"] += event.get("total_cost_usd") or 0.0
                summary["cached_input_tokens"] += (
                    usage.get("cache_read_input_tokens") or 0)
                summary["reasoning_output_tokens"] += (
                    (usage.get("output_tokens_details") or {}).get(
                        "thinking_tokens") or 0)
            elif client == "codex" and event.get("type") == "turn.completed":
                usage = event.get("usage") or {}
            else:
                continue
            keys = ("input_tokens", "output_tokens") if client == "claude" else (
                "input_tokens", "cached_input_tokens", "output_tokens",
                "reasoning_output_tokens")
            for key in keys:
                summary[key] += usage.get(key) or 0
    if client == "claude":
        summary["estimated_usd"] = round(summary["estimated_usd"], 6)
    return summary


def _version(client):
    result = subprocess.run(
        [client, "--version"], capture_output=True, text=True, timeout=15,
        check=False, encoding='utf-8')
    return (result.stdout or result.stderr).strip()


def _setup_runtime(plugin, workspace, env):
    result = subprocess.run(
        [sys.executable, str(plugin / "skills/tao-dev/scripts/tao.py"),
         "env", "prepare", "--wheelhouse", str(ROOT / "tmp/tao/wheels"),
         "--format", "json"],
        env=env, capture_output=True, text=True, timeout=180, check=False, encoding='utf-8')
    if result.returncode:
        raise RuntimeError(
            "Isolated offline runtime preparation failed: "
            + result.stdout + result.stderr)


def _boundary(workspace):
    return (
        "This is an isolated CLI acceptance experiment. Do not install, register, "
        "or change global skills, plugins, hooks, marketplaces, authentication, or "
        "client configuration. Work only inside the experiment workspace at "
        f"{workspace}. Do not search outside it, use network tools, or delegate. "
        "The client may load the advertised tao-dev skill resources; for project files, "
        "inspect only example.py and requirements.txt. Do not run find, rg, ls, pwd, "
        "directory scans, or inspect unrelated plugin/runtime files. "
        "On the first turn, ask the single material question before writing anything, "
        "and wait for the user's reply before editing. "
    )


def prepare_material_fixture(directory):
    """Remove unrelated requirements without supplying the missing policy choice."""
    (directory / "requirements.txt").write_text(
        "Exports are stored on disk. The product retention policy has not been "
        "decided.\n", encoding='utf-8')


def execute(client, workspace, timeout):
    """Run the catalog's material-choice scenario in isolated real client state."""
    workspace = Path(workspace).resolve()
    if workspace.exists() or workspace.is_relative_to(ROOT):
        raise RuntimeError("Choose a fresh behavior workspace outside the repository.")
    directory = workspace / client / "inside"
    directory.mkdir(parents=True)
    plugin = prepare(directory, client, native_plugin=client == "codex")
    prepare_material_fixture(directory)
    env = os.environ.copy()
    credentials = nullcontext([])
    secrets = []

    if client == "codex":
        from acceptance import isolated_codex

        isolated_codex.configure(workspace, directory, plugin)
        boundary = isolated_codex.check_boundary(workspace, directory)
        config = directory / ".codex/config.toml"
        config.write_text(config.read_text(encoding='utf-8').replace("hooks = true", "hooks = false"), encoding='utf-8')
        env = isolated_codex.environment(workspace)
        credentials = isolated_codex.access_snapshot(workspace, timeout)
    else:
        from acceptance import isolated_claude

        isolated_claude.configure(workspace, directory, "local")
        boundary = None
        env = isolated_claude.environment(workspace)
        settings = workspace / "client-config/settings.json"
        value = json.loads(settings.read_text(encoding='utf-8')) if settings.exists() else {}
        value["disableAllHooks"] = True
        settings.write_text(json.dumps(value), encoding='utf-8')
        credentials = isolated_claude.access_environment(workspace, timeout)

    env["TAO_PYTHON"] = sys.executable
    env["TAO_RUNTIME_DIR"] = str(workspace / "runtime")
    _setup_runtime(plugin, workspace, env)
    catalog = load_catalog(
        ROOT / "tests/acceptance/behavior-contract.yaml",
        ROOT / "tests/acceptance/behavior-scenarios.yaml")
    scenario = next(
        item for item in catalog.scenarios
        if item.id == "material-unknown-is-asked-once")
    scenario = replace(scenario, prompt=_boundary(workspace) + scenario.prompt)
    name = f"{client}-material-interaction-{time.time_ns()}"
    artifacts = ROOT / "tmp/tao/client-acceptance" / name
    before = global_configuration()
    started = time.monotonic()
    run = None
    try:
        with credentials as values:
            if client == "claude":
                scoped, secrets = values
                env = scoped | {
                    "TAO_RUNTIME_DIR": env["TAO_RUNTIME_DIR"],
                    "TAO_PYTHON": env["TAO_PYTHON"],
                }
            else:
                secrets = values
            run = run_scenario(
                scenario, client, directory,
                SubprocessExecutor(env=env, timeout=timeout),
                artifact_dir=artifacts)
    finally:
        from acceptance.isolated_codex import redact

        redact(list(artifacts.glob("*")), secrets)
    after = global_configuration()
    assessment = assess_material_interaction(run)
    if before != after:
        assessment = {
            **assessment,
            "status": "failed",
            "global_configuration_unchanged": False,
        }
    else:
        assessment["global_configuration_unchanged"] = True
    summary = {
        "client": client,
        "client_version": _version(client),
        "scenario": scenario.id,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "session_id": run.session_id,
        "runner_status": run.status,
        "trace_complete": run.trace.complete,
        "usage": summarize_usage(run.log_paths, client),
        "log_paths": [str(path) for path in run.log_paths],
        "native_skill_boundary": boundary,
        "assessment": assessment,
    }
    artifacts.mkdir(parents=True, exist_ok=True)
    (artifacts / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding='utf-8')
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--client", choices=("claude", "codex"), required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=300)
    args = parser.parse_args()
    if not 1 <= args.timeout <= 300:
        parser.error("timeout must be between 1 and 300 seconds")
    try:
        summary = execute(args.client, args.workspace, args.timeout)
    except RuntimeError as exc:
        summary = {
            "client": args.client,
            "assessment": {"status": "blocked", "reason": str(exc)},
        }
    print(json.dumps(summary, indent=2, sort_keys=True))
    status = summary["assessment"]["status"]
    return 0 if status == "passed" else 2 if status == "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
