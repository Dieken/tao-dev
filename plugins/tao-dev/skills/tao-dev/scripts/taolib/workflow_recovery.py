"""Explicit recovery and migration; discovery is always read-only."""
from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path
import shlex
import yaml

from .frontmatter import load_frontmatter

from . import workflow_records as records, workflows
from .project import Project, ConfigurationError, ConflictError, mutation_lock, create_file, replace_file
from .verification import file_digest


def candidate_sources(project, identity):
    """Discover physical sources without recursively validating local state."""
    from . import git_workflow
    rows = []
    for root in git_workflow.roots(project):
        owner = project if root == project.root else Project(root)
        for kind, target in (('local-state', workflows.state_path(owner, identity)),
                             ('workflow-record', records.path(owner, identity))):
            if target.is_file():
                rows.append({'kind': kind, 'project': str(root), 'path': str(target)})
        for target in owner.sources():
            try:
                data = load_frontmatter(target.read_text(encoding='utf-8'))
                if isinstance(data, dict) and data.get('schema') == 'tao.project.plan/v0.1' and data.get('change') == identity:
                    rows.append({'kind': 'plan', 'project': str(root), 'path': str(target)})
            except (OSError, ValueError, yaml.YAMLError):
                continue
    return rows


def missing(project, identity, reason='missing'):
    path = workflows.state_path(project, identity)
    argv = ['tao', '--project', str(project.root), 'workflow', 'recover', identity]
    return {'rule_id': 'TAO-CLI-001', 'change': identity, 'project': str(project.root),
            'state': reason, 'expected_path': str(path),
            'candidate_sources': candidate_sources(project, identity),
            'recovery_commands': [argv, argv + ['--apply']],
            'message': str(path) + ': ' + reason + '. Preview recovery: ' + shlex.join(argv)}


def ambiguity(project, identity, owners):
    details = missing(project, identity, 'ambiguous: ' + ', '.join(str(p.root) for p in owners))
    details.update(selection_required=True, recovery_commands=[])
    details['message'] = details['state'] + '; select the workflow project explicitly with --project.'
    return details


def source_problem(project, identity, target, error):
    details = missing(project, identity, 'formal-record-invalid')
    details.update(expected_path=str(target), recovery_commands=[], message=str(error))
    return details


def documents(project):
    from .documents import validate
    return validate(project.root, project.sources())


def candidates(project):
    result = documents(project)
    ids = set(records.identities(project))
    for document in result.documents.values():
        if document.metadata.get('schema') != 'tao.project.plan/v0.1':
            continue
        identity = document.metadata.get('change')
        try:
            workflows.state_path(project, identity)
        except ConfigurationError:
            continue  # Invalid source metadata is reported by document validation.
        ids.add(identity)
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
    from . import git_workflow
    owners = [Project(root) for root in git_workflow.roots(project)
              if root != project.root and workflows.state_path(Project(root), identity).is_file()]
    if owners and not workflows.state_path(project, identity).exists():
        raise WorkflowStateError(ambiguity(project, identity, owners))

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
    try:
        record = records.read(project, identity)
    except (ValueError, OSError) as exc:
        return source_problem(project, identity, records.path(project, identity), exc)
    if target.exists():
        try:
            state = workflows.read(project, identity)
        except WorkflowStateError as exc:
            return exc.details
        # Other source/handoff errors must not masquerade as corrupt local JSON.
        value = workflows.observe(project, state)
        value['candidate_sources'] = candidate_sources(project, identity)
        if record is None:
            value.setdefault('lifecycle', 'unknown')
            value['recovery_commands'] = [['tao', '--project', str(project.root), 'workflow', 'migrate', identity]]
        return value
    try:
        state, record = reconstruct(project, identity)
        return state | missing(project, identity) | {'record_path': str(records.path(project, identity)) if record else None}
    except (ValueError, OSError) as exc:
        return missing(project, identity, str(exc))


class WorkflowStateError(ConflictError):
    def __init__(self, details):
        self.details = details
        super().__init__(details['message'])
