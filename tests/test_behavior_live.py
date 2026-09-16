"""Real multi-turn acceptance uses the same trace checks as offline replay."""

import json

from acceptance.behavior_live import (
    assess_material_interaction,
    prepare_material_fixture,
    summarize_usage,
)
from acceptance.behavior_runner import ScenarioRun
from acceptance.behavior_trace import Event, Trace


def event(number, turn, kind, **data):
    return Event(f"event-{number}", turn, kind, "synthetic", float(number), data)


def run(*events, status="recorded"):
    return ScenarioRun(
        status, "", "session-1", Trace(tuple(events), complete=status == "recorded"),
        (),
    )


def test_material_interaction_passes_only_for_question_then_same_session_work():
    result = assess_material_interaction(run(
        event(1, 1, "message.assistant", text="How many days should exports remain?"),
        event(2, 2, "message.assistant", text="Implemented the requested policy."),
        event(3, 2, "file.modified", path="example.py"),
    ))

    assert result["status"] == "passed"
    assert result["asked_before_writing"] is True
    assert result["repeated_questions"] == 0
    assert result["confidence"] == 1.0
    assert result["writes_after_reply"] == ["example.py"]


def test_material_interaction_fails_on_early_write_or_repeated_question():
    result = assess_material_interaction(run(
        event(1, 1, "file.modified", path="example.py"),
        event(2, 1, "message.assistant", text="How many days?"),
        event(3, 2, "message.assistant", text="Are you sure?"),
    ))

    assert result["status"] == "failed"
    assert result["writes_before_reply"] == ["example.py"]
    assert result["repeated_questions"] == 1


def test_blocked_runner_cannot_pass_interaction_acceptance():
    result = assess_material_interaction(run(status="blocked"))

    assert result["status"] == "blocked"
    assert result["confidence"] == 0.0


def test_material_fixture_removes_unrelated_overwrite_requirement(tmp_path):
    prepare_material_fixture(tmp_path)

    requirement = (tmp_path / "requirements.txt").read_text()
    assert "retention policy has not been decided" in requirement
    assert "overwrite" not in requirement
    assert "30 days" not in requirement


def test_usage_summary_uses_observed_client_events(tmp_path):
    claude = tmp_path / "claude.jsonl"
    claude.write_text("\n".join((
        json.dumps({"type": "system", "subtype": "init", "model": "sonnet"}),
        json.dumps({"type": "result", "total_cost_usd": 0.125, "usage": {
            "input_tokens": 10, "cache_read_input_tokens": 8,
            "output_tokens": 4,
            "output_tokens_details": {"thinking_tokens": 2}}}),
    )) + "\n")
    codex = tmp_path / "codex.jsonl"
    codex.write_text(json.dumps({"type": "turn.completed", "usage": {
        "input_tokens": 20, "cached_input_tokens": 5,
        "output_tokens": 7, "reasoning_output_tokens": 2}}) + "\n")

    claude_usage = summarize_usage((claude,), "claude")
    codex_usage = summarize_usage((codex,), "codex")

    assert claude_usage["model"] == "sonnet"
    assert claude_usage["estimated_usd"] == 0.125
    assert claude_usage["input_tokens"] == 10
    assert claude_usage["cached_input_tokens"] == 8
    assert claude_usage["reasoning_output_tokens"] == 2
    assert codex_usage["estimated_usd"] is None
    assert codex_usage["input_tokens"] == 20
    assert codex_usage["reasoning_output_tokens"] == 2
