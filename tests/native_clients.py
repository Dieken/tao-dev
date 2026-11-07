"""Executable-only readiness for non-billable native inspection."""

import shutil

CLI = {"claude": "claude", "codex": "codex", "cursor": "agent", "kiro": "kiro-cli"}


def cli_skip_reason(client):
    try:
        name = CLI[client]
    except KeyError as exc:
        raise ValueError(f"Unknown native client: {client}") from exc
    return None if shutil.which(name) else f"{client} CLI ({name}) is not installed"


def require_cli(client):
    import pytest

    if reason := cli_skip_reason(client):
        pytest.skip(reason)
