import json

import pytest

from taolib.documents import validate
from test_documents import DOC, REQ, codes, spec


CHANGE_DOC = "DOC_20260914_0000000000000003"
CHG = "CHG_20260914_0000000000000004"
TASK = "TASK_20260914_0000000000000005"
TASK_TWO = "TASK_20260914_0000000000000006"
OLD = "REQ_20260913_0000000000000007"


def change():
    return f'''---
schema: tao.project.plan/v0.1
id: {CHANGE_DOC}
title: 导出检查
locale: zh-Hans
status: draft
created: "2026-09-14"
change: {CHG}
---

# 导出检查

<!-- tao:section scope -->
## 范围

拒绝覆盖。

<!-- tao:section references -->
## 依据

{{need}}`{REQ}`

<!-- tao:section design -->
## 设计

检查文件是否存在。

<!-- tao:section tasks -->
## 任务

- [x] `{TASK}` 拒绝覆盖已有目标
  - relates: ["{CHG}", "{REQ}"]
  - depends_on: []
  - verify: 执行导出后原有文件内容不变。
  - evidence: [检查结果](#{CHANGE_DOC}--verification)

<!-- tao:section verification -->
## 检查

本例仅用于格式测试，不能作为开发完成证据。

<!-- tao:section questions -->
## 待定

无。
'''


def check_change(tmp_path, content):
    (tmp_path / "spec.md").write_text(spec(), encoding="utf-8")
    path = tmp_path / "docs/plans/2026-09/20260914-export.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return validate(tmp_path, [tmp_path / "spec.md", path])


def test_completed_task_accepts_inline_plan_evidence(tmp_path):
    result = check_change(tmp_path, change())
    assert codes(result) == set()
    assert result.definitions[TASK].status == "completed"


@pytest.mark.parametrize("old,new,rule", [
    ("  - depends_on: []\n", "", "TAO-TASK-001"),
    ("  - depends_on: []", "   - depends_on: []", "TAO-TASK-001"),
    ("  - depends_on: []", f'  - depends_on: ["{TASK}"]', "TAO-REF-002"),
    ("  - depends_on: []", f'  - depends_on: ["{REQ}"]', "TAO-REF-002"),
    ("  - depends_on: []", f'  - depends_on: ["{TASK_TWO}"]', "TAO-REF-001"),
    (f'  - relates: ["{CHG}", "{REQ}"]', '  - relates: []', "TAO-TASK-001"),
    ("- [x]", "- [X]", "TAO-TASK-001"),
    (f'  - evidence: [检查结果](#{CHANGE_DOC}--verification)', "", "TAO-TASK-001"),
    (f'  - evidence: [检查结果](#{CHANGE_DOC}--verification)', '  - evidence: 已检查', "TAO-TASK-001"),
    (f'  - evidence: [检查结果](#{CHANGE_DOC}--verification)', f'  - evidence: [结果](#{CHANGE_DOC}--verification) extra', "TAO-TASK-001"),
    ("  - verify: 执行导出后原有文件内容不变。", "  - verify: ", "TAO-TASK-001"),
    ("created: \"2026-09-14\"", "created: \"2026-09-15\"", "TAO-DOC-002"),
])
def test_rejects_invalid_tasks(tmp_path, old, new, rule):
    assert rule in codes(check_change(tmp_path, change().replace(old, new)))


def test_two_tasks_cannot_depend_on_each_other(tmp_path):
    second = f'''- [ ] `{TASK_TWO}` 检查错误返回
  - relates: ["{CHG}"]
  - depends_on: ["{TASK}"]
  - verify: 断言错误。

'''
    content = change().replace('  - depends_on: []', f'  - depends_on: ["{TASK_TWO}"]')
    content = content.replace('<!-- tao:section verification -->', second + '<!-- tao:section verification -->')
    assert "TAO-REF-002" in codes(check_change(tmp_path, content))


def retirement(tmp_path, records, filename="20260914.jsonl"):
    directory = tmp_path / "docs/retired"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / filename).write_text(records, encoding="utf-8")


def record(**updates):
    return {"id": OLD, "retired_on": "2026-09-14", "reason": "Merged requirement.", "replaced_by": [REQ]} | updates


def retired_check(tmp_path):
    path = tmp_path / "spec.md"
    path.write_text(spec() + f'\n{{need}}`{OLD}`\n', encoding="utf-8")
    return validate(tmp_path, [path], baseline_ids={OLD})


def test_retirement_resolves_old_reference_without_erasing_history(tmp_path):
    retirement(tmp_path, json.dumps(record()) + "\n")
    result = retired_check(tmp_path)
    assert codes(result) == set()
    assert result.definitions[OLD].status == "retired"
    assert any(d.rule_id == "TAO-REF-003" for d in result.diagnostics)
    assert result.deletion_checked


@pytest.mark.parametrize("updates,rule", [
    ({"id": REQ}, "TAO-ID-002"),
    ({"retired_on": "2026-09-15"}, "TAO-DOC-001"),
    ({"retired_on": "2026-02-30"}, "TAO-DOC-001"),
    ({"reason": " "}, "TAO-DOC-001"),
    ({"extra": "value"}, "TAO-DOC-001"),
    ({"replaced_by": [DOC]}, "TAO-REF-002"),
    ({"replaced_by": [OLD]}, "TAO-REF-002"),
    ({"replaced_by": [REQ, REQ]}, "TAO-DOC-001"),
    ({"replaced_by": ["REQ_20260914_0000000000000009"]}, "TAO-REF-001"),
])
def test_invalid_retirement_is_rejected(tmp_path, updates, rule):
    retirement(tmp_path, json.dumps(record(**updates)) + "\n")
    assert rule in codes(retired_check(tmp_path))


def test_duplicate_json_keys_and_blank_retirement_lines_are_errors(tmp_path):
    value = json.dumps(record()).replace('"reason":', '"reason": "one", "reason":')
    retirement(tmp_path, value + "\n\n")
    assert "TAO-DOC-001" in codes(retired_check(tmp_path))


def test_navigation_requires_a_connected_tree(tmp_path):
    (tmp_path / "spec.md").write_text(spec(), encoding="utf-8")
    nav = tmp_path / "index.md"
    nav.write_text(navigation("spec.md"), encoding="utf-8")
    assert codes(validate(tmp_path, [nav, tmp_path / "spec.md"], book_root=nav)) == set()
    nav.write_text(navigation("index.md"), encoding="utf-8")
    assert "TAO-DOC-002" in codes(validate(tmp_path, [nav, tmp_path / "spec.md"], book_root=nav))


def navigation(entries):
    return f'''---
schema: tao.project.navigation/v0.1
id: {CHANGE_DOC}
title: Book
locale: en
status: draft
created: "2026-09-14"
---

# Book

<!-- tao:section overview -->
## Overview

Read in order.

<!-- tao:section contents -->
## Contents

```{{toctree}}
:maxdepth: 2
:titlesonly:

{entries}
```
'''


@pytest.mark.parametrize("entry", ["https://example.com", "spec.md#part", "*.md", "Title <spec.md>", "spec", "spec.md\nspec.md", "missing.md"])
def test_invalid_navigation_is_rejected(tmp_path, entry):
    (tmp_path / "spec.md").write_text(spec(), encoding="utf-8")
    nav = tmp_path / "index.md"
    nav.write_text(navigation(entry), encoding="utf-8")
    assert "TAO-DOC-002" in codes(validate(tmp_path, [nav, tmp_path / "spec.md"], book_root=nav))


def test_link_text_in_prose_is_not_read_as_a_task_checkbox(tmp_path):
    """A review finding cites a file and a task in one bullet; only a checkbox declares a task."""
    prose = (f'\n- **定位:** [规格](../../../spec.md)，收尾任务 {{need}}`{TASK}`。\n'
             f'- **约束:** 另一处 [规格](../../../spec.md) 与 {{need}}`{TASK}` 同列。\n')
    result = check_change(tmp_path, change().replace('检查文件是否存在。', '检查文件是否存在。' + prose))
    assert not [d for d in result.diagnostics if d.rule_id == 'TAO-TASK-001'], [
        (d.rule_id, d.message) for d in result.diagnostics]
    assert result.definitions[TASK].status == "completed"
