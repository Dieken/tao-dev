"""Requirement coverage is enumerated from the baseline, never from memory."""

import pytest

from taolib import coverage
from taolib.documents import validate
from taolib.project import Project
from test_documents import DOC, UC, spec
from test_relationships import change, CHG, REQ


OTHER_DOC = "DOC_20260914_0000000000000011"
OTHER_REQ = "REQ_20260914_0000000000000012"


def other_spec():
    """A second specification, so a declared range can leave one out."""
    return spec().replace(DOC, OTHER_DOC).replace(REQ, OTHER_REQ).replace(
        UC, "UC_20260914_0000000000000013").replace('文件导出', '文件导入')


def declaring(*documents):
    """The plan fixture, naming the specifications its range covers."""
    return change().replace('created: "2026-09-14"',
                            'created: "2026-09-14"\nspec_docs: [' + ', '.join(documents) + ']')


def project_with(root, *, spec_text=None, plan_text=None, extra=None):
    (root / 'docs').mkdir()
    (root / 'docs/spec.md').write_text(spec_text if spec_text is not None else spec(), encoding='utf-8')
    for name, content in (extra or {}).items():
        (root / 'docs' / name).write_text(content, encoding='utf-8')
    (root / 'docs/plans/2026-09').mkdir(parents=True)
    (root / 'docs/plans/2026-09/20260914-export.md').write_text(
        plan_text if plan_text is not None else change(), encoding='utf-8')
    (root / '.tao').mkdir()
    (root / '.tao/config.toml').write_text('version = 1\n', encoding='utf-8')
    project = Project(root)
    return project, validate(project.root, project.sources())


def at(previous):
    """A baseline reader returning the given text for the specification."""
    return lambda revision, name: previous if name.endswith('spec.md') else None


def test_a_requirement_changed_without_a_task_is_reported(tmp_path):
    changed = spec().replace('当目标已存在时，系统应拒绝导出并保留其内容。', '当目标已存在时，系统应拒绝导出、保留其内容并记录拒绝原因。')
    project, index = project_with(tmp_path, spec_text=changed)
    result = coverage.report(project, index, CHG, 'BASE', at(spec()))
    assert result['state'] == 'evaluated'
    assert REQ in result['changed']


def test_an_unchanged_requirement_is_not_asked_for(tmp_path):
    project, index = project_with(tmp_path)
    result = coverage.report(project, index, CHG, 'BASE', at(spec()))
    assert result['changed'] == [] and result['uncovered'] == []


def test_a_declared_deferral_exempts_and_a_malformed_one_fails(tmp_path):
    changed = spec().replace('当目标已存在时，系统应拒绝导出并保留其内容。', '当目标已存在时，系统应拒绝导出、保留其内容并记录拒绝原因。')
    deferral = f'\n- deferred: {REQ} — 等上游接口确定后由下一个事项承接\n'
    plan = change().replace('<!-- tao:section questions -->', '<!-- tao:section questions -->' + deferral)
    project, index = project_with(tmp_path, spec_text=changed, plan_text=plan)
    result = coverage.report(project, index, CHG, 'BASE', at(spec()))
    assert result['uncovered'] == [] and REQ in result['deferred']
    assert not result['invalid_deferrals']

    broken = change().replace('<!-- tao:section questions -->', f'<!-- tao:section questions -->\n- deferred: {REQ}\n')
    (tmp_path / 'docs/plans/2026-09/20260914-export.md').write_text(broken, encoding='utf-8')
    index = validate(project.root, project.sources())
    result = coverage.report(project, index, CHG, 'BASE', at(spec()))
    assert result['invalid_deferrals'], 'a deferral without a trigger is not an exemption'


@pytest.mark.parametrize('baseline,state', [(None, 'not-applicable'), ('', 'not-evaluated')])
def test_a_missing_baseline_is_never_reported_as_passing(tmp_path, baseline, state):
    """No workflow record is a condition; a record without a revision is an
    unfinished check. Neither may read as coverage confirmed."""
    project, index = project_with(tmp_path)
    result = coverage.report(project, index, CHG, baseline, at(spec()))
    assert result['state'] == state and 'uncovered' not in result


def test_a_plan_without_declared_specifications_states_no_range(tmp_path):
    """spec_docs is optional, so an absent range is a condition to report, not
    a range to infer from whichever specifications happen to be managed."""
    project, index = project_with(tmp_path)
    result = coverage.report(project, index, CHG, 'BASE', at(spec()))
    assert result['scope']['state'] == 'not-declared'
    assert 'uncovered' not in result['scope']


def test_the_declared_range_asks_for_requirements_the_baseline_no_longer_reports(tmp_path):
    """Once a requirement reaches the baseline it stops being a difference,
    while the plan still owes it a task."""
    plan = declaring(DOC).replace(f'"{CHG}", "{REQ}"', f'"{CHG}"')
    project, index = project_with(tmp_path, plan_text=plan)
    result = coverage.report(project, index, CHG, 'BASE', at(spec()))
    assert result['uncovered'] == [], 'the requirement is unchanged against the baseline'
    assert result['scope']['uncovered'] == [REQ]
    assert result['scope']['requirements'] == 1 and result['scope']['specifications'] == ['docs/spec.md']


def test_a_deferral_exempts_a_requirement_from_the_declared_range(tmp_path):
    deferral = f'\n- deferred: {REQ} — 等上游接口确定后由下一个事项承接\n'
    plan = declaring(DOC).replace(f'"{CHG}", "{REQ}"', f'"{CHG}"').replace(
        '<!-- tao:section questions -->', '<!-- tao:section questions -->' + deferral)
    project, index = project_with(tmp_path, plan_text=plan)
    result = coverage.report(project, index, CHG, 'BASE', at(spec()))
    assert result['scope']['uncovered'] == [] and REQ in result['deferred']


def test_a_task_relating_outside_the_declared_range_is_reported(tmp_path):
    """The requirement resolves and carries the right type; what fails is that
    the plan never declared the specification defining it."""
    plan = declaring(DOC).replace(f'"{CHG}", "{REQ}"', f'"{CHG}", "{REQ}", "{OTHER_REQ}"')
    project, index = project_with(tmp_path, plan_text=plan, extra={'other.md': other_spec()})
    assert index.valid, [d.rule_id for d in index.diagnostics]
    result = coverage.report(project, index, CHG, 'BASE', at(spec()))
    assert result['scope']['out_of_scope'] == [OTHER_REQ]
    assert result['scope']['uncovered'] == []


def test_declaring_both_specifications_puts_the_requirement_back_in_range(tmp_path):
    plan = declaring(DOC, OTHER_DOC).replace(f'"{CHG}", "{REQ}"', f'"{CHG}", "{REQ}", "{OTHER_REQ}"')
    project, index = project_with(tmp_path, plan_text=plan, extra={'other.md': other_spec()})
    result = coverage.report(project, index, CHG, 'BASE', at(spec()))
    assert result['scope']['out_of_scope'] == [] and result['scope']['uncovered'] == []
    assert result['scope']['requirements'] == 2


@pytest.mark.parametrize('baseline', [None, ''])
def test_the_declared_range_is_reported_without_a_baseline(tmp_path, baseline):
    """The range needs no revision to compare against, so it still answers in
    exactly the case that stops the baseline angle."""
    plan = declaring(DOC).replace(f'"{CHG}", "{REQ}"', f'"{CHG}"')
    project, index = project_with(tmp_path, plan_text=plan)
    result = coverage.report(project, index, CHG, baseline, at(spec()))
    assert result['scope']['uncovered'] == [REQ]


def test_a_malformed_deferral_is_reported_without_a_baseline(tmp_path):
    plan = declaring(DOC).replace('<!-- tao:section questions -->',
                                  f'<!-- tao:section questions -->\n- deferred: {REQ}\n')
    project, index = project_with(tmp_path, plan_text=plan)
    result = coverage.report(project, index, CHG, None, at(spec()))
    assert result['state'] == 'not-applicable' and result['invalid_deferrals']


def test_an_unresolved_requirement_is_left_to_the_reference_resolver(tmp_path):
    """Naming a missing ID as out of range would report the wrong cause."""
    missing = "REQ_20260914_0000000000000014"
    plan = declaring(DOC).replace(f'"{CHG}", "{REQ}"', f'"{CHG}", "{REQ}", "{missing}"')
    project, index = project_with(tmp_path, plan_text=plan)
    assert 'TAO-REF-001' in {d.rule_id for d in index.diagnostics}
    assert coverage.report(project, index, CHG, 'BASE', at(spec()))['scope']['out_of_scope'] == []


def test_a_deferral_declaration_is_not_a_prose_citation(tmp_path):
    """The declaration the coverage check requires must not collide with the
    prose citation rule: written as the grammar demands, it is not a finding."""
    deferral = f'- deferred: {REQ} — 等上游接口确定后由下一个事项承接'
    plan = change().replace('## 待定\n\n无。', '## 待定\n\n' + deferral)
    project, index = project_with(tmp_path, plan_text=plan)
    assert [d.rule_id for d in index.diagnostics] == []
    declared, faults = coverage.deferrals(project, index, CHG)
    assert declared.get(REQ) and not faults


def test_a_bare_requirement_id_in_prose_is_still_reported(tmp_path):
    """Only the declaration is exempt; the section is not a quiet corner."""
    plan = change().replace('## 待定\n\n无。', f'## 待定\n\n还需确认 {REQ} 的上游接口。')
    project, index = project_with(tmp_path, plan_text=plan)
    assert [d.rule_id for d in index.diagnostics] == ['TAO-REF-005']
