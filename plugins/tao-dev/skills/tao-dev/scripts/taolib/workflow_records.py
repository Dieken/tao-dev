"""Small, versioned project records; local execution state is never a backup."""
from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path
import uuid
import re

import yaml

from .project import ConfigurationError, ConflictError, contained, create_file, replace_file
from .verification import digest_json, file_digest
from .frontmatter import load_frontmatter

SCHEMA = 'tao.project.workflow/v0.1'
LIFECYCLES = {'active', 'paused', 'completed', 'cancelled', 'unknown'}
PHASES = {'spec', 'design', 'plan', 'implement', 'review', 'finish', 'complete'}
FIELDS = {'schema', 'id', 'title', 'locale', 'status', 'created', 'updated', 'change',
          'slug', 'summary', 'record_revision', 'lifecycle', 'phase', 'plan_path',
          'artifacts', 'approvals', 'baseline', 'review_batches', 'closure', 'provenance', 'last_operation_id'}


def path(project, identity):
    from .workflows import state_path
    state_path(project, identity)
    return contained(project.root, Path(project.paths['workflows']) / (identity + '.md'))


def validate_record(data):
    if not isinstance(data, dict) or data.keys() - FIELDS or FIELDS - {'updated'} - data.keys():
        raise ConfigurationError('Invalid workflow record fields.')
    for key in ('id', 'title', 'locale', 'status', 'created', 'change', 'slug', 'summary', 'plan_path', 'last_operation_id'):
        if not isinstance(data[key], str) or not data[key].strip():
            raise ConfigurationError('Invalid workflow record fields.')
    for key, prefix in (('id', 'DOC'), ('change', 'CHG')):
        if not re.fullmatch(prefix + r'_[0-9]{8}_[0-9A-HJKMNP-TV-Z]{16}', data[key]):
            raise ConfigurationError('Invalid workflow record fields.')
    if data['schema'] != SCHEMA or not isinstance(data['lifecycle'], str) or data['lifecycle'] not in LIFECYCLES or not isinstance(data['phase'], str) or data['phase'] not in PHASES:
        raise ConfigurationError('Invalid workflow record lifecycle or phase.')
    if type(data['record_revision']) is not int or data['record_revision'] < 1:
        raise ConfigurationError('Invalid workflow record revision.')
    for key in ('artifacts', 'approvals', 'review_batches', 'provenance'):
        if not isinstance(data[key], dict):
            raise ConfigurationError('Invalid workflow record mapping: ' + key)
    if data['baseline'] is not None and not isinstance(data['baseline'], dict):
        raise ConfigurationError('Invalid workflow baseline.')
    if isinstance(data['baseline'], dict) and (set(data['baseline']) != {'branch', 'base_commit', 'base_branch'} or any(data['baseline'][k] is not None and not isinstance(data['baseline'][k], str) for k in data['baseline'])):
        raise ConfigurationError('Invalid workflow baseline.')
    if data['provenance'].keys() - {'kind', 'unknown_fields', 'source_digest', 'source_revision', 'lifecycle_decision', 'review_budget_unknown'}:
        raise ConfigurationError('Invalid workflow record fields.')
    if 'review_budget_unknown' in data['provenance'] and (not isinstance(data['provenance']['review_budget_unknown'], list) or any(k not in ('docs', 'code') for k in data['provenance']['review_budget_unknown'])):
        raise ConfigurationError('Invalid workflow review batch.')
    if data['closure'] is not None and not isinstance(data['closure'], dict):
        raise ConfigurationError('Invalid workflow closure.')
    if 'unknown_fields' in data['provenance'] and (not isinstance(data['provenance']['unknown_fields'], list) or any(not isinstance(k, str) for k in data['provenance']['unknown_fields'])):
        raise ConfigurationError('Invalid workflow record fields.')
    if data['lifecycle'] == 'unknown' and (data['provenance'].get('kind') != 'legacy'
            or 'lifecycle' not in data['provenance'].get('unknown_fields', [])):
        raise ConfigurationError('Unknown lifecycle requires legacy provenance.')
    if data['lifecycle'] in {'completed', 'cancelled'} and not data['closure']:
        raise ConfigurationError('Closed workflow requires a closure record.')
    if data['closure']:
        closure = data['closure']
        required = {'evidence', 'unfinished', 'result', 'decision', 'recorded_at'}
        if required - closure.keys() or closure.keys() - required - {'operation_id'} or closure['result'] != data['lifecycle'] or any(not isinstance(closure[k], str) or not closure[k] for k in ('decision', 'recorded_at')):
            raise ConfigurationError('Invalid workflow closure.')
        for key in ('evidence', 'unfinished'):
            if not isinstance(closure[key], list) or any(not isinstance(v, str) or not v for v in closure[key]):
                raise ConfigurationError('Invalid workflow closure.')
    if data['lifecycle'] == 'completed' and data['phase'] != 'complete':
        raise ConfigurationError('Completed lifecycle requires complete phase.')
    for role, names in data['artifacts'].items():
        if role not in {'spec', 'design', 'plan'} or not isinstance(names, list) or any(not isinstance(n, str) or not n.startswith('DOC_') for n in names) or len(names) != len(set(names)):
            raise ConfigurationError('Invalid workflow artifact identities.')
    for phase, approval in data['approvals'].items():
        if phase not in {'spec', 'design', 'plan'} or not isinstance(approval, dict) or not isinstance(approval.get('digest'), str) or not isinstance(approval.get('decision'), str) or set(approval) - {'digest', 'decision', 'algorithm'} or not re.fullmatch('[0-9a-f]{64}', approval['digest']) or approval.get('algorithm', 'path-v0') not in ('path-v0', 'doc-v1'):
            raise ConfigurationError('Invalid workflow approval.')
    for kind, batch in data['review_batches'].items():
        if kind not in {'docs', 'code'}:
            raise ConfigurationError('Invalid workflow review batch.')
        validate_batch(batch, kind, data['change'])
    return data


def validate_batch(batch, kind, change=None):
    required = {'id', 'phase', 'decision', 'started_at', 'max_rounds', 'runs', 'round_decisions'}
    optional = {'budget_seconds', 'history'}
    if (not isinstance(batch, dict) or required - batch.keys() or batch.keys() - required - optional
            or any(not isinstance(batch[k], str) or not batch[k] for k in ('id', 'phase', 'decision', 'started_at'))
            or type(batch['max_rounds']) is not int or batch['max_rounds'] < 1
            or not isinstance(batch['runs'], list) or not isinstance(batch['round_decisions'], list)):
        raise ConfigurationError('Invalid workflow review batch.')
    for decision in batch['round_decisions']:
        if not isinstance(decision, dict) or set(decision) != {'before', 'after', 'decision'} or any(type(decision[k]) is not int or decision[k] < 1 for k in ('before', 'after')) or not isinstance(decision['decision'], str):
            raise ConfigurationError('Invalid workflow review batch.')
    seen = set()
    for run in batch['runs']:
        required_run = {'id', 'round', 'started_at', 'outcome', 'mode', 'reviewers', 'decision', 'request', 'recovered_context'}
        optional_run = {'inputs', 'reports', 'summary', 'ended_at', 'evidence_boundary', 'input_error', 'budget'}
        if (not isinstance(run, dict) or required_run - run.keys() or run.keys() - required_run - optional_run
                or any(not isinstance(run[k], str) or not run[k] for k in ('id', 'started_at', 'outcome', 'mode', 'decision'))
                or type(run['round']) is not int or run['round'] < 1 or run['round'] in seen
                or type(run['reviewers']) is not int or not 1 <= run['reviewers'] <= 3
                or run['mode'] not in {'serial', 'parallel'} or run['outcome'] not in {'running', 'passed', 'changes-requested', 'failed', 'stale'}
                or run['recovered_context'] is not True):
            raise ConfigurationError('Invalid workflow review attempt.')
        seen.add(run['round'])
        request = run['request']
        required_request = {'schema', 'change', 'scope', 'kind', 'base_commit', 'target_commit', 'include', 'input_digest', 'excluded_record_directories'}
        if (not isinstance(request, dict) or required_request - request.keys() or request.keys() - required_request - {'output_files'}
                or request.get('schema') != 'tao.review-scope/v0.1' or request.get('kind') != kind
                or not isinstance(request.get('scope'), str) or request['scope'] not in {'feature', 'project'}
                or (change is not None and request.get('change') != change)
                or not isinstance(request.get('change'), str) or not re.fullmatch(r'CHG_[0-9]{8}_[0-9A-HJKMNP-TV-Z]{16}', request['change'])
                or any(request[k] is not None and (not isinstance(request[k], str) or not re.fullmatch('[0-9a-f]{40}|[0-9a-f]{64}', request[k])) for k in ('base_commit', 'target_commit'))
                or not isinstance(request.get('input_digest'), str) or not re.fullmatch('[0-9a-f]{64}', request['input_digest'])):
            raise ConfigurationError('Invalid workflow review attempt.')
        for key in ('include', 'excluded_record_directories', 'output_files'):
            if key in request and (not isinstance(request[key], list) or any(not isinstance(v, str) or not v for v in request[key])):
                raise ConfigurationError('Invalid workflow review attempt.')
        if run['outcome'] not in {'running'}:
            if not isinstance(run.get('reports'), list) or not isinstance(run.get('summary'), str) or not isinstance(run.get('ended_at'), str):
                raise ConfigurationError('Invalid workflow review attempt.')
            for report in run['reports']:
                if not isinstance(report, dict) or report.keys() - {'path', 'digest', 'validated'} or not isinstance(report.get('path'), str) or not isinstance(report.get('digest'), str):
                    raise ConfigurationError('Invalid workflow review attempt.')
    history = batch.get('history', [])
    if not isinstance(history, list):
        raise ConfigurationError('Invalid workflow review batch.')
    for previous in history:
        if not isinstance(previous, dict) or 'history' in previous:
            raise ConfigurationError('Invalid workflow review batch.')
        validate_batch(previous, kind, change)


def read(project, identity):
    target = path(project, identity)
    if not target.exists():
        return None
    try:
        content = target.read_text(encoding='utf-8')
        if not content.startswith('---\n'):
            raise ValueError('frontmatter')
        data = load_frontmatter(content)
        validate_record(data)
        if data['change'] != identity:
            raise ValueError('identity')
        return data
    except (ValueError, IndexError, yaml.YAMLError) as exc:
        raise ConfigurationError('Invalid workflow record: ' + str(target)) from exc


def identities(project):
    directory = contained(project.root, project.paths['workflows'])
    return [p.stem for p in sorted(directory.glob('CHG_*.md'))]


def artifact_ids(project, state):
    # Parse metadata directly: validation must not recursively read local state.
    result = {}
    for role, names in state.get('artifacts', {}).items():
        result[role] = []
        for name in names:
            target = contained(project.root, name)
            try:
                data = load_frontmatter(target.read_text(encoding='utf-8'))
                identity = data['id']
                if not isinstance(identity, str) or not identity.startswith('DOC_'):
                    raise ValueError()
            except (OSError, ValueError, IndexError, TypeError, KeyError, yaml.YAMLError) as exc:
                raise ConfigurationError('Cannot bind workflow artifact: ' + name) from exc
            result[role].append(identity)
    return result


def compact_reviews(reviews):
    result = deepcopy(reviews)
    for batch in result.values():
        for run in batch.get('runs', []):
            request = run.get('request', {})
            run['request'] = {k: v for k, v in request.items() if k not in {'context_files', 'index_entries', 'selected_files', 'excluded_files', 'instruction', 'input_bytes'}}
            for key in ('snapshot', 'snapshot_digest', 'index_snapshot', 'index_snapshot_digest'):
                run.pop(key, None)
            run['recovered_context'] = True
    return result


def build(project, state, old=None, provenance=None):
    from .documents import ASSETS
    from .identifiers import new_id
    registry = json.loads((ASSETS / 'document-profiles.json').read_text(encoding='utf-8'))
    # A checkpoint's summary is local execution progress, not a new goal.
    # Later durable events preserve the authoritative record's title/summary.
    data = {'schema': SCHEMA, 'id': old['id'] if old else new_id('DOC', registry, set()),
            'title': old['title'] if old else state['summary'], 'locale': state['locale'], 'status': 'draft', 'created': state['created'],
            'change': state['change'], 'slug': state['slug'], 'summary': old['summary'] if old else state['summary'],
            'record_revision': old['record_revision'] + 1 if old else 1,
            'lifecycle': state.get('lifecycle', 'active'), 'phase': state['phase'],
            'plan_path': state['plan_path'], 'artifacts': artifact_ids(project, state),
            'approvals': deepcopy(state['approvals']), 'baseline': state.get('git'),
            'review_batches': compact_reviews(state.get('reviews', {})), 'closure': state.get('closure'),
            'provenance': deepcopy(provenance if provenance is not None else (old or {}).get('provenance', {})),
            'last_operation_id': uuid.uuid4().hex}
    if 'review_budget_unknown' in state:
        data['provenance']['review_budget_unknown'] = state['review_budget_unknown']
    for kind, history in state.get('review_history', {}).items():
        if kind in data['review_batches']:
            data['review_batches'][kind]['history'] = [compact_reviews({kind: b})[kind] for b in history]
    if data['closure'] and data['lifecycle'] in ('completed', 'cancelled'):
        data['provenance']['unknown_fields'] = [k for k in data['provenance'].get('unknown_fields', []) if k != 'lifecycle']
        data['provenance']['lifecycle_decision'] = data['closure']['decision']
    return validate_record(data)


def render(data):
    return ('---\n' + yaml.safe_dump(data, allow_unicode=True, sort_keys=False) + '---\n\n# ' + data['title'] +
            '\n\n<!-- tao:section overview -->\n## Overview\n\n' + data['summary'] +
            '\n\n<!-- tao:section decisions -->\n## Decisions\n\nStructured metadata records decisions and their bindings.\n'
            '\n<!-- tao:section closure -->\n## Closure\n\nThe lifecycle and closure metadata are authoritative.\n')


def write(project, data, before=None):
    target = path(project, data['change'])
    relative = target.relative_to(project.root)
    # Match configured globs even before the file exists.
    if (not any(project.matches_file(relative, p) for p in project.includes)
            or any(project.matches_file(relative, p) for p in project.excludes)):
        raise ConfigurationError('Workflow record directory is outside managed documents: ' + str(target))
    from .git_workflow import run, context
    if context(project.root) and run(project.root, 'check-ignore', str(relative), required=False):
        raise ConfigurationError('Workflow record must not be ignored: ' + str(target))
    text = render(validate_record(data))
    if before is None:
        create_file(project.root, target, text)
    else:
        replace_file(project.root, target, text, before)
    return {'record_revision': data['record_revision'], 'record_digest': file_digest(target),
            'record_operation': data['last_operation_id']}


def synchronized(project, state, record):
    return (record and state.get('record_revision') == record['record_revision']
            and state.get('record_digest') == file_digest(path(project, state['change'])))


def source_digest(project, state=None):
    rows = [(p.relative_to(project.root).as_posix(), file_digest(p)) for p in project.sources()]
    if state:
        from .workflows import state_path
        rows.append((str(state_path(project, state['change'])), file_digest(state_path(project, state['change']))))
    return digest_json(rows)


def review_contract(content, kind, change=None):
    """Exclude this review's bookkeeping, retaining all domain decisions."""
    if not content.startswith('---\n'):
        return None
    try:
        data = load_frontmatter(content)
        if not isinstance(data, dict) or data.get('schema') != SCHEMA:
            return None
        if change is not None and data.get('change') != change:
            return None
        # The request itself binds the current batch scope. Other batches and
        # approval/lifecycle/domain fields remain part of the reviewed input.
        data = deepcopy(data)
        data.pop('record_revision', None)
        data.pop('last_operation_id', None)
        if kind == 'code' and data.get('phase') in {'implement', 'review', 'finish'}:
            data['phase'] = 'delivery'
        data.get('review_batches', {}).pop(kind, None)
        if 'review_budget_unknown' in data.get('provenance', {}):
            data['provenance']['review_budget_unknown'] = [k for k in data['provenance']['review_budget_unknown'] if k != kind]
        return json.dumps(data, ensure_ascii=False, sort_keys=True)
    except (ValueError, IndexError, TypeError, yaml.YAMLError):
        return None
