import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from taolib.documents import ASSETS
from test_documents import DOC, spec


ENTRY = ASSETS.parent / "scripts/tao.py"


def run(root, *args):
    return subprocess.run([sys.executable, str(ENTRY), "--project", str(root), "--format", "json", *args], capture_output=True, text=True)


def project(root):
    (root / "docs").mkdir()
    (root / "docs/spec.md").write_text(spec(), encoding="utf-8")


def test_doctor_reports_only_implemented_capabilities_without_writing(tmp_path):
    before = list(tmp_path.iterdir())
    completed = run(tmp_path, "doctor")
    assert completed.returncode == 0, completed.stderr
    report = json.loads(completed.stdout)
    assert report["tool"] == "tao-dev"
    assert "verify.docs" in report["capabilities"]
    assert "verify.code" not in report["capabilities"]
    assert list(tmp_path.iterdir()) == before


def test_doctor_discovers_separately_prepared_publication_environment(tmp_path):
    report = json.loads(run(tmp_path, "doctor").stdout)
    assert "docs.build" in report["capabilities"]
    assert report["outputs"]["runtime"]["publication"]["state"] == "ready"


def test_docs_verify_pass_is_explicitly_partial_without_vcs(tmp_path):
    project(tmp_path)
    completed = run(tmp_path, "verify", "--only", "docs", "--scope", "changed")
    assert completed.returncode == 0, completed.stderr
    report = json.loads(completed.stdout)
    assert report["coverage"] == "partial"
    assert report["readiness"] == "not-evaluated"
    assert report["scope"] == "all"
    assert report["outputs"]["documents"]["valid"]


def test_full_verify_does_not_pass_when_only_docs_are_available(tmp_path):
    project(tmp_path)
    completed = run(tmp_path, "verify")
    assert completed.returncode == 2
    assert json.loads(completed.stdout)["readiness"] == "blocked"


def test_dry_run_never_claims_execution(tmp_path):
    project(tmp_path)
    report = json.loads(run(tmp_path, "verify", "--only", "docs", "--dry-run").stdout)
    assert report["coverage"] == "unknown"
    assert report["readiness"] == "not-evaluated"
    assert "documents" not in report["outputs"]


def test_show_locates_definition(tmp_path):
    project(tmp_path)
    completed = run(tmp_path, "show", DOC)
    assert completed.returncode == 0
    definition = json.loads(completed.stdout)["outputs"]["definition"]
    assert definition["path"] == "docs/spec.md" and definition["line"] == 3
    assert definition["title"] == "文件导出"


def test_id_generator_uses_current_local_date_and_allowed_alphabet(tmp_path):
    from datetime import date
    import re

    completed = run(tmp_path, "id", "new", "REQ")
    assert completed.returncode == 0, completed.stderr
    identity = json.loads(completed.stdout)["outputs"]["id"]
    assert re.fullmatch("REQ_" + date.today().strftime("%Y%m%d") + r"_[0-9A-HJKMNP-TV-Z]{16}", identity)
    assert list(tmp_path.iterdir()) == []


def test_new_creates_localized_skeleton_without_overwriting(tmp_path):
    from datetime import date

    completed = run(tmp_path, "new", "--slug", "export", "--locale", "en")
    assert completed.returncode == 0, completed.stderr
    report = json.loads(completed.stdout)
    path = tmp_path / report["outputs"]["path"]
    assert path.name == date.today().strftime("%Y%m%d") + "-export.md"
    assert path.parent.name == date.today().strftime("%Y-%m")
    assert "## Goal and scope" in path.read_text()
    assert "{{SCOPE}}" in path.read_text()
    assert report["outputs"]["draft_complete"] is False
    before = path.read_bytes()
    repeated = run(tmp_path, "new", "--slug", "export", "--locale", "en")
    assert repeated.returncode == 1
    assert path.read_bytes() == before


@pytest.mark.parametrize("args", [("new",), ("new", "--slug", "../escape", "--locale", "en"), ("new", "--slug", "okay")])
def test_bad_or_incomplete_generation_input_does_not_write(tmp_path, args):
    completed = run(tmp_path, *args)
    assert completed.returncode == 2
    assert json.loads(completed.stdout)["status"] == "not_run"
    assert list(tmp_path.iterdir()) == []


def test_project_config_is_local_and_determines_managed_scope(tmp_path):
    (tmp_path / ".tao").mkdir()
    (tmp_path / ".tao/config.toml").write_text('version = 1\nlocale = "en"\n[documents]\ninclude = ["manual/*.md"]\n')
    (tmp_path / "manual").mkdir()
    (tmp_path / "manual/spec.md").write_text(spec(), encoding="utf-8")
    (tmp_path / "README.md").write_text("# Not managed\n")
    completed = subprocess.run([sys.executable, str(ENTRY), "verify", "--only", "docs", "--format", "json"], cwd=tmp_path, text=True, capture_output=True)
    assert completed.returncode == 0, completed.stderr
    assert list(json.loads(completed.stdout)["outputs"]["documents"]["documents"]) == ["manual/spec.md"]


def test_symlinked_config_and_output_cannot_escape_project(tmp_path):
    project(tmp_path)
    (tmp_path / "docs/changes").symlink_to(tmp_path.parent, target_is_directory=True)
    assert run(tmp_path, "new", "--slug", "escape", "--locale", "en").returncode == 2


def test_empty_managed_scope_does_not_pass_verification(tmp_path):
    completed = run(tmp_path, "verify", "--only", "docs")
    assert completed.returncode == 2
    assert json.loads(completed.stdout)["status"] == "not_run"


def test_id_allocation_does_not_ignore_unreadable_index_scope(tmp_path):
    project(tmp_path)
    (tmp_path / "docs/broken.md").write_text("# Unknown schema\n")
    assert run(tmp_path, "id", "new", "REQ").returncode == 2


def test_generator_handles_concurrent_creation_without_overwriting(tmp_path):
    command = [sys.executable, str(ENTRY), "--project", str(tmp_path), "--format", "json", "new", "--slug", "same", "--locale", "en"]
    processes = [subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(2)]
    results = [(p.communicate(), p.returncode) for p in processes]
    assert sorted(code for _, code in results) == [0, 1]
    assert len(list((tmp_path / "docs").rglob("*.md"))) == 1


def test_id_collision_limit_and_full_random_alphabet():
    from datetime import date
    from taolib.identifiers import new_id

    registry = json.loads((ASSETS / "document-profiles.json").read_text())
    identity = "REQ_20260914_0000000000000000"
    calls = []

    def zeros(count):
        calls.append(count)
        return bytes(count)

    with pytest.raises(ValueError, match="three"):
        new_id("REQ", registry, {identity}, today=date(2026, 9, 14), random_bytes=zeros)
    assert calls == [10, 10, 10]
    assert new_id("REQ", registry, set(), today=date(2026, 9, 14), random_bytes=zeros) == identity
    assert new_id("REQ", registry, set(), today=date(2026, 9, 14), random_bytes=lambda n: b"\xff" * n) == "REQ_20260914_ZZZZZZZZZZZZZZZZ"


def test_handoff_saves_valid_summary_without_stopping_or_committing(tmp_path):
    from test_relationships import change, check_change, CHG

    check_change(tmp_path, change())
    # Include the requirement source at the default managed location.
    (tmp_path / "spec.md").rename(tmp_path / "docs/spec.md")
    draft = tmp_path / "draft.md"
    identity = "DOC_20260914_0000000000000008"
    text = f'''---
schema: tao.project.handoff/v0.1
id: {identity}
title: Export handoff
locale: en
status: draft
created: "2026-09-14"
change: {CHG}
---

# Export handoff
'''
    for key in ("scope", "state", "decisions", "evidence", "next"):
        text += f'\n<!-- tao:section {key} -->\n## {key.title()}\n\nConcrete recovery context.\n'
    draft.write_text(text)
    completed = run(tmp_path, "handoff", CHG, "--from", "draft.md")
    assert completed.returncode == 0, completed.stdout
    target = tmp_path / json.loads(completed.stdout)["outputs"]["path"]
    assert target == tmp_path / "docs/changes/2026-09/20260914-export/handoff.md"
    assert "Concrete recovery context." in target.read_text()
    assert "CLI observation" in target.read_text()
    assert not (tmp_path / ".git").exists()
    draft.write_text(text.replace("Concrete recovery context.", "Updated recovery context."))
    assert run(tmp_path, "handoff", CHG, "--from", "draft.md").returncode == 0
    assert "Updated recovery context." in target.read_text()
    previous = target.read_bytes()
    draft.write_text(text.replace(identity, "DOC_20260914_0000000000000009"))
    assert run(tmp_path, "handoff", CHG, "--from", "draft.md").returncode == 1
    assert target.read_bytes() == previous


def test_equals_json_format_is_preserved_on_parser_failure(tmp_path):
    completed = subprocess.run([sys.executable, str(ENTRY), '--project', str(tmp_path), '--format=json', 'unknown-operation'], capture_output=True, text=True)
    assert completed.returncode == 2
    result = json.loads(completed.stdout)
    assert result['status'] == 'not_run'
