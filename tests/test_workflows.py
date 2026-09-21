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
    assert not list((tmp_path / 'docs').rglob('*.md'))
    before = {str(p): p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}
    code, report = call(tmp_path, capsys, 'status', state['change'])
    assert code == 0, report
    assert report['outputs']['workflows'][0]['phase'] == 'spec'
    assert before == {str(p): p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}


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
    p = tmp_path / 'docs/spec.md'; p.parent.mkdir(); p.write_text(spec(), encoding='utf-8')
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
