"""Reviews bind cumulative changes and retain their finite budget across sessions."""
import json
import zipfile
import pytest
from test_workflows import call, start, git


def repository(root, capsys):
    git(root, 'init', '-b', 'main'); git(root, 'config', 'user.email', 'test@example.test'); git(root, 'config', 'user.name', 'Test')
    (root / '.gitignore').write_text('/tmp/tao/\n', encoding='utf-8')
    (root / 'code.py').write_text('value = 0\n', encoding='utf-8', newline='\n')
    git(root, 'add', '.'); git(root, 'commit', '-m', 'Initial')
    state = start(root, capsys)
    return state


def test_review_preview_covers_commits_dirty_and_untracked_without_writes(tmp_path, capsys):
    state = repository(tmp_path, capsys)
    for number in (1, 2):
        (tmp_path / f'feature{number}.py').write_text(f'value = {number}\n', encoding='utf-8')
        git(tmp_path, 'add', f'feature{number}.py'); git(tmp_path, 'commit', '-m', f'Part {number}')
    (tmp_path / 'code.py').write_text('value = 3\n', encoding='utf-8', newline='\n')
    (tmp_path / 'new_test.py').write_text('assert True\n', encoding='utf-8')
    before = {str(p): p.read_bytes() for p in tmp_path.rglob('*') if p.is_file() and '.git' not in p.parts}
    code, report = call(tmp_path, capsys, 'workflow', 'review-preview', state['change'], '--kind', 'code')
    assert code == 0, report
    preview = report['outputs']
    assert set(preview['selected_files']) == {'code.py', 'feature1.py', 'feature2.py', 'new_test.py'}
    assert preview['base_commit'] == state['git']['base_commit']
    assert preview['target_commit'] == git(tmp_path, 'rev-parse', 'HEAD')
    assert before == {str(p): p.read_bytes() for p in tmp_path.rglob('*') if p.is_file() and '.git' not in p.parts}


def test_rounds_require_fixed_inputs_and_do_not_reset_on_reload(tmp_path, capsys):
    state = repository(tmp_path, capsys)
    from taolib.review_runs import preview, begin, finish
    from taolib.project import Project, ConflictError
    project = Project(tmp_path)
    request = preview(project, state, 'project', 'code')
    state = begin(project, state['change'], 1, request, 'serial', 1, 'Review all code')
    run = state['reviews']['code']['runs'][-1]
    with zipfile.ZipFile(tmp_path / run['snapshot']) as archive:
        assert archive.read('code.py') == b'value = 0\n'
    with pytest.raises(ConflictError):
        begin(Project(tmp_path), state['change'], state['revision'], request, 'serial', 1, 'Retry while running')
    (tmp_path / 'tmp/tao/report.md').write_text('Review found an incorrect default.\n', encoding='utf-8')
    state = finish(project, state['change'], state['revision'], {'outcome': 'changes-requested', 'reports': ['tmp/tao/report.md'], 'summary': 'Fix the default'})
    (tmp_path / 'code.py').write_text('value = 1\n', encoding='utf-8')
    request = preview(project, state, 'project', 'code')
    state = begin(project, state['change'], state['revision'], request, 'parallel', 2, 'Targeted recheck')
    assert len(state['reviews']['code']['runs']) == 2
    state = finish(project, state['change'], state['revision'], {'outcome': 'failed', 'reports': [], 'summary': 'Reviewer unavailable'})
    (tmp_path / 'code.py').write_text('value = 2\n', encoding='utf-8')
    request = preview(Project(tmp_path), state, 'project', 'code')
    with pytest.raises(ConflictError, match='budget'):
        begin(Project(tmp_path), state['change'], state['revision'], request, 'serial', 1, 'Try again')


def test_changed_preview_and_unreviewed_success_are_rejected(tmp_path, capsys):
    state = repository(tmp_path, capsys)
    from taolib.review_runs import preview, begin, finish
    from taolib.project import Project, ConflictError
    project = Project(tmp_path)
    request = preview(project, state, 'project', 'code')
    (tmp_path / 'code.py').write_text('value = 9\n', encoding='utf-8')
    with pytest.raises(ConflictError):
        begin(project, state['change'], 1, request, 'serial', 1, 'Use old preview')
    state = begin(project, state['change'], 1, preview(project, state, 'project', 'code'), 'parallel', 2, 'Review')
    with pytest.raises(ConflictError):
        finish(project, state['change'], state['revision'], {'outcome': 'passed', 'reports': [], 'summary': 'Assume success'})


def test_elapsed_budget_is_preserved_when_a_session_resumes(tmp_path, capsys):
    state = repository(tmp_path, capsys)
    from taolib.review_runs import preview, begin, finish
    from taolib.workflows import mutate
    from taolib.project import Project, ConflictError
    project = Project(tmp_path)
    state = begin(project, state['change'], 1, preview(project, state, 'project', 'code'), 'serial', 1, 'Review')
    state = mutate(project, state['change'], state['revision'], lambda owner, current: current['reviews']['code'].update(started_at='2000-01-01T00:00:00+00:00'))
    (tmp_path / 'tmp/tao/report.md').write_text('Late review output', encoding='utf-8')
    state = finish(project, state['change'], state['revision'], {'outcome': 'passed', 'reports': ['tmp/tao/report.md'], 'summary': 'Late result'})
    assert state['reviews']['code']['runs'][-1]['outcome'] == 'budget-exceeded'
    with pytest.raises(ConflictError, match='budget'):
        begin(Project(tmp_path), state['change'], state['revision'], preview(project, state, 'project', 'code'), 'serial', 1, 'New session')


def test_index_is_in_scope_snapshot_and_freshness_even_when_worktree_reverted(tmp_path, capsys):
    state = repository(tmp_path, capsys)
    from taolib.review_runs import preview, begin, finish
    from taolib.project import Project
    project = Project(tmp_path)
    (tmp_path/'code.py').write_text('value = 999\n', encoding='utf-8'); git(tmp_path, 'add', 'code.py')
    (tmp_path/'code.py').write_text('value = 0\n', encoding='utf-8')
    request = preview(project, state, 'feature', 'code')
    assert 'code.py' in request['selected_files']
    state = begin(project, state['change'], 1, request, 'serial', 1, 'Review both index and working tree')
    run = state['reviews']['code']['runs'][-1]
    with zipfile.ZipFile(tmp_path/run['index_snapshot']) as archive:
        assert archive.read('code.py') == b'value = 999\n'
    git(tmp_path, 'add', 'code.py')  # Only index content changes now.
    (tmp_path/'tmp/tao/report.md').write_text('Initial staged version was reviewed.', encoding='utf-8')
    state = finish(project, state['change'], state['revision'], {'outcome': 'passed', 'reports': ['tmp/tao/report.md'], 'summary': 'Reviewed initial input'})
    assert state['reviews']['code']['runs'][-1]['outcome'] == 'stale'


def test_failed_review_can_close_after_history_invalidates_comparison(tmp_path, capsys):
    state = repository(tmp_path, capsys)
    from taolib.review_runs import preview, begin, finish
    from taolib.project import Project
    project = Project(tmp_path)
    (tmp_path/'code.py').write_text('value = 1\n', encoding='utf-8')
    state = begin(project, state['change'], 1, preview(project, state, 'feature', 'code'), 'serial', 1, 'Review feature')
    git(tmp_path, 'checkout', '--orphan', 'replacement')
    git(tmp_path, 'add', 'code.py'); git(tmp_path, 'commit', '-m', 'Replacement history')
    state = finish(project, state['change'], state['revision'], {'outcome': 'failed', 'reports': [], 'summary': 'History changed; reviewer interrupted'})
    assert state['reviews']['code']['runs'][-1]['outcome'] == 'failed'
    assert 'ancestor' in state['reviews']['code']['runs'][-1]['input_error']


def test_explicit_new_batch_resets_budget_and_retains_previous_stage(tmp_path, capsys):
    state = repository(tmp_path, capsys)
    from taolib.review_runs import preview, begin, finish
    from taolib.workflows import mutate
    from taolib.project import Project, ConflictError
    project = Project(tmp_path)
    (tmp_path/'spec.md').write_text('# Spec\n', encoding='utf-8')
    request = preview(project, state, 'project', 'docs')
    state = begin(project, state['change'], 1, request, 'serial', 1, 'Review specification')
    state = mutate(project, state['change'], state['revision'], lambda owner, current: current['reviews']['docs'].update(started_at='2000-01-01T00:00:00+00:00'))
    state = finish(project, state['change'], state['revision'], {'outcome': 'failed', 'reports': [], 'summary': 'Old review ended'})
    old = state['reviews']['docs']
    (tmp_path/'design.md').write_text('# Design\n', encoding='utf-8')
    request = preview(project, state, 'project', 'docs')
    with pytest.raises(ConflictError, match='budget'):
        begin(project, state['change'], state['revision'], request, 'serial', 1, 'Continue prior review')
    state = begin(project, state['change'], state['revision'], request, 'serial', 1,
                  'User requests a new design review', new_batch=True)
    assert state['reviews']['docs']['runs'][0]['round'] == 1
    assert state['reviews']['docs']['started_at'] != old['started_at']
    assert state['review_history']['docs'] == [old]
    assert state['reviews']['docs']['decision'] == 'User requests a new design review'
    with pytest.raises(ConflictError, match='running'):
        begin(project, state['change'], state['revision'], request, 'serial', 1,
              'Do not hide running review', new_batch=True)


def test_new_batch_flag_reaches_workflow_command(tmp_path, capsys):
    state = repository(tmp_path, capsys)
    from taolib.review_runs import preview
    from taolib.project import Project
    request = preview(Project(tmp_path), state, 'project', 'code')
    (tmp_path/'tmp/tao').mkdir(parents=True, exist_ok=True)
    path = tmp_path/'tmp/tao/preview.json'; path.write_text(json.dumps(request), encoding='utf-8')
    code, result = call(tmp_path, capsys, 'workflow', 'review-begin', state['change'],
                        '--expect', str(state['revision']), '--from', str(path),
                        '--mode', 'serial', '--reviewers', '1', '--decision', 'New requested review', '--new-batch')
    assert code == 0, result
