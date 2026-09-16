import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from taolib.documents import ASSETS, validate
from test_documents import REQ, codes, spec
from test_relationships import CHG, CHANGE_DOC, change, check_change


@pytest.mark.parametrize("content", [
    spec().replace("<!-- tao:section terms -->", "<!-- tao:section terms -->\n<!-- tao:section alien -->"),
    spec().replace("<!-- tao:field source -->", "<!-- tao:field alien -->\n\nUnused.\n\n<!-- tao:field source -->"),
    spec().replace("无。", ""),
    spec().replace("```\n\n<!-- tao:section cases", "\n\n<!-- tao:section cases"),
])
def test_damaged_structure_is_not_silently_accepted(tmp_path, content):
    path = tmp_path / "spec.md"
    path.write_text(content, encoding="utf-8")
    assert not validate(tmp_path, [path]).valid


def test_all_bundled_profiles_and_locales_render_as_valid_sources(tmp_path):
    registry = json.loads((ASSETS / "document-profiles.json").read_text())
    for locale in ("en", "zh-Hans"):
        root = tmp_path / locale
        root.mkdir()
        labels = json.loads((ASSETS / f"locales/{locale}.json").read_text())
        paths = []
        for index, profile in enumerate(registry["profiles"].values(), 1):
            template = (ASSETS / profile["template"]).read_text()
            name = Path(profile["template"]).name
            if name == "plan.md":
                name = "2026-09/20260914-export.md"
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            values = {
                "DOC_ID": f"DOC_20260914_{index:016d}", "CHG_ID": CHG,
                "REQ_ID": REQ, "UC_ID": "UC_20260914_0000000000000001",
                "ADR_ID": "ADR_20260914_0000000000000001",
                "TASK_ID": f"TASK_20260914_{index:016d}",
                "EVD_ID": "EVD_20260914_0000000000000001",
                "CREATED": "2026-09-14", "LOCALE": locale,
                "RECORDED_AT": "2026-09-14T12:00:00+08:00",
                "TITLE": "Example" if locale == "en" else "样例",
                "ENTRIES": "spec.md",
            } | labels
            rendered = re.sub(r"\{\{([^}]+)\}\}", lambda m: values.get(m[1], "Concrete example content."), template)
            path.write_text(rendered, encoding="utf-8")
            paths.append(path)
        result = validate(root, paths)
        assert result.valid, result.to_dict()


def test_chinese_evidence_template_labels_the_input_reference():
    labels = json.loads((ASSETS / "locales/zh-Hans.json").read_text())
    template = (ASSETS / "templates/evidence.md").read_text()
    rendered = template.replace(
        "{{label.fingerprint}}", labels["label.fingerprint"]
    )
    assert "**受检输入引用:**" in rendered


def test_split_task_attachment_requires_matching_change_and_no_duplicate_collection(tmp_path):
    task_doc = "DOC_20260914_0000000000000008"
    source = change().replace(f"change: {CHG}", f"change: {CHG}\ntasks_doc: {task_doc}")
    path = tmp_path / "tasks.md"
    path.write_text(f'''---
schema: tao.project.tasks/v0.1
id: {task_doc}
title: Tasks
locale: en
status: draft
created: "2026-09-14"
change: {CHG}
---

# Tasks

<!-- tao:section scope -->
## Scope

Check export.

<!-- tao:section tasks -->
## Tasks

- [ ] `TASK_20260914_0000000000000009` Handle error
  - relates: ["{CHG}"]
  - depends_on: []
  - verify: Assert unchanged file.
''', encoding="utf-8")
    check_change(tmp_path, source)
    result = validate(tmp_path, list(tmp_path.rglob("*.md")))
    assert "TAO-TASK-001" in codes(result)


def test_runtime_copy_works_without_development_repository(tmp_path):
    package = tmp_path / "skill"
    shutil.copytree(ASSETS, package / "assets")
    shutil.copytree(ASSETS.parent / "scripts", package / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
    project = tmp_path / "project"
    project.mkdir()
    (project / "spec.md").write_text(spec(), encoding="utf-8")
    command = [sys.executable, str(package / "scripts/validate_documents.py"), "--project", str(project), "--format", "json", "spec.md"]
    run = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True)
    assert run.returncode == 0, run.stderr
    report = json.loads(run.stdout)
    assert report["valid"] and report["deletion_checked"] is False
    (project / "spec.md").write_text("# No schema\n", encoding="utf-8")
    run = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True)
    assert run.returncode == 1
    assert json.loads(run.stdout)["diagnostics"][0]["rule_id"] == "TAO-DOC-001"
