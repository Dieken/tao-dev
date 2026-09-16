"""Multi-turn behavior scenarios must use one observable client session."""

import json

from acceptance.behavior_clients import adapter_for
from acceptance.behavior_contract import Scenario
from acceptance.behavior_runner import InvocationResult, run_scenario


def scenario(*, turns=(), rules=("AUTH-001",), expectations=None):
    return Scenario(
        "test-scenario",
        "Test scenario",
        ("claude", "codex"),
        "fixture",
        "Please make the requested change.",
        turns,
        rules,
        expectations or {},
    )


class FakeExecutor:
    def __init__(self, client, responses, mutation=None):
        self.client = client
        self.responses = iter(responses)
        self.requests = []
        self.mutation = mutation
        self.session_id = None

    def __call__(self, request):
        self.requests.append(request)
        response = next(self.responses)
        session_id = response.get("session_id", "session-1")
        if session_id == "$requested":
            session_id = request.requested_session_id
        elif session_id == "$same":
            session_id = self.session_id
        self.session_id = session_id
        text = response.get("text", "Done.")
        if self.client == "claude":
            rows = [{"type": "assistant", "session_id": session_id,
                     "message": {"content": [{"type": "text", "text": text}]}}]
        else:
            rows = [
                {"type": "thread.started", "thread_id": session_id},
                {"type": "item.completed", "item": {
                    "type": "agent_message", "text": text}},
            ]
        request.log_path.write_text(
            "\n".join(json.dumps(row) for row in rows) + "\n")
        if self.mutation:
            self.mutation(request)
        return InvocationResult(
            response.get("returncode", 0),
            response.get("timed_out", False),
            response.get("error"),
        )


def event_kinds(result, kind):
    return [event for event in result.trace.events if event.kind == kind]


def test_adapters_resume_the_same_observed_session(tmp_path):
    turn = ({"when": "asks-material-question", "user": "Keep it for 30 days."},)
    for client in ("claude", "codex"):
        workspace = tmp_path / client
        workspace.mkdir()
        executor = FakeExecutor(client, [
            {"session_id": "$requested" if client == "claude" else "codex-session",
             "text": "How long should I keep it?"},
            {"session_id": "$same", "text": "Done."},
        ])

        result = run_scenario(scenario(turns=turn), client, workspace, executor)

        assert result.status == "recorded"
        assert result.session_id
        assert len(executor.requests) == 2
        assert executor.requests[1].resume is True
        assert result.session_id in executor.requests[1].command
        assert [event.turn for event in event_kinds(result, "message.assistant")] == [1, 2]


def test_lost_or_changed_session_blocks_multiturn_acceptance(tmp_path):
    turns = ({"when": "asks-material-question", "user": "Thirty days."},)
    executor = FakeExecutor("codex", [
        {"session_id": "original", "text": "How many days?"},
        {"session_id": "independent", "text": "Done."},
    ])

    result = run_scenario(scenario(turns=turns), "codex", tmp_path, executor)

    assert result.status == "blocked"
    assert result.trace.complete is False
    assert "session" in result.reason.lower()


def test_claude_must_report_the_explicitly_requested_initial_session(tmp_path):
    executor = FakeExecutor("claude", [
        {"session_id": "different", "text": "Done."},
    ])

    result = run_scenario(scenario(), "claude", tmp_path, executor)

    assert result.status == "blocked"
    assert "requested session" in result.reason.lower()


def test_missing_session_id_cannot_be_treated_as_a_continuation(tmp_path):
    log = tmp_path / "codex.jsonl"
    log.write_text(json.dumps({"type": "item.completed", "item": {
        "type": "agent_message", "text": "How many days?"}}) + "\n")

    assert adapter_for("codex").session_id(log) is None


def test_scripted_reply_is_not_sent_when_condition_does_not_match(tmp_path):
    turns = ({"when": "asks-material-question", "user": "Thirty days."},)
    executor = FakeExecutor("claude", [
        {"session_id": "$requested", "text": "I will choose a default."},
    ])

    result = run_scenario(scenario(turns=turns), "claude", tmp_path, executor)

    assert result.status == "blocked"
    assert len(executor.requests) == 1
    assert "condition" in result.reason.lower()


def test_workspace_changes_are_captured_for_each_turn(tmp_path):
    (tmp_path / "example.py").write_text("before\n")

    def mutate(request):
        if request.turn == 1:
            (request.workspace / "example.py").write_text("after\n")

    executor = FakeExecutor(
        "codex", [{"session_id": "session-1", "text": "Done."}], mutation=mutate)

    result = run_scenario(scenario(), "codex", tmp_path, executor)

    changes = event_kinds(result, "file.modified")
    assert [(event.turn, event.data["path"]) for event in changes] == [(1, "example.py")]


def test_timeout_and_malformed_telemetry_are_blocked(tmp_path):
    timeout = FakeExecutor("claude", [
        {"session_id": "$requested", "timed_out": True, "text": ""},
    ])
    malformed = FakeExecutor("codex", [
        {"session_id": "session-1", "returncode": 2, "text": ""},
    ])

    timed_out = run_scenario(scenario(), "claude", tmp_path / "one", timeout)
    failed = run_scenario(scenario(), "codex", tmp_path / "two", malformed)

    assert timed_out.status == "blocked"
    assert timed_out.trace.complete is False
    assert failed.status == "blocked"
    assert failed.trace.complete is False


def test_adapters_build_real_cli_commands_without_other_agents(tmp_path):
    claude = adapter_for("claude").request(
        "Prompt", tmp_path, tmp_path / "claude.jsonl", 1, None)
    codex = adapter_for("codex").request(
        "Prompt", tmp_path, tmp_path / "codex.jsonl", 1, None)

    assert claude.command[0] == "claude"
    assert "--session-id" in claude.command
    assert codex.command[0] == "codex"
    assert "exec" in codex.command
    assert {claude.client, codex.client} == {"claude", "codex"}
