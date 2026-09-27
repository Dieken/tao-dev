"""Resolve native client commands for portable subprocess launches."""

from __future__ import annotations

import shutil


_NAMES = {'claude': 'claude', 'codex': 'codex', 'cursor': 'agent', 'kiro': 'kiro-cli'}


def cli_executable(client):
    """Return the executable path, including Windows command shims."""
    try:
        name = _NAMES[client]
    except KeyError as exc:
        raise ValueError(f'Unknown native client: {client}') from exc
    path = shutil.which(name)
    if path is None:
        raise RuntimeError(f'{name} CLI is not installed or is not on PATH.')
    return path
