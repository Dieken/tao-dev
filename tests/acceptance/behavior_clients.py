"""Command and session adapters for supported real coding-agent clients."""

import json
import uuid
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class InvocationRequest:
    client: str
    turn: int
    prompt: str
    workspace: Path
    log_path: Path
    command: tuple[str, ...]
    resume: bool
    requested_session_id: str | None


class ClientAdapter:
    def __init__(self, client):
        self.client = client

    def request(self, prompt, workspace, log_path, turn, session_id):
        resume = session_id is not None
        requested_session_id = session_id
        if self.client == "claude":
            command = [
                "claude", "-p", "--output-format", "stream-json", "--verbose",
                "--strict-mcp-config", "--permission-mode", "acceptEdits",
                "--permission-prompts", "none", "--max-budget-usd", "2",
                "--tools", "Read,Glob,Grep,Skill,Bash,Write,Edit",
                "--allowedTools", "Read,Glob,Grep,Skill,Bash,Write,Edit",
            ]
            if resume:
                command.extend(("--resume", session_id))
            else:
                requested_session_id = str(uuid.uuid4())
                command.extend(("--session-id", requested_session_id))
        else:
            command = ["codex", "-a", "never", "exec"]
            if resume:
                command.extend(("resume", "--json", "--skip-git-repo-check",
                                session_id, "-"))
            else:
                command.extend(("--json", "--skip-git-repo-check", "--sandbox",
                                "workspace-write", "-"))
        return InvocationRequest(
            self.client, turn, prompt, Path(workspace), Path(log_path),
            tuple(command), resume, requested_session_id,
        )

    def session_id(self, log_path):
        try:
            rows = [json.loads(line) for line in Path(log_path).read_text().splitlines()
                    if line.strip()]
        except (OSError, json.JSONDecodeError):
            return None
        if self.client == "claude":
            return next((row.get("session_id") for row in rows
                         if row.get("session_id")), None)
        return next((row.get("thread_id") for row in rows
                     if row.get("type") == "thread.started"
                     and row.get("thread_id")), None)


def adapter_for(client):
    if client not in {"claude", "codex"}:
        raise ValueError(f"Unsupported client: {client}")
    return ClientAdapter(client)
