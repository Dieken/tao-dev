"""Durable review history keeps facts and allowances, not execution payloads."""
from copy import deepcopy

import pytest

from taolib import review_runs, workflow_records as records, workflow_recovery as recovery, workflows
from taolib.project import ConflictError
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


def test_durable_review_is_bounded_and_local_payload_is_preserved(tmp_path):
    project, state = reviewed(tmp_path)
    local = deepcopy(state['reviews'])
    record = records.read(project, state['change'])
    run = record['review_batches']['code']['runs'][0]
    assert run['compacted'] is True
    assert 'summary' not in run and 'evidence_boundary' not in run
    assert 'include' not in run['request'] and 'output_files' not in run['request']
    assert len(records.render(record).encode()) < 5000
    assert state['reviews'] == local
    assert 'Long execution details.' in local['code']['runs'][0]['summary']
    assert run['reports'] == local['code']['runs'][0]['reports']
    assert records.compact_reviews(record['review_batches']) == record['review_batches']


def test_recovery_retains_failed_rounds_and_does_not_reset_allowance(tmp_path):
    project, state = reviewed(tmp_path, allowance=1)
    workflows.state_path(project, state['change']).unlink()
    recovered = recovery.recover(project, state['change'], True)['candidate']
    series = recovered['reviews']['code']
    assert series['max_rounds'] == 1 and len(series['runs']) == 1
    assert series['runs'][0]['outcome'] == 'failed'
    request = review_runs.preview(project, recovered, scope='project', kind='code')
    with pytest.raises(ConflictError, match='round limit'):
        review_runs.begin(project, state['change'], recovered['revision'], request,
                          'serial', 1, 'Continue')


@pytest.mark.parametrize('outcome', ['passed', 'running'])
def test_recovery_never_turns_compact_history_into_current_pass(tmp_path, outcome):
    project, state = reviewed(tmp_path, outcome)
    workflows.state_path(project, state['change']).unlink()
    state = recovery.recover(project, state['change'], True)['candidate']
    assert not review_runs.passed(project, state, 'code')
    if outcome == 'running':
        state = review_runs.finish(project, state['change'], state['revision'], {
            'outcome': 'failed', 'reports': [], 'summary': 'Interrupted operation reconciled'})
        assert state['reviews']['code']['runs'][0]['outcome'] == 'failed'


def test_historical_batches_compact_recursively_and_keep_decisions(tmp_path):
    project, state = reviewed(tmp_path)
    request = review_runs.preview(project, state, scope='project', kind='code')
    state = review_runs.begin(project, state['change'], state['revision'], request,
                              'serial', 1, 'New authorized batch', new_batch=True)
    batch = records.read(project, state['change'])['review_batches']['code']
    assert batch['history'][0]['runs'][0]['compacted'] is True
    assert batch['history'][0]['max_rounds'] == 2
    assert batch['decision'] == 'New authorized batch'
    assert batch['history'][0]['decision'] == 'Authorize review'


def test_legacy_full_records_remain_readable(tmp_path):
    project, state = reviewed(tmp_path)
    record = records.read(project, state['change'])
    legacy = deepcopy(state['reviews']['code']['runs'][0])
    legacy['request'] = {k: v for k, v in legacy['request'].items() if k not in {
        'context_files', 'index_entries', 'selected_files', 'excluded_files', 'instruction', 'input_bytes'}}
    for key in ('snapshot', 'snapshot_digest', 'index_snapshot', 'index_snapshot_digest'):
        legacy.pop(key, None)
    legacy['recovered_context'] = True
    record['review_batches']['code']['runs'] = [legacy]
    records.validate_record(record)
    records.path(project, state['change']).write_text(records.render(record))
    assert records.read(project, state['change']) == record
    assert records.compact_reviews(record['review_batches'])['code']['runs'][0]['compacted']


def test_scope_digest_changes_when_only_selection_changes():
    request = {'scope': 'feature', 'base_commit': 'a' * 40, 'target_commit': 'b' * 40,
               'schema': 'tao.review-scope/v0.1', 'change': 'CHG', 'kind': 'code',
               'input_digest': 'c' * 64, 'include': ['one.py'],
               'excluded_record_directories': [], 'output_files': []}
    first = records.compact_request(request)
    request['include'] = ['two.py']
    assert records.compact_request(request) != first


@pytest.mark.parametrize('invalid_request', [None, [], {}, {'schema': 'tao.review-scope/v0.1'}])
def test_invalid_local_request_is_rejected_without_publishing(tmp_path, invalid_request):
    project, state = reviewed(tmp_path)
    before = records.path(project, state['change']).read_bytes()
    state['reviews']['code']['runs'][0]['request'] = invalid_request
    with pytest.raises(ValueError, match='Invalid workflow review attempt'):
        records.build(project, state, records.read(project, state['change']))
    assert records.path(project, state['change']).read_bytes() == before


def test_execution_payload_growth_does_not_grow_durable_record(tmp_path):
    project, state = reviewed(tmp_path)
    first = records.compact_reviews(state['reviews'])
    run = state['reviews']['code']['runs'][0]
    run['summary'] *= 100
    run['request']['include'] = [f'source/{n}.py' for n in range(10000)]
    run['request']['output_files'] = [f'tmp/{n}.md' for n in range(10000)]
    second = records.compact_reviews(state['reviews'])
    import json
    assert len(json.dumps(first)) == len(json.dumps(second))
    assert first['code']['runs'][0]['summary_digest'] != second['code']['runs'][0]['summary_digest']
    assert first['code']['runs'][0]['request'] != second['code']['runs'][0]['request']


@pytest.mark.parametrize(('field', 'value'), [
    ('compacted', False), ('compacted', 1), ('summary_digest', []),
    ('summary_digest', 'invalid'), ('summary', 'Unbounded payload'),
])
def test_malformed_compact_history_is_rejected(tmp_path, field, value):
    project, state = reviewed(tmp_path)
    record = records.read(project, state['change'])
    record['review_batches']['code']['runs'][0][field] = value
    with pytest.raises(ValueError):
        records.validate_record(record)


@pytest.mark.parametrize('changed_selection', [False, True])
def test_resume_keeps_local_proof_only_for_matching_compact_binding(tmp_path, changed_selection):
    project, state = reviewed(tmp_path, 'passed')
    original = deepcopy(state['reviews'])
    record = records.read(project, state['change'])
    if changed_selection:
        record['review_batches']['code']['runs'][0]['request']['selection_digest'] = 'f' * 64
    record['record_revision'] += 1
    records.path(project, state['change']).write_text(records.render(record))
    state = recovery.reconcile(project, state['change'], state['revision'], 'Reconcile publication')
    run = state['reviews']['code']['runs'][0]
    if changed_selection:
        assert run['recovered_context'] and run['compacted']
        assert not review_runs.passed(project, state, 'code')
    else:
        assert run['request'] == original['code']['runs'][0]['request']
        assert run['summary'] == original['code']['runs'][0]['summary']
        assert not run.get('recovered_context') and not run.get('compacted')
