"""Harness safety and consumer-visible project installation guarantees."""

import json
from pathlib import Path
import sys

import pytest

from acceptance import project_skills as acceptance


def test_environment_does_not_inherit_credentials_or_personal_paths(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", "/personal/home")
    monkeypatch.setenv("CODEX_HOME", "/personal/codex")
    monkeypatch.setenv("OPENAI_API_KEY", "not-for-the-inspector")
    monkeypatch.setenv("ANTHROPIC_AUTH_TOKEN", "not-for-the-inspector")
    monkeypatch.setenv("PYTHONPATH", "/personal/modules")
    monkeypatch.setenv("TAO_RUNTIME_DIR", "/personal/runtime")
    environment = acceptance.isolated_environment(tmp_path)
    assert not {"OPENAI_API_KEY", "ANTHROPIC_AUTH_TOKEN", "PYTHONPATH", "TAO_RUNTIME_DIR"} & environment.keys()
    for name in ("HOME", "USERPROFILE", "CODEX_HOME", "XDG_CONFIG_HOME", "TMPDIR"):
        assert Path(environment[name]).is_relative_to(tmp_path)
    assert environment["GIT_CONFIG_NOSYSTEM"] == "1"


@pytest.mark.parametrize("client", tuple(acceptance.CLIENT_PATHS))
def test_cli_refuses_modified_installed_skill_without_changing_files(tmp_path, client):
    environment = acceptance.isolated_environment(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    acceptance.invoke("install", project, client, environment)
    destination = project / acceptance.CLIENT_PATHS[client]
    (destination / "SKILL.md").write_text("My local edits.\n", encoding="utf-8")
    before = acceptance.snapshot(tmp_path)
    for action in ("upgrade", "uninstall"):
        with pytest.raises(RuntimeError, match=f"{client} {action} failed"):
            acceptance.invoke(action, project, client, environment)
        assert acceptance.snapshot(tmp_path) == before


@pytest.mark.parametrize("client", tuple(acceptance.CLIENT_PATHS))
def test_cli_refuses_unowned_destination_without_changing_files(tmp_path, client):
    environment = acceptance.isolated_environment(tmp_path)
    project = tmp_path / "project"
    destination = project / acceptance.CLIENT_PATHS[client]
    destination.mkdir(parents=True)
    (destination / "SKILL.md").write_text("Existing user skill.\n", encoding="utf-8")
    before = acceptance.snapshot(tmp_path)
    with pytest.raises(RuntimeError, match=f"{client} install failed"):
        acceptance.invoke("install", project, client, environment)
    assert acceptance.snapshot(tmp_path) == before


def fake_server(tmp_path, monkeypatch, *, mode="success", rows=None):
    """A protocol fixture, not a substitute for the actual native discovery test."""
    requests = tmp_path / "requests.jsonl"
    server = '''
import json, sys, time
log, mode, rows = sys.argv[1:]
for line in sys.stdin:
    with open(log, 'a', encoding='utf-8') as output:
        output.write(line)
    request = json.loads(line)
    if request['method'] == 'initialize':
        print(json.dumps({'id': request['id'], 'result': {}}), flush=True)
    elif request['method'] == 'skills/list':
        if mode == 'timeout':
            time.sleep(60)
        elif mode == 'exit':
            sys.exit(0)
        elif mode == 'malformed':
            print('not-json', flush=True)
        elif mode == 'error':
            print(json.dumps({'id': request['id'], 'error': {'message': 'not supported'}}), flush=True)
        else:
            print(json.dumps({'method': 'notification'}), flush=True)
            print(json.dumps({'id': request['id'], 'result': {'data': json.loads(rows)}}), flush=True)
'''
    popen = acceptance.subprocess.Popen
    processes = []

    def launch(command, **kwargs):
        assert command == ["/fake/codex", "app-server"]
        process = popen([sys.executable, "-u", "-c", server, str(requests), mode, json.dumps(rows)], **kwargs)
        processes.append(process)
        return process

    monkeypatch.setattr(acceptance.shutil, "which", lambda name: "/fake/codex")
    monkeypatch.setattr(acceptance.subprocess, "Popen", launch)
    return requests, processes


def test_discovery_protocol_never_starts_a_model_turn(tmp_path, monkeypatch):
    environment = acceptance.isolated_environment(tmp_path)
    requests, processes = fake_server(
        tmp_path, monkeypatch, rows=[{"cwd": str(tmp_path), "skills": [], "errors": []}],
    )
    assert acceptance.discover_codex([tmp_path], environment) == {tmp_path: []}
    sent = [json.loads(line) for line in requests.read_text(encoding="utf-8").splitlines()]
    assert [item["method"] for item in sent] == ["initialize", "initialized", "skills/list"]
    assert sent[2]["params"] == {"cwds": [str(tmp_path)], "forceReload": True}
    assert all(process.poll() is not None for process in processes)


@pytest.mark.parametrize("mode", ("timeout", "exit", "malformed", "error"))
def test_failed_native_inspection_is_bounded_and_reaped(tmp_path, monkeypatch, mode):
    environment = acceptance.isolated_environment(tmp_path)
    _, processes = fake_server(tmp_path, monkeypatch, mode=mode)
    with pytest.raises((RuntimeError, json.JSONDecodeError)):
        acceptance.discover_codex([tmp_path], environment, timeout=1)
    assert all(process.poll() is not None for process in processes)


@pytest.mark.parametrize("rows", (
    [],
    [{"cwd": "PROJECT", "skills": [], "errors": ["invalid skill"]}],
    [{"cwd": "PROJECT", "skills": []}, {"cwd": "PROJECT", "skills": []}],
))
def test_native_scan_errors_and_incomplete_results_cannot_pass(tmp_path, monkeypatch, rows):
    environment = acceptance.isolated_environment(tmp_path)
    rows = [{**row, "cwd": str(tmp_path)} for row in rows]
    fake_server(tmp_path, monkeypatch, rows=rows)
    with pytest.raises(RuntimeError):
        acceptance.discover_codex([tmp_path], environment)


def test_missing_codex_is_not_reported_as_discovery_success(tmp_path, monkeypatch):
    monkeypatch.setattr(acceptance.shutil, "which", lambda name: None)
    with pytest.raises(RuntimeError, match="not installed"):
        acceptance.discover_codex([tmp_path], {})


@pytest.mark.parametrize("timeout", (0, -1, 61))
def test_native_inspection_rejects_unbounded_deadlines(tmp_path, timeout):
    with pytest.raises(ValueError, match="timeout"):
        acceptance.discover_codex([tmp_path], {}, timeout=timeout)


@pytest.mark.parametrize("mutation", ("disabled", "wrong-path", "duplicate", "outside", "missing"))
def test_discovery_requires_enabled_exact_project_skill(tmp_path, mutation):
    inside, outside = tmp_path / "inside", tmp_path / "outside"
    skill = {"name": "tao-dev", "enabled": True,
             "path": str(inside / acceptance.CLIENT_PATHS["codex"] / "SKILL.md")}
    rows = {inside: [skill], outside: []}
    if mutation == "disabled":
        skill["enabled"] = False
    elif mutation == "wrong-path":
        skill["path"] = str(tmp_path / "other/SKILL.md")
    elif mutation == "duplicate":
        rows[inside].append(dict(skill))
    elif mutation == "outside":
        rows[outside].append(dict(skill))
    else:
        rows[inside].clear()
    with pytest.raises(RuntimeError):
        acceptance.assert_discovery(rows, inside, outside, installed=True)


def test_discovery_rejects_skill_remaining_after_uninstall(tmp_path):
    inside, outside = tmp_path / "inside", tmp_path / "outside"
    with pytest.raises(RuntimeError, match="after uninstall"):
        acceptance.assert_discovery({inside: [{"name": "tao-dev"}], outside: []},
                                    inside, outside, installed=False)


def test_native_discovery_does_not_claim_unsupported_clients():
    with pytest.raises(ValueError, match="only for Codex"):
        acceptance.run("claude", native=True)
