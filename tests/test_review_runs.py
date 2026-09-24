"""Reviews bind cumulative changes and retain round limits across sessions."""
import json
from datetime import datetime, timedelta, timezone
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



def evidence_report(title, doc, evd):
    """A registrable report is a managed document, so fixtures write one."""
    return f"""---
schema: tao.project.evidence/v0.1
id: "{doc}"
title: "{title}"
locale: "en"
status: draft
created: "2026-09-14"
evidence: "{evd}"
recorded_at: "2026-09-14T00:00:00+00:00"
result: "passed"
coverage: "partial"
---

# {title}

<!-- tao:section scope -->
## Scope

Fixture report.

<!-- tao:section inputs -->
## Inputs

<!-- tao:field fingerprint -->
**Inputs:** Fixture tree.

<!-- tao:field environment -->
**Environment:** Fixture reviewer.

<!-- tao:section checks -->
## Checks

<!-- tao:field command -->
**Command:** None.

<!-- tao:field expected -->
**Expected:** None.

<!-- tao:field observed -->
**Observed:** None.

<!-- tao:field reports -->
**Reports:** This file.

<!-- tao:section findings -->
## Findings

<!-- tao:field limits -->
**Limits:** Fixture only.

<!-- tao:section retention -->
## Retention

<!-- tao:field retention -->
**Retention:** Discarded with the fixture.
"""


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
    with pytest.raises(ConflictError, match='round limit'):
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


def test_legacy_time_budget_does_not_block_a_remaining_round(tmp_path, capsys):
    state = repository(tmp_path, capsys)
    from taolib.review_runs import preview, begin, finish
    from taolib.workflows import mutate
    from taolib.project import Project
    project = Project(tmp_path)
    request = preview(project, state, 'project', 'code')
    state = begin(project, state['change'], 1, request, 'serial', 1, 'Review')
    def age_legacy_batch(owner, current):
        current['reviews']['code'].update(started_at='2000-01-01T00:00:00+00:00', budget_seconds=7200)
    state = mutate(project, state['change'], state['revision'], age_legacy_batch)
    (tmp_path / 'tmp/tao/report.md').write_text('Late review output', encoding='utf-8')
    state = finish(project, state['change'], state['revision'], {'outcome': 'changes-requested', 'reports': ['tmp/tao/report.md'], 'summary': 'Late result'})
    run = state['reviews']['code']['runs'][-1]
    assert run['outcome'] == 'changes-requested' and 'budget' not in run
    state = begin(Project(tmp_path), state['change'], state['revision'], request, 'serial', 1, 'New session')
    assert len(state['reviews']['code']['runs']) == 2
    assert state['reviews']['code']['budget_seconds'] == 7200
    state = finish(project, state['change'], state['revision'], {'outcome': 'failed', 'reports': [], 'summary': 'Interrupted'})
    state = begin(project, state['change'], state['revision'], request, 'serial', 1,
                  'Authorized another round', max_rounds=3)
    assert state['reviews']['code']['round_decisions'] == [
        {'before': 2, 'after': 3, 'decision': 'Authorized another round'}]


def test_discussion_across_days_does_not_consume_review_rounds(tmp_path, capsys, monkeypatch):
    from taolib import review_runs
    from taolib.project import Project
    state = repository(tmp_path, capsys)
    project = Project(tmp_path)
    started = datetime(2026, 9, 18, tzinfo=timezone.utc)
    now = started

    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return now.astimezone(tz)

    monkeypatch.setattr(review_runs, 'datetime', Clock)
    request = review_runs.preview(project, state, 'project', 'code')
    state = review_runs.begin(project, state['change'], state['revision'], request, 'serial', 1, 'Review')
    assert state['reviews']['code']['max_rounds'] == 2
    assert 'budget_seconds' not in state['reviews']['code']
    report = tmp_path / 'tmp/tao/report.md'
    report.write_text('A correction is required.', encoding='utf-8')
    now = started + timedelta(days=1)
    state = review_runs.finish(project, state['change'], state['revision'], {
        'outcome': 'changes-requested', 'reports': ['tmp/tao/report.md'], 'summary': 'Correct the default',
    })
    assert state['reviews']['code']['runs'][-1]['outcome'] == 'changes-requested'
    now = started + timedelta(days=3)
    state = review_runs.begin(Project(tmp_path), state['change'], state['revision'], request, 'serial', 1, 'Recheck after discussion')
    assert state['reviews']['code']['started_at'] == started.isoformat()
    now = started + timedelta(days=4)
    state = review_runs.finish(project, state['change'], state['revision'], {
        'outcome': 'passed', 'reports': ['tmp/tao/report.md'], 'summary': 'Late result',
    })
    run = state['reviews']['code']['runs'][-1]
    assert run['outcome'] == 'passed' and 'budget' not in run


@pytest.mark.parametrize('limit', [3, 4])
def test_resume_preserves_explicit_round_limit_and_new_batch_uses_default(tmp_path, capsys, limit):
    from taolib.review_runs import preview, begin, finish
    from taolib.project import Project
    state = repository(tmp_path, capsys)
    project = Project(tmp_path)
    request = preview(project, state, 'project', 'code')
    state = begin(project, state['change'], state['revision'], request, 'serial', 1, 'Explicit limit', max_rounds=limit)
    state = finish(project, state['change'], state['revision'], {'outcome': 'failed', 'reports': [], 'summary': 'Interrupted'})
    state = begin(Project(tmp_path), state['change'], state['revision'], request, 'serial', 1, 'Resume')
    assert state['reviews']['code']['max_rounds'] == limit
    assert state['reviews']['code']['round_decisions'] == []
    state = finish(project, state['change'], state['revision'], {'outcome': 'failed', 'reports': [], 'summary': 'Interrupted again'})
    state = begin(project, state['change'], state['revision'], request, 'serial', 1, 'User requests another batch', new_batch=True)
    assert state['review_history']['code'][-1]['max_rounds'] == limit
    assert state['reviews']['code']['max_rounds'] == 2


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
    run = state['reviews']['code']['runs'][-1]
    assert (run['outcome'], run['inputs']) == ('passed', 'stale')  # The verdict stands; its inputs do not.
    from taolib.review_runs import passed as gate
    assert not gate(project, state, 'code')


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


def test_explicit_new_batch_resets_round_limit_and_retains_previous_stage(tmp_path, capsys):
    state = repository(tmp_path, capsys)
    from taolib.review_runs import preview, begin, finish
    from taolib.workflows import mutate
    from taolib.project import Project, ConflictError
    project = Project(tmp_path)
    (tmp_path/'spec.md').write_text('# Spec\n', encoding='utf-8')
    request = preview(project, state, 'project', 'docs')
    state = begin(project, state['change'], 1, request, 'serial', 1, 'Review specification', max_rounds=1)
    state = mutate(project, state['change'], state['revision'], lambda owner, current: current['reviews']['docs'].update(started_at='2000-01-01T00:00:00+00:00'))
    state = finish(project, state['change'], state['revision'], {'outcome': 'failed', 'reports': [], 'summary': 'Old review ended'})
    old = state['reviews']['docs']
    (tmp_path/'design.md').write_text('# Design\n', encoding='utf-8')
    request = preview(project, state, 'project', 'docs')
    with pytest.raises(ConflictError, match='round limit'):
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


@pytest.mark.parametrize('scope', ['feature', 'project'])
def test_reserved_formal_reports_validate_without_staling_inputs(tmp_path, capsys, scope):
    from taolib.review_runs import preview, begin, finish, passed
    from taolib.project import Project
    from taolib.documents import validate
    from test_documents import spec
    from test_review_documents import review
    from test_relationships import navigation
    state = repository(tmp_path, capsys)
    project = Project(tmp_path)
    (tmp_path / 'docs').mkdir()
    (tmp_path / 'docs/spec.md').write_text(spec(), encoding='utf-8')
    directory = 'docs/engineering/reviews/20260918-contract'
    report = directory + '/01-contract-reviewer.md'
    index = directory + '/index.md'
    request = preview(project, state, scope, 'docs', outputs=[report, index])
    assert request['output_files'] == [report, index]
    assert report not in request['context_files']
    state = begin(project, state['change'], state['revision'], request, 'serial', 1, 'Review fixed inputs')
    (tmp_path / directory).mkdir(parents=True)
    (tmp_path / report).write_text(review().replace('../../spec.md', '../../../spec.md'), encoding='utf-8')
    (tmp_path / index).write_text(navigation('01-contract-reviewer.md'), encoding='utf-8')
    documents = validate(tmp_path, list((tmp_path / 'docs').rglob('*.md')))
    assert documents.valid and not documents.diagnostics, documents.to_dict()
    state = finish(project, state['change'], state['revision'], {
        'outcome': 'passed', 'reports': [report], 'summary': 'Reviewed the unchanged specification',
    })
    assert state['reviews']['docs']['runs'][-1]['outcome'] == 'passed'
    assert passed(Project(tmp_path), state, 'docs')
    # The next review includes this round's reports; there is no global exemption.
    assert report in preview(project, state, 'project', 'docs')['context_files']


@pytest.mark.parametrize('changed', ['code.py', 'docs/engineering/reviews/20260901-earlier/01-earlier.md', 'new.py'])
def test_reserved_outputs_do_not_hide_source_or_historical_report_changes(tmp_path, capsys, changed):
    from taolib.review_runs import preview, begin, finish
    from taolib.project import Project
    state = repository(tmp_path, capsys)
    project = Project(tmp_path)
    history = tmp_path / 'docs/engineering/reviews/20260901-earlier/01-earlier.md'
    history.parent.mkdir(parents=True)
    history.write_text(evidence_report('Earlier review', 'DOC_20260914_0000000000000101', 'EVD_20260914_0000000000000102'), encoding='utf-8')
    report = 'docs/engineering/reviews/20260914-current/01-current.md'
    (tmp_path / report).parent.mkdir(parents=True)
    request = preview(project, state, 'project', 'code', outputs=[report])
    state = begin(project, state['change'], state['revision'], request, 'serial', 1, 'Review')
    (tmp_path / report).write_text(evidence_report('New review', 'DOC_20260914_0000000000000103', 'EVD_20260914_0000000000000104'), encoding='utf-8')
    (tmp_path / changed).write_text('Changed input', encoding='utf-8')
    state = finish(project, state['change'], state['revision'], {'outcome': 'passed', 'reports': [report], 'summary': 'Old input'})
    run = state['reviews']['code']['runs'][-1]
    assert (run['outcome'], run['inputs']) == ('passed', 'stale')
    from taolib.review_runs import passed as gate
    assert not gate(project, state, 'code')


def test_review_outputs_must_be_new_exact_paths_and_stay_absent_until_begin(tmp_path, capsys):
    from taolib.review_runs import preview, begin
    from taolib.project import Project, ConfigurationError, ConflictError
    state = repository(tmp_path, capsys)
    project = Project(tmp_path)
    (tmp_path / 'old.md').write_text('Existing report', encoding='utf-8')
    git(tmp_path, 'add', 'old.md'); git(tmp_path, 'commit', '-m', 'Existing report')
    for name in ['old.md', '../escape.md', 'docs/**/*.md', '/absolute.md', 'code.py']:
        with pytest.raises((ConfigurationError, ConflictError)):
            preview(project, state, outputs=[name])
    git(tmp_path, 'rm', 'old.md')
    with pytest.raises(ConflictError):
        preview(project, state, outputs=['old.md'])
    request = preview(project, state, 'project', 'code', outputs=['new.md'])
    (tmp_path / 'new.md').write_text('Created after confirmation', encoding='utf-8')
    with pytest.raises(ConflictError):
        begin(project, state['change'], state['revision'], request, 'serial', 1, 'Review')


def test_review_output_option_is_bound_by_cli_preview(tmp_path, capsys):
    state = repository(tmp_path, capsys)
    code, report = call(tmp_path, capsys, 'workflow', 'review-preview', state['change'],
                        '--scope', 'project', '--output', 'docs/review.md', '--output', 'docs/index.md')
    assert code == 0, report
    assert report['outputs']['output_files'] == ['docs/index.md', 'docs/review.md']


def test_saved_preview_envelope_is_rejected_with_its_own_reason(tmp_path, capsys):
    """The agent saves a command result to a file; only its outputs object is the scope."""
    state = repository(tmp_path, capsys)
    (tmp_path / 'code.py').write_text('value = 1\n', encoding='utf-8', newline='\n')
    code, report = call(tmp_path, capsys, 'workflow', 'review-preview', state['change'], '--kind', 'code')
    assert code == 0, report
    scope = tmp_path / 'tmp/tao/scope.json'
    scope.parent.mkdir(parents=True, exist_ok=True)

    scope.write_text(json.dumps(report), encoding='utf-8')
    code, envelope = call(tmp_path, capsys, 'workflow', 'review-begin', state['change'], '--expect',
                          str(state['revision']), '--from', 'tmp/tao/scope.json', '--mode', 'serial',
                          '--reviewers', '1', '--decision', 'Envelope by mistake')
    assert code == 2 and envelope['status'] == 'not_run'
    assert 'outputs object' in envelope['diagnostics'][0]['message']

    scope.write_text(json.dumps({'kind': 'code'}), encoding='utf-8')
    code, bare = call(tmp_path, capsys, 'workflow', 'review-begin', state['change'], '--expect',
                      str(state['revision']), '--from', 'tmp/tao/scope.json', '--mode', 'serial',
                      '--reviewers', '1', '--decision', 'No identifier')
    assert code == 2 and 'missing its change identifier' in bare['diagnostics'][0]['message']

    scope.write_text(json.dumps(report['outputs']), encoding='utf-8')
    code, accepted = call(tmp_path, capsys, 'workflow', 'review-begin', state['change'], '--expect',
                          str(state['revision']), '--from', 'tmp/tao/scope.json', '--mode', 'serial',
                          '--reviewers', '1', '--decision', 'Round one')
    assert code == 0, accepted
    assert accepted['outputs']['reviews']['code']['runs'][-1]['outcome'] == 'running'


def test_old_budget_result_does_not_veto_a_review_that_passed(tmp_path, capsys):
    """A legacy budget marker does not override the actual review verdict."""
    from taolib import review_runs, workflows
    from taolib.project import Project
    state = repository(tmp_path, capsys)
    project = Project(tmp_path)
    request = review_runs.preview(project, state, 'project', 'code')
    state = review_runs.begin(project, state['change'], state['revision'], request, 'serial', 1, 'Review code')
    (tmp_path / 'tmp/tao/report.md').write_text('No findings.', encoding='utf-8')
    state = review_runs.finish(project, state['change'], state['revision'], {
        'outcome': 'passed', 'reports': ['tmp/tao/report.md'], 'summary': 'Clean',
    })
    state = workflows.mutate(project, state['change'], state['revision'],
                             lambda owner, current: current['reviews']['code']['runs'][-1].update(
                                 budget='exceeded'))
    run = state['reviews']['code']['runs'][-1]
    assert (run['outcome'], run['inputs'], run['budget']) == ('passed', 'current', 'exceeded')
    assert review_runs.passed(project, state, 'code')


def test_records_written_before_the_split_are_read_without_new_fields(tmp_path, capsys):
    """Old runs carry freshness inside outcome; the gate must read them as it used to."""
    from taolib import review_runs, workflows
    from taolib.project import Project
    state = repository(tmp_path, capsys)
    project = Project(tmp_path)
    request = review_runs.preview(project, state, 'project', 'code')
    state = review_runs.begin(project, state['change'], state['revision'], request, 'serial', 1, 'Review code')
    (tmp_path / 'tmp/tao/report.md').write_text('No findings.', encoding='utf-8')
    state = review_runs.finish(project, state['change'], state['revision'], {
        'outcome': 'passed', 'reports': ['tmp/tao/report.md'], 'summary': 'Clean',
    })

    def strip(owner, current):
        run = current['reviews']['code']['runs'][-1]
        run.pop('inputs', None)
        run.pop('budget', None)
    state = workflows.mutate(project, state['change'], state['revision'], strip)
    run = state['reviews']['code']['runs'][-1]
    assert 'inputs' not in run and 'budget' not in run
    assert review_runs.passed(project, state, 'code')

    # Short-circuiting stops before the default, so this only holds the older
    # outcome values to their meaning; the default branch is covered above.
    state = workflows.mutate(project, state['change'], state['revision'],
                             lambda owner, current: current['reviews']['code']['runs'][-1].update(outcome='stale'))
    assert not review_runs.passed(project, state, 'code')


def test_review_end_refuses_a_report_that_does_not_validate(tmp_path, capsys):
    """Registering pairs a conclusion with the material carrying it; an
    unreadable report leaves nothing to register, and a round that has ended
    cannot be registered again to correct its digest."""
    from taolib.review_runs import preview, begin, finish
    from taolib.project import Project, ConflictError
    state = repository(tmp_path, capsys)
    project = Project(tmp_path)
    (tmp_path / 'docs/engineering/reviews').mkdir(parents=True)
    report = 'docs/engineering/reviews/current.md'
    request = preview(project, state, 'project', 'code', outputs=[report])
    state = begin(project, state['change'], state['revision'], request, 'serial', 1, 'Review')
    (tmp_path / report).write_text('Not a managed document', encoding='utf-8')
    with pytest.raises(ConflictError):
        finish(project, state['change'], state['revision'], {'outcome': 'passed', 'reports': [report], 'summary': 'x'})
    assert state['reviews']['code']['runs'][-1]['outcome'] == 'running', 'the round stays open for a corrected report'
    (tmp_path / report).write_text(evidence_report('Fixed', 'DOC_20260914_0000000000000105', 'EVD_20260914_0000000000000106'), encoding='utf-8')
    state = finish(project, state['change'], state['revision'], {'outcome': 'passed', 'reports': [report], 'summary': 'x'})
    run = state['reviews']['code']['runs'][-1]
    assert run['outcome'] == 'passed'
    from taolib.verification import file_digest
    assert run['reports'][0]['digest'] == file_digest(tmp_path / report)


def test_a_rounds_own_records_do_not_reopen_the_finish_gate(tmp_path, capsys):
    """Every derived field must describe the same material: a size taken from
    the file while the digest comes from its contract reopens the hole."""
    from taolib.review_runs import preview, begin, repreview, passed, finish
    from taolib.project import Project
    state = repository(tmp_path, capsys)
    project = Project(tmp_path)
    plan = tmp_path / state['plan_path']
    plan.parent.mkdir(parents=True, exist_ok=True)
    from test_relationships import change
    plan.write_text(change(), encoding='utf-8')
    batch = 'docs/plans/2026-09/20260914-export/reviews/20260914-first'
    report = batch + '/01-first-claude.md'
    # The batch navigation page is in place before the round, as the scheduling
    # rules require; only the report is reserved.
    (tmp_path / batch).mkdir(parents=True)
    (tmp_path / batch / 'index.md').write_text('# batch\n', encoding='utf-8')
    request = preview(project, state, 'project', 'code', outputs=[report])
    state = begin(project, state['change'], state['revision'], request, 'serial', 1, 'Review')
    # Completing a round writes the report, the adjudication and the plan's
    # execution record; none of them may expire the round that produced them.
    (tmp_path / report).write_text(evidence_report('R', 'DOC_20260914_0000000000000201', 'EVD_20260914_0000000000000202'), encoding='utf-8')
    (tmp_path / batch / '00-adjudication.md').write_text('# adjudication\n', encoding='utf-8')
    plan.write_text(change().replace('<!-- tao:section questions -->',
                                     '<!-- tao:results -->\n实测记录。\n<!-- /tao:results -->\n\n<!-- tao:section questions -->'), encoding='utf-8')
    assert repreview(project, state, request, started=True) == request
    state = finish(project, state['change'], state['revision'], {'outcome': 'passed', 'reports': [report], 'summary': 'x'})
    assert state['reviews']['code']['runs'][-1]['inputs'] == 'current'
    assert passed(project, state, 'code'), 'the finish gate stays open after the round writes its own records'


def test_a_report_outside_the_document_globs_is_still_validated(tmp_path, capsys):
    """A report the project does not manage may use another format, but the
    record must say it was not validated rather than imply that it was."""
    from taolib.review_runs import preview, begin, finish
    from taolib.project import Project, ConflictError
    state = repository(tmp_path, capsys)
    (tmp_path / '.tao/config.toml').write_text(
        'version = 1\n[documents]\ninclude = ["docs/**/*.md"]\n', encoding='utf-8')
    project = Project(tmp_path)
    report = 'reviews/01-outside.md'
    (tmp_path / 'reviews').mkdir()
    request = preview(project, state, 'project', 'code', outputs=[report])
    state = begin(project, state['change'], state['revision'], request, 'serial', 1, 'Review')
    assert all(not str(s).endswith('01-outside.md') for s in project.sources()), 'the report is outside the globs'
    (tmp_path / report).write_text('Not a managed document\n', encoding='utf-8')
    state = finish(project, state['change'], state['revision'], {'outcome': 'passed', 'reports': [report], 'summary': 'x'})
    entry = state['reviews']['code']['runs'][-1]['reports'][0]
    assert entry['validated'] is False, 'an unchecked report must not read as a checked one'
