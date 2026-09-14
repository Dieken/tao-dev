"""Preview validated retirement; save IDs before removing their source text."""

from dataclasses import asdict
from datetime import date
import json
from pathlib import Path
import re

from .documents import parser, validate
from .project import ConfigurationError, ConflictError, contained, create_file, mutation_lock, replace_file
from .relationships import unique_object
from .verification import file_digest


def source_state(project):
    paths = set(project.sources()) | set(project.output('retired').glob('*.jsonl'))
    return {p.relative_to(project.root).as_posix(): file_digest(contained(project.root, p)) for p in paths}


def remove_block(source, identity):
    lines = source.splitlines(keepends=True)
    end = next(i for i in range(1, len(lines)) if lines[i].strip() == '---')
    offset = end + 1
    for token in parser().parse(''.join(lines[offset:])):
        if token.map is None:
            continue
        start, finish = [line + offset for line in token.map]
        formal = (token.type == 'fence' and token.level == 0
                  and re.fullmatch(r'\{(?:req|uc|adr)\}\s+.+', token.info.strip())
                  and re.search(r'^:id:\s*' + re.escape(identity) + r'\s*$', token.content, re.MULTILINE))
        task = token.type == 'list_item_open' and token.level == 1 and re.match(
            r'- \[[ x]\] `' + re.escape(identity) + r'` ', lines[start])
        if formal or task:
            return ''.join(lines[:start] + lines[finish:])
    raise ConfigurationError('Cannot locate the complete formal block; inspect its source before retirement.')


def prepare(project, identity, reason, replacements):
    if not reason.strip():
        raise ConfigurationError('Retirement requires a nonempty reason.')
    result = validate(project.root, project.sources(), book_root=project.book_root,
                      retirement_directory=project.paths['retired'], section_redirects=project.section_redirects)
    target = result.definitions.get(identity)
    if target is None:
        raise ConfigurationError('Retirement requires an existing source or retirement definition.')
    records = {}
    for ledger in project.output('retired').glob('*.jsonl'):
        contained(project.root, ledger)
        for line in ledger.read_text(encoding='utf-8').splitlines():
            row = json.loads(line, object_pairs_hook=unique_object)
            if (not isinstance(row, dict) or set(row) != {'id', 'retired_on', 'reason', 'replaced_by'}
                    or not isinstance(row.get('id'), str)):
                raise ConfigurationError('Repair malformed retirement records before writing.')
            if row['id'] in records:
                raise ConfigurationError('Repair duplicate retirement records before writing.')
            records[row['id']] = (ledger, row)
    if Path(target.path).suffix == '.jsonl':
        saved = records[identity][1]
        if saved['reason'] != reason or saved['replaced_by'] != replacements:
            raise ConflictError('An existing retirement record cannot be silently rewritten.')
        if not result.valid:
            raise ConfigurationError('Repair existing source diagnostics before confirming retirement.')
        return {'retired_ids': [identity], 'already_retired': True}, [], result
    path = contained(project.root, target.path)
    if target.path not in result.documents:
        raise ConfigurationError('The retirement source is not a managed document.')
    original = path.read_bytes()
    source = original.decode('utf-8')
    whole_document = target.kind in ('DOC', 'CHG', 'EVD')
    identities = sorted(d.id for d in result.definitions.values() if d.path == target.path) if whole_document else [identity]
    updated = None if whole_document else remove_block(source, identity)
    old = [records[item] for item in identities if item in records]
    ledger = old[0][0] if old else project.output('retired', date.today().strftime('%Y%m%d') + '.jsonl')
    retired_on = old[0][1]['retired_on'] if old else date.today().isoformat()
    original_ledger = ledger.read_bytes() if ledger.exists() else None
    additions = []
    for item in identities:
        row = {'id': item, 'retired_on': retired_on, 'reason': reason,
               'replaced_by': replacements if item == identity else []}
        if item in records:
            if records[item] != (ledger, row):
                raise ConflictError('Existing retirement intent differs; inspect the interrupted operation.')
        else:
            additions.append(json.dumps(row, ensure_ascii=False))
    ledger_text = (original_ledger or b'').decode('utf-8')
    if additions:
        ledger_text = ledger_text.rstrip('\n') + ('\n' if ledger_text else '') + '\n'.join(additions) + '\n'
    overrides = {target.path: updated, ledger.relative_to(project.root).as_posix(): ledger_text}
    proposed = validate(project.root, project.sources(), book_root=project.book_root,
                        retirement_directory=project.paths['retired'], overrides=overrides, section_redirects=project.section_redirects)
    output = {'retired_ids': identities, 'source': target.path, 'remove_document': whole_document,
              'record': ledger.relative_to(project.root).as_posix(), 'already_retired': False,
              'references': [asdict(ref) for ref in result.references if ref.target in identities and ref.path != target.path]}
    return output, [(ledger, ledger_text, original_ledger), (path, updated, original)], proposed


def retire(project, identity, reason, replacements, *, apply=False):
    def operation():
        before = source_state(project)
        output, changes, proposed = prepare(project, identity, reason, replacements)
        report = {'outputs': output, 'diagnostics': [asdict(d) for d in proposed.diagnostics],
                  'status': 'failed' if not proposed.valid else 'passed' if apply else 'planned'}
        if not proposed.valid or not apply:
            return report, 1 if not proposed.valid else 0
        if source_state(project) != before:
            raise ConflictError('Managed inputs changed during retirement preparation; preview again.')
        # The ledger is durable first. An interrupted second write leaves a
        # detectable duplicate definition, never an unrecorded deleted ID.
        for path, content, expected in changes:
            if content is None:
                if path.read_bytes() != expected:
                    raise ConflictError('Source changed before removal; inspect the saved retirement record.')
                path.unlink()
            elif expected is None:
                create_file(project.root, path, content)
            elif path.read_bytes() != content.encode('utf-8'):
                replace_file(project.root, path, content, expected)
        return report, 0
    if not apply:
        return operation()
    with mutation_lock(project):
        return operation()
