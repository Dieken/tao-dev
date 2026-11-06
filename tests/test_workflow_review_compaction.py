"""Durable review history keeps facts and allowances, not execution payloads."""
from copy import deepcopy

import pytest

from taolib import review_runs, workflow_records as records, workflow_recovery as recovery, workflows
from test_workflow_recovery import started


def reviewed(tmp_path, outcome='failed', allowance=2):
    project, state = started(tmp_path)
    request = review_runs.preview(project, state, scope='project', kind='code')
    state = review_runs.begin(project, state['change'], state['revision'], request,
                              'serial', 1, 'Authorize review', max_rounds=allowance)
    if outcome != 'running':
        report = project.output('temporary', 'actual-review.txt')
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text('Actual synthetic review report')
        state = review_runs.finish(project, state['change'], state['revision'], {
            'outcome': outcome, 'reports': ['tmp/tao/actual-review.txt'],
            'summary': 'Long execution details. ' * 1000})
    return project, state


@pytest.mark.parametrize('compact', [False, True])
def test_full_and_compact_legacy_records_remain_readable(tmp_path, compact):
    from test_workflow_recovery import legacy_record
    project, state = reviewed(tmp_path)
    record = legacy_record(project, state, compact)
    records.path(project, state['change']).write_text(records.render(record))
    assert records.read(project, state['change']) == record
    workflows.state_path(project, state['change']).unlink()
    restored = recovery.recover(project, state['change'], True)['candidate']
    assert restored['reviews']['code']['runs'][0]['outcome'] == 'failed'
    assert restored['reviews']['code']['runs'][0]['recovered_context']
    assert not review_runs.passed(project, restored, 'code')


@pytest.mark.parametrize('changed_binding', [False, True])
def test_resume_keeps_local_proof_only_for_matching_control_digest(tmp_path, changed_binding):
    project, state = reviewed(tmp_path, 'passed')
    original = deepcopy(state['reviews'])
    record = records.read(project, state['change'])
    if changed_binding:
        record['review_control']['code']['local_digest'] = 'f' * 64
    record['record_revision'] += 1
    records.path(project, state['change']).write_text(records.render(record))
    state = recovery.reconcile(project, state['change'], state['revision'], 'Reconcile publication')
    if changed_binding:
        assert state['reviews']['code']['runs'] == []
        assert not review_runs.passed(project, state, 'code')
        assert original['code'] in state['recovery_local_reviews'].values()
    else:
        assert state['reviews'] == original
