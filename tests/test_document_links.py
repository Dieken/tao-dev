"""Typed document relationships reject missing or mismatched targets."""
import json
import re
import pytest
from taolib.documents import ASSETS, validate
from test_documents import DOC
from test_relationships import CHANGE_DOC, CHG, change, check_change

DESIGN = 'DOC_20260914_0000000000000010'
SECOND = 'DOC_20260914_0000000000000011'


def design(identity=DESIGN, specs=None):
    text = (ASSETS/'templates/design.md').read_text(encoding='utf-8')
    values = {'DOC_ID': identity, 'TITLE': 'Export design', 'LOCALE': 'en'}
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
    (tmp_path/'first.md').write_text(design(specs=[DOC]), encoding='utf-8')
    (tmp_path/'second.md').write_text(design(SECOND, [DOC]), encoding='utf-8')
    result = validate(tmp_path, list(tmp_path.rglob('*.md')))
    assert result.valid, result.to_dict()
    assert {(r.source,r.target,r.relation) for r in result.references if r.relation=='design_docs'} == {(CHANGE_DOC,DESIGN,'design_docs'),(CHANGE_DOC,SECOND,'design_docs')}


@pytest.mark.parametrize('specs,designs', [([DESIGN],[DOC]), ([DOC,DOC],[DESIGN]), ([],[DESIGN]), ([DOC],['DOC_20260914_0000000000000099'])])
def test_invalid_type_duplicate_empty_and_missing_targets(tmp_path,specs,designs):
    check_change(tmp_path, linked_plan(specs,designs))
    (tmp_path/'design.md').write_text(design(specs=[DOC]), encoding='utf-8')
    assert not validate(tmp_path,list(tmp_path.rglob('*.md'))).valid


