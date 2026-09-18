"""Review conclusions share the evidence schema and publish real citations."""

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


def review(locale='en'):
    labels = json.loads((ASSETS / f'locales/{locale}.json').read_text(encoding='utf-8'))
    values = labels | {
        'DOC_ID': REVIEW, 'EVD_ID': EVIDENCE, 'TITLE': 'Export review',
        'LOCALE': locale, 'CREATED': '2026-09-18',
        'RECORDED_AT': '2026-09-18T12:00:00+08:00',
        'FINDINGS_WITH_LOCATION_CONSTRAINT_TRIGGER_EVIDENCE_IMPACT_AND_MINIMUM_REMEDY':
            f'F1: {{need}}`{REQ}`; [source](../../spec.md#{DOC}--requirements), line 26.',
    }
    registry = json.loads((ASSETS / 'document-profiles.json').read_text(encoding='utf-8'))
    template_path = registry['profiles']['tao.project.evidence/v0.1']['alternate_templates']['review']
    template = (ASSETS / template_path).read_text(encoding='utf-8')
    return re.sub(r'\{\{([^}]+)\}\}', lambda m: values.get(m[1], 'Not independently reviewed.'), template)


@pytest.mark.parametrize('locale', ['en', 'zh-Hans'])
def test_review_template_validates_as_evidence_and_indexes_citations(tmp_path, locale):
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


@pytest.mark.parametrize('citation,rule', [
    (f'Constraint {REQ}.', 'TAO-REF-005'),
    (f'Constraint `{REQ}`.', 'TAO-REF-005'),
    ('Source `docs/product/spec.md`.', 'TAO-LINK-002'),
    ('Source `docs-snapshot/docs/spec.md:48`.', 'TAO-LINK-002'),
])
def test_unlinked_citations_are_visible_but_not_invented_references(tmp_path, citation, rule):
    result = check(tmp_path, spec() + '\n' + citation + '\n')
    warning = next(d for d in result.diagnostics if d.rule_id == rule)
    assert warning.severity == 'warning'
    assert result.valid
    assert warning.line == len((spec() + '\n' + citation).splitlines())
    assert warning.message_locale == 'zh-Hans'
    assert not any(r.relation == 'links' for r in result.references)


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
