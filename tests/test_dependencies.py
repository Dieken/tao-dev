"""The distributed dependency inventory must match its development source."""

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def test_release_requirements_are_current_locked_exports():
    completed = subprocess.run(
        [sys.executable, str(ROOT / "scripts/export_dependencies.py"), "--check"],
        cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_shipped_dependency_lists_have_no_development_or_local_packages():
    scripts = ROOT / "plugins/tao-dev/skills/tao-dev/scripts"
    for name in ("requirements.txt", "requirements-publication.txt"):
        text = (scripts / name).read_text(encoding='utf-8')
        assert "--hash=sha256:" in text
        assert not any(value in text for value in
                       ("pytest==", "coverage==", "ruff==", "-e .", "file://"))
