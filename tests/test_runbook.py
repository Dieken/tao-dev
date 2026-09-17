"""Validate operational procedures and their actual book navigation."""

import re

import pytest

from taolib.documents import validate
from taolib.project import ConfigurationError
from taolib.publication import build
from test_publication import Page, project
from test_relationships import CHANGE_DOC, navigation


RUNBOOK = "DOC_20260916_0000000000000080"
OPERATIONS = "DOC_20260916_0000000000000081"
SECTIONS = {
    "scope": ("Scope", "Restore the service from a verified backup."),
    "prerequisites": ("Prerequisites", "Have a backup and service access."),
    "steps": ("Steps", "Stop the service, restore the backup, then restart."),
    "verification": ("Verification", "Check health and compare restored records."),
    "recovery": ("Recovery", "If verification fails, restore the previous snapshot."),
}


def runbook():
    header = f'''---
schema: tao.project.runbook/v0.1
id: {RUNBOOK}
title: Restore service
locale: en
status: draft
created: "2026-09-16"
---

# Restore service
'''
    return header + "".join(
        f"\n<!-- tao:section {key} -->\n## {title}\n\n{body}\n"
        for key, (title, body) in SECTIONS.items()
    )


@pytest.mark.parametrize("missing", [None, *SECTIONS])
def test_runbook_requires_all_operational_sections(tmp_path, missing):
    path = tmp_path / "restore.md"
    content = runbook()
    if missing:
        content = re.sub(
            rf"\n<!-- tao:section {missing} -->.*?(?=\n<!-- tao:section |\Z)",
            "", content, flags=re.S,
        )
    path.write_text(content, encoding='utf-8')
    result = validate(tmp_path, [path])
    errors = [item for item in result.diagnostics if item.severity == "error"]
    if missing:
        assert any(item.rule_id == "TAO-DOC-002" for item in errors)
    else:
        assert not errors
        assert RUNBOOK in result.definitions


def sidebar(html):
    return re.search(r'<nav class="bd-links bd-docs-nav".*?</nav>', html, re.S)[0]


def test_operations_book_has_explicit_group_and_stable_runbook_links(tmp_path):
    configured = project(tmp_path)
    first = build(configured)
    directory = tmp_path / first["directory"]
    assert "operations/" not in sidebar((directory / "docs/index.html").read_text(encoding='utf-8'))

    operations = tmp_path / "docs/operations"
    operations.mkdir()
    (operations / "index.md").write_text(
        navigation("restore.md").replace(CHANGE_DOC, OPERATIONS)
        .replace("Book", "Operations guide")
    , encoding='utf-8')
    source = operations / "restore.md"
    source.write_text(runbook(), encoding='utf-8')
    (tmp_path / "docs/index.md").write_text(navigation("spec.md\noperations/index.md"), encoding='utf-8')
    build(configured)

    toc = sidebar((directory / "docs/index.html").read_text(encoding='utf-8'))
    assert re.search(r'class="toctree-l1[^\"]*"[^>]*><a[^>]*href="operations/index.html">2\. Operations guide</a>', toc)
    assert re.search(r'class="toctree-l2[^\"]*"[^>]*><a[^>]*href="operations/restore.html">2\.1\. Restore service</a>', toc)
    page = Page((directory / "docs/operations/restore.html").read_text(encoding='utf-8'))
    assert RUNBOOK in page.ids
    assert page.section_numbers[0] == "2.1. "
    for section in SECTIONS:
        assert f"{RUNBOOK}--{section}" in page.ids
        assert any(link.get("href") == f"../../refs/{RUNBOOK}.html#{RUNBOOK}--{section}"
                   for link in page.links)
    resolver = (directory / f"refs/{RUNBOOK}.html").read_text(encoding='utf-8')
    assert f"../docs/operations/restore.html#{RUNBOOK}" in resolver

    # Invalid operational instructions must fail before replacing the book.
    source.write_text(runbook().split("<!-- tao:section recovery -->")[0], encoding='utf-8')
    previous = (directory / "docs/operations/restore.html").read_text(encoding='utf-8')
    with pytest.raises(ConfigurationError, match="Book sources are invalid"):
        build(configured)
    assert (directory / "docs/operations/restore.html").read_text(encoding='utf-8') == previous
