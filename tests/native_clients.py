"""Readiness checks for optional native coding-agent probes.

CLI-only probes require just the executable. Real sessions additionally require
read-only evidence of an existing login. Tests never log in or refresh tokens,
and local development and CI use the same rules.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

CLI = {'claude': 'claude', 'codex': 'codex', 'cursor': 'agent', 'kiro': 'kiro-cli'}


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


def _kiro_logged_in():
    try:
        result = subprocess.run(['kiro-cli', 'whoami'], capture_output=True, text=True,
                                timeout=8, check=False, encoding='utf-8')
    except (OSError, subprocess.TimeoutExpired):
        return False
    output = (result.stdout or result.stderr or '').lower()
    return result.returncode == 0 and bool(output.strip()) and 'not logged in' not in output


def logged_in(client):
    probes = {
        'claude': _claude_logged_in,
        'codex': _codex_logged_in,
        'cursor': _cursor_logged_in,
        'kiro': _kiro_logged_in,
    }
    return probes[client]()


def cli_skip_reason(client):
    """Why a CLI-only probe should skip, or None when it can run."""
    name = cli_name(client)
    return None if installed(client) else f'{client} CLI ({name}) is not installed'


def session_skip_reason(client):
    """Why a real client session should skip, or None when it can run."""
    reason = cli_skip_reason(client)
    if reason:
        return reason
    return None if logged_in(client) else f'{client} is not logged in'


def require_cli(client):
    import pytest
    reason = cli_skip_reason(client)
    if reason:
        pytest.skip(reason)


def require_session(client):
    import pytest
    reason = session_skip_reason(client)
    if reason:
        pytest.skip(reason)


def skip_reason(client):
    """Backward-compatible name for the stricter real-session check."""
    return session_skip_reason(client)


def require(client):
    """Backward-compatible guard for real sessions."""
    require_session(client)
