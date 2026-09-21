"""Review conclusions share the evidence schema and publish real citations."""

import json
import re

import pytest

from taolib.documents import ASSETS, validate
from taolib.publication import build
from test_documents import DOC, REQ, check, spec
from test_publication import Page, project
from test_relationships import CHANGE_DOC, CHG, change, check_change, navigation
from test_reviews import setup_review
from test_verification import report as cli_report

REVIEW = 'DOC_20260918_0000000000000001'
EVIDENCE = 'EVD_20260918_0000000000000001'


def review(locale='en', variant='review', **overrides):
    labels = json.loads((ASSETS / f'locales/{locale}.json').read_text(encoding='utf-8'))
    values = labels | {
        'DOC_ID': REVIEW, 'EVD_ID': EVIDENCE, 'TITLE': 'Export review',
        'LOCALE': locale, 'CREATED': '2026-09-18',
        'RECORDED_AT': '2026-09-18T12:00:00+08:00',
        'RESULT': 'unknown', 'COVERAGE': 'unknown',
        'CONSTRAINT':
            f'F1: {{need}}`{REQ}`; [source](../../spec.md#{DOC}--requirements), line 26.',
        'RATIONALE': f'{{need}}`{REQ}`',
    } | overrides
    registry = json.loads((ASSETS / 'document-profiles.json').read_text(encoding='utf-8'))
    template_path = registry['profiles']['tao.project.evidence/v0.1']['alternate_templates'][variant]
    template = (ASSETS / template_path).read_text(encoding='utf-8')
    for key in re.findall(r'\{\{((?:heading|label)\.[^}]+)\}\}', template):
        assert key in labels, f'Missing {locale} translation: {key}'
    return re.sub(r'\{\{([^}]+)\}\}', lambda m: values.get(m[1], 'Not independently reviewed.'), template)


@pytest.mark.parametrize('locale', ['en', 'zh-Hans'])
@pytest.mark.parametrize('variant', ['review', 'review-adjudication'])
def test_review_template_validates_as_evidence_and_indexes_citations(tmp_path, locale, variant):
    (tmp_path / 'docs/engineering/reviews').mkdir(parents=True)
    source = tmp_path / 'docs/spec.md'
    source.write_text(spec(), encoding='utf-8')
    report = tmp_path / 'docs/engineering/reviews/export.md'
    report.write_text(review(locale, variant), encoding='utf-8')
    result = validate(tmp_path, [source, report])
    assert result.valid, result.to_dict()
    assert not result.diagnostics
    assert result.definitions[EVIDENCE].path == 'docs/engineering/reviews/export.md'
    assert any(r.path.endswith('export.md') and r.target == REQ for r in result.references)
    assert result.documents['docs/engineering/reviews/export.md'].metadata['result'] == 'unknown'
    report.write_text(review(locale, variant).replace('<!-- tao:field limits -->', ''), encoding='utf-8')
    assert not validate(tmp_path, [source, report]).valid
    report.write_text(review(locale, variant, RESULT='{{RESULT}}', COVERAGE='{{COVERAGE}}'), encoding='utf-8')
    assert not validate(tmp_path, [source, report]).valid, 'An unfilled outcome must not validate'


@pytest.mark.parametrize('outcome', ['passed', 'failed', 'not_run', 'not_applicable', 'stale', 'unknown'])
def test_evidence_result_extension_preserves_existing_values(tmp_path, outcome):
    source = tmp_path / 'spec.md'
    source.write_text(spec(), encoding='utf-8')
    report = tmp_path / 'report.md'
    report.write_text(review().replace('../../spec.md', 'spec.md').replace('result: "unknown"', f'result: {outcome}'), encoding='utf-8')
    result = validate(tmp_path, [source, report])
    assert result.valid, result.to_dict()
    assert result.documents['report.md'].metadata['result'] == outcome
    report.write_text(report.read_text(encoding='utf-8').replace(f'result: {outcome}', 'result: changes-requested'), encoding='utf-8')
    assert not validate(tmp_path, [source, report]).valid


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


@pytest.mark.parametrize('outcome', ['unknown', 'passed'])
def test_markdown_report_cannot_replace_required_review_receipt(tmp_path, outcome):
    setup_review(tmp_path)
    report = tmp_path / 'docs/engineering/reviews/export.md'
    report.parent.mkdir(parents=True)
    report.write_text(review().replace('result: "unknown"', f'result: {outcome}'), encoding='utf-8')
    code, result = cli_report(tmp_path, 'verify', CHG, '--only', 'docs')
    assert code == 0, result
    assert result['readiness'] == 'not-evaluated'
    code, result = cli_report(tmp_path, 'verify', CHG)
    assert code == 2 and result['readiness'] == 'blocked', result
    assert result['outputs']['reviews'][0]['state'] == 'missing'


@pytest.mark.parametrize('locale', ['en', 'zh-Hans'])
@pytest.mark.parametrize('parent', ['engineering', 'plans/2026-09/20260918-export'])
def test_review_batch_publishes_nested_tables_lists_and_source_links(tmp_path, locale, parent):
    """Synthetic reports exercise rich content inside the five-section contract."""
    configured = project(tmp_path)
    directory = tmp_path / 'docs' / parent / 'reviews/20260918-export-contract'
    directory.mkdir(parents=True)
    source_path = '../' * (len(directory.relative_to(tmp_path / 'docs').parts)) + 'spec.md'
    names = ['01-contract-alpha.md', '02-recovery-beta.md', '03-test-gamma.md']
    for number, name in enumerate(names, 1):
        identity = f'DOC_20260918_{number:016d}'
        fields = {
            'DOC_ID': identity, 'EVD_ID': f'EVD_20260918_{number:016d}',
            'LOCAL_FINDING_ID_AND_TITLE': f'D{number}: qualified defect',
            'LOCATION': f'[source]({source_path}#{DOC}--requirements), line 26',
            'CONSTRAINT': f'{{need}}`{REQ}`',
            'TRIGGER': f'TRIGGER_{number}: only after interrupted export',
            'EVIDENCE': f'HYPOTHESIS_{number}: not reproduced',
            'IMPACT': f'IMPACT_{number}: may lose a partial export',
            'REMEDY': f'REMEDY_{number}: reproduce interruption first',
            'SEVERITY': f'SEVERITY_{number}: blocks only when reproduced',
            'RISKS': f'#### Recovery risk\n\n- RISK_{number}: preserve uncertainty',
            'SUGGESTIONS': f'1. SUGGESTION_{number}: **optional** `retry` label\n\n---',
            'ACCEPTED_LIMITS': f'LIMIT_{number}: offline operation accepted by the owner',
            'UNRESOLVED': f'- UNRESOLVED_{number}: external input remains unknown',
            'NEXT_IMPACT': f'NEXT_{number}: investigate before deciding',
        }
        text = review(locale, **fields)
        if number == 3:
            # An existing report can keep numbered six-element findings.
            text = re.sub(r'^- (\*\*[^\n]+)', r'1. \1', text, flags=re.MULTILINE)
        (directory / name).write_text(text, encoding='utf-8')
    adjudication = 'DOC_20260918_0000000000000004'
    link = f'[{names[0]}]({names[0]}#{REVIEW}--findings)'
    fields = {
        'DOC_ID': adjudication, 'EVD_ID': 'EVD_20260918_0000000000000004',
        'SOURCE_REPORT_LINK': link,
        'REPORTS': '\n'.join(f'- [{name}]({name})' for name in names),
        'SOURCE_REPORT_LINK_AND_LOCAL_FINDING_ID': link + ' D1',
        'FOLLOWUP': 'REVISIT: after a reproducible failure',
        'UNRESOLVED': '- REMAINING: execution time unknown',
        'NEXT_IMPACT': 'IMPACT_ON_PLAN: no implementation authorized',
    }
    text = review(locale, 'review-adjudication', **fields)
    labels = json.loads((ASSETS / f'locales/{locale}.json').read_text(encoding='utf-8'))
    # Complex authors can group the single-table starting point without a
    # different schema; no disposition category is mandatory.
    start = text.index('| ' + labels['label.finding'])
    end = text.index('\n\n', start)
    table = text[start:end]
    groups = ''.join(
        f'### Theme {letter}\n\nDETAIL_{letter}: keep the original explanation.\n\n{table}\n\n'
        for letter in 'ABCDEFG'
    )
    text = text[:start] + groups + 'REJECT_REASON: source premise contradicted by the contract.\n' + text[end:]
    (directory / '00-adjudication.md').write_text(text, encoding='utf-8')
    (directory / 'index.md').write_text(
        navigation('00-adjudication.md\n' + '\n'.join(names)).replace(CHANGE_DOC, 'DOC_20260918_0000000000000005'), encoding='utf-8')
    (tmp_path / 'docs/index.md').write_text(
        navigation('spec.md\n' + (directory / 'index.md').relative_to(tmp_path / 'docs').as_posix()), encoding='utf-8')
    result = validate(tmp_path, list((tmp_path / 'docs').rglob('*.md')), book_root=tmp_path / 'docs/index.md')
    assert result.valid and not result.diagnostics, result.to_dict()
    output = build(configured)
    site = tmp_path / output['directory']
    pages = site / directory.relative_to(tmp_path)
    html = (pages / '00-adjudication.html').read_text(encoding='utf-8')
    assert html.count('<table') == 8
    for sentinel in ['DETAIL_' + letter for letter in 'ABCDE'] + [
        'REVISIT', 'REMAINING', 'IMPACT_ON_PLAN', 'REJECT_REASON',
    ] + [labels[key] for key in ('label.accepted', 'label.partial', 'label.deferred', 'label.rejected')]:
        assert sentinel in html
    assert f'01-contract-alpha.html#{REVIEW}--findings' in [a.get('href') for a in Page(html).links]
    for number, name in enumerate(names, 1):
        html = (pages / name.replace('.md', '.html')).read_text(encoding='utf-8')
        for sentinel in ['SEVERITY', 'TRIGGER', 'HYPOTHESIS', 'IMPACT', 'REMEDY', 'RISK', 'SUGGESTION', 'LIMIT', 'UNRESOLVED', 'NEXT']:
            assert f'{sentinel}_{number}' in html
        assert '<ol' in html and '<ul' in html and '<hr' in html
        assert '<strong>optional</strong>' in html
        hrefs = [a.get('href') for a in Page(html).links]
        assert source_path.replace('.md', '.html') + f'#{DOC}--requirements' in hrefs
        assert '../' * (len(directory.relative_to(tmp_path).parts)) + f'refs/{REQ}.html#{REQ}' in hrefs
        assert f'DOC_20260918_{number:016d}--findings' in Page(html).ids
    assert DOC + '--requirements' in Page((site / 'docs/spec.html').read_text(encoding='utf-8')).ids


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
