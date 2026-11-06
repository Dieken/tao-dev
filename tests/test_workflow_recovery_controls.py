"""Recovery authority is bounded independently of review history length."""
from copy import deepcopy

import pytest

from taolib import review_runs, workflow_records as records, workflow_recovery as recovery, workflows
from taolib.project import ConflictError
from test_workflow_review_compaction import reviewed


def test_record_contains_only_current_recovery_control(tmp_path):
    project, state = reviewed(tmp_path)
    record = records.read(project, state['change'])
    control = record['review_control']['code']
    assert control['used'] == 1 and control['limit'] == 2
    assert control['in_flight'] is None
    assert 'review_batches' not in record and 'summary' not in record
    assert len(records.render(record).splitlines()) < 100
    assert 'Long execution details.' in state['reviews']['code']['runs'][0]['summary']


def test_record_size_does_not_grow_with_attempts_or_history(tmp_path):
    project, state = reviewed(tmp_path)
    first = records.render(records.build(project, state))
    batch = state['reviews']['code']
    batch['runs'] *= 1000
    batch['runs'][-1]['round'] = 1000
    state['review_history'] = {'code': [deepcopy(batch)] * 100}
    second = records.render(records.build(project, state))
    assert len(second.encode()) < len(first.encode()) + 20


@pytest.mark.parametrize('outcome', ['passed', 'changes-requested', 'failed'])
def test_recovery_keeps_consumed_allowance_without_fabricating_runs(tmp_path, outcome):
    project, state = reviewed(tmp_path, outcome, allowance=1)
    workflows.state_path(project, state['change']).unlink()
    state = recovery.recover(project, state['change'], True)['candidate']
    assert state['reviews']['code']['runs'] == []
    assert state['reviews']['code']['used_rounds'] == 1
    assert not review_runs.passed(project, state, 'code')
    request = review_runs.preview(project, state, scope='project', kind='code')
    with pytest.raises(ConflictError, match='round limit'):
        review_runs.begin(project, state['change'], state['revision'], request, 'serial', 1, 'Continue')


def test_next_attempt_after_recovery_uses_next_consumed_number(tmp_path):
    project, state = reviewed(tmp_path, allowance=3)
    workflows.state_path(project, state['change']).unlink()
    state = recovery.recover(project, state['change'], True)['candidate']
    request = review_runs.preview(project, state, scope='project', kind='code')
    state = review_runs.begin(project, state['change'], state['revision'], request, 'serial', 1, 'Continue')
    assert state['reviews']['code']['runs'][0]['round'] == 2
    assert records.read(project, state['change'])['review_control']['code']['used'] == 2


def test_recovered_pending_attempt_blocks_dispatch_and_requires_failure_reconciliation(tmp_path):
    project, state = reviewed(tmp_path, 'running')
    pending = state['reviews']['code']['runs'][-1]['id']
    workflows.state_path(project, state['change']).unlink()
    state = recovery.recover(project, state['change'], True)['candidate']
    assert state['reviews']['code']['pending']['id'] == pending
    request = review_runs.preview(project, state, scope='project', kind='code')
    with pytest.raises(ConflictError, match='still recorded as running'):
        review_runs.begin(project, state['change'], state['revision'], request, 'serial', 1, 'Continue', new_batch=True)
    with pytest.raises(ConflictError, match='recovered'):
        review_runs.finish(project, state['change'], state['revision'], {'outcome': 'passed', 'reports': [], 'summary': 'Claim'})
    state = review_runs.finish(project, state['change'], state['revision'], {'outcome': 'failed', 'reports': [], 'summary': 'Actual operation inspected; no usable result'})
    assert state['reviews']['code']['used_rounds'] == 1
    assert records.read(project, state['change'])['review_control']['code']['in_flight'] is None


def test_current_call_limits_are_structured_and_recoverable(tmp_path):
    project, state = reviewed(tmp_path)
    limits = {'timeout_seconds': 1200, 'cost_limit_usd': None}
    state = workflows.mutate(project, state['change'], state['revision'], lambda _, s: s['reviews']['code'].update(limits=limits))
    assert records.read(project, state['change'])['review_control']['code']['limits'] == limits
    workflows.state_path(project, state['change']).unlink()
    recovered = recovery.recover(project, state['change'], True)['candidate']
    assert recovered['reviews']['code']['limits'] == limits


@pytest.mark.parametrize(('field', 'value'), [
    ('used', True), ('used', -1), ('limit', 0), ('limit', False),
    ('phase', []), ('local_digest', []), ('local_digest', 'not-a-digest'),
    ('in_flight', {'id': 'x', 'round': 0}),
    ('in_flight', {'id': 'x', 'round': 2}),
    ('limits', {}), ('limits', {'timeout_seconds': True, 'cost_limit_usd': None}),
    ('limits', {'timeout_seconds': 20, 'cost_limit_usd': float('nan')}),
    ('limits', {'timeout_seconds': 20, 'cost_limit_usd': False}),
    ('limits', {'timeout_seconds': 20, 'cost_limit_usd': 10 ** 400}),
])
def test_malformed_control_rejected_before_recovery(tmp_path, field, value):
    project, state = reviewed(tmp_path)
    record = records.read(project, state['change'])
    record['review_control']['code'][field] = value
    with pytest.raises(ValueError):
        records.validate_record(record)


def test_consumed_count_survives_multiple_recoveries(tmp_path):
    project, state = reviewed(tmp_path, allowance=3)
    for number in (2, 3):
        workflows.state_path(project, state['change']).unlink()
        state = recovery.recover(project, state['change'], True)['candidate']
        request = review_runs.preview(project, state, scope='project', kind='code')
        state = review_runs.begin(project, state['change'], state['revision'], request, 'serial', 1, 'Continue')
        assert state['reviews']['code']['runs'][-1]['round'] == number
        state = review_runs.finish(project, state['change'], state['revision'], {'outcome': 'failed', 'reports': [], 'summary': 'No conclusion'})
    workflows.state_path(project, state['change']).unlink()
    state = recovery.recover(project, state['change'], True)['candidate']
    request = review_runs.preview(project, state, scope='project', kind='code')
    with pytest.raises(ConflictError, match='round limit'):
        review_runs.begin(project, state['change'], state['revision'], request, 'serial', 1, 'Continue')


@pytest.mark.parametrize('when', ['begin', 'end'])
def test_interrupted_local_write_keeps_consumed_attempt_without_fabricated_pass(tmp_path, monkeypatch, when):
    from test_workflow_recovery import started
    project, state = started(tmp_path)
    request = review_runs.preview(project, state, scope='project', kind='code')
    if when == 'end':
        state = review_runs.begin(project, state['change'], state['revision'], request, 'serial', 1, 'Review')
    original_replace = workflows.replace_file
    def fail(*args):
        raise OSError('injected local publication failure')
    monkeypatch.setattr(workflows, 'replace_file', fail)
    with pytest.raises(OSError):
        if when == 'begin':
            review_runs.begin(project, state['change'], state['revision'], request, 'serial', 1, 'Review')
        else:
            review_runs.finish(project, state['change'], state['revision'], {'outcome': 'failed', 'reports': [], 'summary': 'No conclusion'})
    monkeypatch.setattr(workflows, 'replace_file', original_replace)
    state = recovery.reconcile(project, state['change'], state['revision'], 'Inspect interrupted publication')
    assert state['reviews']['code']['used_rounds'] == 1
    assert bool(state['reviews']['code']['pending']) == (when == 'begin')
    assert not review_runs.passed(project, state, 'code')
    assert records.synchronized(project, state, records.read(project, state['change']))


def test_closed_record_drops_consumed_review_control(tmp_path):
    project, state = reviewed(tmp_path)
    state = workflows.finish(project, state['change'], state['revision'], 'Cancel', 'cancelled', {'evidence': [], 'unfinished': ['User abandoned implementation']})
    assert records.read(project, state['change'])['review_control'] == {}
    workflows.state_path(project, state['change']).unlink()
    assert recovery.observation(project, state['change'])['lifecycle'] == 'cancelled'


def test_cli_records_authorized_call_limits(tmp_path, capsys):
    import json
    from test_workflow_recovery import started
    from test_workflows import call
    project, state = started(tmp_path)
    folder = project.output('temporary', 'requests'); folder.mkdir(parents=True)
    limits = {'timeout_seconds': 1200, 'cost_limit_usd': None}
    (folder / 'limits.json').write_text(json.dumps(limits))
    (folder / 'scope.json').write_text(json.dumps(review_runs.preview(project, state, scope='project', kind='code')))
    code, report = call(tmp_path, capsys, 'workflow', 'review-begin', state['change'],
                        '--expect', str(state['revision']), '--from', 'tmp/tao/requests/scope.json',
                        '--mode', 'serial', '--reviewers', '1', '--decision', 'Authorized limits',
                        '--limits-from', 'tmp/tao/requests/limits.json')
    assert code == 0, report
    assert records.read(project, state['change'])['review_control']['code']['limits'] == limits


def test_missing_control_cannot_reuse_local_pass_or_grant_fresh_allowance(tmp_path):
    project, state = reviewed(tmp_path, 'passed')
    original = deepcopy(state['reviews']['code'])
    record = records.read(project, state['change'])
    record['review_control'] = {}
    record['record_revision'] += 1
    records.path(project, state['change']).write_text(records.render(record))
    state = recovery.reconcile(project, state['change'], state['revision'], 'Inspect conflicting local history')
    assert not review_runs.passed(project, state, 'code')
    assert original in state['recovery_local_reviews'].values()
    request = review_runs.preview(project, state, scope='project', kind='code')
    with pytest.raises(ConflictError, match='Unknown review history'):
        review_runs.begin(project, state['change'], state['revision'], request, 'serial', 1, 'Continue')
