"""Explicit recovery and migration; discovery is always read-only."""
from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path
import shlex

from . import workflow_records as records, workflows
from .project import Project, ConfigurationError, ConflictError, mutation_lock, create_file, replace_file
from .verification import file_digest


def missing(project, identity, reason='missing'):
    path = workflows.state_path(project, identity)
    argv = ['tao', '--project', str(project.root), 'workflow', 'recover', identity]
    return {'change': identity, 'state': reason, 'expected_path': str(path),
            'recovery_commands': [argv, argv + ['--apply']],
            'message': str(path) + ': ' + reason + '. Preview recovery: ' + shlex.join(argv)}


def documents(project):
    from .documents import validate
    return validate(project.root, project.sources())


def candidates(project):
    result = documents(project)
    ids = set(records.identities(project))
    ids.update(d.metadata['change'] for d in result.documents.values() if d.metadata.get('schema') == 'tao.project.plan/v0.1')
    ids.update(p.stem for p in (project.root / '.tao/workflows').glob('CHG_*.json'))
    return sorted(ids)


def reconstruct(project, identity):
    record = records.read(project, identity)
    result = documents(project)
    if not result.valid:
        raise ConflictError('Managed documents must validate before recovery.')
    plans = [d for d in result.documents.values() if d.metadata.get('schema') == 'tao.project.plan/v0.1' and d.metadata.get('change') == identity]
    if not record and len(plans) != 1:
        raise ConflictError(missing(project, identity, 'no authoritative record or unique plan')['message'])
    by_id = {d.metadata['id']: d for d in result.documents.values()}
    mapping = deepcopy(record['artifacts']) if record else {'plan': [plans[0].metadata['id']]}
    if not record:
        for role, key in [('spec', 'spec_docs'), ('design', 'design_docs')]:
            if plans[0].metadata.get(key):
                mapping[role] = plans[0].metadata[key]
    artifacts = {}
    for role, ids in mapping.items():
        if any(i not in by_id for i in ids):
            raise ConflictError('Workflow artifact identity cannot be resolved.')
        artifacts[role] = [by_id[i].path for i in ids]
    data = record or plans[0].metadata
    plan_path = record['plan_path'] if record else plans[0].path
    state = {'schema': workflows.SCHEMA, 'change': identity, 'slug': data.get('slug', Path(plan_path).stem),
             'summary': data.get('summary', data['title']), 'locale': data['locale'], 'created': data['created'],
             'updated_at': datetime.now().astimezone().isoformat(), 'revision': 1,
             'phase': record['phase'] if record else 'spec', 'lifecycle': record['lifecycle'] if record else 'unknown',
             'plan_path': plan_path, 'artifacts': artifacts, 'approvals': deepcopy(record['approvals']) if record else {},
             'decision': 'Recovered recorded facts; reconcile missing decisions before continuing.',
             'next': 'Inspect actual operations, approvals and current inputs.',
             'blockers': ['Reconcile actual running operations and missing decisions.'], 'operations': [],
             'git': record['baseline'] if record else None, 'handoff': None, 'resumed_handoff': None,
             'reviews': deepcopy(record['review_batches']) if record else {}, 'closure': record['closure'] if record else None}
    unknown = record['provenance'].get('unknown_fields', []) if record else ['review_batches']
    state['review_budget_unknown'] = record['provenance'].get('review_budget_unknown', ['docs', 'code'] if 'review_batches' in unknown else []) if record else ['docs', 'code']
    state['review_history'] = {k: b.pop('history') for k, b in state['reviews'].items() if 'history' in b}
    return state, record


def recover(project, identity, apply=False, expected_source=None):
    target = workflows.state_path(project, identity)
    if target.exists():
        raise ConflictError(missing(project, identity, 'already exists; inspect or migrate without overwriting')['message'])
    with mutation_lock(project) if apply else _readonly():
        if target.exists():
            raise ConflictError('Workflow state was created concurrently.')
        state, record = reconstruct(project, identity)
        digest = records.source_digest(project)
        if expected_source is not None and digest != expected_source:
            raise ConflictError('Recovery sources changed; preview again.')
        output = missing(project, identity) | {'source_digest': digest, 'candidate': state, 'record_path': str(records.path(project, identity)), 'applied': False}
        if not apply:
            return output
        if record is None:
            record = records.build(project, state, provenance={'kind': 'legacy', 'unknown_fields': ['lifecycle', 'approvals', 'baseline', 'review_batches']})
            state.update(records.write(project, record))
        else:
            state.update(record_revision=record['record_revision'], record_digest=file_digest(records.path(project, identity)), record_operation=record['last_operation_id'])
        create_file(project.root, target, json.dumps(state, ensure_ascii=False, indent=2)+'\n')
        return output | {'applied': True, 'candidate': state}


class _readonly:
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False


def migrate(project, identity, apply=False, expected=None, expected_source=None):
    with mutation_lock(project) if apply else _readonly():
        state = workflows.read(project, identity)
        target = workflows.state_path(project, identity)
        before = target.read_bytes()
        if records.read(project, identity):
            raise ConflictError('Formal workflow record already exists; use workflow resume to reconcile.')
        if not documents(project).valid:
            raise ConflictError('Managed documents must validate before recovery.')
        digest = records.source_digest(project, state)
        output = {'change': identity, 'revision': state['revision'], 'source_digest': digest,
                  'record_path': str(records.path(project, identity)), 'applied': False}
        if not apply:
            return output
        if expected != state['revision'] or expected_source != digest:
            raise ConflictError('Migration requires the preview revision and source digest.')
        proposed = deepcopy(state)
        proposed['lifecycle'] = 'unknown'
        proposed['review_budget_unknown'] = ['docs', 'code'] if 'reviews' not in state else []
        record = records.build(project, proposed, provenance={'kind': 'legacy', 'source_digest': file_digest(target),
                                'source_revision': state['revision'], 'unknown_fields': ['lifecycle']})
        marks = records.write(project, record)
        state.update(marks)
        state['lifecycle'] = 'unknown'
        state['review_budget_unknown'] = proposed['review_budget_unknown']
        state['revision'] += 1
        replace_file(project.root, target, json.dumps(state, ensure_ascii=False, indent=2)+'\n', before)
        return output | {'applied': True, 'revision': state['revision']}


def reconcile(project, identity, expected, decision, lifecycle=None):
    with mutation_lock(project):
        state = workflows.read(project, identity)
        target = workflows.state_path(project, identity)
        before = target.read_bytes()
        if expected != state['revision']:
            raise ConflictError('Workflow checkpoint changed; inspect status before resuming.')
        record = records.read(project, identity)
        if not record:
            raise ConflictError('No formal workflow record; preview workflow migrate first.')
        if not records.synchronized(project, state, record):
            source = record['provenance'].get('source_digest')
            if source and file_digest(target) != source and not state.get('record_revision'):
                raise ConflictError('Legacy state changed after migration; reconcile the conflict explicitly.')
            candidate, _ = reconstruct(project, identity)
            # Local operations and extension fields remain intact.
            for key in ('phase', 'lifecycle', 'approvals', 'git', 'closure', 'artifacts', 'review_budget_unknown'):
                state[key] = candidate[key]
            for kind, batch in candidate['reviews'].items():
                originals = {r['id']: r for r in state.get('reviews', {}).get(kind, {}).get('runs', [])}
                for run in batch['runs']:
                    if run['id'] in originals:
                        original = originals[run['id']]
                        run.update({k: original[k] for k in ('request', 'snapshot', 'snapshot_digest', 'index_snapshot', 'index_snapshot_digest') if k in original})
                        run.pop('recovered_context', None)
                state.setdefault('reviews', {})[kind] = batch
            state['review_history'] = candidate.get('review_history', {})
            state.update(record_revision=record['record_revision'], record_digest=file_digest(records.path(project, identity)), record_operation=record['last_operation_id'])
        if lifecycle:
            if lifecycle not in {'active', 'paused'} or state.get('lifecycle') in {'completed', 'cancelled'}:
                raise ConflictError('Closed workflows cannot be reopened by resume.')
            state['lifecycle'] = lifecycle
            provenance = deepcopy(record['provenance'])
            provenance['unknown_fields'] = [k for k in provenance.get('unknown_fields', []) if k != 'lifecycle']
            provenance['lifecycle_decision'] = decision
            state.update(records.write(project, records.build(project, state, record, provenance), records.path(project, identity).read_bytes()))
        state['recovery'] = workflows.text(decision)
        state['revision'] += 1
        replace_file(project.root, target, json.dumps(state, ensure_ascii=False, indent=2)+'\n', before)
        return state


def observation(project, identity):
    target = workflows.state_path(project, identity)
    if target.exists():
        try:
            return workflows.observe(project, workflows.read(project, identity))
        except (ValueError, OSError):
            return missing(project, identity, 'corrupt; preserve the file before recovery')
    try:
        state, record = reconstruct(project, identity)
        return state | missing(project, identity) | {'project': str(project.root), 'record_path': str(records.path(project, identity)) if record else None}
    except (ValueError, OSError) as exc:
        return missing(project, identity, str(exc))


class WorkflowStateError(ConflictError):
    def __init__(self, details):
        self.details = details
        super().__init__(details['message'])
