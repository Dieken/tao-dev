"""Durable phase checkpoints. Recorded decisions are context, not authentication."""
from datetime import datetime, date
import json
from pathlib import Path
import re

from .project import Project, ConfigurationError, ConflictError, contained, create_file, replace_file, mutation_lock
from .verification import file_digest, digest_json
from .reviews import load
from . import git_workflow

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
    data = load(path)
    if (not isinstance(data, dict) or data.get('schema') != SCHEMA or data.get('change') != identity
            or data.get('phase') not in PHASES or type(data.get('revision')) is not int
            or data['revision'] < 1 or not isinstance(data.get('artifacts'), dict)
            or not isinstance(data.get('approvals'), dict)):
        raise ConfigurationError('Invalid workflow state; recover the file before continuing.')
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
        raise ConflictError('Select one existing workflow in its workspace.')
    return matches[0]


def artifact_digest(project, state, phase):
    names = state['artifacts'].get(phase, [])
    return digest_json([(name, file_digest(contained(project.root, name))) for name in names]) if names else None


def observe(project, state):
    stale = [phase for phase, approval in state['approvals'].items()
             if phase in DOC_PHASES and artifact_digest(project, state, phase) != approval['digest']]
    return state | {'project': str(project.root), 'stale_approvals': stale,
                    'next_action': 'refine' if stale else 'continue',
                    'observation': 'Read-only; inspect live operations and actual files before resuming.'}


def status(project, identity=None):
    if identity:
        owner = locate(project, identity)
        return [observe(owner, read(owner, identity))]
    values = []
    seen = set()
    for root in git_workflow.roots(project):
        owner = Project(root)
        for state in local(owner):
            if state['change'] in seen:
                raise ConflictError('Workflow identity occurs in several workspaces; select its owner explicitly.')
            seen.add(state['change'])
            values.append(observe(owner, state))
    return values


def start(project, slug, summary, locale, decision, worktree=False):
    text(summary); text(decision)
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', slug):
        raise ConfigurationError('Workflow slug must be lowercase ASCII words separated by hyphens.')
    locale = locale or project.locale
    if locale not in ('en', 'zh-Hans'):
        raise ConfigurationError('Resolve the project document language first: en or zh-Hans.')
    if any(s['slug'] == slug and s['phase'] != 'complete' for s in local(project)):
        raise ConflictError('An active workflow already uses this slug; continue it.')
    owner, info = git_workflow.prepare(project, slug) if worktree else (project, git_workflow.context(project.root))
    from .documents import ASSETS, validate
    from .identifiers import new_id
    registry = json.loads((ASSETS / 'document-profiles.json').read_text())
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
        create_file(owner.root, state_path(owner, identity), json.dumps(state, ensure_ascii=False, indent=2)+'\n')
    return state


def mutate(project, identity, expected, edit):
    project = locate(project, identity)
    with mutation_lock(project):
        path = state_path(project, identity)
        before = path.read_bytes()
        state = read(project, identity)
        if type(expected) is not int or state['revision'] != expected:
            raise ConflictError('Workflow checkpoint changed; read status and reconcile before retrying.')
        edit(project, state)
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
    return mutate(project, identity, expected, edit)


def advance(project, identity, expected, decision, doc_review=None):
    text(decision)
    def edit(owner, state):
        if observe(owner, state)['stale_approvals']:
            raise ConflictError('Approved documents changed; refine and obtain a new decision first.')
        phase = state['phase']
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
            expected_schema = f'tao.project.{phase}/v0.1'
            if any(name not in result.documents or result.documents[name].metadata['schema'] != expected_schema for name in names):
                raise ConflictError('Stage artifacts must use the matching document profile.')
            if phase == 'plan' and doc_review not in ('completed', 'skipped'):
                raise ConflictError('Record the user decision about document review before implementation.')
            state['approvals'][phase] = {'digest': artifact_digest(owner, state, phase), 'decision': decision}
            if phase == 'plan':
                state['doc_review'] = doc_review
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


def dispatch(project, args):
    if args.operation == 'start':
        return start(project, args.slug, args.summary, args.locale, args.decision, args.worktree)
    if args.operation == 'status':
        return {'workflows': status(project, args.change)}
    if args.operation == 'checkpoint':
        return checkpoint(project, args.change, args.expect, load(contained(project.root, args.source)))
    if args.operation == 'advance':
        return advance(project, args.change, args.expect, args.decision, args.doc_review)
    return revise(project, args.change, args.expect, args.phase, args.decision)
