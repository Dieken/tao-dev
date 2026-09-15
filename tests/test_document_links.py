"""Typed document relationships and phase completeness are distinct checks."""
import json
import re
import pytest
from taolib.documents import ASSETS, validate
from test_documents import DOC, spec
from test_relationships import CHANGE_DOC, CHG, change, check_change

DESIGN = 'DOC_20260914_0000000000000010'
SECOND = 'DOC_20260914_0000000000000011'


def design(identity=DESIGN, specs=None):
    text = (ASSETS/'templates/design.md').read_text()
    values = {'DOC_ID': identity, 'TITLE': 'Export design', 'LOCALE': 'en', 'CREATED': '2026-09-14'}
    text = re.sub(r'\{\{([^}]+)\}\}', lambda m: values.get(m[1], 'Existing export contract.'), text)
    if specs is not None:
        text = text.replace('status: draft', 'status: draft\nspec_docs: '+json.dumps(specs))
    return text


def linked_plan(specs=None, designs=None):
    fields = ''
    if specs is not None: fields += '\nspec_docs: '+json.dumps(specs)
    if designs is not None: fields += '\ndesign_docs: '+json.dumps(designs)
    return change().replace('change: '+CHG, 'change: '+CHG+fields)


def test_multiple_shared_designs_and_typed_reference_sources(tmp_path):
    check_change(tmp_path, linked_plan([DOC], [DESIGN, SECOND]))
    (tmp_path/'first.md').write_text(design(specs=[DOC]))
    (tmp_path/'second.md').write_text(design(SECOND, [DOC]))
    result = validate(tmp_path, list(tmp_path.rglob('*.md')))
    assert result.valid, result.to_dict()
    assert {(r.source,r.target,r.relation) for r in result.references if r.relation=='design_docs'} == {(CHANGE_DOC,DESIGN,'design_docs'),(CHANGE_DOC,SECOND,'design_docs')}


@pytest.mark.parametrize('specs,designs', [([DESIGN],[DOC]), ([DOC,DOC],[DESIGN]), ([],[DESIGN]), ([DOC],['DOC_20260914_0000000000000099'])])
def test_invalid_type_duplicate_empty_and_missing_targets(tmp_path,specs,designs):
    check_change(tmp_path, linked_plan(specs,designs))
    (tmp_path/'design.md').write_text(design(specs=[DOC]))
    assert not validate(tmp_path,list(tmp_path.rglob('*.md'))).valid


def test_draft_can_be_incomplete_but_design_approval_cannot(tmp_path,capsys):
    from test_workflows import start
    from taolib.project import Project, ConflictError
    from taolib.workflows import checkpoint, advance
    state=start(tmp_path,capsys); project=Project(tmp_path)
    (tmp_path/'docs').mkdir();(tmp_path/'docs/spec.md').write_text(spec())
    state=checkpoint(project,state['change'],state['revision'],{'artifacts':{'spec':['docs/spec.md']}})
    state=advance(project,state['change'],state['revision'],'Approve spec and write design')
    (tmp_path/'docs/design.md').write_text(design())
    state=checkpoint(project,state['change'],state['revision'],{'artifacts':{'design':['docs/design.md']}})
    assert validate(tmp_path,list(tmp_path.rglob('*.md'))).valid
    with pytest.raises(ConflictError,match='spec_docs'):
        advance(project,state['change'],state['revision'],'Approve incomplete design')
    (tmp_path/'docs/design.md').write_text(design(specs=[DOC]))
    state=advance(project,state['change'],state['revision'],'Approve linked design')
    assert state['phase']=='plan'


def test_split_task_contract_is_bound_to_plan_approval(tmp_path):
    from taolib.project import Project
    from taolib.workflows import artifact_digest
    task_doc='DOC_20260914_0000000000000020'
    plan=linked_plan([DOC],[DESIGN])
    block=re.search(r'<!-- tao:section tasks -->(.*?)<!-- tao:section verification -->',plan,re.S)[1]
    tasks=f'''---
schema: tao.project.tasks/v0.1
id: {task_doc}
title: Tasks
locale: en
status: draft
created: "2026-09-14"
change: {CHG}
---
# Tasks
<!-- tao:section scope -->
## Scope
Export.
<!-- tao:section tasks -->
{block}
'''.replace(f'#{CHANGE_DOC}--verification',f'docs/plans/2026-09/20260914-export.md#{CHANGE_DOC}--verification')
    plan=plan.replace(block,'\n## Tasks\n\nExternal tasks.\n\n').replace('change: '+CHG,'change: '+CHG+'\ntasks_doc: '+task_doc)
    check_change(tmp_path,plan);(tmp_path/'design.md').write_text(design(specs=[DOC]));(tmp_path/'tasks.md').write_text(tasks)
    project=Project(tmp_path)
    # Include these explicit fixture sources in the test project.
    (tmp_path/'.tao').mkdir(exist_ok=True);(tmp_path/'.tao/config.toml').write_text('version=1\n[documents]\ninclude=["**/*.md"]\n')
    project=Project(tmp_path)
    state={'artifacts':{'plan':['docs/plans/2026-09/20260914-export.md']}}
    before=artifact_digest(project,state,'plan')
    (tmp_path/'tasks.md').write_text(tasks.replace('拒绝覆盖已有目标','删除已有目标'))
    assert artifact_digest(project,state,'plan') != before
