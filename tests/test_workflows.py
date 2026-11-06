"""Workflow checkpoints survive sessions without authorizing stale artifacts."""
import json
import subprocess
from pathlib import Path
import pytest
from taolib.cli import main


def call(root, capsys, *args):
    code = main(['--project', str(root), '--format', 'json', *args])
    report = json.loads(capsys.readouterr().out)
    return code, report


def start(root, capsys, *extra):
    code, report = call(root, capsys, 'workflow', 'start', '--slug', 'filter', '--summary', 'Filter tasks', '--locale', 'en', '--decision', 'Write the specification', *extra)
    assert code == 0, report
    return report['outputs']


def test_start_without_plan_then_read_only_status(tmp_path, capsys):
    state = start(tmp_path, capsys)
    assert state['phase'] == 'spec' and state['revision'] == 1
    assert not list((tmp_path / 'docs/plans').rglob('*.md'))
    assert len(list((tmp_path / 'docs/workflows').glob('*.md'))) == 1
    before = {str(p): p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}
    code, report = call(tmp_path, capsys, 'status', state['change'])
    assert code == 0, report
    assert report['outputs']['workflows'][0]['phase'] == 'spec'
    full_size = len(json.dumps(report))
    code, concise = call(tmp_path, capsys, 'status', state['change'], '--simplified')
    assert code == 0, concise
    assert concise['outputs']['output_mode'] == 'simplified'
    assert concise['outputs']['workflows'][0]['phase'] == 'spec'
    assert len(json.dumps(concise)) < full_size
    assert before == {str(p): p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}


def test_workflow_status_simplified_bounds_local_history(tmp_path, capsys):
    state = start(tmp_path, capsys)
    path = tmp_path / '.tao/workflows' / f"{state['change']}.json"
    stored = json.loads(path.read_text(encoding='utf-8'))
    stored['review_history'] = {'code': [{'round': 1, 'report': 'verbose history'}]}
    path.write_text(json.dumps(stored), encoding='utf-8')
    code, report = call(tmp_path, capsys, 'workflow', 'status', state['change'], '--simplified')
    assert code == 0, report
    assert report['outputs']['output_mode'] == 'simplified'
    row = report['outputs']['workflows'][0]
    assert row['phase'] == 'spec'
    assert 'review_history' not in row
    assert row['review_history_count'] == 1
    assert row['review_history_counts'] == {'code': 1}


def test_checkpoint_rejects_stale_revision_and_escaping_artifact(tmp_path, capsys):
    state = start(tmp_path, capsys)
    from taolib.workflows import checkpoint
    from taolib.project import Project, ConflictError, ConfigurationError
    project = Project(tmp_path)
    state = checkpoint(project, state['change'], 1, {'summary': 'Clarified', 'next': 'Write spec'})
    with pytest.raises(ConflictError):
        checkpoint(project, state['change'], 1, {'summary': 'old writer'})
    with pytest.raises(ConfigurationError):
        checkpoint(project, state['change'], 2, {'artifacts': {'spec': ['../outside.md']}})
    assert state['revision'] == 2


def test_approval_tracks_content_and_requires_new_decision_after_edits(tmp_path, capsys):
    state = start(tmp_path, capsys)
    from taolib.workflows import checkpoint, advance, observe
    from taolib.project import Project, ConflictError
    from test_documents import spec
    p = tmp_path / 'docs/spec.md'; p.parent.mkdir(exist_ok=True); p.write_text(spec(), encoding='utf-8')
    project = Project(tmp_path)
    state = checkpoint(project, state['change'], 1, {'artifacts': {'spec': ['docs/spec.md']}})
    state = advance(project, state['change'], 2, 'Spec accepted; write design')
    assert state['phase'] == 'design'
    p.write_text(p.read_text(encoding='utf-8')+'\nChanged requirement interpretation.\n', encoding='utf-8')
    view = observe(project, state)
    assert view['stale_approvals'] == ['spec']
    # The refusal names the stale phase, which is not the phase being advanced.
    with pytest.raises(ConflictError, match='spec'):
        advance(project, state['change'], 3, 'Continue')


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True, encoding='utf-8').strip()


def test_worktree_records_fork_and_parent_can_find_workflow(tmp_path, capsys):
    git(tmp_path, 'init', '-b', 'main')
    git(tmp_path, 'config', 'user.email', 'test@example.test'); git(tmp_path, 'config', 'user.name', 'Test')
    (tmp_path / '.gitignore').write_text('/.worktrees/\n', encoding='utf-8')
    git(tmp_path, 'add', '.gitignore'); git(tmp_path, 'commit', '-m', 'Initial')
    base = git(tmp_path, 'rev-parse', 'HEAD')
    state = start(tmp_path, capsys, '--worktree')
    assert state['git']['base_commit'] == base
    assert state['git']['branch'] == 'tao/filter'
    worktree = tmp_path / '.worktrees/filter'
    assert worktree.is_dir()
    code, report = call(tmp_path, capsys, 'workflow', 'status')
    assert code == 0 and report['outputs']['workflows'][0]['change'] == state['change']
    assert not (tmp_path / '.tao/workflows').exists()


def test_plan_creation_reuses_reserved_identity_with_design_attachment(tmp_path, capsys):
    state = start(tmp_path, capsys)
    attachment = (tmp_path / state['plan_path']).with_suffix('')
    attachment.mkdir(parents=True)
    code, report = call(tmp_path, capsys, 'new', '--slug', 'filter', '--change', state['change'])
    assert code == 0, report
    assert report['outputs']['ids']['CHG_ID'] == state['change']
    assert report['outputs']['path'] == state['plan_path']
    code, _ = call(tmp_path, capsys, 'new', '--slug', 'filter', '--change', state['change'])
    assert code == 1  # Never overwrite even a partially filled plan.


def test_missing_stage_document_does_not_advance(tmp_path, capsys):
    state = start(tmp_path, capsys)
    code, report = call(tmp_path, capsys, 'workflow', 'advance', state['change'], '--expect', '1', '--decision', 'Continue')
    assert code == 1
    code, report = call(tmp_path, capsys, 'workflow', 'status', state['change'])
    assert report['outputs']['workflows'][0]['phase'] == 'spec'


def test_dirty_source_is_not_silently_left_out_of_worktree(tmp_path, capsys):
    git(tmp_path, 'init', '-b', 'main'); git(tmp_path, 'config', 'user.email', 'test@example.test'); git(tmp_path, 'config', 'user.name', 'Test')
    (tmp_path / '.gitignore').write_text('/.worktrees/\n', encoding='utf-8')
    git(tmp_path, 'add', '.gitignore'); git(tmp_path, 'commit', '-m', 'Initial')
    (tmp_path / '.gitignore').write_text('/.worktrees/\n/build/\n', encoding='utf-8')
    code, report = call(tmp_path, capsys, 'workflow', 'start', '--slug', 'filter', '--summary', 'Filter', '--locale', 'en', '--decision', 'Write', '--worktree')
    assert code == 1, report
    assert not (tmp_path / '.worktrees/filter').exists()


PLAN_RESULTS = '\n<!-- tao:results -->\n执行记录。\n<!-- /tao:results -->\n'


@pytest.mark.parametrize('mutation,rule', [
    (lambda t: t.replace('<!-- /tao:results -->\n', ''), 'TAO-DOC-003'),
    (lambda t: t.replace('<!-- tao:results -->\n', ''), 'TAO-DOC-003'),
    (lambda t: t.replace('<!-- tao:results -->', '<!-- tao:results -->\n<!-- tao:results -->'), 'TAO-DOC-003'),
    (lambda t: t.replace(PLAN_RESULTS, '').replace('<!-- tao:section verification -->', PLAN_RESULTS + '\n<!-- tao:section verification -->'), 'TAO-DOC-003'),
])
def test_unpaired_or_misplaced_results_markers_are_reported(tmp_path, mutation, rule):
    """The structure stays intact while these markers are wrong, so nothing
    else reports them and the plan contract silently changes instead."""
    from taolib.documents import validate
    from test_relationships import change
    body = change().replace('<!-- tao:section questions -->', PLAN_RESULTS + '\n<!-- tao:section questions -->')
    path = tmp_path / 'docs/plans/2026-09/20260914-export.md'
    path.parent.mkdir(parents=True)
    path.write_text(mutation(body), encoding='utf-8')
    result = validate(tmp_path, [path])
    assert rule in {d.rule_id for d in result.diagnostics}, result.to_dict()


def test_a_paired_results_block_is_accepted_and_excluded_from_the_contract(tmp_path):
    from taolib.documents import validate
    from taolib.workflows import plan_contract
    from test_relationships import change
    body = change().replace('<!-- tao:section questions -->', PLAN_RESULTS + '\n<!-- tao:section questions -->')
    path = tmp_path / 'docs/plans/2026-09/20260914-export.md'
    path.parent.mkdir(parents=True)
    path.write_text(body, encoding='utf-8')
    result = validate(tmp_path, [path])
    assert 'TAO-DOC-003' not in {d.rule_id for d in result.diagnostics}, result.to_dict()
    assert '执行记录。' not in plan_contract(body)
    assert plan_contract(body) == plan_contract(body.replace('执行记录。', '改写后的执行记录。'))


@pytest.mark.parametrize('corrupt', [False, True])
def test_parent_locates_worktree_when_local_state_is_missing_or_corrupt(tmp_path, capsys, corrupt):
    root = tmp_path / 'project with spaces'
    root.mkdir()
    git(root, 'init', '-b', 'main')
    git(root, 'config', 'user.email', 'test@example.test')
    git(root, 'config', 'user.name', 'Test')
    (root / '.gitignore').write_text('/.worktrees/\n')
    git(root, 'add', '.gitignore')
    git(root, 'commit', '-m', 'Fixture')
    state = start(root, capsys, '--worktree')
    host = root / '.worktrees/filter'
    path = host / '.tao/workflows' / (state['change'] + '.json')
    if corrupt:
        path.write_bytes(b'{invalid JSON')
    else:
        path.unlink()
    for args in [('status', state['change']), ('workflow', 'status', state['change'])]:
        code, report = call(root, capsys, *args)
        assert code == 0, report
        row = report['outputs']['workflows'][0]
        assert row['project'] == str(host)
        assert row['expected_path'] == str(path)
    code, report = call(root, capsys, 'workflow', 'advance', state['change'],
                        '--expect', '1', '--decision', 'Continue')
    assert code == 1
    assert str(path).replace('\\', '\\\\') in json.dumps(report)
    assert 'recover' in json.dumps(report)
    if corrupt:
        assert path.read_bytes() == b'{invalid JSON'
    else:
        assert not path.exists()



def test_live_worktree_wins_over_merged_document_copy_and_duplicates_need_selection(tmp_path, capsys, monkeypatch):
    import shutil
    root = tmp_path / 'repository'
    root.mkdir()
    git(root, 'init', '-b', 'main')
    git(root, 'config', 'user.email', 'test@example.test')
    git(root, 'config', 'user.name', 'Test')
    (root / '.gitignore').write_text('/.worktrees/\n')
    git(root, 'add', '.gitignore')
    git(root, 'commit', '-m', 'Fixture')
    state = start(root, capsys, '--worktree')
    host = root / '.worktrees/filter'
    shutil.copytree(host / 'docs', root / 'docs')
    code, report = call(root, capsys, 'status', state['change'])
    assert code == 0, report
    assert report['outputs']['workflows'][0]['project'] == str(host)
    code, report = call(root, capsys, 'workflow', 'recover', state['change'], '--apply')
    assert code == 1 and report['outputs']['workflow_state']['selection_required']
    assert not (root / '.tao/workflows').exists()
    local = root / '.tao/workflows' / (state['change'] + '.json')
    local.parent.mkdir(parents=True)
    local.write_bytes((host / '.tao/workflows' / local.name).read_bytes())
    code, report = call(root, capsys, 'workflow', 'status')
    assert code == 0
    rows = report['outputs']['workflows']
    assert len(rows) == 2 and all(row['selection_required'] for row in rows)
    assert all(not row['recovery_commands'] for row in rows)
    monkeypatch.chdir(root)
    code = main(['--format', 'json', 'workflow', 'status', state['change']])
    report = json.loads(capsys.readouterr().out)
    assert code == 1 and report['outputs']['workflow_state']['selection_required']
    code, report = call(host, capsys, 'workflow', 'status', state['change'])
    assert code == 0 and report['outputs']['workflows'][0]['project'] == str(host)



def test_status_missing_unknown_change_keeps_structured_recovery_guidance(tmp_path, capsys):
    identity = 'CHG_20260101_0000000000000000'
    code, report = call(tmp_path, capsys, 'status', identity)
    assert code == 1
    details = report['outputs']['workflow_state']
    assert details['expected_path'] == str(tmp_path / '.tao/workflows' / (identity + '.json'))
    assert details['recovery_commands'][0][-2:] == ['recover', identity]
    assert details['candidate_sources'] == []



def test_primary_status_reports_broken_formal_record_and_legacy_json_only(tmp_path, capsys):
    state = start(tmp_path, capsys)
    record = tmp_path / 'docs/workflows' / (state['change'] + '.md')
    local = tmp_path / '.tao/workflows' / (state['change'] + '.json')
    before = local.read_bytes()
    record.write_text('---\n<<<<<<< conflict\n---\n')
    code, report = call(tmp_path, capsys, 'status', state['change'])
    assert code == 1, report
    row = report['outputs']['workflows'][0]
    assert row['state'] == 'formal-record-invalid'
    assert row['expected_path'] == str(record)
    assert not row['recovery_commands']
    assert local.read_bytes() == before
    record.unlink()
    code, report = call(tmp_path, capsys, 'status', state['change'])
    assert code == 0, report
    assert report['outputs']['workflows'][0]['record_sync'] == 'legacy'
    assert report['outputs']['workflows'][0]['recovery_commands'][0][-2:] == ['migrate', state['change']]
