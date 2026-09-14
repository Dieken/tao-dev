"""Measure maintained Python tests, including their Python subprocesses."""

import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / 'tmp/tao/coverage'
OUTPUT.mkdir(parents=True, exist_ok=True)
environment = os.environ.copy()
environment['TAO_COVERAGE_SOURCE'] = str(ROOT / 'plugins/tao-dev/skills/tao-dev/scripts/taolib')
environment['TAO_COVERAGE_DATA'] = str(OUTPUT / '.coverage')
commands = [
    ['erase'],
    ['run', '-m', 'pytest', '-q'],
    ['combine'],
    ['json', '-o', str(OUTPUT / 'coverage.json')],
    ['report'],
]
failed = 0
for arguments in commands:
    completed = subprocess.run([sys.executable, '-m', 'coverage', *arguments], cwd=ROOT, env=environment)
    failed = failed or completed.returncode
raise SystemExit(failed)
