"""Durable phase checkpoints. Recorded decisions are context, not authentication."""
from datetime import datetime, date
import json
from pathlib import Path
import re

from .project import Project, ConfigurationError, ConflictError, contained, create_file, replace_file, mutation_lock
from .verification import file_digest, digest_json
from .reviews import load
from . import git_workflow
from tao_messages import Message

PHASES = ('spec', 'design', 'plan', 'implement', 'review', 'finish', 'complete')
DOC_PHASES = PHASES[:3]
SCHEMA = 'tao.workflow/v0.1'


def text(value):
    if not isinstance(value, str) or not value.strip():
        raise ConfigurationError('A nonempty decision or summary is required.')
    return value


def state_path(project, identity):
    if not isinstance(identity, str) or not re.fullmatch(r'CHG_[0-9]{8}_[0-9A-HJKMNP-TV-Z]{16}', identity):
        raise ConfigurationError('Invalid workflow CHG identity.')
    return contained(project.root, f'.tao/workflows/{identity}.json')


def read(project, identity):
    path = state_path(project, identity)
    if not path.exists():
        from .workflow_recovery import missing, WorkflowStateError
        raise WorkflowStateError(missing(project, identity))
    try:
        data = load(path)
    except (ValueError, OSError) as exc:
        from .workflow_recovery import missing, WorkflowStateError
        raise WorkflowStateError(missing(project, identity, 'corrupt; preserve the file before recovery')) from exc
    if (not isinstance(data, dict) or data.get('schema') != SCHEMA or data.get('change') != identity
            or data.get('phase') not in PHASES or type(data.get('revision')) is not int
            or data['revision'] < 1 or not isinstance(data.get('artifacts'), dict)
            or not isinstance(data.get('approvals'), dict)):
        from .workflow_recovery import missing, WorkflowStateError
        raise WorkflowStateError(missing(project, identity, 'corrupt; preserve the file before recovery'))
    return data


def local(project):
    directory = contained(project.root, '.tao/workflows')
    return [read(project, p.stem) for p in sorted(directory.glob('CHG_*.json'))]


def locate(project, identity):
    if state_path(project, identity).is_file():
        return project
    matches = [Project(root) for root in git_workflow.roots(project)
               if root != project.root and state_path(Project(root), identity).is_file()]
    if len(matches) != 1:
        from .workflow_recovery import missing, WorkflowStateError
        raise WorkflowStateError(missing(project, identity, 'missing' if not matches else 'ambiguous: ' + ', '.join(str(p.root) for p in matches)))
    return matches[0]


def plan_contract(content):
    """Exclude actual execution metadata, preserving code examples verbatim."""
    from .documents import parser, SECTION
    lines = content.splitlines(keepends=True)
    protected, markers = set(), {}
    for token in parser().parse(content):
        if token.map and token.type in {'fence', 'code_block'}:
            protected.update(range(*token.map))
        if token.map and token.type == 'html_block' and token.level == 0:
            value = token.content.strip()
            match = SECTION.fullmatch(value)
            if match:
                markers[token.map[0]] = match[1]
            elif value in {'<!-- tao:results -->', '<!-- /tao:results -->'}:
                markers[token.map[0]] = value
    section, pending = None, None
    excluded = set()
    for number, marker in sorted(markers.items()):
        if marker == '<!-- tao:results -->' and section == 'verification':
            pending = number
        elif marker == '<!-- /tao:results -->' and pending is not None:
            excluded.update(range(pending, number + 1))
            pending = None
        elif marker not in {'<!-- tao:results -->', '<!-- /tao:results -->'}:
            section, pending = marker, None
    section, in_task, result = None, False, []
    for number, line in enumerate(lines):
        if number in excluded:
            continue
        if number in protected:
            result.append(line)
            in_task = False
            continue
        if number in markers:
            section, in_task = markers[number], False
        if section == 'tasks':
            if re.match(r'^- \[([ x])\] `TASK_', line):
                in_task = True
                line = re.sub(r'^- \[([ x])\]', '- [ ]', line)
            elif in_task and line.startswith('  - evidence:'):
                continue
            elif line.strip() and not line.startswith('  '):
                in_task = False
        # Ignore incidental blank lines around appended execution records.
        if not line.strip() and result and not result[-1].strip():
            continue
        result.append(line)
    return ''.join(result)


def artifact_digest(project, state, phase, algorithm="path-v0"):
    if algorithm not in {"path-v0", "doc-v1"}:
        return None
    names = list(state['artifacts'].get(phase, []))
    if phase == 'plan' and names:
        from .documents import validate
        result = validate(project.root, project.sources())
        for name in list(names):
            doc = result.documents.get(name)
            target = result.definitions.get(doc.metadata.get('tasks_doc')) if doc else None
            if target and target.path not in names:
                names.append(target.path)
    rows = []
    for name in names:
        path = contained(project.root, name)
        if not path.is_file():
            rows.append((name, None))
            continue
        binding_name = name
        if algorithm == 'doc-v1':
            import yaml
            try:
                from .frontmatter import load_frontmatter
                binding_name = load_frontmatter(path.read_text(encoding='utf-8'))['id']
            except (ValueError, KeyError, TypeError, IndexError, yaml.YAMLError):
                return None
        if phase == 'plan':
            content = plan_contract(path.read_text(encoding='utf-8'))
            rows.append((binding_name, digest_json(content)))
        else:
            rows.append((binding_name, file_digest(path)))
    return digest_json(rows) if names else None


def handoff_observation(project, state):
    path = (Path(state['plan_path']).with_suffix('') / 'handoff.md').as_posix()
    target = contained(project.root, path)
    if not target.is_file():
        return {'handoff_state': 'missing' if state.get('handoff') else 'absent', 'handoff_path': path, 'handoff_digest': None}
    digest = file_digest(target)
    previous = state.get('resumed_handoff') or {}
    return {'handoff_state': 'resumed' if previous.get('digest') == digest and previous.get('path') == path else 'unread',
            'handoff_path': path, 'handoff_digest': digest}


def available_actions(project, state, stale):
    if stale:
        return ['refine']
    phase = state['phase']
    blocked = bool(state.get('blockers') or state.get('operations'))
    if phase in DOC_PHASES:
        actions = ['refine', 'review-docs']
        if not blocked:
            actions.append('approve-and-advance')
        return actions
    if phase == 'implement':
        actions = ['refine', 'continue']
        if not blocked:
            actions.append('approve-and-advance')
        return actions
    if phase == 'review':
        actions = ['refine', 'review-code']
        if not blocked:
            from .review_runs import passed
            try:
                if passed(project, state, 'code'):
                    actions.append('approve-and-advance')
            except (KeyError, OSError, ValueError, ConflictError):
                pass
        return actions
    if phase == 'finish':
        return ['refine'] if blocked else ['refine', 'approve-and-advance']
    return []


def observe(project, state):
    stale = [phase for phase, approval in state['approvals'].items()
             if phase in DOC_PHASES and artifact_digest(project, state, phase, approval.get('algorithm', 'path-v0')) != approval['digest']]
    from . import workflow_records
    record = workflow_records.read(project, state['change'])
    state = state | {'record_sync': 'current' if workflow_records.synchronized(project, state, record) else 'pending' if record else 'legacy'}
    return state | handoff_observation(project, state) | {'project': str(project.root), 'stale_approvals': stale,
                    'next_action': 'refine' if stale else 'continue',
                    'available_actions': available_actions(project, state, stale),
                    'observation': 'Read-only; inspect live operations and actual files before resuming.'}


def status(project, identity=None):
    from .workflow_recovery import candidates, observation
    if identity:
        if identity in candidates(project):
            return [observation(project, identity)]
        matches = [Project(root) for root in git_workflow.roots(project) if root != project.root and identity in candidates(Project(root))]
        if len(matches) == 1:
            return [observation(matches[0], identity)]
        if len(matches) > 1:
            from .workflow_recovery import missing, WorkflowStateError
            raise WorkflowStateError(missing(project, identity, 'ambiguous: ' + ', '.join(str(p.root) for p in matches)))
        return [observation(project, identity)]
    values = []
    for root in git_workflow.roots(project):
        owner = Project(root)
        values.extend(observation(owner, i) for i in candidates(owner))
    return values


def start(project, slug, summary, locale, decision, worktree=False):
    text(summary); text(decision)
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', slug):
        raise ConfigurationError('Workflow slug must be lowercase ASCII words separated by hyphens.')
    locale = locale or project.locale
    if locale not in ('en', 'zh-Hans'):
        raise ConfigurationError('Resolve the project document language first: en or zh-Hans.')
    from .workflow_recovery import candidates, observation
    if any(s.get('slug') == slug and s.get('lifecycle') not in {'completed', 'cancelled'} and s.get('phase') != 'complete' for s in (observation(project, i) for i in candidates(project))):
        raise ConflictError('An active workflow already uses this slug; continue it.')
    owner, info = git_workflow.prepare(project, slug) if worktree else (project, git_workflow.context(project.root))
    from .documents import ASSETS, validate
    from .identifiers import new_id
    registry = json.loads((ASSETS / 'document-profiles.json').read_text(encoding='utf-8'))
    existing = set(validate(owner.root, owner.sources()).definitions) | {s['change'] for s in local(owner)}
    identity = new_id('CHG', registry, existing)
    day = date.today()
    plan_path = (Path(owner.paths['plans']) / day.strftime('%Y-%m') / (day.strftime('%Y%m%d-')+slug+'.md')).as_posix()
    state = {'schema': SCHEMA, 'change': identity, 'slug': slug, 'summary': summary,
             'locale': locale, 'created': day.isoformat(), 'updated_at': datetime.now().astimezone().isoformat(),
             'revision': 1, 'phase': 'spec', 'plan_path': plan_path,
             'artifacts': {}, 'approvals': {}, 'decision': decision, 'next': 'Write or update the specification.',
             'blockers': [], 'operations': [], 'git': info, 'handoff': None, 'resumed_handoff': None,
             'reviews': {}}
    with mutation_lock(owner):
        from . import workflow_records
        state['lifecycle'] = 'active'
        state.update(workflow_records.write(owner, workflow_records.build(owner, state)))
        create_file(owner.root, state_path(owner, identity), json.dumps(state, ensure_ascii=False, indent=2)+'\n')
    return state


def mutate(project, identity, expected, edit, durable=True):
    project = locate(project, identity)
    with mutation_lock(project):
        path = state_path(project, identity)
        before = path.read_bytes()
        state = read(project, identity)
        if type(expected) is not int or state['revision'] != expected:
            raise ConflictError('Workflow checkpoint changed; run tao workflow status and reconcile before retrying.')
        from . import workflow_records
        record = workflow_records.read(project, identity)
        if record and not workflow_records.synchronized(project, state, record):
            raise ConflictError('Formal workflow record differs from local state; use workflow resume.')
        if state.get('lifecycle') in {'completed', 'cancelled'}:
            raise ConflictError('Workflow is closed; create a new change for follow-up work.')
        edit(project, state)
        if durable and record:
            record_path = workflow_records.path(project, identity)
            state.update(workflow_records.write(project, workflow_records.build(project, state, record), record_path.read_bytes()))
        state['revision'] += 1
        state['updated_at'] = datetime.now().astimezone().isoformat()
        replace_file(project.root, path, json.dumps(state, ensure_ascii=False, indent=2)+'\n', before)
    return state


def checkpoint(project, identity, expected, patch):
    def edit(owner, state):
        if not isinstance(patch, dict) or patch.keys() - {'summary', 'next', 'blockers', 'operations', 'artifacts'}:
            raise ConfigurationError('Checkpoint accepts summary, next, blockers, operations and artifacts only.')
        for key in ('summary', 'next'):
            if key in patch:
                text(patch[key])
        for key in ('blockers', 'operations'):
            if key in patch and (not isinstance(patch[key], list) or any(not isinstance(x, str) or not x.strip() for x in patch[key])):
                raise ConfigurationError('Blockers and operations must be nonempty string arrays.')
        if 'artifacts' in patch:
            mapping = patch['artifacts']
            if not isinstance(mapping, dict) or mapping.keys() - set(DOC_PHASES):
                raise ConfigurationError('Artifact roles are spec, design and plan.')
            for names in mapping.values():
                if not isinstance(names, list) or not names or len(names) != len(set(names)):
                    raise ConfigurationError('Each artifact role requires distinct document paths.')
                for name in names:
                    if not isinstance(name, str) or Path(name).is_absolute() or not contained(owner.root, name).is_file():
                        raise ConfigurationError('Checkpoint artifacts must be existing project-relative files.')
            patch_copy = patch | {'artifacts': state['artifacts'] | mapping}
        else:
            patch_copy = patch
        state.update(patch_copy)
    return mutate(project, identity, expected, edit, durable=False)


def advance(project, identity, expected, decision, doc_review=None):
    text(decision)
    def edit(owner, state):
        stale = observe(owner, state)['stale_approvals']
        if stale:
            # Any stale approval blocks, not only the phase being advanced, so
            # the message names the phase to revise instead of sending the
            # reader to status for the one fact the refusal already knows.
            raise ConflictError(Message('Approved documents changed in {arg0}; refine and obtain a new decision first.',
                                        ', '.join(stale)))
        phase = state['phase']
        if phase == 'finish':
            raise ConflictError('Use workflow finish with closure evidence before completing the workflow.')
        if state.get('lifecycle') == 'unknown':
            raise ConflictError('Confirm the legacy lifecycle explicitly with workflow resume first.')
        if phase == 'complete' or state['blockers'] or state['operations']:
            raise ConflictError('Resolve blockers and reconcile active operations before advancing.')
        if phase in DOC_PHASES:
            names = state['artifacts'].get(phase, [])
            if not names:
                raise ConflictError('Link the current stage document before advancing.')
            from .documents import validate
            result = validate(owner.root, owner.sources())
            if not result.valid:
                raise ConflictError('Managed documents must validate before stage approval.')
            from .documents import ASSETS
            registry = json.loads((ASSETS / 'document-profiles.json').read_text(encoding='utf-8'))
            expected_schema = f'tao.project.{phase}/v0.1'
            if any(name not in result.documents or result.documents[name].metadata['schema'] != expected_schema for name in names):
                raise ConflictError('Stage artifacts must use the matching document profile.')
            profile = registry['profiles'][expected_schema]
            for key in profile.get('approval_requires', []):
                role = {'spec_docs': 'spec', 'design_docs': 'design'}[key]
                expected_ids = {result.documents[n].metadata['id'] for n in state['artifacts'].get(role, []) if n in result.documents}
                linked = set()
                for name in names:
                    values = result.documents[name].metadata.get(key, [])
                    if not values or not expected_ids.intersection(values):
                        raise ConflictError(Message('Link {arg0} to the approved stage documents before advancing.', key))
                    linked.update(values)
                if not expected_ids or not expected_ids.issubset(linked):
                    raise ConflictError(Message('The {arg0} relationship must cover the approved stage documents.', key))
            if phase == 'plan' and any(result.documents[n].metadata.get('change') != identity for n in names):
                raise ConflictError('Plan documents must belong to this workflow change.')
            if phase == 'plan' and doc_review not in ('completed', 'skipped'):
                raise ConflictError('Record the user decision about document review before implementation.')
            if phase == 'plan' and doc_review == 'completed':
                from .review_runs import passed
                if not passed(owner, state, 'docs'):
                    raise ConflictError('A current completed document review is required for this choice.')
            state['approvals'][phase] = {'digest': artifact_digest(owner, state, phase, 'doc-v1'), 'algorithm': 'doc-v1', 'decision': decision}
            if phase == 'plan':
                state['doc_review'] = doc_review
        if phase == 'review':
            from .review_runs import passed
            if not passed(owner, state, 'code'):
                raise ConflictError('Complete a current code review before entering finish.')
        state['phase'] = PHASES[PHASES.index(phase)+1]
        state['decision'] = decision
        state['next'] = 'Begin '+state['phase']+' within the recorded decision.'
    return mutate(project, identity, expected, edit)


def revise(project, identity, expected, phase, decision):
    text(decision)
    if phase not in DOC_PHASES:
        raise ConfigurationError('Refinement starts at spec, design or plan.')
    def edit(owner, state):
        if PHASES.index(phase) > PHASES.index(state['phase']):
            raise ConflictError('Cannot refine a stage not yet reached.')
        state['approvals'] = {k: v for k, v in state['approvals'].items() if PHASES.index(k) < PHASES.index(phase)}
        state['phase'] = phase
        state['decision'] = decision
        state['next'] = 'Revise '+phase+' and reassess downstream artifacts.'
    return mutate(project, identity, expected, edit)


def resume(project, identity, expected, decision, handoff_digest=None):
    text(decision)
    def edit(owner, state):
        observed = handoff_observation(owner, state)
        if observed['handoff_digest'] != handoff_digest:
            raise ConflictError('Handoff changed since inspection; read and reconcile its current content first.')
        if observed['handoff_digest']:
            state['resumed_handoff'] = {'path': observed['handoff_path'], 'digest': observed['handoff_digest'],
                                        'revision': state['revision'], 'decision': decision}
        state['recovery'] = decision
        # Keep phase, current next step, approvals and all actual task progress.
    return mutate(project, identity, expected, edit)


def dispatch(project, args):
    if args.operation in ('recover', 'migrate'):
        from . import workflow_recovery
        if args.operation == 'recover':
            return workflow_recovery.recover(project, args.change, args.apply, args.expect_source)
        return workflow_recovery.migrate(project, args.change, args.apply, args.expect, args.expect_source)
    if args.operation == 'finish':
        return finish(project, args.change, args.expect, args.decision, args.outcome, load(contained(project.root, args.source)))
    if args.operation.startswith('review-'):
        from . import review_runs
        owner = locate(project, args.change)
        if args.operation == 'review-preview':
            return review_runs.preview(owner, read(owner, args.change), args.scope, args.kind, args.base, args.include, args.output)
        source = load(contained(owner.root, args.source))
        if args.operation == 'review-begin':
            return review_runs.begin(owner, args.change, args.expect, source, args.mode, args.reviewers,
                                     args.decision, args.max_rounds, args.new_batch)
        return review_runs.finish(owner, args.change, args.expect, source)
    if args.operation == 'start':
        return start(project, args.slug, args.summary, args.locale, args.decision, args.worktree)
    if args.operation == 'status':
        return {'workflows': status(project, args.change)}
    if args.operation == 'checkpoint':
        return checkpoint(project, args.change, args.expect, load(contained(project.root, args.source)))
    if args.operation == 'resume':
        from . import workflow_records, workflow_recovery
        state = read(project, args.change)
        record = workflow_records.read(project, args.change)
        if record and (args.lifecycle or not workflow_records.synchronized(project, state, record)):
            return workflow_recovery.reconcile(project, args.change, args.expect, args.decision, args.lifecycle)
        return resume(project, args.change, args.expect, args.decision, args.handoff_digest)
    if args.operation == 'advance':
        return advance(project, args.change, args.expect, args.decision, args.doc_review)
    return revise(project, args.change, args.expect, args.phase, args.decision)


def finish(project, identity, expected, decision, outcome, closure):
    text(decision)
    if outcome not in {'completed', 'cancelled'} or not isinstance(closure, dict) or set(closure) != {'evidence', 'unfinished'}:
        raise ConfigurationError('Closure requires evidence and unfinished arrays.')
    if any(not isinstance(closure[k], list) or any(not isinstance(v, str) or not v.strip() for v in closure[k]) for k in closure):
        raise ConfigurationError('Closure requires evidence and unfinished arrays.')
    state = read(project, identity)
    from . import workflow_records, workflow_recovery
    record = workflow_records.read(project, identity)
    if record and record.get('closure') and not workflow_records.synchronized(project, state, record):
        state = workflow_recovery.reconcile(project, identity, expected, decision)
    if state.get('closure'):
        if state['closure'].get('decision') == decision and state['closure'].get('result') == outcome and all(state['closure'].get(k) == v for k, v in closure.items()):
            return state
        raise ConflictError('Workflow already has a different closure.')
    verified = None
    if outcome == 'completed':
        from .cli import arguments, verify, document_snapshot
        args = arguments(['--project', str(project.root), 'verify', identity])
        report, code = verify(project, args, {'outputs': {}, 'diagnostics': []})
        if code:
            raise ConflictError('Delivery verification must pass before completion.')
        verified = document_snapshot(project)
    def edit(owner, current):
        if outcome == 'completed':
            from .cli import document_snapshot
            from .review_runs import passed
            if not passed(owner, current, 'code'):
                raise ConflictError('Complete a current code review before entering finish.')
            if verified != document_snapshot(owner) or current['phase'] != 'finish' or current['blockers'] or current['operations'] or observe(owner, current)['stale_approvals']:
                raise ConflictError('Workflow is not ready to finish.')
            current['phase'] = 'complete'
        elif not closure['unfinished']:
            raise ConflictError('Cancellation requires disposition of unfinished work.')
        current['lifecycle'] = outcome
        current['closure'] = closure | {'result': outcome, 'decision': decision,
                                      'recorded_at': datetime.now().astimezone().isoformat()}
    return mutate(project, identity, expected, edit)
