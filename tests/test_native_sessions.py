"""Logged-in Cursor and Kiro sessions must trigger their installed hooks."""

import pytest

import native_clients
from acceptance.native_session_hooks import run


@pytest.mark.parametrize('client', ('cursor', 'kiro'))
def test_logged_in_native_session_triggers_tao_hook(client, tmp_path):
    native_clients.require_session(client)
    summary = run(client, tmp_path / 'workspace')
    assert summary['exact_native_write'] is True
    assert summary['hook_feedback_observed'] is True
    assert summary['personal_state_unchanged'] is True


def test_native_session_termination_stops_process_group():
    import os
    if os.name != 'posix':
        pytest.skip('POSIX process-group assertion')
    import signal
    import subprocess
    import sys
    import time

    from acceptance.native_session_hooks import _terminate

    process = subprocess.Popen([
        sys.executable, '-c',
        'import subprocess,sys,time; subprocess.Popen([sys.executable,"-c","import time; time.sleep(30)"]); time.sleep(30)',
    ], start_new_session=True)
    time.sleep(0.2)
    _terminate(process, signal.SIGTERM)
    process.wait(timeout=5)
    with pytest.raises(ProcessLookupError):
        os.killpg(process.pid, 0)


def test_native_hook_timeout_cannot_exceed_45_seconds(tmp_path):
    with pytest.raises(ValueError, match='between 1 and 45'):
        run('cursor', tmp_path / 'unused', timeout=46)
