"""Published design reuse and task progress preserve the approved plan contract."""
from pathlib import Path
from taolib.documents import ASSETS, validate
from test_relationships import change, check_change, CHG
from test_workflows import start


def test_plan_can_reference_existing_shared_design_without_claiming_ownership(tmp_path):
    import re
    identity = 'DOC_20260914_0000000000000008'
    template = (ASSETS/'templates/design.md').read_text(encoding='utf-8')
    values = {'DOC_ID': identity, 'TITLE': 'Existing design', 'LOCALE': 'en', 'CREATED': '2026-09-14'}
    design = re.sub(r'\{\{([^}]+)\}\}', lambda m: values.get(m[1], 'Existing design contract.'), template)
    (tmp_path/'shared-design.md').write_text(design, encoding='utf-8')
    check_change(tmp_path, change().replace('change: '+CHG, 'change: '+CHG+'\ndesign_docs: ["'+identity+'"]'))
    result = validate(tmp_path, list(tmp_path.rglob('*.md')))
    assert result.valid, result.to_dict()


def test_task_progress_does_not_revoke_plan_but_task_contract_change_does(tmp_path, capsys):
    state = start(tmp_path, capsys)
    from taolib.workflows import mutate, advance, observe
    from test_document_links import design, DESIGN
    from test_documents import DOC
    from taolib.project import Project
    source = change().replace('change: '+CHG, 'change: '+state['change']+'\nspec_docs: ["'+DOC+'"]\ndesign_docs: ["'+DESIGN+'"]')
    check_change(tmp_path, source.replace(CHG, state['change']))
    (tmp_path/'docs/design.md').write_text(design(specs=[DOC]), encoding='utf-8')
    (tmp_path/'spec.md').rename(tmp_path/'docs/spec.md')
    plan = tmp_path/'docs/plans/2026-09/20260914-export.md'
    def prepare(owner, current):
        current.update(phase='plan', artifacts={'plan': [plan.relative_to(tmp_path).as_posix()], 'spec': ['docs/spec.md'], 'design': ['docs/design.md']})
    project = Project(tmp_path)
    state = mutate(project, state['change'], 1, prepare)
    state = advance(project, state['change'], state['revision'], 'Plan approved; skip optional docs review and implement', 'skipped')
    original = plan.read_text(encoding='utf-8')
    progressed = original.replace('- [x]', '- [ ]').replace('<!-- tao:section questions -->', '<!-- tao:results -->\nTests ran successfully.\n<!-- /tao:results -->\n\n<!-- tao:section questions -->')
    plan.write_text(progressed, encoding='utf-8')
    assert observe(project, state)['stale_approvals'] == []
    plan.write_text(progressed.replace('拒绝覆盖已有目标', '允许覆盖已有目标'), encoding='utf-8')
    assert observe(project, state)['stale_approvals'] == ['plan']


def test_fenced_contract_examples_remain_part_of_plan_approval(tmp_path):
    from taolib.project import Project
    from taolib.workflows import artifact_digest
    plan = tmp_path / 'plan.md'
    state = {'artifacts': {'plan': ['plan.md']}}
    contract = change().replace('<!-- tao:section tasks -->', '```yaml\nchecks:\n  - evidence: required\n```\n\n<!-- tao:section tasks -->')
    plan.write_text(contract, encoding='utf-8')
    before = artifact_digest(Project(tmp_path), state, 'plan')
    plan.write_text(contract.replace('evidence: required', 'evidence: optional'), encoding='utf-8')
    assert artifact_digest(Project(tmp_path), state, 'plan') != before
