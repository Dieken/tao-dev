"""Plan progress is a read-only inference, never a review or delivery verdict."""

import json
import re
import subprocess

import pytest

from taolib.cli import main
from test_documents import spec
from test_cli import run
from test_relationships import change, CHANGE_DOC, CHG, TASK, TASK_TWO


PLAN = "docs/plans/2026-09/20260914-export.md"
TASKS_DOC = 'DOC_20260914_0000000000000020'


def split(root):
    """Move the plan's inline tasks into its declared task attachment."""
    path = root / PLAN
    plan = path.read_text(encoding='utf-8')
    block = re.search(r'<!-- tao:section tasks -->(.*?)<!-- tao:section verification -->', plan, re.S)[1]
    path.write_text(plan.replace(block, '\n## 任务\n\n任务在附件中维护。\n\n')
                    .replace('change: ' + CHG, 'change: ' + CHG + '\ntasks_doc: ' + TASKS_DOC), encoding='utf-8')
    (root / 'docs/tasks.md').write_text(f"""---
schema: tao.project.tasks/v0.1
id: {TASKS_DOC}
title: 导出检查任务
locale: zh-Hans
status: draft
change: {CHG}
---

# 导出检查任务

<!-- tao:section scope -->
## 范围

承接导出检查的任务。

<!-- tao:section tasks -->{block}""".replace('(#DOC', '(plans/2026-09/20260914-export.md#DOC'), encoding='utf-8')


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
    code, report = call(tmp_path, capsys, "status", target)
    assert code == 0, report
    plan, = report["outputs"]["plans"]
    assert plan["path"] == PLAN
    assert plan["progress"] == "pending"
    assert plan["progress_basis"] == "inferred_from_tasks"
    assert plan["task_counts"] == {"total": 1, "completed": 0, "pending": 1}
    assert plan["pending_tasks"][0]["id"] == TASK
    assert not {"review", "delivery", "tasks", "verification_summary", "section_summary"} & plan.keys()
    assert "本例仅用于格式测试，不能作为开发完成证据。" not in json.dumps(report, ensure_ascii=False)
    assert "本例仅用于格式测试，不能作为开发完成证据。" in (tmp_path / PLAN).read_text(encoding="utf-8")
    assert files(tmp_path) == before
    assert not (tmp_path / ".tao").exists()
    assert not (tmp_path / "tmp").exists()


@pytest.mark.parametrize("attachment", [False, True])
def test_all_checked_means_tasks_complete_not_reviewed(tmp_path, capsys, attachment):
    make_plan(tmp_path, completed=True)
    if attachment:
        split(tmp_path)
    code, report = call(tmp_path, capsys, "status", CHG)
    assert code == 0, report
    outputs = report["outputs"]
    plan, = outputs["plans"]
    assert "output_mode" not in outputs
    assert plan["progress"] == "tasks_complete"
    assert not {"review", "delivery", "tasks", "verification_summary"} & plan.keys()
    assert plan["pending_tasks"] == []
    assert plan["task_counts"] == {"total": 1, "completed": 1, "pending": 0}
    assert plan["task_source"] == ("docs/tasks.md" if attachment else PLAN)
    assert "readiness" not in report
    assert "workflows" not in outputs and "evidence" not in outputs


def test_mixed_tasks_are_in_progress_and_preserve_pending_only(tmp_path, capsys):
    path = make_plan(tmp_path, completed=True)
    source = path.read_text(encoding="utf-8")
    task = re.search(r"- \[x\].*?(?=<!-- tao:section verification -->)", source, re.S)[0]
    source = source.replace("<!-- tao:section verification -->",
                            task.replace(TASK, TASK_TWO).replace("- [x]", "- [ ]") + "<!-- tao:section verification -->")
    path.write_text(source, encoding="utf-8")
    code, report = call(tmp_path, capsys, "status")
    assert code == 0, report
    plan, = report["outputs"]["plans"]
    assert plan["progress"] == "in_progress"
    assert plan["task_counts"] == {"total": 2, "completed": 1, "pending": 1}
    assert [task["id"] for task in plan["pending_tasks"]] == [TASK_TWO]
    assert "tasks" not in plan
    assert TASK not in json.dumps(report)


def test_spec_without_plan_is_planning_and_creates_nothing(tmp_path, capsys):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/spec.md").write_text(spec(), encoding="utf-8")
    before = files(tmp_path)
    code, report = call(tmp_path, capsys, "status")
    assert code == 0, report
    assert report["outputs"]["plans"] == []
    assert report["outputs"]["planning"][0]["progress"] == "planning"
    assert "review" not in report["outputs"]["planning"][0]
    assert files(tmp_path) == before


def test_multiple_plans_are_listed_and_can_be_selected(tmp_path, capsys):
    path = make_plan(tmp_path)
    other = path.with_name("20260914-second.md")
    other.write_text(path.read_text(encoding="utf-8").replace(CHANGE_DOC, "DOC_20260914_0000000000000013")
                     .replace(CHG, "CHG_20260914_0000000000000014")
                     .replace(TASK, "TASK_20260914_0000000000000015"), encoding="utf-8")
    code, report = call(tmp_path, capsys, "status")
    assert code == 0, report
    assert len(report["outputs"]["plans"]) == 2
    code, report = call(tmp_path, capsys, "status", CHANGE_DOC)
    assert code == 0, report
    assert [plan["path"] for plan in report["outputs"]["plans"]] == [PLAN]


def test_malformed_plan_is_reported_without_repair(tmp_path, capsys):
    path = make_plan(tmp_path)
    path.write_text(path.read_text(encoding="utf-8").replace("schema:", "invalid_schema:"), encoding="utf-8")
    before = files(tmp_path)
    code, report = call(tmp_path, capsys, "status")
    assert code == 0 and report["status"] == "partial", report
    assert report["outputs"]["documents_valid"] is False
    assert any(row["path"] == PLAN for row in report["diagnostics"])
    assert files(tmp_path) == before


@pytest.mark.parametrize("problem", ["inline", "attachment", "missing", "mismatched"])
def test_corrupt_task_source_never_implies_tasks_complete(tmp_path, capsys, problem):
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
    assert "review" not in row


@pytest.mark.parametrize('attachment', [False, True])
def test_documents_pass_independently_of_task_completion_or_reviews(tmp_path, capsys, attachment):
    make_plan(tmp_path)
    if attachment:
        split(tmp_path)
    code, result = call(tmp_path, capsys, 'verify')
    assert code == 0, result
    assert 'readiness' not in result
    assert not {'open_tasks', 'reviews', 'requirement_coverage'} & result['outputs'].keys()
    code, result = call(tmp_path, capsys, 'status', CHG)
    assert code == 0, result
    plan, = result['outputs']['plans']
    assert plan['task_counts']['pending'] == 1
    assert "review" not in plan


@pytest.mark.parametrize("attachment", [False, True])
def test_status_reads_task_updates_across_processes_without_copying_results(tmp_path, attachment):
    path = make_plan(tmp_path)
    if attachment:
        split(tmp_path)
    source = tmp_path / "docs/tasks.md" if attachment else path
    before = files(tmp_path)
    first = run(tmp_path, "status", CHG)
    assert first.returncode == 0, first.stdout
    assert json.loads(first.stdout)["outputs"]["plans"][0]["progress"] == "pending"
    assert files(tmp_path) == before

    source.write_text(source.read_text(encoding="utf-8").replace("- [ ]", "- [x]"), encoding="utf-8")
    before = files(tmp_path)
    second = run(tmp_path, "status", CHG)
    assert second.returncode == 0, second.stdout
    plan, = json.loads(second.stdout)["outputs"]["plans"]
    assert plan["progress"] == "tasks_complete"
    assert plan["pending_tasks"] == []
    assert plan["task_source"] == ("docs/tasks.md" if attachment else PLAN)
    assert not {"tasks", "verification_summary", "review", "delivery"} & plan.keys()
    assert "本例仅用于格式测试，不能作为开发完成证据。" not in second.stdout
    assert "本例仅用于格式测试，不能作为开发完成证据。" in path.read_text(encoding="utf-8")
    assert files(tmp_path) == before


@pytest.mark.parametrize("option", ["--simplified", "--simplifed", "--summary", "--full"])
def test_unsupported_status_options_are_rejected_without_writes(tmp_path, capsys, monkeypatch, option):
    make_plan(tmp_path)
    before = files(tmp_path)

    def forbidden(*args, **kwargs):
        pytest.fail("Rejected options must not execute a process")

    monkeypatch.setattr(subprocess, "Popen", forbidden)
    code, report = call(tmp_path, capsys, "status", CHG, option)
    assert code == 2 and report["status"] == "not_run"
    assert report["diagnostics"]
    assert report["outputs"] == {}
    assert files(tmp_path) == before
