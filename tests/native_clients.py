"""Readiness checks for optional native Claude / Codex / Cursor probes.

Personal credentials are inspected read-only. Probes never log in, refresh
tokens, or write authentication files. CI sets TAO_TEST_NATIVE_CLIENTS=1 so
install/scope/removal probes can run on runners that have the CLI but no login.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

CLI = {'claude': 'claude', 'codex': 'codex', 'cursor': 'agent'}


def cli_name(client):
    try:
        return CLI[client]
    except KeyError as exc:
        raise ValueError(f'Unknown native client: {client}') from exc


def installed(client):
    return shutil.which(cli_name(client)) is not None


def _claude_logged_in():
    raw = None
    if sys.platform == 'darwin':
        try:
            result = subprocess.run(
                ['security', 'find-generic-password', '-s', 'Claude Code-credentials', '-w'],
                capture_output=True, text=True, timeout=8, check=False, encoding='utf-8')
            if result.returncode == 0 and result.stdout.strip():
                raw = result.stdout.strip()
        except (OSError, subprocess.TimeoutExpired):
            raw = None
    if raw is None:
        path = Path.home() / '.claude/.credentials.json'
        if not path.is_file():
            return False
        try:
            raw = path.read_text(encoding='utf-8')
        except OSError:
            return False
    try:
        data = json.loads(raw).get('claudeAiOauth', {})
    except (ValueError, TypeError):
        return False
    return isinstance(data.get('accessToken'), str) and bool(data['accessToken'])


def _codex_logged_in():
    path = Path.home() / '.codex/auth.json'
    if not path.is_file():
        return False
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        tokens = data.get('tokens') or {}
        return bool(data.get('auth_mode') and tokens.get('access_token'))
    except (OSError, ValueError, TypeError):
        return False


def _cursor_logged_in():
    try:
        result = subprocess.run(['agent', 'status'], capture_output=True, text=True,
                                timeout=8, check=False, encoding='utf-8')
        if result.returncode == 0 and 'Logged in' in (result.stdout or ''):
            return True
    except (OSError, subprocess.TimeoutExpired):
        pass
    path = Path.home() / '.cursor/cli-config.json'
    if not path.is_file():
        return False
    try:
        info = json.loads(path.read_text(encoding='utf-8')).get('authInfo') or {}
    except (OSError, ValueError, TypeError):
        return False
    return bool(info.get('email') or info.get('userId') or info.get('authId'))


def logged_in(client):
    return {'claude': _claude_logged_in, 'codex': _codex_logged_in, 'cursor': _cursor_logged_in}[client]()


def skip_reason(client):
    """Why a native probe for this client should be skipped, or None to run."""
    name = cli_name(client)
    if not installed(client):
        return f'{client} CLI ({name}) is not installed'
    # CI and explicit maintainer overrides exercise install without credentials.
    if os.environ.get('TAO_TEST_NATIVE_CLIENTS') == '1':
        return None
    if not logged_in(client):
        return f'{client} is not logged in'
    return None


def require(client):
    import pytest
    reason = skip_reason(client)
    if reason:
        pytest.skip(reason)
