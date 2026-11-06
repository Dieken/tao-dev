"""Required attestations survive their own bookkeeping, never domain edits."""
import pytest
from taolib import reviews, review_runs, workflow_records, workflow_recovery, workflows
from taolib.project import Project
from taolib.verification import policy, snapshot
from test_relationships import CHG
from test_reviews import attestation, setup_review, submit


def fixture(tmp_path):
    plan=setup_review(tmp_path)
    project=Project(tmp_path)
    state=workflow_recovery.recover(project, CHG, True)['candidate']
    # Synthetic review-stage test setup; never used as project review evidence.
    state=workflows.mutate(project, CHG, state['revision'],
                           lambda _, s: s.update(phase='implement', lifecycle='active', blockers=[]))
    request=review_runs.preview(project, state, scope='project', kind='code')
    state=review_runs.begin(project, CHG, state['revision'], request, 'serial', 1,
                            'Synthetic test review', new_batch=True, max_rounds=2)
    value=attestation(tmp_path)
    before=snapshot(project, policy(project))['source_digest']
    report=tmp_path/'tmp/tao/round.txt';report.write_text('Synthetic test conclusion')
    state=review_runs.finish(project, CHG, state['revision'],
                             {'outcome':'passed','reports':['tmp/tao/round.txt'],'summary':'Synthetic test pass'})
    return project,state,plan,value,before


def test_actual_receipt_can_be_imported_after_persistent_review_end(tmp_path):
    project,state,plan,value,before=fixture(tmp_path)
    assert snapshot(project, policy(project))['source_digest'] != before
    assert reviews.binding(project, policy(project), CHG) == value['binding']
    assert submit(tmp_path, value)[0] == 0
    state=workflows.advance(project, CHG, state['revision'], 'Enter review')
    state=workflows.advance(project, CHG, state['revision'], 'Enter finish')
    assert reviews.status(project, policy(project), CHG)[0]['state']=='satisfied'
    # Execution-only plan changes do not rewrite what the reviewer examined.
    plan.write_text(plan.read_text().replace('- [x]', '- [ ]').replace('<!-- tao:section questions -->',
                    '<!-- tao:results -->\nMeasured test result.\n<!-- /tao:results -->\n\n<!-- tao:section questions -->'))
    assert reviews.status(project, policy(project), CHG)[0]['state']=='satisfied'
    assert snapshot(project, policy(project))['source_digest'] != before


@pytest.mark.parametrize('mutation',['code','task-contract','approval','lifecycle','other-workflow'])
def test_domain_changes_still_expire_the_required_receipt(tmp_path, mutation):
    project,state,plan,value,before=fixture(tmp_path)
    assert submit(tmp_path, value)[0] == 0
    if mutation=='code':
        (tmp_path/'check.py').write_text('print("changed")')
    elif mutation=='task-contract':
        plan.write_text(plan.read_text().replace('verify:', 'verify: Additional behavior; ',1))
    elif mutation=='approval':
        workflows.mutate(project, CHG, state['revision'],
                         lambda _, s: s['approvals'].update(spec={'digest':'a'*64,'algorithm':'doc-v1','decision':'Changed'}))
    elif mutation=='lifecycle':
        workflows.mutate(project, CHG, state['revision'], lambda _, s: s.update(lifecycle='paused'))
    else:
        other=workflows.start(project, 'other', 'Other workflow', 'en', 'Synthetic setup')
        # Creating or changing another workflow remains a real input change.
        assert workflow_records.path(project,other['change']).exists()
    assert reviews.status(project, policy(project), CHG)[0]['state']=='stale'


def test_other_workflows_review_bookkeeping_is_not_our_own_output(tmp_path):
    project,state,plan,value,before=fixture(tmp_path)
    other=workflows.start(project, 'other', 'Other workflow', 'en', 'Synthetic setup')
    request=review_runs.preview(project, state, scope='project', kind='code')
    state=review_runs.begin(project, CHG, state['revision'], request, 'serial', 1, 'Review expanded fixture')
    value=attestation(tmp_path)
    state=review_runs.finish(project, CHG, state['revision'],
                             {'outcome':'passed','reports':['tmp/tao/round.txt'],'summary':'Synthetic test pass'})
    assert submit(tmp_path,value)[0]==0
    assert review_runs.passed(project,state,'code')
    other_request=review_runs.preview(project,other,scope='project',kind='code')
    review_runs.begin(project,other['change'],other['revision'],other_request,'serial',1,'Independent other workflow')
    assert not review_runs.passed(project,state,'code')
    assert reviews.status(project,policy(project),CHG)[0]['state']=='stale'


@pytest.mark.parametrize('content', [b'\xff', b'---\ninvalid: [\n---\n', b'---\nschema: tao.project.workflow/v0.1\nchange: '+CHG.encode()+b'\nphase: [invalid]\n---\n'])
def test_invalid_documents_remain_raw_inputs_instead_of_crashing(tmp_path, content):
    setup_review(tmp_path)
    path=tmp_path/'docs/broken.md';path.write_bytes(content)
    project=Project(tmp_path);config=policy(project)
    before=reviews.binding(project,config,CHG)
    path.write_bytes(content+b'\nChanged invalid input\n')
    assert reviews.binding(project,config,CHG) != before
