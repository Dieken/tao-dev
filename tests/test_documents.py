"""Contract examples are deliberately independent of the shipped templates."""

from pathlib import Path

import pytest

from taolib.documents import validate


DOC = "DOC_20260914_0000000000000001"
REQ = "REQ_20260914_ZZZZZZZZZZZZZZZZ"
UC = "UC_20260914_0000000000000002"


def spec():
    return f'''---
schema: tao.project.spec/v0.1
id: {DOC}
title: 文件导出
locale: zh-Hans
status: draft
created: "2026-09-14"
---

# 文件导出

<!-- tao:section scope -->
## 范围

保留已有文件。

<!-- tao:section terms -->
## 术语

文件指输出目标。

<!-- tao:section requirements -->
## 需求

```{{req}} 拒绝覆盖
:id: {REQ}
:status: accepted

当目标已存在时，系统应拒绝导出并保留其内容。

<!-- tao:field acceptance -->
比较导出前后的内容。

<!-- tao:field source -->
用户的数据保护要求。
```

<!-- tao:section cases -->
## 场景

```{{uc}} 已有目标
:id: {UC}
:status: proposed
:verifies: {REQ}

<!-- tao:field given -->
目标已有内容。

<!-- tao:field when -->
请求导出。

<!-- tao:field then -->
内容不变且返回错误。
```

<!-- tao:section questions -->
## 待定

无。
'''


def check(tmp_path, content, **kwargs):
    path = tmp_path / "spec.md"
    path.write_text(content, encoding="utf-8")
    return validate(tmp_path, [path], **kwargs)


def codes(result):
    return {d.rule_id for d in result.diagnostics if d.severity == "error"}


def test_valid_chinese_spec_indexes_forward_references(tmp_path):
    result = check(tmp_path, spec())
    assert codes(result) == set()
    assert set(result.definitions) == {DOC, REQ, UC}
    assert result.definitions[REQ].line == 26


@pytest.mark.parametrize("old,new,rule", [
    ("status: draft", "status: draft\nstatus: accepted", "TAO-DOC-001"),
    ("status: draft", "status: draft\nextra: yes", "TAO-DOC-001"),
    ('"2026-09-14"', '"2026-02-30"', "TAO-DOC-001"),
    ('"2026-09-14"', '2026-09-14', "TAO-DOC-001"),
    ("locale: zh-Hans", "locale: !custom zh-Hans", "TAO-DOC-001"),
    ("locale: zh-Hans", "locale: zh_Hans", "TAO-DOC-001"),
    ("/v0.1", "/v99", "TAO-DOC-001"),
    ("# 文件导出", "# 另一个标题", "TAO-DOC-002"),
    ("<!-- tao:section terms -->", "<!-- tao:section scope -->", "TAO-DOC-002"),
    ("## 术语", "### 术语", "TAO-DOC-002"),
    ("## 术语", "## 术语\n\n#### 跳级", "TAO-DOC-002"),
    ("<!-- tao:field source -->\n用户的数据保护要求。", "", "TAO-ENTITY-001"),
    ("比较导出前后的内容。", "", "TAO-ENTITY-001"),
    (":status: accepted", ":status: invented", "TAO-ENTITY-001"),
    (":status: accepted", ":status: superseded", "TAO-REF-002"),
    (f":verifies: {REQ}", f":verifies: {DOC}", "TAO-REF-002"),
    (f":verifies: {REQ}", ":verifies: REQ_20260914_0000000000000009", "TAO-REF-001"),
    (REQ, "REQ_20260230_ZZZZZZZZZZZZZZZZ", "TAO-ID-001"),
    ("无。", "{{QUESTIONS}}", "TAO-ENTITY-001"),
])
def test_rejects_invalid_contract(tmp_path, old, new, rule):
    result = check(tmp_path, spec().replace(old, new))
    assert rule in codes(result)
    assert all(d.line >= 1 and d.path == "spec.md" for d in result.diagnostics)


def test_examples_do_not_define_or_reference_entities(tmp_path):
    example = f'\n````markdown\n```{{req}} Example\n:id: {REQ}\n```\n{{need}}`REQ_20260914_0000000000000009`\n````\n'
    quoted = f'\n> ```{{req}} Example\n> :id: {REQ}\n> ```\n'
    result = check(tmp_path, spec() + example + quoted)
    assert codes(result) == set()
    assert len(result.definitions) == 3


def test_quoted_field_does_not_satisfy_required_field(tmp_path):
    result = check(tmp_path, spec().replace("<!-- tao:field source -->", "> <!-- tao:field source -->"))
    assert "TAO-ENTITY-001" in codes(result)


def test_duplicate_reports_both_locations(tmp_path):
    one, two = tmp_path / "one.md", tmp_path / "two.md"
    one.write_text(spec(), encoding="utf-8")
    two.write_text(spec(), encoding="utf-8")
    result = validate(tmp_path, [one, two])
    duplicate = next(d for d in result.diagnostics if d.rule_id == "TAO-ID-002")
    assert duplicate.path == "two.md"
    assert duplicate.related_locations[0]["path"] == "one.md"


def test_need_role_resolves_but_inline_code_does_not(tmp_path):
    missing = "REQ_20260914_0000000000000009"
    assert codes(check(tmp_path, spec() + f'\n`{{need}}` and `{missing}`\n')) == set()
    result = check(tmp_path, spec() + f'\n{{need}}`{missing}`\n')
    assert "TAO-REF-001" in codes(result)


@pytest.mark.parametrize("url,rule", [
    ("/private/source.md", "TAO-REF-004"),
    ("file:///private/source.md", "TAO-REF-004"),
    ("../source.md", "TAO-REF-004"),
    ("%2e%2e/source.md", "TAO-REF-004"),
    ("missing.md", "TAO-REF-001"),
    ("spec.md#unstable-heading", "TAO-LINK-001"),
])
def test_rejects_bad_file_links(tmp_path, url, rule):
    assert rule in codes(check(tmp_path, spec() + f'\n[资料]({url})\n'))


def test_relative_stable_link_and_external_source_are_valid(tmp_path):
    result = check(tmp_path, spec() + f'\n[章节](spec.md#{DOC}--requirements) [公共资料](https://example.org/docs)\n')
    assert codes(result) == set()


def test_symlink_cannot_escape_project(tmp_path):
    (tmp_path / "outside").symlink_to(tmp_path.parent, target_is_directory=True)
    assert "TAO-REF-004" in codes(check(tmp_path, spec() + '\n[资料](outside/source.md)\n'))


def test_deleted_definitions_require_baseline_or_retirement(tmp_path):
    missing = "REQ_20260914_0000000000000009"
    result = check(tmp_path, spec(), baseline_ids={missing})
    assert "TAO-ID-003" in codes(result)
    assert check(tmp_path, spec()).deletion_checked is False


def test_bad_utf8_is_a_diagnostic_not_an_exception(tmp_path):
    path = tmp_path / "bad.md"
    path.write_bytes(b"\xff")
    result = validate(tmp_path, [path])
    assert "TAO-DOC-001" in codes(result)


def test_input_file_outside_root_is_not_read(tmp_path):
    result = validate(tmp_path, [tmp_path.parent / "outside.md"])
    assert "TAO-REF-004" in codes(result)
