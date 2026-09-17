"""Deterministic multi-turn orchestration for behavior scenarios."""

import os
import signal
import subprocess
from contextlib import ExitStack
from dataclasses import dataclass, replace
from pathlib import Path

from acceptance.behavior_clients import adapter_for
from acceptance.behavior_trace import (
    Trace,
    normalize_client_log,
    snapshot_workspace,
    workspace_events,
)


@dataclass(frozen=True)
class InvocationResult:
    returncode: int | None
    timed_out: bool = False
    error: str | None = None


@dataclass(frozen=True)
class ScenarioRun:
    status: str
    reason: str
    session_id: str | None
    trace: Trace
    log_paths: tuple[Path, ...]


class SubprocessExecutor:
    """Run a prepared client request with bounded process-group cleanup."""

    def __init__(self, *, env=None, timeout=180):
        self.env = env
        self.timeout = timeout

    def __call__(self, request):
        request.log_path.parent.mkdir(parents=True, exist_ok=True)
        error_path = request.log_path.with_suffix(".stderr")
        process = None
        timed_out = False
        error = None
        try:
            with ExitStack() as stack:
                stdout = stack.enter_context(os.fdopen(os.open(
                    request.log_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                    0o600), "w"))
                stderr = stack.enter_context(os.fdopen(os.open(
                    error_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                    0o600), "w"))
                process = subprocess.Popen(
                    request.command,
                    cwd=request.workspace,
                    env=self.env,
                    stdin=subprocess.PIPE,
                    stdout=stdout,
                    stderr=stderr,
                    text=True,
                    start_new_session=True,
                    encoding='utf-8',
                )
                try:
                    process.communicate(request.prompt, timeout=self.timeout)
                except subprocess.TimeoutExpired:
                    timed_out = True
                finally:
                    if process.poll() is None:
                        os.killpg(process.pid, signal.SIGTERM)
                        try:
                            process.wait(timeout=10)
                        except subprocess.TimeoutExpired:
                            os.killpg(process.pid, signal.SIGKILL)
                            process.wait()
        except OSError as exc:
            error = str(exc)
        return InvocationResult(
            process.returncode if process is not None else None, timed_out, error)


def _renumber(events, turn, client, start):
    result = []
    for offset, event in enumerate(events, start):
        result.append(replace(
            event,
            id=f"event-{offset}",
            turn=turn,
            client=client,
            timestamp=float(offset),
        ))
    return result


def _condition_met(condition, events):
    if condition == "asks-material-question":
        return any(
            event.kind == "message.assistant"
            and ("?" in event.data.get("text", "")
                 or "？" in event.data.get("text", ""))
            for event in events
        )
    return False


def _blocked(reason, session_id, events, logs):
    return ScenarioRun(
        "blocked", reason, session_id, Trace(tuple(events), complete=False), tuple(logs))


def run_scenario(scenario, client, workspace, executor, *, artifact_dir=None):
    """Run deterministic user turns and require observable session continuity."""
    if client not in scenario.clients:
        raise ValueError(f"Scenario {scenario.id} does not support {client}")
    workspace = Path(workspace)
    workspace.mkdir(parents=True, exist_ok=True)
    artifact_dir = Path(artifact_dir) if artifact_dir else (
        workspace.parent / f".{workspace.name}-{scenario.id}-{client}-evidence")
    artifact_dir.mkdir(parents=True, exist_ok=True)
    adapter = adapter_for(client)
    prompts = [scenario.prompt]
    events = []
    logs = []
    session_id = None

    for turn, prompt in enumerate(prompts, 1):
        log_path = artifact_dir / f"turn-{turn}.jsonl"
        request = adapter.request(prompt, workspace, log_path, turn, session_id)
        before = snapshot_workspace(workspace)
        outcome = executor(request)
        after = snapshot_workspace(workspace)
        logs.append(log_path)

        trace = normalize_client_log(log_path, client)
        normalized = _renumber(trace.events, turn, client, len(events) + 1)
        events.extend(normalized)
        changes = workspace_events(before, after, client=client, turn=turn)
        events.extend(_renumber(changes, turn, client, len(events) + 1))

        observed_session = adapter.session_id(log_path)
        if outcome.error:
            return _blocked(outcome.error, session_id, events, logs)
        if outcome.timed_out:
            return _blocked("client invocation timed out", session_id, events, logs)
        if outcome.returncode != 0 or not trace.complete:
            return _blocked("client invocation or telemetry failed", session_id,
                            events, logs)
        if not observed_session:
            return _blocked("client telemetry omitted the session id", session_id,
                            events, logs)
        if (request.requested_session_id is not None
                and observed_session != request.requested_session_id):
            return _blocked("client did not use the requested session", session_id,
                            events, logs)
        if session_id is not None and observed_session != session_id:
            return _blocked("client resumed a different session", session_id,
                            events, logs)
        session_id = observed_session

        script_index = turn - 1
        if script_index < len(scenario.turns):
            scripted = scenario.turns[script_index]
            if not _condition_met(scripted.get("when"), normalized):
                return _blocked("scripted turn condition did not match", session_id,
                                events, logs)
            prompts.append(scripted["user"])

    return ScenarioRun(
        "recorded", "", session_id, Trace(tuple(events), complete=True), tuple(logs))
