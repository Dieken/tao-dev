"""Formal citations and portable source links retain their normal semantics."""

import pytest

from taolib.documents import validate
from taolib.publication import build
from test_documents import DOC, REQ, check, spec
from test_publication import Page, project
from test_relationships import CHANGE_DOC, change, check_change


def test_plan_html_links_reach_source_and_requirement(tmp_path):
    configured = project(tmp_path)
    report = tmp_path / 'docs/plans/2026-09/export.md'
    report.parent.mkdir(parents=True)
    content = change().replace(CHANGE_DOC, DOC[:-1] + '9')
    report.write_text(content + f'\n[source](../../spec.md#{DOC}--requirements)\n', encoding='utf-8')
    index = tmp_path / 'docs/index.md'
    index.write_text(index.read_text(encoding='utf-8').replace(
        '\nspec.md\n', '\nspec.md\nplans/2026-09/export.md\n'), encoding='utf-8')
    output = build(configured)
    directory = tmp_path / output['directory']
    page = Page((directory / 'docs/plans/2026-09/export.html').read_text(encoding='utf-8'))
    hrefs = [link.get('href', '') for link in page.links]
    assert f'../../../refs/{REQ}.html#{REQ}' in hrefs
    assert f'../../spec.html#{DOC}--requirements' in hrefs
    assert DOC + '--requirements' in Page((directory / 'docs/spec.html').read_text(encoding='utf-8')).ids
    assert '../docs/spec.html#' + REQ in (directory / f'refs/{REQ}.html').read_text(encoding='utf-8')


@pytest.mark.parametrize('citation,rule', [
    (f'Constraint {REQ}.', 'TAO-REF-005'),
    (f'Constraint `{REQ}`.', 'TAO-REF-005'),
    ('Source `docs/product/spec.md`.', 'TAO-LINK-002'),
])
def test_unlinked_citations_are_visible_but_not_invented_references(tmp_path, citation, rule):
    result = check(tmp_path, spec() + '\n' + citation + '\n')
    warning = next(d for d in result.diagnostics if d.rule_id == rule)
    assert warning.severity == 'warning'
    assert result.valid
    assert warning.line == len((spec() + '\n' + citation).splitlines())
    assert warning.message_locale == 'zh-Hans'
    assert not any(r.relation == 'links' for r in result.references)


@pytest.mark.parametrize('citation', ['`docs/spec.md:48`', '`docs/spec.md:48-52`',
                                     '`docs-snapshot/docs/spec.md:26`'])
def test_a_file_reference_carrying_a_line_is_a_citation_not_a_destination(tmp_path, citation):
    """A single line and a line range are one kind of citation, so they are
    judged alike, and neither is asked to become a link: a Markdown link may
    not carry a line number at all, which TAO-REF-004 reports as an error."""
    result = check(tmp_path, spec() + '\nSource ' + citation + '.\n')
    assert not result.diagnostics


def test_linked_ids_examples_and_task_fields_do_not_warn(tmp_path):
    text = spec() + f'''
{{need}}`{REQ}` [{REQ}](spec.md#{REQ})
`tao show {REQ}` `docs/**/*.md` `<scope>.md`
`@AGENTS.md`

({DOC}--scope)=

```markdown
{REQ} `docs/spec.md`
```
'''
    assert not check(tmp_path, text).diagnostics
    check_change(tmp_path, change())
    assert not validate(tmp_path, list(tmp_path.rglob('*.md'))).diagnostics


@pytest.mark.parametrize('target,rule', [
    ('spec.md:26', 'TAO-REF-004'),
    ('docs-snapshot/docs/spec.md:26', 'TAO-REF-001'),
])
def test_markdown_line_number_is_not_a_portable_destination(tmp_path, target, rule):
    result = check(tmp_path, spec() + f'\n[source]({target})\n')
    assert not result.valid
    assert any(d.rule_id == rule for d in result.diagnostics)
