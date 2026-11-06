"""Let model adapters unwind their cleanup when an outer runner cancels them."""

import signal
from contextlib import contextmanager


@contextmanager
def termination_guard():
    """Translate SIGTERM into an exit that runs existing finally blocks.

    Model clients own separate process groups. Killing only the Python adapter
    bypasses their cleanup; ignoring repeated SIGTERM while unwinding also lets
    its bounded TERM/KILL cleanup finish before the outer runner escalates.
    """
    previous = signal.getsignal(signal.SIGTERM)

    def interrupted(number, frame):
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        raise SystemExit(128 + number)

    signal.signal(signal.SIGTERM, interrupted)
    try:
        yield
    finally:
        signal.signal(signal.SIGTERM, previous)
