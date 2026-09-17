"""Review scope snapshots and persistent round budgets; agents conduct reviews."""
from datetime import datetime, timezone
import os
import subprocess
from pathlib import Path
import uuid
import zipfile

from . import git_workflow, workflows
from .project import ConfigurationError, ConflictError, contained
from .verification import digest_json, file_digest
from .project_setup import EXCLUDED


def names(value):
    return set(filter(None, (value or '').split('\0')))


def preview(project, state, scope='feature', kind=None, base=None, include=None):
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
    excluded = sorted(name for name in files if not admitted(name))
    files = {name for name in files if admitted(name)}
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
        rows.append([name, file_digest(path) if exists else None, mode, index.get(name)])
        if exists:
            total += path.stat().st_size
    selected &= files
    if kind == 'docs':
        selected = {name for name in selected if name.endswith('.md')}
    if include:
        selected = {name for name in selected if any(name == p or name.startswith(p.rstrip('/')+'/') for p in include)}
    return {'schema': 'tao.review-scope/v0.1', 'change': state['change'], 'scope': scope, 'kind': kind,
            'base_commit': source, 'target_commit': target, 'include': include,
            'selected_files': sorted(selected), 'context_files': [r[0] for r in rows], 'excluded_files': excluded,
            'input_digest': digest_json(rows), 'input_bytes': total, 'index_entries': {name: index[name] for name in sorted(files & index.keys())},
            'instruction': 'Confirm this scope before starting. The snapshot includes unchanged context; inspect relevant callers and authoritative documents. No review has run.'}


def begin(project, identity, expected, request, mode, reviewers, decision, max_rounds=None, budget_seconds=None, new_batch=False):
    workflows.text(decision)
    if mode not in ('serial', 'parallel') or type(reviewers) is not int or not 1 <= reviewers <= 3 or (mode == 'serial' and reviewers != 1):
        raise ConfigurationError('Use one serial reviewer or up to three parallel reviewers.')
    if not isinstance(request, dict) or request.get('change') != identity:
        raise ConfigurationError('Review scope belongs to another workflow.')
    def edit(owner, state):
        fresh = preview(owner, state, request.get('scope'), request.get('kind'), request.get('base_commit'), request.get('include'))
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
                      'budget_seconds': budget_seconds or 1800, 'runs': [], 'budget_decisions': []}
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
        if preview(owner, state, request['scope'], key, request['base_commit'], request['include']) != request:
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
        try:
            current = preview(owner, state, run['request']['scope'], kind, run['request']['base_commit'], run['request']['include'])
            outcome = result['outcome'] if current == run['request'] or result['outcome'] == 'failed' else 'stale'
        except (OSError, ValueError) as exc:
            run['input_error'] = str(exc)
            outcome = 'failed' if result['outcome'] == 'failed' else 'stale'
        if (datetime.now(timezone.utc)-datetime.fromisoformat(series['started_at'])).total_seconds() >= series['budget_seconds']:
            outcome = 'budget-exceeded'
        run.update(outcome=outcome, reports=saved, summary=result['summary'], ended_at=datetime.now(timezone.utc).isoformat())
        run['evidence_boundary'] = 'Scheduling record only. Required independent attestations use tao review imports; report existence does not prove correctness or identity.'
    return workflows.mutate(project, identity, expected, edit)


def passed(project, state, kind):
    series = state['reviews'].get(kind)
    if not series or not series['runs']:
        return False
    run = series['runs'][-1]
    return run['outcome'] == 'passed' and preview(project, state, run['request']['scope'], kind, run['request']['base_commit'], run['request']['include']) == run['request']
