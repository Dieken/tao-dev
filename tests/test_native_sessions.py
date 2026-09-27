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


def test_native_session_termination_stops_process_group(tmp_path):
    import os
    if os.name != 'posix':
        pytest.skip('POSIX process-group assertion')
    import signal
    import subprocess
    import sys
    import time

    from acceptance.native_session_hooks import _terminate

    marker = tmp_path / 'tao-process-group-child'
    child = (
        'import os,pathlib,time; '
        f'pathlib.Path({str(marker)!r}).write_text(str(os.getpid())); '
        'time.sleep(30)'
    )
    process = subprocess.Popen([
        sys.executable, '-c',
        'import subprocess,sys,time; '
        'subprocess.Popen([sys.executable,"-c",sys.argv[1]]); time.sleep(30)',
        child,
    ], start_new_session=True)
    try:
        deadline = time.monotonic() + 5
        while not marker.is_file() and time.monotonic() < deadline:
            time.sleep(0.05)
        assert marker.is_file(), 'process-group child did not start'
        child_pid = int(marker.read_text())
        _terminate(process, signal.SIGTERM)
        process.wait(timeout=5)

        # killpg(pid, 0) can report EPERM on macOS after the group leader
        # exits, and the original PID can be reused. Inspect the uniquely
        # marked descendant instead of treating either condition as proof of
        # a surviving process group. A zombie is already terminated; its
        # eventual reaping is outside this assertion.
        for _ in range(100):
            listing = subprocess.run(
                ['ps', '-p', str(child_pid), '-o', 'stat=,command='],
                capture_output=True, text=True, check=False,
            ).stdout.strip()
            status = listing.split(None, 1)[0] if listing else ''
            if 'tao-process-group-child' not in listing or status.startswith('Z'):
                break
            time.sleep(0.05)
        else:
            pytest.fail('process group child still exists after termination')
    finally:
        if process.poll() is None:
            _terminate(process, signal.SIGKILL)
            process.wait(timeout=5)


def test_native_hook_timeout_cannot_exceed_45_seconds(tmp_path):
    with pytest.raises(ValueError, match='between 1 and 45'):
        run('cursor', tmp_path / 'unused', timeout=46)
