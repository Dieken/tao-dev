"""Requirement coverage is enumerated from the baseline, never from memory."""

import pytest

from taolib import coverage
from taolib.documents import validate
from taolib.project import Project
from test_documents import spec
from test_relationships import change, CHG, REQ


def project_with(root, *, spec_text=None, plan_text=None):
    (root / 'docs').mkdir()
    (root / 'docs/spec.md').write_text(spec_text if spec_text is not None else spec(), encoding='utf-8')
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
