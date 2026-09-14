"""Opt-in native Claude scope checks with an isolated client configuration."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time


ROOT = Path(__file__).resolve().parents[2]


def snapshot():
    paths = [".claude.json", ".claude/settings.json", ".claude/plugins/installed_plugins.json",
             ".claude/plugins/known_marketplaces.json", ".codex/config.toml", ".gitconfig",
             ".config/git/ignore", ".agents/plugins/marketplace.json"]
    return {name: hashlib.sha256((Path.home() / name).read_bytes()).hexdigest()
            if (Path.home() / name).is_file() else None for name in paths}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--scope", choices=("user", "project", "local"), required=True)
    parser.add_argument("--probe", action="store_true", help="Also call the configured model to inspect session initialization.")
    args = parser.parse_args()
    workspace = args.workspace.resolve()
    if workspace.exists():
        raise SystemExit("Choose a fresh experiment directory.")
    if workspace.is_relative_to(ROOT):
        raise SystemExit("Choose a directory outside the maintenance repository.")
    workspace.mkdir(parents=True)
    config = workspace / "client-config"
    config.mkdir()
    inside, outside = workspace / "inside", workspace / "outside"
    inside.mkdir()
    outside.mkdir()
    marketplace = workspace / "marketplace"
    shutil.copytree(ROOT / "plugins/tao-dev", marketplace / "plugins/tao-dev",
                    ignore=shutil.ignore_patterns("__pycache__"))
    (marketplace / ".claude-plugin").mkdir()
    (marketplace / ".claude-plugin/marketplace.json").write_text(json.dumps({
        "name": "tao-runtime-test", "owner": {"name": "tao-dev acceptance"},
        "plugins": [{"name": "tao-dev", "source": "./plugins/tao-dev"}]}))
    (inside / ".gitignore").write_text(".claude/settings.local.json\n")
    environment = os.environ | {"CLAUDE_CONFIG_DIR": str(config),
        "XDG_CONFIG_HOME": str(workspace / "xdg-config"),
        "GIT_CONFIG_GLOBAL": str(workspace / "gitconfig"),
        "TAO_RUNTIME_DIR": str(workspace / "runtime"),
        "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1"}
    before = snapshot()
    runs = []
    commands = [(inside, ["plugin", "marketplace", "add", str(marketplace)]),
                (inside, ["plugin", "install", "tao-dev@tao-runtime-test", "--scope", args.scope, "--json"]),
                (inside, ["plugin", "list", "--json"]),
                (outside, ["plugin", "list", "--json"])]
    if args.probe:
        probe = ["-p", "--output-format", "stream-json", "--verbose", "--tools", "",
                 "--strict-mcp-config", "--no-session-persistence", "--max-turns", "1",
                 "--max-budget-usd", "0.25", "Reply OK. Do not use tools or change any settings."]
        commands += [(inside, probe), (outside, probe)]
    for number, (cwd, arguments) in enumerate(commands):
        started = time.monotonic()
        stdout, stderr = workspace / f"{number}.jsonl", workspace / f"{number}.stderr"
        try:
            with stdout.open("w") as out, stderr.open("w") as err:
                completed = subprocess.run(["claude", *arguments], cwd=cwd, env=environment,
                                           stdout=out, stderr=err, timeout=60)
            code = completed.returncode
        except subprocess.TimeoutExpired:
            code = 124
        run = {"cwd": cwd.name, "operation": arguments[0], "exit_code": code,
               "elapsed_seconds": round(time.monotonic() - started, 3), "stdout": stdout.name}
        events = []
        for line in stdout.read_text().splitlines():
            try:
                item = json.loads(line)
            except ValueError:
                continue
            if isinstance(item, dict) and item.get("type") == "system" and item.get("subtype") == "init":
                events.append(item)
        if events:
            run["initialized_plugins"] = events[0].get("plugins", [])
            run["initialized_skills"] = events[0].get("skills", [])
            run["model"] = events[0].get("model")
        runs.append(run)
        if snapshot() != before:
            break
        if code and number < 2:
            break
    unchanged = before == snapshot()
    probes = [run for run in runs if run["operation"] == "-p"]
    activation = []
    for run in probes:
        present = any(p.get("name", "").startswith("tao-dev") for p in run.get("initialized_plugins", []))
        expected = args.scope == "user" or run["cwd"] == "inside"
        activation.append("initialized_plugins" in run and present == expected)
    report = {"scope": args.scope, "configuration_directory": str(config), "runs": runs,
              "personal_configuration_unchanged": unchanged,
              "scope_loading_verified": len(activation) == 2 and all(activation),
              "model_execution_verified": len(probes) == 2 and all(run["exit_code"] == 0 for run in probes),
              "model_probe_requested": args.probe}
    (workspace / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 0 if unchanged and all(run["exit_code"] == 0 for run in runs if run["operation"] != "-p") and (not args.probe or report["scope_loading_verified"]) else 2


if __name__ == "__main__":
    raise SystemExit(main())
