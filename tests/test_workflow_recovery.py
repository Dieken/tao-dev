"""Cross-directory recovery and interrupted migration preserve actual facts."""
import json
import shutil
import pytest
from taolib import workflows, workflow_records as records, workflow_recovery as recovery
from taolib.project import Project, ConflictError


def started(tmp_path):
    project = Project(tmp_path)
    state = workflows.start(project, 'example', 'Example', 'en', 'Start')
    return project, state


def test_cross_directory_recovery_before_plan(tmp_path):
    a = tmp_path / 'a'; a.mkdir()
    p, state = started(a)
    b = tmp_path / 'b'; b.mkdir()
    shutil.copytree(a / 'docs', b / 'docs')
    other = Project(b)
    before = {str(f): f.read_bytes() for f in b.rglob('*') if f.is_file()}
    preview = recovery.recover(other, state['change'])
    assert before == {str(f): f.read_bytes() for f in b.rglob('*') if f.is_file()}
    result = recovery.recover(other, state['change'], True, preview['source_digest'])
    assert result['candidate']['change'] == state['change']
    assert result['candidate']['phase'] == 'spec'
    assert result['candidate']['blockers']
    with pytest.raises(ConflictError):
        recovery.recover(other, state['change'], True)


def test_migration_partial_write_and_extension_preservation(tmp_path, monkeypatch):
    p, state = started(tmp_path)
    records.path(p, state['change']).unlink()
    target = workflows.state_path(p, state['change'])
    state = {k: v for k, v in state.items() if not k.startswith('record_')}
    state['extension'] = {'unknown': [1, 'value']}
    target.write_text(json.dumps(state))
    preview = recovery.migrate(p, state['change'])
    before = target.read_bytes()
    actual = recovery.replace_file
    def fail(*args):
        raise OSError('injected local publication failure')
    monkeypatch.setattr(recovery, 'replace_file', fail)
    with pytest.raises(OSError):
        recovery.migrate(p, state['change'], True, preview['revision'], preview['source_digest'])
    assert target.read_bytes() == before
    assert records.read(p, state['change'])['lifecycle'] == 'unknown'
    monkeypatch.setattr(recovery, 'replace_file', actual)
    restored = recovery.reconcile(p, state['change'], state['revision'], 'Inspect and reconcile')
    assert restored['extension'] == state['extension']
    assert restored['lifecycle'] == 'unknown'
    assert records.synchronized(p, restored, records.read(p, state['change']))


def test_migration_rejects_stale_preview(tmp_path):
    p, state = started(tmp_path)
    records.path(p, state['change']).unlink()
    preview = recovery.migrate(p, state['change'])
    workflows.checkpoint(p, state['change'], 1, {'summary': 'Changed'})
    with pytest.raises(ConflictError):
        recovery.migrate(p, state['change'], True, 1, preview['source_digest'])
    assert not records.path(p, state['change']).exists()


def test_durable_failure_stops_local_advance(tmp_path, monkeypatch):
    p, state = started(tmp_path)
    before = workflows.state_path(p, state['change']).read_bytes()
    def fail(*args, **kwargs):
        raise OSError('injected record publication failure')
    monkeypatch.setattr(records, 'write', fail)
    with pytest.raises(OSError):
        workflows.mutate(p, state['change'], 1, lambda _, s: s.update(phase='design'))
    assert workflows.state_path(p, state['change']).read_bytes() == before


def test_local_failure_blocks_next_event_until_resume(tmp_path, monkeypatch):
    p, state = started(tmp_path)
    before = workflows.state_path(p, state['change']).read_bytes()
    def fail(*args, **kwargs):
        raise OSError('injected local failure')
    monkeypatch.setattr(workflows, 'replace_file', fail)
    with pytest.raises(OSError):
        workflows.mutate(p, state['change'], 1, lambda _, s: s.update(phase='design'))
    assert workflows.state_path(p, state['change']).read_bytes() == before
    with pytest.raises(ConflictError):
        workflows.mutate(p, state['change'], 1, lambda _, s: s.update(phase='plan'))
    result = recovery.reconcile(p, state['change'], 1, 'Reconcile actual outcome')
    assert result['phase'] == 'design'
    assert records.read(p, state['change'])['record_revision'] == 2


def test_unknown_requires_legacy_provenance(tmp_path):
    p, state = started(tmp_path)
    record = records.read(p, state['change']); record['lifecycle'] = 'unknown'
    with pytest.raises(ValueError):
        records.validate_record(record)


def test_plan_only_recovery_keeps_unknown(tmp_path):
    from test_relationships import change
    target = tmp_path / 'docs/plans/2026-09/20260914-export.md'; target.parent.mkdir(parents=True)
    target.write_text(change())
    from test_documents import spec
    (target.parent / "spec.md").write_text(spec())
    p = Project(tmp_path)
    identity = recovery.candidates(p)[0]
    result = recovery.recover(p, identity, True)
    assert result['candidate']['lifecycle'] == 'unknown'
    from taolib.documents import validate
    assert validate(p.root, p.sources()).valid
    workflows.state_path(p, identity).unlink()
    assert recovery.recover(p, identity)['candidate']['lifecycle'] == 'unknown'


def test_cancellation_is_durable_and_idempotent(tmp_path):
    p, state = started(tmp_path)
    result = workflows.finish(p, state['change'], 1, 'Cancel', 'cancelled', {'evidence': [], 'unfinished': ['No implementation; abandoned by user']})
    assert result['lifecycle'] == 'cancelled'
    again = workflows.finish(p, state['change'], 1, 'Cancel', 'cancelled', {'evidence': [], 'unfinished': ['No implementation; abandoned by user']})
    assert again == result
    workflows.state_path(p, state['change']).unlink()
    assert recovery.observation(p, state['change'])['lifecycle'] == 'cancelled'


def test_read_only_missing_diagnostic_and_multiple_candidates(tmp_path):
    p, first = started(tmp_path)
    second = workflows.start(p, 'another', 'Another', 'en', 'Start another')
    workflows.state_path(p, first['change']).unlink()
    rows = workflows.status(p)
    assert {r['change'] for r in rows} == {first['change'], second['change']}
    missing = next(r for r in rows if r['change'] == first['change'])
    assert missing['expected_path'] == str(workflows.state_path(p, first['change']))
    assert missing['recovery_commands'][0][-2:] == ['recover', first['change']]
    assert not workflows.state_path(p, first['change']).exists()


def test_corrupt_state_does_not_break_formal_document_validation(tmp_path):
    p, state = started(tmp_path)
    workflows.state_path(p, state['change']).write_text('{broken')
    from taolib.documents import validate
    assert validate(p.root, p.sources()).valid
    assert 'corrupt' in recovery.observation(p, state['change'])['state']
    with pytest.raises(ConflictError):
        recovery.recover(p, state['change'], True)


def test_approved_doc_identity_survives_move_and_recovery(tmp_path):
    from test_documents import spec
    p, state = started(tmp_path)
    source = tmp_path / 'docs/spec.md'; source.write_text(spec())
    state = workflows.checkpoint(p, state['change'], 1, {'artifacts': {'spec': ['docs/spec.md']}})
    state = workflows.advance(p, state['change'], 2, 'Approve spec')
    source.rename(tmp_path / 'docs/moved.md')
    workflows.state_path(p, state['change']).unlink()
    restored = recovery.recover(p, state['change'], True)['candidate']
    assert restored['artifacts']['spec'] == ['docs/moved.md']
    assert workflows.observe(p, restored)['stale_approvals'] == []
    (tmp_path / 'docs/moved.md').write_text(spec() + '\nChanged requirement.\n')
    assert workflows.observe(p, restored)['stale_approvals'] == ['spec']


def test_embedded_delimiters_round_trip_and_bind(tmp_path):
    from test_documents import spec
    p = Project(tmp_path)
    state = workflows.start(p, 'delimiters', 'Support --- separators', 'en', 'Start')
    assert records.read(p, state['change'])['summary'] == 'Support --- separators'
    source = tmp_path / 'docs/spec.md'; source.write_text(spec().replace('文件导出', '文件---导出'))
    state = workflows.checkpoint(p, state['change'], 1, {'artifacts': {'spec': ['docs/spec.md']}})
    state = workflows.advance(p, state['change'], 2, 'Accept --- unchanged meaning')
    assert workflows.observe(p, state)['stale_approvals'] == []
    assert records.review_contract(records.path(p, state['change']).read_text(), 'docs')
    workflows.state_path(p, state['change']).unlink()
    assert recovery.recover(p, state['change'], True)['candidate']['phase'] == 'design'


def test_unknown_review_budget_requires_new_explicit_allowance(tmp_path):
    from test_relationships import change, CHG
    from test_documents import spec
    from taolib import review_runs
    target = tmp_path / 'docs/plans/2026-09/20260914-export.md'; target.parent.mkdir(parents=True)
    target.write_text(change()); (tmp_path / 'docs/spec.md').write_text(spec())
    p = Project(tmp_path); state = recovery.recover(p, CHG, True)['candidate']
    request = review_runs.preview(p, state, scope='project', kind='code')
    with pytest.raises(ConflictError, match='Unknown review history'):
        review_runs.begin(p, CHG, state['revision'], request, 'serial', 1, 'Continue')
    with pytest.raises(ConflictError):
        review_runs.begin(p, CHG, state['revision'], request, 'serial', 1, 'New batch', new_batch=True)
    state = review_runs.begin(p, CHG, state['revision'], request, 'serial', 1, 'Authorize two new attempts despite missing history', new_batch=True, max_rounds=2)
    assert state['review_budget_unknown'] == ['docs']
    assert records.read(p, CHG)['provenance']['review_budget_unknown'] == ['docs']


def test_incomplete_nested_review_rejected_before_recovery(tmp_path):
    from taolib.documents import validate
    p, state = started(tmp_path)
    data = records.read(p, state['change'])
    data['review_batches'] = {'code': {'max_rounds': 2, 'runs': [{'id': 'arbitrary', 'outcome': 'passed'}]}}
    records.path(p, state['change']).write_text(records.render(data))
    assert not validate(p.root, p.sources()).valid
    workflows.state_path(p, state['change']).unlink()
    with pytest.raises(ValueError):
        recovery.recover(p, state['change'], True)
    assert not workflows.state_path(p, state['change']).exists()


@pytest.mark.parametrize('changed', [False, True])
def test_finish_requires_current_scheduler_review(tmp_path, changed):
    from test_verification import configured
    from test_relationships import change, CHG
    from test_workflows import git
    from taolib import review_runs
    from taolib.git_workflow import context
    configured(tmp_path)
    (tmp_path/'.gitignore').write_text('/tmp/\n/.tao/workflows/\n')
    (tmp_path/'docs/plans/2026-09/20260914-export.md').write_text(change())
    git(tmp_path, 'init', '-b', 'main'); git(tmp_path, 'config', 'user.email', 'test@example.test'); git(tmp_path, 'config', 'user.name', 'Test')
    git(tmp_path, 'add', '.'); git(tmp_path, 'commit', '-m', 'Fixture')
    p = Project(tmp_path); state = recovery.recover(p, CHG, True)['candidate']
    state = workflows.mutate(p, CHG, state['revision'], lambda _, s: s.update(phase='review', lifecycle='active', git=context(tmp_path), blockers=[]))
    request = review_runs.preview(p, state, scope='project', kind='code')
    state = review_runs.begin(p, CHG, state['revision'], request, 'serial', 1, 'Authorize new review with two attempts', new_batch=True, max_rounds=2)
    report = tmp_path/'tmp/tao/report.txt'; report.parent.mkdir(parents=True, exist_ok=True); report.write_text('Actual fixture review')
    state = review_runs.finish(p, CHG, state['revision'], {'outcome': 'passed', 'reports': ['tmp/tao/report.txt'], 'summary': 'Pass'})
    state = workflows.advance(p, CHG, state['revision'], 'Finish')
    assert review_runs.passed(p, state, 'code')
    if changed:
        (tmp_path/'check.py').write_text('print("changed after review")')
        with pytest.raises(ConflictError, match='current code review'):
            workflows.finish(p, CHG, state['revision'], 'Complete', 'completed', {'evidence': [], 'unfinished': []})
        assert records.read(p, CHG)['lifecycle'] == 'active'
    else:
        state = workflows.finish(p, CHG, state['revision'], 'Complete', 'completed', {'evidence': [], 'unfinished': []})
        assert state['lifecycle'] == 'completed'


@pytest.mark.parametrize(('field', 'value'), [
    ('base_commit', ['invalid type']), ('base_commit', 42),
    ('target_commit', {}), ('target_commit', ''),
    ('change', []), ('change', 'CHG_invalid'),
    ('change', 'CHG_20260101_0000000000000000'), ('scope', []),
    ('kind', {}), ('schema', []), ('input_digest', []),
    ('include', [42]), ('excluded_record_directories', {}),
    ('output_files', [None]),
])
def test_invalid_review_request_rejected_at_source(tmp_path, field, value):
    from taolib import review_runs
    from taolib.documents import validate
    p, state = started(tmp_path)
    request = review_runs.preview(p, state, scope='project', kind='code')
    state = review_runs.begin(p, state['change'], state['revision'], request, 'serial', 1, 'Review')
    data = records.read(p, state['change'])
    data['review_batches']['code']['runs'][0]['request'][field] = value
    records.path(p, state['change']).write_text(records.render(data))
    assert not validate(p.root, p.sources()).valid
    workflows.state_path(p, state['change']).unlink()
    with pytest.raises(ValueError):
        recovery.recover(p, state['change'], True)
    assert not workflows.state_path(p, state['change']).exists()


def test_recovered_running_project_review_can_record_failure(tmp_path):
    from taolib import review_runs
    p, state = started(tmp_path)
    request = review_runs.preview(p, state, scope='project', kind='code')
    assert request['base_commit'] is None and request['target_commit'] is None
    state = review_runs.begin(p, state['change'], state['revision'], request, 'serial', 1, 'Review')
    workflows.state_path(p, state['change']).unlink()
    state = recovery.recover(p, state['change'], True)['candidate']
    state = review_runs.finish(p, state['change'], state['revision'],
                              {'outcome': 'failed', 'reports': [], 'summary': 'Interrupted'})
    assert state['reviews']['code']['runs'][0]['outcome'] == 'failed'


@pytest.mark.parametrize('identity', [None, [], 42, 'not-a-change'])
def test_invalid_plan_identity_does_not_break_workflow_discovery(tmp_path, identity):
    import yaml
    from taolib.documents import validate
    p, state = started(tmp_path)
    target = tmp_path / 'docs/broken-plan.md'
    target.write_text('---\n' + yaml.safe_dump({
        'schema': 'tao.project.plan/v0.1', 'id': 'DOC_20260101_0000000000000000',
        'title': 'Incomplete plan', 'locale': 'en', 'status': 'draft',
        'created': '2026-01-01', 'change': identity,
    }) + '---\n\n# Incomplete plan\n')
    assert not validate(p.root, p.sources()).valid
    assert recovery.candidates(p) == [state['change']]
    updated = workflows.checkpoint(p, state['change'], state['revision'], {'summary': 'Preserve current progress'})
    assert updated['summary'] == 'Preserve current progress'
