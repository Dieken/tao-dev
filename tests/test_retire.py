"""Retirement previews, graph preservation and interrupted-write recovery."""

from datetime import date
import json

from taolib.documents import validate
from test_cli import run
from test_documents import DOC, REQ, UC, spec
from test_relationships import change, CHG, TASK, TASK_TWO, CHANGE_DOC


OTHER_REQ = 'REQ_20260914_0000000000000010'


def setup_project(root):
    (root / 'docs').mkdir()
    source = spec()
    start = source.index('```{req}')
    end = source.index('\n```', start) + 4
    block = source[start:end]
    source = source[:end] + '\n\n' + block.replace(REQ, OTHER_REQ) + source[end:]
    path = root / 'docs/spec.md'
    path.write_text(source)
    return path


def retire(root, identity, *args):
    completed = run(root, 'retire', identity, '--reason', 'Replaced by the maintained requirement.', *args)
    return completed.returncode, json.loads(completed.stdout)


def test_preview_is_read_only_and_apply_preserves_formal_references(tmp_path):
    path = setup_project(tmp_path)
    before = path.read_bytes()
    code, preview = retire(tmp_path, REQ, '--replaced-by', OTHER_REQ)
    assert code == 0, preview
    assert preview['status'] == 'planned'
    assert preview['outputs']['retired_ids'] == [REQ]
    assert path.read_bytes() == before
    assert not (tmp_path / 'tmp').exists()
    assert not (tmp_path / 'docs/retired').exists()
    code, applied = retire(tmp_path, REQ, '--replaced-by', OTHER_REQ, '--apply')
    assert code == 0, applied
    assert f':id: {REQ}' not in path.read_text()
    assert f':id: {OTHER_REQ}' in path.read_text()
    ledger = tmp_path / 'docs/retired' / (date.today().strftime('%Y%m%d') + '.jsonl')
    row = json.loads(ledger.read_text())
    assert row == {'id': REQ, 'retired_on': date.today().isoformat(), 'reason': 'Replaced by the maintained requirement.', 'replaced_by': [OTHER_REQ]}
    result = validate(tmp_path, [path])
    assert result.valid, result.diagnostics
    assert result.definitions[REQ].status == 'retired'
    assert retire(tmp_path, REQ, '--replaced-by', OTHER_REQ, '--apply')[0] == 0
    assert len(ledger.read_text().splitlines()) == 1


def test_invalid_replacement_or_remaining_document_does_not_write(tmp_path):
    path = setup_project(tmp_path)
    before = path.read_bytes()
    code, result = retire(tmp_path, REQ, '--replaced-by', DOC, '--apply')
    assert code != 0, result
    assert path.read_bytes() == before
    assert not (tmp_path / 'docs/retired').exists()
    path.write_text(spec())
    before = path.read_bytes()
    code, result = retire(tmp_path, REQ, '--apply')
    assert code != 0, result
    assert path.read_bytes() == before
    assert not (tmp_path / 'docs/retired').exists()


def test_document_retirement_includes_owned_ids_and_rejects_broken_file_links(tmp_path):
    path = setup_project(tmp_path)
    another = tmp_path / 'docs/another.md'
    another.write_text(spec().replace(DOC, 'DOC_20260914_0000000000000020').replace(REQ, 'REQ_20260914_0000000000000021').replace(UC, 'UC_20260914_0000000000000022') + '\n[old document](spec.md)\n')
    code, result = retire(tmp_path, DOC, '--apply')
    assert code != 0, result
    assert path.exists()
    another.write_text(another.read_text().replace('[old document](spec.md)', 'No file dependency.'))
    code, preview = retire(tmp_path, DOC)
    assert code == 0, preview
    assert {DOC, REQ, OTHER_REQ} <= set(preview['outputs']['retired_ids'])
    assert retire(tmp_path, DOC, '--apply')[0] == 0
    assert not path.exists()
    result = validate(tmp_path, [another])
    assert result.valid, result.diagnostics
    assert result.definitions[DOC].status == 'retired'


def test_task_removal_preserves_neighbor_and_document_contract(tmp_path):
    setup_project(tmp_path)
    folder = tmp_path / 'docs/plans/2026-09'
    folder.mkdir(parents=True)
    source = change()
    start = source.index('- [x]')
    end = source.index('<!-- tao:section verification -->')
    source = source[:end] + source[start:end].replace(TASK, TASK_TWO) + source[end:]
    path = folder / '20260914-export.md'
    path.write_text(source)
    code, result = retire(tmp_path, TASK, '--apply')
    assert code == 0, result
    assert f'`{TASK}`' not in path.read_text()
    assert f'`{TASK_TWO}`' in path.read_text()
    assert validate(tmp_path, list((tmp_path / 'docs').rglob('*.md'))).valid
    code, preview = retire(tmp_path, CHG)
    assert code == 0, preview
    assert {CHANGE_DOC, CHG, TASK_TWO} <= set(preview['outputs']['retired_ids'])


def test_existing_record_cannot_be_silently_rewritten(tmp_path):
    setup_project(tmp_path)
    assert retire(tmp_path, REQ, '--replaced-by', OTHER_REQ, '--apply')[0] == 0
    before = next((tmp_path / 'docs/retired').glob('*.jsonl')).read_bytes()
    assert retire(tmp_path, REQ, '--apply')[0] != 0
    assert next((tmp_path / 'docs/retired').glob('*.jsonl')).read_bytes() == before


def test_interrupted_source_update_keeps_id_and_can_resume(tmp_path, monkeypatch):
    from taolib import retirement
    from taolib.project import Project
    path = setup_project(tmp_path)
    project = Project(tmp_path)
    original = retirement.replace_file
    def interrupted(root, destination, text, expected):
        if destination == path:
            raise OSError('Simulated interruption after the retirement record was saved.')
        return original(root, destination, text, expected)
    monkeypatch.setattr(retirement, 'replace_file', interrupted)
    try:
        retirement.retire(project, REQ, 'Replaced by the maintained requirement.', [OTHER_REQ], apply=True)
    except OSError:
        pass
    else:
        raise AssertionError('Expected the simulated interruption')
    assert f':id: {REQ}' in path.read_text()
    assert REQ in next((tmp_path / 'docs/retired').glob('*.jsonl')).read_text()
    assert not validate(tmp_path, [path]).valid
    monkeypatch.setattr(retirement, 'replace_file', original)
    code, result = retire(tmp_path, REQ, '--replaced-by', OTHER_REQ, '--apply')
    assert code == 0, result
    assert validate(tmp_path, [path]).valid


def test_malformed_existing_record_returns_diagnostics_without_removing_source(tmp_path):
    path = setup_project(tmp_path)
    before = path.read_bytes()
    ledger = tmp_path / 'docs/retired' / (date.today().strftime('%Y%m%d') + '.jsonl')
    ledger.parent.mkdir(parents=True)
    ledger.write_text(json.dumps({'id': REQ}) + '\n')
    code, result = retire(tmp_path, REQ, '--apply')
    assert code == 2, result
    assert result['diagnostics']
    assert path.read_bytes() == before


def test_append_keeps_preexisting_records_intact(tmp_path):
    setup_project(tmp_path)
    ledger = tmp_path / 'docs/retired' / (date.today().strftime('%Y%m%d') + '.jsonl')
    ledger.parent.mkdir(parents=True)
    row = {'id': 'REQ_20260913_0000000000000030', 'retired_on': date.today().isoformat(), 'reason': 'Earlier retirement.', 'replaced_by': []}
    original = json.dumps(row) + '\n'
    ledger.write_text(original)
    code, result = retire(tmp_path, REQ, '--replaced-by', OTHER_REQ, '--apply')
    assert code == 0, result
    assert ledger.read_text().startswith(original)
    assert len(ledger.read_text().splitlines()) == 2
