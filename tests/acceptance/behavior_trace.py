"""Normalize client telemetry and evaluate deterministic behavior rules."""

import fnmatch
import hashlib
import json
import re
import shlex
from dataclasses import dataclass
from pathlib import Path

RESOURCE = re.compile(
    r"(?:^|/)skills/tao-dev/"
    r"(?P<resource>SKILL\.md|references/[A-Za-z0-9_.-]+|assets/[A-Za-z0-9_./-]+)"
)
FILE_EVENTS = frozenset(("file.created", "file.modified", "file.deleted"))
READ_COMMANDS = frozenset(("awk", "cat", "head", "less", "more", "rg", "sed", "tail"))
VERIFY_MARKERS = ("pytest", "compileall", "py_compile", "tao verify")


@dataclass(frozen=True)
class Event:
    id: str
    turn: int
    kind: str
    client: str
    timestamp: float
    data: dict


@dataclass(frozen=True)
class Trace:
    events: tuple[Event, ...]
    complete: bool


@dataclass(frozen=True)
class WorkspaceSnapshot:
    root: Path
    files: dict[str, str]


@dataclass(frozen=True)
class RuleResult:
    rule_id: str
    status: str
    evidence: tuple[str, ...] = ()
    reason: str = ""


@dataclass(frozen=True)
class DeterministicEvaluation:
    by_rule: dict[str, RuleResult]


class _Events:
    def __init__(self, client):
        self.client = client
        self.items = []

    def add(self, kind, turn=1, **data):
        number = len(self.items) + 1
        self.items.append(Event(
            f"event-{number}", turn, kind, self.client, float(number), data))


def _resources(text):
    seen = set()
    result = []
    for match in RESOURCE.finditer(text or ""):
        resource = match.group("resource")
        if resource not in seen:
            seen.add(resource)
            result.append(resource)
    return result


def _shell_tokens(command):
    try:
        tokens = shlex.split(command)
    except ValueError:
        return []
    if len(tokens) >= 3 and Path(tokens[0]).name in {"bash", "sh", "zsh"}:
        for index, token in enumerate(tokens[1:], 1):
            if token in {"-c", "-lc"} and index + 1 < len(tokens):
                return _shell_tokens(tokens[index + 1])
    return tokens


def _command_resources(command):
    mentioned = _resources(command)
    tokens = _shell_tokens(command)
    executable = Path(tokens[0]).name if tokens else ""
    opened = mentioned if executable in READ_COMMANDS else []
    return opened, [item for item in mentioned if item not in opened]


def _record_command(events, command, exit_code=None, started=True,
                    record_resources=True):
    if started:
        events.add("command.started", command=command)
    if record_resources:
        opened, mentioned = _command_resources(command)
        for resource in opened:
            events.add("resource.opened", resource=resource, command=command)
            if resource == "SKILL.md":
                events.add("skill.invoked", skill="tao-dev")
        for resource in mentioned:
            events.add("resource.mentioned", resource=resource, command=command)
    if exit_code is not None:
        events.add("command.finished", command=command, exit_code=exit_code)
        lowered = command.lower()
        if any(marker in lowered for marker in VERIFY_MARKERS):
            events.add(
                "verification.finished",
                command=command,
                status="passed" if exit_code == 0 else "failed",
                exit_code=exit_code,
            )


def _normalize_claude(rows, events):
    for row in rows:
        if row.get("type") != "assistant":
            continue
        content = row.get("message", {}).get("content", [])
        for block in content if isinstance(content, list) else []:
            if block.get("type") == "text":
                events.add("message.assistant", text=block.get("text", ""))
                continue
            if block.get("type") != "tool_use":
                continue
            name = block.get("name")
            inputs = block.get("input") or {}
            if name == "Skill":
                events.add("skill.invoked", skill=inputs.get("skill", ""))
            elif name == "Read":
                for resource in _resources(inputs.get("file_path", "")):
                    events.add("resource.opened", resource=resource, tool="Read")
            elif name == "Bash":
                _record_command(events, inputs.get("command", ""))


def _normalize_codex(rows, events):
    pending = {}
    for row in rows:
        item = row.get("item") or {}
        if (row.get("type") == "item.completed"
                and item.get("type") == "agent_message"):
            events.add("message.assistant", text=item.get("text", ""))
            continue
        if item.get("type") != "command_execution":
            continue
        command = item.get("command", "")
        if row.get("type") == "item.started":
            pending[command] = pending.get(command, 0) + 1
            _record_command(events, command)
        elif row.get("type") == "item.completed":
            already_started = pending.get(command, 0) > 0
            if already_started:
                pending[command] -= 1
            _record_command(
                events, command, item.get("exit_code"), started=not already_started,
                record_resources=not already_started)


def normalize_client_log(path, client):
    """Convert Claude or Codex JSONL into stable evidence events."""
    rows = []
    complete = True
    try:
        for line in Path(path).read_text().splitlines():
            if line.strip():
                rows.append(json.loads(line))
    except (OSError, json.JSONDecodeError):
        complete = False
    events = _Events(client)
    if client == "claude":
        _normalize_claude(rows, events)
    elif client == "codex":
        _normalize_codex(rows, events)
    else:
        raise ValueError(f"Unsupported client: {client}")
    return Trace(tuple(events.items), complete)


def snapshot_workspace(root):
    """Hash relevant workspace files without inspecting Git internals."""
    root = Path(root)
    files = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if not path.is_file() or ".git" in relative.parts:
            continue
        files[relative.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return WorkspaceSnapshot(root, files)


def workspace_events(before, after, client, turn):
    """Return stable events for the difference between two snapshots."""
    changes = []
    paths = sorted(set(before.files) | set(after.files))
    for path in paths:
        if path not in after.files:
            kind = "file.deleted"
        elif path not in before.files:
            kind = "file.created"
        elif before.files[path] != after.files[path]:
            kind = "file.modified"
        else:
            continue
        number = len(changes) + 1
        changes.append(Event(
            f"workspace-{turn}-{number}", turn, kind, client, float(number),
            {"path": path},
        ))
    return tuple(changes)


def _path_matches(path, pattern):
    if pattern == "**/*":
        return True
    return fnmatch.fnmatch(path, pattern)


def _result(rule_id, passed, evidence=(), reason=""):
    return RuleResult(rule_id, "pass" if passed else "fail", tuple(evidence), reason)


def _forbidden_writes(rule_id, expectations, trace):
    patterns = expectations.get("forbidden_writes", [])
    evidence = tuple(
        event.id for event in trace.events
        if event.kind in FILE_EVENTS
        and any(_path_matches(event.data.get("path", ""), pattern)
                for pattern in patterns)
    )
    return _result(rule_id, not evidence, evidence, "forbidden workspace mutation")


def _verification(rule_id, trace):
    mutations = [event for event in trace.events if event.kind in FILE_EVENTS]
    last_mutation = max((event.timestamp for event in mutations), default=float("-inf"))
    current = [
        event for event in trace.events
        if event.kind == "verification.finished"
        and event.timestamp > last_mutation
        and event.data.get("status") == "passed"
    ]
    return _result(
        rule_id, bool(current), (current[-1].id,) if current else (),
        "no passing verification after the final mutation",
    )


def _claim(rule_id, expectations, trace):
    claims = [
        event for event in trace.events
        if event.kind == "claim" and event.data.get("claim") == "complete"
    ]
    if not claims and expectations.get("expected_readiness") == "blocked":
        return _result(rule_id, True)
    verifications = {
        event.id: event for event in trace.events
        if event.kind == "verification.finished" and event.data.get("status") == "passed"
    }
    last_mutation = max(
        (event.timestamp for event in trace.events if event.kind in FILE_EVENTS),
        default=float("-inf"),
    )
    valid = []
    for claim in claims:
        evidence = claim.data.get("evidence", [])
        if any(identity in verifications
               and verifications[identity].timestamp > last_mutation
               and verifications[identity].timestamp < claim.timestamp
               for identity in evidence):
            valid.append(claim)
    passed = bool(claims) and len(valid) == len(claims)
    return _result(
        rule_id, passed, tuple(claim.id for claim in claims if claim not in valid),
        "completion claim lacks current passing evidence",
    )


def _evaluate_rule(rule_id, expectations, trace):
    opened = [event for event in trace.events if event.kind == "resource.opened"]
    if rule_id == "LOAD-001":
        invoked = [event.id for event in trace.events if event.kind == "skill.invoked"]
        return _result(rule_id, bool(invoked), invoked)
    if rule_id == "LOAD-002":
        observed = {event.data.get("resource") for event in opened}
        missing = set(expectations.get("required_resources", [])) - observed
        return _result(rule_id, not missing, (), f"missing resources: {sorted(missing)}")
    if rule_id == "LOAD-003":
        forbidden = set(expectations.get("forbidden_resources", []))
        evidence = tuple(
            event.id for event in opened
            if event.data.get("resource") in forbidden
        ) + tuple(
            event.id for event in trace.events if event.kind == "resource.broad_scan"
        )
        return _result(rule_id, not evidence, evidence, "unrelated or broad resource read")
    if rule_id in {"AUTH-001", "AUTH-002", "REVIEW-001"}:
        return _forbidden_writes(rule_id, expectations, trace)
    if rule_id == "STATUS-001":
        forbidden = expectations.get("forbidden_commands", [])
        evidence = tuple(
            event.id for event in trace.events
            if event.kind in FILE_EVENTS or (
                event.kind in {"command.started", "command.finished"}
                and any(marker in event.data.get("command", "") for marker in forbidden)
            )
        )
        return _result(rule_id, not evidence, evidence, "status action changed or verified")
    if rule_id == "VERIFY-001":
        return _verification(rule_id, trace)
    if rule_id == "CLAIM-001":
        return _claim(rule_id, expectations, trace)
    if rule_id == "RECOVERY-001":
        commands = "\n".join(
            event.data.get("command", "") for event in trace.events
            if event.kind == "command.finished"
        )
        missing = [marker for marker in expectations.get("required_commands", [])
                   if marker not in commands]
        return _result(rule_id, not missing, (), f"missing recovery commands: {missing}")
    raise ValueError(f"No deterministic evaluator for {rule_id}")


def evaluate_deterministic(catalog, scenario, trace):
    """Evaluate only rules whose oracle is deterministic."""
    definitions = {rule.id: rule for rule in catalog.rules}
    rule_ids = [rule_id for rule_id in scenario.rules
                if definitions[rule_id].oracle == "deterministic"]
    if not trace.complete:
        return DeterministicEvaluation({
            rule_id: RuleResult(rule_id, "blocked", (), "telemetry is incomplete")
            for rule_id in rule_ids
        })
    return DeterministicEvaluation({
        rule_id: _evaluate_rule(rule_id, scenario.expectations, trace)
        for rule_id in rule_ids
    })
