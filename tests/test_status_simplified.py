"""Plan progress is a read-only inference, never a review or delivery verdict."""

import json
import re
import subprocess

import pytest

from taolib.cli import main
from test_documents import spec
from test_relationships import change, CHANGE_DOC, CHG, TASK, TASK_TWO
from test_verification import split


PLAN = "docs/plans/2026-09/20260914-export.md"


def make_plan(root, *, completed=False):
    path = root / PLAN
    path.parent.mkdir(parents=True)
    path.write_text(change() if completed else change().replace('- [x]', '- [ ]'), encoding="utf-8")
    (root / "docs/spec.md").write_text(spec(), encoding="utf-8")
    return path


def call(root, capsys, *arguments):
    code = main(["--project", str(root), "--format", "json", *arguments])
    return code, json.loads(capsys.readouterr().out)


def files(root):
    return {p.relative_to(root).as_posix(): (p.read_bytes(), p.stat().st_mtime_ns)
            for p in root.rglob("*") if p.is_file()}


@pytest.mark.parametrize("target", [CHG, CHANGE_DOC, PLAN])
def test_status_without_configuration_is_read_only_and_project_scoped(tmp_path, capsys, monkeypatch, target):
    make_plan(tmp_path)
    before = files(tmp_path)
    def forbidden(*args, **kwargs):
        pytest.fail("Status must not execute a process or project check")
    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr("taolib.cli.execute", forbidden)
    code, report = call(tmp_path, capsys, "status", target)
    assert code == 0, report
    plan, = report["outputs"]["plans"]
    assert plan["path"] == PLAN
    assert plan["progress"] == "pending"
    assert plan["progress_basis"] == "inferred_from_tasks"
    assert plan["task_counts"] == {"total": 1, "completed": 0, "pending": 1}
    assert plan["pending_tasks"][0]["id"] == TASK
    assert plan["review"] == "unknown"
    assert plan["verification_summary"] == "本例仅用于格式测试，不能作为开发完成证据。"
    assert files(tmp_path) == before
    assert not (tmp_path / ".tao").exists()
    assert not (tmp_path / "tmp").exists()


@pytest.mark.parametrize("attachment", [False, True])
def test_all_checked_means_implementation_complete_not_reviewed(tmp_path, capsys, attachment):
    make_plan(tmp_path, completed=True)
    if attachment:
        split(tmp_path)
    code, report = call(tmp_path, capsys, "status", CHG, "--simplified")
    assert code == 0, report
    outputs = report["outputs"]
    plan, = outputs["plans"]
    assert outputs["output_mode"] == "simplified"
    assert plan["progress"] == "implementation_complete"
    assert plan["review"] == "unknown"
    assert plan["tasks"] == plan["pending_tasks"] == []
    assert plan["task_counts"] == {"total": 1, "completed": 1, "pending": 0}
    assert plan["task_source"] == ("docs/tasks.md" if attachment else PLAN)
    assert "review code" in plan["next_actions"]
    assert "readiness" not in report
    assert "workflows" not in outputs and "evidence" not in outputs


def test_mixed_tasks_are_in_progress_and_simplified_preserves_pending(tmp_path, capsys):
    path = make_plan(tmp_path, completed=True)
    source = path.read_text(encoding="utf-8")
    task = re.search(r"- \[x\].*?(?=<!-- tao:section verification -->)", source, re.S)[0]
    source = source.replace("<!-- tao:section verification -->",
                            task.replace(TASK, TASK_TWO).replace("- [x]", "- [ ]") + "<!-- tao:section verification -->")
    path.write_text(source, encoding="utf-8")
    code, report = call(tmp_path, capsys, "status", "--simplified")
    assert code == 0, report
    plan, = report["outputs"]["plans"]
    assert plan["progress"] == "in_progress"
    assert plan["task_counts"] == {"total": 2, "completed": 1, "pending": 1}
    assert [task["id"] for task in plan["tasks"]] == [TASK_TWO]


def test_spec_without_plan_is_planning_and_creates_nothing(tmp_path, capsys):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/spec.md").write_text(spec(), encoding="utf-8")
    before = files(tmp_path)
    code, report = call(tmp_path, capsys, "status")
    assert code == 0, report
    assert report["outputs"]["plans"] == []
    assert report["outputs"]["planning"][0]["progress"] == "planning"
    assert files(tmp_path) == before


def test_multiple_plans_are_listed_and_handoff_requires_selection(tmp_path, capsys):
    path = make_plan(tmp_path)
    other = path.with_name("20260914-second.md")
    other.write_text(path.read_text(encoding="utf-8").replace(CHANGE_DOC, "DOC_20260914_0000000000000013")
                     .replace(CHG, "CHG_20260914_0000000000000014")
                     .replace(TASK, "TASK_20260914_0000000000000015"), encoding="utf-8")
    code, report = call(tmp_path, capsys, "status")
    assert code == 0, report
    assert len(report["outputs"]["plans"]) == 2
    (tmp_path / "draft.md").write_text("# Next\n", encoding="utf-8")
    before = files(tmp_path)
    code, report = call(tmp_path, capsys, "handoff", "--from", "draft.md")
    assert code == 2, report
    assert PLAN in report["diagnostics"][0]["message"]
    assert other.name in report["diagnostics"][0]["message"]
    assert files(tmp_path) == before
    assert not (tmp_path / "tmp").exists()
    code, report = call(tmp_path, capsys, "handoff", CHANGE_DOC, "--from", "draft.md")
    assert code == 0, report
    assert report["outputs"]["plan"] == PLAN


def test_malformed_plan_is_reported_without_repair(tmp_path, capsys):
    path = make_plan(tmp_path)
    path.write_text(path.read_text(encoding="utf-8").replace("schema:", "invalid_schema:"), encoding="utf-8")
    before = files(tmp_path)
    code, report = call(tmp_path, capsys, "status")
    assert code == 0 and report["status"] == "partial", report
    assert report["outputs"]["documents_valid"] is False
    assert any(row["path"] == PLAN for row in report["diagnostics"])
    assert files(tmp_path) == before


@pytest.mark.parametrize("unrelated", ["# Unfinished draft", spec()])
def test_unrelated_draft_does_not_block_temporary_handoff(tmp_path, capsys, unrelated):
    plan = make_plan(tmp_path)
    (tmp_path / "docs/unrelated.md").write_text(unrelated, encoding="utf-8")
    draft = tmp_path / "context.md"
    draft.write_text("# Next\nImplement the pending task.\n", encoding="utf-8")
    before = plan.read_bytes()
    code, report = call(tmp_path, capsys, "handoff", CHG, "--from", "context.md")
    assert code == 0 and report["status"] == "partial", report
    assert report["outputs"]["documents_valid"] is False
    assert any(row["path"] == "docs/unrelated.md" for row in report["diagnostics"])
    assert (tmp_path / report["outputs"]["path"]).read_bytes() == draft.read_bytes()
    assert plan.read_bytes() == before


def test_handoff_rejects_escaping_source_and_destination(tmp_path, capsys):
    make_plan(tmp_path)
    code, _ = call(tmp_path, capsys, "handoff", CHG, "--from", "../outside.md")
    assert code == 2
    draft = tmp_path / "draft.md"
    draft.write_text("# Next\n", encoding="utf-8")
    destination = tmp_path / "tmp/tao/handoffs"
    destination.parent.mkdir(parents=True)
    destination.symlink_to(tmp_path.parent, target_is_directory=True)
    code, _ = call(tmp_path, capsys, "handoff", CHG, "--from", "draft.md")
    assert code == 2


@pytest.mark.parametrize("problem", ["inline", "attachment", "missing", "mismatched"])
def test_corrupt_task_source_never_implies_implementation_complete(tmp_path, capsys, problem):
    plan = make_plan(tmp_path, completed=True)
    task_source = plan
    if problem != "inline":
        split(tmp_path)
        task_source = tmp_path / "docs/tasks.md"
    if problem == "missing":
        task_source.unlink()
    elif problem == "mismatched":
        task_source.write_text(task_source.read_text(encoding="utf-8").replace(
            CHG, "CHG_20260914_0000000000000099"), encoding="utf-8")
    else:
        text = task_source.read_text(encoding="utf-8")
        insertion = f"\n- [-] `{TASK_TWO}` Unresolved work\n"
        task_source.write_text(text + insertion, encoding="utf-8")
    code, report = call(tmp_path, capsys, "status", CHG)
    assert code == 0 and report["status"] == "partial", report
    row, = report["outputs"]["plans"]
    assert row["progress"] == "unavailable"
    assert row["task_set_valid"] is False and row["task_counts"] is None
    assert "review code" not in row["next_actions"]
    assert row["review"] == "unknown"


def test_invalid_change_identity_cannot_overwrite_shared_handoff(tmp_path, capsys):
    plan = make_plan(tmp_path)
    plan.write_text(plan.read_text(encoding="utf-8").replace(CHG, "draft"), encoding="utf-8")
    note = tmp_path / "context.md"
    note.write_text("new context", encoding="utf-8")
    existing = tmp_path / "tmp/tao/handoffs/draft.md"
    existing.parent.mkdir(parents=True)
    existing.write_text("another plan's context", encoding="utf-8")
    before = files(tmp_path)
    code, report = call(tmp_path, capsys, "handoff", CHANGE_DOC, "--from", "context.md")
    assert code == 2, report
    assert files(tmp_path) == before
