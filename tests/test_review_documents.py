"""Explicit evidence is optional knowledge, never a workflow approval receipt."""

import json
import re

import pytest

from taolib.documents import ASSETS, validate
from taolib.publication import build
from test_documents import DOC, REQ, check, spec
from test_publication import Page, project
from test_relationships import change, check_change

REVIEW = 'DOC_20260918_0000000000000001'
EVIDENCE = 'EVD_20260918_0000000000000001'


def review(locale='en', **overrides):
    labels = json.loads((ASSETS / f'locales/{locale}.json').read_text(encoding='utf-8'))
    values = labels | {
        'DOC_ID': REVIEW, 'EVD_ID': EVIDENCE, 'TITLE': 'Export review',
        'LOCALE': locale,
        'RECORDED_AT': '2026-09-18T12:00:00+08:00',
        'SCOPE': 'An explicitly retained finding, not a completion certificate.',
        'CONSTRAINT':
            f'F1: {{need}}`{REQ}`; [source](../../spec.md#{DOC}--requirements), line 26.',
        'RATIONALE': f'{{need}}`{REQ}`',
    } | overrides
    registry = json.loads((ASSETS / 'document-profiles.json').read_text(encoding='utf-8'))
    template_path = registry['profiles']['tao.project.evidence/v0.1']['template']
    template = (ASSETS / template_path).read_text(encoding='utf-8')
    values['LIMITS'] = values['CONSTRAINT'] + '\n\n' + values['RATIONALE']
    for key in re.findall(r'\{\{((?:heading|label)\.[^}]+)\}\}', template):
        assert key in labels, f'Missing {locale} translation: {key}'
    return re.sub(r'\{\{([^}]+)\}\}', lambda m: values.get(m[1], 'Not independently reviewed.'), template)


@pytest.mark.parametrize('locale', ['en', 'zh-Hans'])
def test_explicit_evidence_template_indexes_citations(tmp_path, locale):
    (tmp_path / 'docs/engineering/reviews').mkdir(parents=True)
    source = tmp_path / 'docs/spec.md'
    source.write_text(spec(), encoding='utf-8')
    report = tmp_path / 'docs/engineering/reviews/export.md'
    report.write_text(review(locale), encoding='utf-8')
    result = validate(tmp_path, [source, report])
    assert result.valid, result.to_dict()
    assert not result.diagnostics
    assert result.definitions[EVIDENCE].path == 'docs/engineering/reviews/export.md'
    assert any(r.path.endswith('export.md') and r.target == REQ for r in result.references)
    report.write_text(review(locale).replace('<!-- tao:field limits -->', ''), encoding='utf-8')
    assert validate(tmp_path, [source, report]).valid
    report.write_text(review(locale).replace('result: not_run', 'result: {{RESULT}}'), encoding='utf-8')
    assert not validate(tmp_path, [source, report]).valid, 'An unfilled outcome must not validate'


@pytest.mark.parametrize('outcome', ['passed', 'failed', 'not_run', 'not_applicable', 'stale', 'unknown'])
def test_evidence_result_extension_preserves_existing_values(tmp_path, outcome):
    source = tmp_path / 'spec.md'
    source.write_text(spec(), encoding='utf-8')
    report = tmp_path / 'report.md'
    report.write_text(review().replace('../../spec.md', 'spec.md').replace('result: not_run', f'result: {outcome}'), encoding='utf-8')
    result = validate(tmp_path, [source, report])
    assert result.valid, result.to_dict()
    assert result.documents['report.md'].metadata['result'] == outcome
    report.write_text(report.read_text(encoding='utf-8').replace(f'result: {outcome}', 'result: changes-requested'), encoding='utf-8')
    assert not validate(tmp_path, [source, report]).valid


@pytest.mark.parametrize('coverage,valid', [(None, True), ('partial', True), ('full', False)])
def test_optional_evidence_coverage_does_not_invent_an_outcome(tmp_path, coverage, valid):
    source = tmp_path / 'spec.md'
    source.write_text(spec(), encoding='utf-8')
    report = tmp_path / 'report.md'
    content = review().replace('../../spec.md', 'spec.md').replace('result: not_run', 'result: failed')
    if coverage is not None:
        content = content.replace('result: failed', f'result: failed\ncoverage: {coverage}')
    report.write_text(content, encoding='utf-8')
    result = validate(tmp_path, [source, report])
    assert result.valid is valid, result.to_dict()
    assert result.documents['report.md'].metadata['result'] == 'failed'
    assert result.definitions[EVIDENCE].path == 'report.md'


def test_review_html_links_reach_source_and_requirement(tmp_path):
    configured = project(tmp_path)
    report = tmp_path / 'docs/engineering/reviews/export.md'
    report.parent.mkdir(parents=True)
    report.write_text(review(), encoding='utf-8')
    index = tmp_path / 'docs/index.md'
    index.write_text(index.read_text(encoding='utf-8').replace('\nspec.md\n', '\nspec.md\nengineering/reviews/export.md\n'), encoding='utf-8')
    output = build(configured)
    directory = tmp_path / output['directory']
    page = Page((directory / 'docs/engineering/reviews/export.html').read_text(encoding='utf-8'))
    hrefs = [link.get('href', '') for link in page.links]
    assert f'../../../refs/{REQ}.html#{REQ}' in hrefs
    assert f'../../spec.html#{DOC}--requirements' in hrefs
    assert DOC + '--requirements' in Page((directory / 'docs/spec.html').read_text(encoding='utf-8')).ids
    assert '../docs/spec.html#' + REQ in (directory / f'refs/{REQ}.html').read_text(encoding='utf-8')


def test_evidence_sections_can_be_minimal_reordered_and_rich(tmp_path):
    configured = project(tmp_path)
    report = tmp_path / 'docs/report.md'
    header = review().split('<!-- tao:section scope -->')[0]
    report.write_text(header + f'''
<!-- tao:section findings -->
## Findings

### Limits

| Observation | Source |
|---|---|
| An explicit finding | {{need}}`{REQ}` |

1. Reproduce before deciding.
2. Keep uncertainty visible.

<!-- tao:section checks -->
## Checks

- Not run; this record is not task completion evidence.
- [Requirement source](spec.md#{DOC}--requirements)
''', encoding='utf-8')
    index = tmp_path / 'docs/index.md'
    index.write_text(index.read_text(encoding='utf-8').replace(
        '\nspec.md\n', '\nspec.md\nreport.md\n'), encoding='utf-8')
    result = validate(tmp_path, list((tmp_path / 'docs').rglob('*.md')), book_root=index)
    assert result.valid, result.to_dict()
    output = build(configured)
    page = Page((tmp_path / output['directory'] / 'docs/report.html').read_text(encoding='utf-8'))
    assert f'{REVIEW}--findings' in page.ids
    assert f'spec.html#{DOC}--requirements' in [link.get('href') for link in page.links]


def test_evidence_is_not_implicitly_added_to_book(tmp_path):
    configured = project(tmp_path)
    report = tmp_path / 'docs/report.md'
    report.write_text(review().replace('../../spec.md', 'spec.md'), encoding='utf-8')
    result = validate(tmp_path, configured.sources(), book_root=tmp_path / 'docs/index.md')
    assert any(item.path == 'docs/report.md' and 'not reachable' in item.message
               for item in result.diagnostics)


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


def test_historical_record_keeps_its_original_citations(tmp_path):
    """An explicit record describes the past, not a new task to rewrite it."""
    source = tmp_path / 'spec.md'
    source.write_text(spec(), encoding='utf-8')
    report = tmp_path / 'report.md'
    report.write_text(review(CONSTRAINT=f'F1: {REQ}, `docs/handoff.md:64`.',
                             RATIONALE=f'Compare `docs/spec.md` with {REQ}.'
                             ).replace('../../spec.md', 'spec.md'), encoding='utf-8')
    result = validate(tmp_path, [source, report])
    assert result.valid, result.to_dict()
    assert not result.diagnostics


def test_a_record_citing_a_retired_id_is_not_asked_for_the_replacement(tmp_path):
    """The record cites what existed when it was written; the later retirement
    is not a finding against it, while an active document still gets the hint."""
    from test_relationships import OLD, record, retirement
    retirement(tmp_path, json.dumps(record()) + '\n')
    source = tmp_path / 'spec.md'
    source.write_text(spec(), encoding='utf-8')
    report = tmp_path / 'report.md'
    report.write_text(review(CONSTRAINT=f'F1: {{need}}`{OLD}` was merged into {{need}}`{REQ}`.',
                             RATIONALE=f'{{need}}`{OLD}`').replace('../../spec.md', 'spec.md'), encoding='utf-8')
    result = validate(tmp_path, [source, report], baseline_ids={OLD})
    assert result.valid, result.to_dict()
    assert not [d for d in result.diagnostics if d.rule_id == 'TAO-REF-003']
    source.write_text(spec() + f'\n{{need}}`{OLD}`\n', encoding='utf-8')
    warned = validate(tmp_path, [source, report], baseline_ids={OLD})
    assert [d.path for d in warned.diagnostics if d.rule_id == 'TAO-REF-003'] == ['spec.md']


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
