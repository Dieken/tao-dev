"""Outer acceptance deadlines must cancel model processes and run cleanup."""

import os
import signal
import subprocess
import sys
from pathlib import Path

import pytest

from acceptance.behavior_clients import InvocationRequest
from acceptance.behavior_runner import SubprocessExecutor
from test_live_acceptance import _run


def _alive(pid, marker):
    listing = subprocess.run(
        ['ps', '-p', str(pid), '-o', 'stat=,command='],
        capture_output=True, text=True, check=False,
    ).stdout.strip()
    return bool(listing and not listing.startswith('Z') and str(marker) in listing)


@pytest.mark.skipif(os.name != 'posix', reason='POSIX nested process groups')
@pytest.mark.parametrize('adapter', ['behavior', 'native', 'review'])
def test_outer_timeout_cleans_detached_model_group(tmp_path, adapter):
    model = tmp_path / 'model.pid'
    child = tmp_path / 'child.pid'
    cleaned = tmp_path / 'cleanup.done'
    worker = tmp_path / 'worker.py'
    descendant = (
        'import os,pathlib,time; '
        f'pathlib.Path({str(child)!r}).write_text(str(os.getpid())); '
        'time.sleep(30)'
    )
    client = (
        'import os,pathlib,subprocess,sys,time; '
        f'pathlib.Path({str(model)!r}).write_text(str(os.getpid())); '
        f'subprocess.Popen([sys.executable,"-c",{descendant!r}]); '
        'time.sleep(30)'
    )
    if adapter == 'behavior':
        invocation = (
            'from acceptance.behavior_clients import InvocationRequest\n'
            'from acceptance.behavior_runner import SubprocessExecutor\n'
            f'request=InvocationRequest("claude",1,"",root,root/"events.jsonl",'
            f'(sys.executable,"-c",{client!r}),False,None)\n'
            'SubprocessExecutor(timeout=30)(request)\n'
        )
    elif adapter == 'native':
        invocation = (
            'from acceptance import native_session_hooks as adapter\n'
            'adapter._install=lambda *a,**kw: {"plugin_id":"synthetic"}\n'
            f'adapter._command=lambda *a: [sys.executable,"-c",{client!r}]\n'
            'adapter.run("cursor",root/"native",timeout=30)\n'
        )
    else:
        invocation = (
            f'sys.path.insert(0,{str(Path(__file__).resolve().parents[1] / "scripts")!r})\n'
            'import review_claude as adapter\n'
            'from contextlib import contextmanager\n'
            '@contextmanager\n'
            'def credentials(*a):\n'
            ' yield {},[]\n'
            'adapter.access_environment=credentials\n'
            'adapter.global_configuration=lambda: {}\n'
            '(root/"review").mkdir()\n'
            f'adapter.run_review([sys.executable,"-c",{client!r}],"",root/"review",30)\n'
        )
    worker.write_text(
        'import pathlib,sys\n'
        f'root=pathlib.Path({str(tmp_path)!r})\n'
        'try:\n'
        + ''.join(' '+line+'\n' for line in invocation.splitlines())
        + 'finally:\n'
        f' pathlib.Path({str(cleaned)!r}).write_text("cleaned")\n',
        encoding='utf-8',
    )
    env = os.environ | {'PYTHONPATH': str(Path(__file__).parent.resolve())}
    try:
        with pytest.raises(pytest.fail.Exception, match='timed out'):
            _run([str(worker)], timeout=2, environment=env)
        assert model.is_file() and child.is_file(), 'Synthetic model did not start'
        assert cleaned.is_file(), 'Outer SIGTERM bypassed Python cleanup'
        assert not _alive(int(model.read_text()), model)
        assert not _alive(int(child.read_text()), child)
    finally:
        if model.is_file():
            try:
                os.killpg(int(model.read_text()), signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass


def test_expired_scenario_budget_does_not_spawn_next_model(tmp_path, monkeypatch):
    from acceptance import behavior_runner

    monkeypatch.setattr(behavior_runner.time, 'monotonic', lambda: 20)
    monkeypatch.setattr(behavior_runner.subprocess, 'Popen',
                        lambda *a, **kw: pytest.fail('Expired budget spawned a model'))
    request = InvocationRequest('claude', 2, '', tmp_path, tmp_path / 'turn.jsonl',
                                ('unused',), True, 'same-session')
    result = SubprocessExecutor(timeout=10, deadline=19)(request)
    assert result.timed_out
    assert not request.log_path.exists()


def test_scenario_budget_limits_remaining_turn(tmp_path, monkeypatch):
    from acceptance import behavior_runner

    monkeypatch.setattr(behavior_runner.time, 'monotonic', lambda: 20)
    observed = []

    class Process:
        returncode = 0

        def communicate(self, prompt, *, timeout):
            observed.append(timeout)

        def poll(self):
            return 0

    monkeypatch.setattr(behavior_runner.subprocess, 'Popen', lambda *a, **kw: Process())
    request = InvocationRequest('claude', 2, '', tmp_path, tmp_path / 'turn.jsonl',
                                ('unused',), True, 'same-session')
    result = SubprocessExecutor(timeout=10, deadline=23)(request)
    assert result.returncode == 0
    assert observed == [3]


def test_termination_guard_restores_previous_handler():
    from acceptance.cancellation import termination_guard

    previous = signal.getsignal(signal.SIGTERM)
    with pytest.raises(SystemExit) as raised:
        with termination_guard():
            handler = signal.getsignal(signal.SIGTERM)
            handler(signal.SIGTERM, None)
    assert raised.value.code == 128 + signal.SIGTERM
    assert signal.getsignal(signal.SIGTERM) == previous


@pytest.mark.skipif(os.name != 'posix', reason='POSIX signal escalation')
def test_outer_force_cleanup_uses_kill_for_uncooperative_adapter(tmp_path):
    import time
    from test_live_acceptance import _terminate

    marker = tmp_path / 'ready'
    process = subprocess.Popen([
        sys.executable, '-c',
        'import pathlib,signal,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); '
        f'pathlib.Path({str(marker)!r}).touch(); time.sleep(30)',
    ], start_new_session=True)
    try:
        deadline = time.monotonic() + 5
        while not marker.exists() and time.monotonic() < deadline:
            time.sleep(0.02)
        assert marker.exists()
        _terminate(process, force=True)
        assert process.wait(timeout=5) == -signal.SIGKILL
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
