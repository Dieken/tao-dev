"""Observed events, not agent prose, decide deterministic behavior rules."""

import json
from pathlib import Path

from acceptance.behavior_contract import load_catalog
from acceptance.behavior_trace import (
    Event,
    Trace,
    evaluate_deterministic,
    normalize_client_log,
    snapshot_workspace,
    workspace_events,
)

ROOT = Path(__file__).resolve().parents[1]
CATALOG = load_catalog(
    ROOT / "tests/acceptance/behavior-contract.yaml",
    ROOT / "tests/acceptance/behavior-scenarios.yaml",
)


def write_events(path, *events):
    path.write_text("\n".join(json.dumps(event) for event in events) + "\n")


def kinds(trace, kind):
    return [event for event in trace.events if event.kind == kind]


def scenario(identity):
    return next(item for item in CATALOG.scenarios if item.id == identity)


def event(number, kind, **data):
    return Event(f"event-{number}", 1, kind, "synthetic", float(number), data)


def test_claude_normalization_requires_an_executed_reader_not_a_path_mention(tmp_path):
    log = tmp_path / "claude.jsonl"
    write_events(log, {
        "type": "assistant",
        "message": {"content": [
            {"type": "tool_use", "name": "Skill", "input": {"skill": "tao-dev:tao-dev"}},
            {"type": "tool_use", "name": "Bash", "input": {
                "command": "test -f /cache/skills/tao-dev/references/workflow.md"}},
            {"type": "tool_use", "name": "Read", "input": {
                "file_path": "/cache/skills/tao-dev/references/engineering.md"}},
            {"type": "tool_use", "name": "Bash", "input": {
                "command": "cat /cache/skills/tao-dev/references/workflow.md"}},
        ]},
    })

    trace = normalize_client_log(log, "claude")

    assert len(kinds(trace, "skill.invoked")) == 1
    assert [item.data["resource"] for item in kinds(trace, "resource.opened")] == [
        "references/engineering.md", "references/workflow.md"]
    assert [item.data["resource"] for item in kinds(trace, "resource.mentioned")] == [
        "references/workflow.md"]


def test_codex_deduplicates_command_lifecycle_and_preserves_completion(tmp_path):
    log = tmp_path / "codex.jsonl"
    read = "/bin/zsh -lc 'sed -n 1,80p .agents/skills/tao-dev/SKILL.md " \
           ".agents/skills/tao-dev/references/workflow.md'"
    mention = "test -f .agents/skills/tao-dev/references/engineering.md"
    write_events(
        log,
        {"type": "item.started", "item": {"type": "command_execution", "command": read}},
        {"type": "item.completed", "item": {"type": "command_execution", "command": read,
                                                   "exit_code": 0}},
        {"type": "item.completed", "item": {"type": "command_execution", "command": mention,
                                                   "exit_code": 0}},
    )

    trace = normalize_client_log(log, "codex")

    assert len(kinds(trace, "command.started")) == 2
    assert len(kinds(trace, "command.finished")) == 2
    assert [item.data["resource"] for item in kinds(trace, "resource.opened")] == [
        "SKILL.md", "references/workflow.md"]
    assert [item.data["resource"] for item in kinds(trace, "resource.mentioned")] == [
        "references/engineering.md"]


def test_workspace_snapshot_reports_created_modified_and_deleted_files(tmp_path):
    (tmp_path / "keep.py").write_text("before\n")
    (tmp_path / "delete.py").write_text("remove\n")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git/config").write_text("ignored\n")
    before = snapshot_workspace(tmp_path)
    (tmp_path / "keep.py").write_text("after\n")
    (tmp_path / "delete.py").unlink()
    (tmp_path / "new.py").write_text("new\n")
    after = snapshot_workspace(tmp_path)

    changes = workspace_events(before, after, client="synthetic", turn=2)

    assert [(item.kind, item.data["path"]) for item in changes] == [
        ("file.deleted", "delete.py"),
        ("file.modified", "keep.py"),
        ("file.created", "new.py"),
    ]


def test_routing_oracle_rejects_missing_and_forbidden_resource_reads():
    trace = Trace((
        event(1, "skill.invoked", skill="tao-dev:tao-dev"),
        event(2, "resource.opened", resource="references/workflow.md"),
        event(3, "resource.opened", resource="references/documents.md"),
        event(4, "verification.finished", status="passed"),
        event(5, "claim", claim="complete", evidence=["event-4"]),
    ), complete=True)

    result = evaluate_deterministic(CATALOG, scenario("routing-local-fix"), trace)

    assert result.by_rule["LOAD-001"].status == "pass"
    assert result.by_rule["LOAD-002"].status == "fail"
    assert result.by_rule["LOAD-003"].status == "fail"


def test_authorization_oracle_rejects_forbidden_stage_write():
    trace = Trace((event(1, "file.created", path="docs/engineering/example.md"),),
                  complete=True)

    result = evaluate_deterministic(
        CATALOG, scenario("feedback-does-not-authorize-design"), trace)

    assert result.by_rule["AUTH-001"].status == "fail"
    assert result.by_rule["AUTH-001"].evidence == ("event-1",)


def test_verification_must_follow_the_last_mutation_and_support_completion():
    stale = Trace((
        event(1, "verification.finished", status="passed"),
        event(2, "file.modified", path="example.py"),
        event(3, "claim", claim="complete", evidence=["event-1"]),
    ), complete=True)
    current = Trace((
        event(1, "file.modified", path="example.py"),
        event(2, "verification.finished", status="passed"),
        event(3, "claim", claim="complete", evidence=["event-2"]),
    ), complete=True)

    stale_result = evaluate_deterministic(
        CATALOG, scenario("completion-claims-have-evidence"), stale)
    current_result = evaluate_deterministic(
        CATALOG, scenario("completion-claims-have-evidence"), current)

    assert stale_result.by_rule["VERIFY-001"].status == "fail"
    assert stale_result.by_rule["CLAIM-001"].status == "fail"
    assert current_result.by_rule["VERIFY-001"].status == "pass"
    assert current_result.by_rule["CLAIM-001"].status == "pass"


def test_status_oracle_rejects_verification_even_without_writes():
    trace = Trace((event(1, "command.finished", command="tao verify", exit_code=0),),
                  complete=True)

    result = evaluate_deterministic(CATALOG, scenario("status-read-only"), trace)

    assert result.by_rule["STATUS-001"].status == "fail"


def test_missing_telemetry_blocks_instead_of_passing():
    result = evaluate_deterministic(
        CATALOG, scenario("routing-local-fix"), Trace((), complete=False))

    assert {item.status for item in result.by_rule.values()} == {"blocked"}
