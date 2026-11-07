import json
import os
from pathlib import Path
import subprocess
import sys
import threading

import pytest

from taolib.documents import ASSETS
from test_documents import DOC, spec


ENTRY = ASSETS.parent / "scripts/tao.py"


def run(root, *args):
    return subprocess.run([sys.executable, str(ENTRY), "--project", str(root), "--format", "json", *args], capture_output=True, text=True, encoding="utf-8")


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


def test_doctor_does_not_advertise_removed_runtime_or_workflow_commands(tmp_path):
    report = json.loads(run(tmp_path, "doctor").stdout)
    assert not {"env.prepare", "workflow", "review", "verify.evidence"} & set(report["capabilities"])
    assert "runtime" not in report["outputs"]


def test_docs_verify_is_not_delivery_certification(tmp_path):
    project(tmp_path)
    completed = run(tmp_path, "verify", "--only", "docs", "--scope", "changed")
    assert completed.returncode == 0, completed.stderr
    report = json.loads(completed.stdout)
    assert "coverage" not in report
    assert "readiness" not in report
    assert report["scope"] == "all"
    assert report["outputs"]["documents"]["valid"]


def test_docs_verify_simplified_reports_counts_without_full_index(tmp_path):
    project(tmp_path)
    completed = run(tmp_path, "verify", "--only", "docs", "--simplified")
    assert completed.returncode == 0, completed.stderr
    report = json.loads(completed.stdout)
    assert report["output_mode"] == "simplified"
    documents = report["outputs"]["documents"]
    assert documents["valid"]
    assert documents["counts"]["definitions"] > 0
    assert "definitions" not in documents


def test_verify_dry_run_simplified_keeps_planned_status(tmp_path):
    project(tmp_path)
    completed = run(tmp_path, "verify", "--only", "docs", "--dry-run", "--simplified")
    assert completed.returncode == 0, completed.stderr
    report = json.loads(completed.stdout)
    assert report["output_mode"] == "simplified"
    assert report["status"] == "planned"


def test_full_verify_does_not_pass_when_only_docs_are_available(tmp_path):
    project(tmp_path)
    completed = run(tmp_path, "verify")
    assert completed.returncode == 2
    assert json.loads(completed.stdout)["missing_capabilities"] == ["code"]


def test_dry_run_never_claims_execution(tmp_path):
    project(tmp_path)
    report = json.loads(run(tmp_path, "verify", "--only", "docs", "--dry-run").stdout)
    assert report["status"] == "planned"
    assert "readiness" not in report
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
    identity, = json.loads(completed.stdout)["outputs"]["ids"]
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
    assert "## Goal and scope" in path.read_text(encoding="utf-8")
    assert "{{SCOPE}}" in path.read_text(encoding="utf-8")
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
    (tmp_path / ".tao/config.toml").write_text('version = 1\nlocale = "en"\n[documents]\ninclude = ["manual/*.md"]\n', encoding="utf-8")
    (tmp_path / "manual").mkdir()
    (tmp_path / "manual/spec.md").write_text(spec(), encoding="utf-8")
    (tmp_path / "README.md").write_text("# Not managed\n", encoding="utf-8")
    completed = subprocess.run([sys.executable, str(ENTRY), "verify", "--only", "docs", "--format", "json"], cwd=tmp_path, text=True, capture_output=True, encoding="utf-8")
    assert completed.returncode == 0, completed.stderr
    assert list(json.loads(completed.stdout)["outputs"]["documents"]["documents"]) == ["manual/spec.md"]


def test_symlinked_config_and_output_cannot_escape_project(tmp_path):
    project(tmp_path)
    (tmp_path / "docs/plans").symlink_to(tmp_path.parent, target_is_directory=True)
    assert run(tmp_path, "new", "--slug", "escape", "--locale", "en").returncode == 2


def test_empty_managed_scope_does_not_pass_verification(tmp_path):
    completed = run(tmp_path, "verify", "--only", "docs")
    assert completed.returncode == 2
    assert json.loads(completed.stdout)["status"] == "not_run"


def test_unfinished_drafts_do_not_block_id_allocation_or_get_rewritten(tmp_path):
    project(tmp_path)
    draft = tmp_path / "docs/broken.md"
    draft.write_text("# Unfinished specification\n" + DOC, encoding="utf-8")
    before = draft.read_bytes()
    result = run(tmp_path, "id", "new", "DOC", "--count", "2")
    assert result.returncode == 0, result.stdout
    ids = json.loads(result.stdout)["outputs"]["ids"]
    assert len(set(ids)) == 2 and DOC not in ids
    assert draft.read_bytes() == before
    assert not (tmp_path / "tmp").exists()


def test_generator_handles_concurrent_creation_without_overwriting(tmp_path):
    command = [sys.executable, str(ENTRY), "--project", str(tmp_path), "--format", "json", "new", "--slug", "same", "--locale", "en"]
    processes = [subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8") for _ in range(2)]
    results = []
    try:
        for process in processes:
            results.append((process.communicate(timeout=300), process.returncode))
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill()
        for process in processes:
            if process.poll() is None:
                process.communicate(timeout=5)
    # Keep only concise report fields so a platform-specific race failure
    # includes its diagnostic without truncating a complete JSON string.
    details = []
    for (stdout, stderr), code in results:
        report = json.loads(stdout)
        details.append({
            "returncode": code,
            "status": report.get("status"),
            "diagnostics": report.get("diagnostics"),
            "outputs": report.get("outputs"),
            "stderr": stderr,
        })
    assert sorted(code for _, code in results) == [0, 1], details
    assert len(list((tmp_path / "docs").rglob("*.md"))) == 1


def test_a_taken_destination_is_a_conflict_whatever_the_platform_reports(tmp_path, monkeypatch):
    """A platform may answer an existing hard-link destination with something
    other than EEXIST, so exclusive publication decides by the destination
    itself. An unrelated failure still propagates: it is not a lost race."""
    import os
    from taolib.project import ConflictError, create_file

    path = tmp_path / "docs/plans/2026-09/20260914-same.md"
    publisher = "rename" if os.name == "nt" else "link"

    winner = None

    def taken(source, destination):
        nonlocal winner
        winner = threading.Timer(0.05, Path(destination).write_text,
                                 args=('the winner',), kwargs={'encoding': 'utf-8'})
        winner.start()
        raise PermissionError(13, "Access is denied")

    monkeypatch.setattr(os, publisher, taken)
    with pytest.raises(ConflictError):
        create_file(tmp_path, path, "the loser")
    winner.join(timeout=1)
    assert not winner.is_alive()
    assert path.read_text(encoding="utf-8") == "the winner"
    assert not list(path.parent.glob(".tao-new-*"))

    monkeypatch.setattr(os, publisher, lambda source, destination: (_ for _ in ()).throw(OSError(5, "Input/output error")))
    with pytest.raises(OSError) as raised:
        create_file(tmp_path, tmp_path / "docs/other.md", "text")
    assert not isinstance(raised.value, ConflictError)


def test_id_collision_limit_and_full_random_alphabet():
    from datetime import date
    from taolib.identifiers import new_id

    registry = json.loads((ASSETS / "document-profiles.json").read_text(encoding="utf-8"))
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


def test_equals_json_format_is_preserved_on_parser_failure(tmp_path):
    completed = subprocess.run([sys.executable, str(ENTRY), '--project', str(tmp_path), '--format=json', 'unknown-operation'], capture_output=True, text=True, encoding="utf-8")
    assert completed.returncode == 2
    result = json.loads(completed.stdout)
    assert result['status'] == 'not_run'


def test_absent_retirement_directory_is_not_resolved(tmp_path, monkeypatch):
    from taolib.documents import validate

    retired = tmp_path / 'docs/retired'
    original = Path.resolve

    def resolve(path, *args, **kwargs):
        if path == retired:
            raise OSError('simulated concurrent parent update')
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, 'resolve', resolve)
    result = validate(tmp_path, [], retirement_directory='docs/retired')
    assert result.valid, result.to_dict()


def test_absent_retirement_directory_still_validates_boundary_and_overrides(tmp_path):
    from taolib.documents import validate

    outside = validate(tmp_path, [], retirement_directory='../outside/retired')
    assert not outside.valid
    assert any(item.rule_id == 'TAO-REF-004' for item in outside.diagnostics)

    identity = 'REQ_20260914_0000000000000001'
    record = json.dumps({
        'id': identity,
        'retired_on': '2026-09-14',
        'reason': 'Replaced by a current requirement.',
        'replaced_by': [],
    }) + '\n'
    result = validate(tmp_path, [], retirement_directory='docs/retired', overrides={
        'docs/retired/20260914.jsonl': record,
    })
    assert result.valid, result.to_dict()
    assert result.definitions[identity].status == 'retired'


def test_batch_ids_are_unique_and_read_only(tmp_path):
    completed = run(tmp_path, "id", "new", "DOC", "--count", "50")
    assert completed.returncode == 0, completed.stdout
    ids = json.loads(completed.stdout)["outputs"]["ids"]
    assert len(ids) == len(set(ids)) == 50
    assert list(tmp_path.iterdir()) == []
    assert run(tmp_path, "id", "new", "DOC", "--count", "0").returncode == 2
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("command", [("workflow", "status"), ("workflow", "finish"),
                                    ("review", "--from", "review.json"), ("finish",),
                                    ("verify", "--only", "evidence")])
def test_removed_engine_commands_are_rejected_without_writes(tmp_path, command):
    assert run(tmp_path, *command).returncode == 2
    assert list(tmp_path.iterdir()) == []
