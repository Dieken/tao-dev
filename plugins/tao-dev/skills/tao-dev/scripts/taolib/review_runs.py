"""Review scope snapshots and persistent round budgets; agents conduct reviews."""
from datetime import datetime, timezone
import os
import subprocess
from pathlib import Path
import uuid
import zipfile

from tao_messages import Message

from . import git_workflow, workflows


def contract_text(path):
    return workflows.plan_contract(path.read_text(encoding='utf-8'))


def contract_digest(text):
    import hashlib
    return hashlib.sha256(text.encode()).hexdigest()
from .project import ConfigurationError, ConflictError, contained
from .verification import digest_json, file_digest
from .project_setup import EXCLUDED


def names(value):
    return set(filter(None, (value or '').split('\0')))


def own_records(outputs):
    """Directories holding the records of the batch these outputs belong to.

    Completing a round requires an adjudication and a batch navigation page
    besides the reserved report, and from the second round on both already
    exist, so neither can be reserved as a new output. Excluding the batch
    directory keeps those mandatory products from expiring the very round
    that produced them. Only this batch's directory is excluded: another
    batch's reports are history, and history changing does expire a result.
    """
    return sorted({name.rsplit('/', 1)[0] + '/' for name in outputs or []
                   if isinstance(name, str) and '/' in name})


def preview(project, state, scope='feature', kind=None, base=None, include=None, outputs=None, *, started=False):
    if scope not in ('feature', 'project'):
        raise ConfigurationError('Review scope must be feature or project.')
    kind = kind or ('docs' if state['phase'] in workflows.DOC_PHASES else 'code')
    if kind not in ('docs', 'code'):
        raise ConfigurationError('Review kind must be docs or code.')
    include = include or []
    for path in include:
        if not isinstance(path, str) or Path(path).is_absolute():
            raise ConfigurationError('Review filters must be project-relative paths.')
        contained(project.root, path)
    outputs = outputs or []
    if not isinstance(outputs, list) or any(not isinstance(p, str) for p in outputs) or len(outputs) != len(set(outputs)):
        raise ConfigurationError('Review outputs must be distinct project-relative Markdown files.')
    for name in outputs:
        path = Path(name)
        if (path.is_absolute() or path.as_posix() != name or '..' in path.parts
                or path.suffix != '.md' or any(c in name for c in '*?[]')):
            raise ConfigurationError('Review outputs must be exact project-relative Markdown paths.')
        target_path = contained(project.root, name)
        if target_path != project.root / name or (target_path.exists() and (not started or not target_path.is_file())):
            raise ConflictError(Message('Reserve a new review output file before starting: {arg0}', name))
    info = git_workflow.context(project.root)
    target = info['base_commit'] if info else None
    source = None
    index = {}
    if info:
        files = names(git_workflow.run(project.root, 'ls-files', '-z', '--cached', '--others', '--exclude-standard'))
        for entry in names(git_workflow.run(project.root, 'ls-files', '--stage', '-z')):
            fields, name = entry.split('\t', 1)
            mode, blob, stage = fields.split()
            if stage != '0':
                raise ConflictError('Resolve or explicitly inspect unmerged index entries before snapshot review.')
            index[name] = {'mode': mode, 'blob': blob}
        untracked = names(git_workflow.run(project.root, 'ls-files', '-z', '--others', '--exclude-standard'))
        if scope == 'feature':
            reference = base or (state.get('git') or {}).get('base_commit')
            if not reference or reference.startswith('-'):
                raise ConflictError('Choose and confirm a comparison base; no reliable recorded fork is available.')
            source = git_workflow.run(project.root, 'rev-parse', '--verify', reference+'^{commit}')
            if git_workflow.run(project.root, 'merge-base', '--is-ancestor', source, target, required=False) is None:
                raise ConflictError('The recorded base is no longer an ancestor. Confirm a new base after rebase or history replacement.')
            selected = names(git_workflow.run(project.root, 'diff', '--name-only', '-z', source, '--')) | untracked
            selected |= names(git_workflow.run(project.root, 'diff', '--cached', '--name-only', '-z', source, '--'))
            files |= selected  # Deleted paths remain visible in the review scope.
        else:
            selected = set(files)
        if outputs and not started:
            tracked_outputs = names(git_workflow.run(project.root, 'ls-tree', '-r', '--name-only', '-z', target, '--', *outputs))
            if tracked_outputs or (set(outputs) & files) - untracked:
                raise ConflictError('Tracked inputs cannot be reserved as review outputs.')
    else:
        if scope != 'project':
            raise ConfigurationError('Feature diff review requires Git; project review can use a file snapshot.')
        files = set()
        for directory, children, entries in os.walk(project.root, followlinks=False):
            children[:] = [c for c in children if c not in EXCLUDED and not (Path(directory)/c).is_symlink()]
            files.update((Path(directory)/name).relative_to(project.root).as_posix() for name in entries)
        selected = set(files)
    temporary = Path(project.paths['temporary']).parts
    def admitted(name):
        parts = Path(name).parts
        return (not set(parts) & (EXCLUDED - {'tmp', '.tao'}) and parts[:len(temporary)] != temporary
                and parts[:2] != ('.tao', 'workflows'))
    records = own_records(outputs)
    own = {name for name in files if any(name.startswith(d) for d in records)}
    # Name the rule, not the files it currently matches: a batch writes its own
    # records while the round is open, and an enumeration would grow with them.
    excluded = sorted({name for name in files if not admitted(name)} | set(outputs))
    files = {name for name in files if admitted(name)} - set(outputs) - own
    rows = []
    total = 0
    for name in sorted(files):
        path = contained(project.root, name)
        if path.is_symlink():
            raise ConfigurationError('Review symlinks explicitly before snapshotting: '+name)
        if path.is_dir():
            raise ConfigurationError('Review submodule contents in an explicit scope: '+name)
        exists = path.is_file()
        # Only POSIX carries permission bits; elsewhere record that the mode
        # is unknown rather than storing a value that restricts nothing.
        mode = path.stat().st_mode & 0o777 if exists and os.name == 'posix' else None
        # The plan carries this run's own execution record; hash the contract
        # it declares, not the results written while completing the round.
        contract = contract_text(path) if exists and name == state.get('plan_path') else None
        digest = contract_digest(contract) if contract is not None else (file_digest(path) if exists else None)
        rows.append([name, digest, mode, index.get(name)])
        if exists:
            # Every derived field must describe the same material. A size taken
            # from the file while the digest comes from its contract reopens the
            # hole the contract transform closed.
            total += len(contract.encode()) if contract is not None else path.stat().st_size
    selected &= files
    if kind == 'docs':
        selected = {name for name in selected if name.endswith('.md')}
    if include:
        selected = {name for name in selected if any(name == p or name.startswith(p.rstrip('/')+'/') for p in include)}
    result = {'schema': 'tao.review-scope/v0.1', 'change': state['change'], 'scope': scope, 'kind': kind,
            'base_commit': source, 'target_commit': target, 'include': include,
            'selected_files': sorted(selected), 'context_files': [r[0] for r in rows], 'excluded_files': excluded,
            'excluded_record_directories': records,
            'input_digest': digest_json(rows), 'input_bytes': total, 'index_entries': {name: index[name] for name in sorted(files & index.keys())},
            'instruction': 'Confirm this scope before starting. The snapshot includes unchanged context; inspect relevant callers and authoritative documents. No review has run.'}
    if outputs:
        result['output_files'] = sorted(outputs)
    return result


def repreview(project, state, request, *, started=False):
    return preview(project, state, request.get('scope'), request.get('kind'), request.get('base_commit'),
                   request.get('include'), request.get('output_files'), started=started)


def begin(project, identity, expected, request, mode, reviewers, decision, max_rounds=None, budget_seconds=None, new_batch=False):
    workflows.text(decision)
    if mode not in ('serial', 'parallel') or type(reviewers) is not int or not 1 <= reviewers <= 3 or (mode == 'serial' and reviewers != 1):
        raise ConfigurationError('Use one serial reviewer or up to three parallel reviewers.')
    if not isinstance(request, dict):
        raise ConfigurationError('Review scope must be a JSON object.')
    if 'change' not in request:
        envelope = request.get('outputs')
        if isinstance(envelope, dict) and 'change' in envelope:
            raise ConfigurationError('Review scope looks like a full command envelope; pass its outputs object.')
        raise ConfigurationError('Review scope is missing its change identifier.')
    if request['change'] != identity:
        raise ConfigurationError('Review scope belongs to another workflow.')
    def edit(owner, state):
        fresh = repreview(owner, state, request)
        if fresh != request:
            raise ConflictError('Review inputs changed after scope confirmation; inspect a fresh preview.')
        if not request['selected_files']:
            raise ConflictError('The selected review scope contains no files.')
        key = request['kind']
        now = datetime.now(timezone.utc)
        series = state['reviews'].get(key)
        if any(s['runs'] and s['runs'][-1]['outcome'] == 'running' for s in state['reviews'].values()):
            raise ConflictError('A review is still recorded as running; reconcile its result or failure first.')
        if series is not None and new_batch:
            state.setdefault('review_history', {}).setdefault(key, []).append(series)
        if series is None or new_batch:
            series = {'id': uuid.uuid4().hex, 'phase': state['phase'], 'decision': decision,
                      'started_at': now.isoformat(), 'max_rounds': max_rounds or 2,
                      'budget_seconds': budget_seconds or 7200, 'runs': [], 'budget_decisions': []}
        for field, value in (('max_rounds', max_rounds), ('budget_seconds', budget_seconds)):
            if value is not None:
                if type(value) is not int or value <= 0:
                    raise ConfigurationError('Review budgets must be positive integers.')
                if value != series[field]:
                    series['budget_decisions'].append({'field': field, 'before': series[field], 'after': value, 'decision': decision})
                    series[field] = value
        if len(series['runs']) >= series['max_rounds'] or (now-datetime.fromisoformat(series['started_at'])).total_seconds() >= series['budget_seconds']:
            raise ConflictError('Review budget exhausted; present unresolved issues and obtain an explicit new budget decision.')
        if series['runs'] and series['runs'][-1]['outcome'] == 'passed' and series['runs'][-1]['request'] == request:
            raise ConflictError('These inputs already passed; no additional round is needed.')
        run_id = uuid.uuid4().hex
        snapshot = owner.output('temporary', f'review-inputs/{run_id}.zip')
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(snapshot, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
            for name in request['context_files']:
                path = contained(owner.root, name)
                if path.is_file():
                    archive.write(path, name)
        index_snapshot = owner.output('temporary', f'review-inputs/{run_id}-index.zip')
        with zipfile.ZipFile(index_snapshot, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
            for name, entry in request['index_entries'].items():
                blob = subprocess.run(['git', '-C', str(owner.root), 'cat-file', 'blob', entry['blob']], capture_output=True, timeout=30)
                if blob.returncode:
                    raise ConfigurationError('Cannot preserve the staged Git blob for '+name)
                member = zipfile.ZipInfo(name)
                member.external_attr = int(entry['mode'], 8) << 16
                archive.writestr(member, blob.stdout)
        if repreview(owner, state, request) != request:
            raise ConflictError('Inputs changed while snapshotting; no review was started.')
        series['runs'].append({'id': run_id, 'round': len(series['runs'])+1, 'started_at': now.isoformat(),
                               'outcome': 'running', 'mode': mode, 'reviewers': reviewers, 'decision': decision,
                               'request': request, 'snapshot': snapshot.relative_to(owner.root).as_posix(),
                               'snapshot_digest': file_digest(snapshot), 'index_snapshot': index_snapshot.relative_to(owner.root).as_posix(),
                               'index_snapshot_digest': file_digest(index_snapshot)})
        state['reviews'][key] = series
    return workflows.mutate(project, identity, expected, edit)


def finish(project, identity, expected, result):
    if not isinstance(result, dict) or set(result) != {'outcome', 'reports', 'summary'} or result['outcome'] not in ('passed', 'changes-requested', 'failed'):
        raise ConfigurationError('Review completion requires outcome, reports and summary.')
    workflows.text(result['summary'])
    reports = result['reports']
    if not isinstance(reports, list) or any(not isinstance(p, str) for p in reports) or len(reports) != len(set(reports)):
        raise ConfigurationError('Review reports must be distinct project-relative files.')
    def edit(owner, state):
        active = [(key, series) for key, series in state['reviews'].items() if series['runs'] and series['runs'][-1]['outcome'] == 'running']
        if len(active) != 1:
            raise ConflictError('Select one active review round before recording its result.')
        kind, series = active[0]
        run = series['runs'][-1]
        if result['outcome'] != 'failed' and len(reports) != run['reviewers']:
            raise ConflictError('Each assigned reviewer must produce an actual report before completion.')
        saved = []
        for name in reports:
            path = contained(owner.root, name)
            if Path(name).is_absolute() or not path.is_file() or not path.stat().st_size:
                raise ConflictError('Review report is missing or empty.')
            saved.append({'path': name, 'digest': file_digest(path)})
        # What is recorded is a conclusion together with the material carrying
        # it, so an unreadable report leaves nothing to record. Validating here
        # also keeps the digest matching the file: a report fixed afterwards
        # cannot be registered again once the round has ended.
        if saved:
            from .documents import validate as validate_documents
            result_index = validate_documents(owner.root, owner.sources())
            faults = [d for d in result_index.diagnostics if d.severity == 'error' and d.path in set(reports)]
            if faults:
                raise ConflictError(Message('Review report does not validate: {arg0}:{arg1} {arg2}.',
                                            faults[0].path, faults[0].line, faults[0].rule_id))
        # The verdict, the freshness of its inputs and the schedule window are three
        # separate facts; recording them in one field loses whichever is written last.
        try:
            fresh = repreview(owner, state, run['request'], started=True) == run['request']
        except (OSError, ValueError) as exc:
            run['input_error'] = str(exc)
            fresh = False
        elapsed = (datetime.now(timezone.utc)-datetime.fromisoformat(series['started_at'])).total_seconds()
        run.update(outcome=result['outcome'], inputs='current' if fresh else 'stale',
                   budget='within' if elapsed < series['budget_seconds'] else 'exceeded',
                   reports=saved, summary=result['summary'], ended_at=datetime.now(timezone.utc).isoformat())
        run['evidence_boundary'] = 'Scheduling record only. Required independent attestations use tao review imports; report existence does not prove correctness or identity.'
    return workflows.mutate(project, identity, expected, edit)


def passed(project, state, kind):
    series = state['reviews'].get(kind)
    if not series or not series['runs']:
        return False
    run = series['runs'][-1]
    # Older records carry freshness inside outcome; newer ones state it separately.
    return (run['outcome'] == 'passed' and run.get('inputs', 'current') == 'current'
            and repreview(project, state, run['request'], started=True) == run['request'])
