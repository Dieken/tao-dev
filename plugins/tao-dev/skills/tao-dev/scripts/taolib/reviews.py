"""Input-bound review attestations; imports never invoke a model or grant authority."""

from datetime import datetime, timezone
import json
from pathlib import Path
import re

from .project import ConfigurationError, ConflictError, contained, mutation_lock, create_file, replace_file
from .verification import snapshot, file_digest
from .review_sources import decode, confirm_codex


def load(path):
    return decode(path.read_text(encoding='utf-8'))


def fields(value, keys):
    if not isinstance(value, dict) or set(value) != set(keys.split()):
        raise ValueError('Review object has missing or unknown fields.')


def text(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('Review text must be nonempty.')


def binding(project, config, change):
    current = snapshot(project, config)
    return {key: current[key] for key in ('source_digest', 'policy_digest')} | {'change': change}


def validate(value):
    fields(value, 'schema requirement binding input_ref recorded_at author reviewer source summary findings limitations')
    if value['schema'] != 'tao.review/v0.1':
        raise ValueError('Unsupported review schema.')
    for key in ('requirement', 'input_ref', 'summary'):
        text(value[key])
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', value['requirement']):
        raise ValueError('Invalid review requirement ID.')
    fields(value['binding'], 'source_digest policy_digest change')
    for key in ('source_digest', 'policy_digest'):
        if not isinstance(value['binding'][key], str) or not re.fullmatch('[0-9a-f]{64}', value['binding'][key]):
            raise ValueError('Invalid review input digest.')
    text(value['binding']['change'])
    text(value['recorded_at'])
    stamp = datetime.fromisoformat(value['recorded_at'].replace('Z', '+00:00'))
    if stamp.tzinfo is None or stamp > datetime.now(timezone.utc):
        raise ValueError('Review timestamp must have an offset and must not be in the future.')
    fields(value['author'], 'name context')
    fields(value['reviewer'], 'kind name context model provider')
    for person in (value['author'], value['reviewer']):
        text(person['name'])
        text(person['context'])
    reviewer = value['reviewer']
    if reviewer['context'] == value['author']['context']:
        raise ValueError('An independent review requires a distinct context.')
    if reviewer['kind'] == 'human':
        if reviewer['name'] == value['author']['name'] or reviewer['model'] is not None or reviewer['provider'] is not None:
            raise ValueError('Human review requires a different named reviewer and no model claims.')
    elif reviewer['kind'] == 'model':
        text(reviewer['model'])
        text(reviewer['provider'])
    else:
        raise ValueError('Unsupported reviewer kind.')
    fields(value['source'], 'path sha256 format')
    text(value['source']['path'])
    if Path(value['source']['path']).is_absolute() or '..' in Path(value['source']['path']).parts:
        raise ValueError('Review source must be project-relative.')
    if not isinstance(value['source']['sha256'], str) or not re.fullmatch('[0-9a-f]{64}', value['source']['sha256']):
        raise ValueError('Invalid review source digest.')
    formats = ('human-json',) if reviewer['kind'] == 'human' else ('claude-stream-json', 'codex-exec-jsonl')
    if value['source']['format'] not in formats:
        raise ValueError('Unsupported reviewer source adapter.')
    if not isinstance(value['limitations'], list) or not isinstance(value['findings'], list):
        raise ValueError('Review findings and limitations must be arrays.')
    for limitation in value['limitations']:
        text(limitation)
    seen = set()
    for finding in value['findings']:
        fields(finding, 'id severity location problem disposition rationale')
        for item in finding.values():
            text(item)
        if finding['id'] in seen:
            raise ValueError('Duplicate review finding ID.')
        seen.add(finding['id'])
        if finding['severity'] not in ('blocker', 'suggestion') or finding['disposition'] not in ('open', 'fixed', 'rejected', 'deferred'):
            raise ValueError('Invalid finding severity or disposition.')
    return stamp


def observed_provider(init, result, model):
    providers = {init['apiProvider']} if init.get('apiProvider') else set()
    for key, usage in result.get('modelUsage', {}).items():
        if key == model or usage.get('canonicalModel') == model:
            if usage.get('provider'):
                providers.add(usage['provider'])
    if len(providers) > 1:
        raise ValueError('Client events disagree about the review provider.')
    return next(iter(providers), 'unknown')


def confirm_source(project, value):
    source = contained(project.root, value['source']['path'])
    if file_digest(source) != value['source']['sha256']:
        raise ValueError('Review source digest does not match.')
    conclusion = {key: value[key] for key in ('binding', 'summary', 'findings', 'limitations')}
    if value['source']['format'] == 'human-json':
        if load(source) != conclusion:
            raise ValueError('Human attestation does not match the recorded conclusion.')
        return
    events = [decode(line) for line in source.read_text(encoding='utf-8').splitlines() if line.strip()]
    if value['source']['format'] == 'codex-exec-jsonl':
        confirm_codex(events, value['reviewer'], conclusion)
        return
    results = [event for event in events if event.get('type') == 'result']
    initial = [event for event in events if event.get('type') == 'system' and event.get('subtype') == 'init']
    if len(results) != 1 or len(initial) != 1:
        raise ValueError('A model review requires one observed session and completed result.')
    result, init = results[0], initial[0]
    reviewer = value['reviewer']
    if result.get('is_error') is not False or result.get('subtype') != 'success':
        raise ValueError('The model review did not complete successfully.')
    if init.get('session_id') != reviewer['context'] or result.get('session_id') != reviewer['context']:
        raise ValueError('Reviewer context does not match observed session.')
    models = {event.get('message', {}).get('model') for event in events if event.get('type') == 'assistant'}
    models.update(result.get('modelUsage', {}))
    if reviewer['model'] not in models or reviewer['provider'] != observed_provider(init, result, reviewer['model']):
        raise ValueError('Reviewer model or provider is not supported by client events.')
    observed = result.get('structured_output')
    if observed is None:
        observed = decode(result.get('result', ''))
    if observed != conclusion:
        raise ValueError('Model output does not match the recorded conclusion and dispositions.')


def path_for(project, change, requirement):
    # Only validated requirement names and indexed CHG IDs reach this function.
    return project.output('temporary', f'reviews/{change}/{requirement}.json')


def import_review(project, config, change, source):
    if Path(source).is_absolute():
        raise ConfigurationError('Use a project-relative review path.')
    value = load(contained(project.root, source))
    validate(value)
    if value['requirement'] not in config.get('required_reviews', []):
        raise ConfigurationError('Review does not satisfy a configured requirement.')
    before = binding(project, config, change)
    if value['binding'] != before:
        raise ConflictError('Review inputs are stale or belong to another change.')
    path = path_for(project, change, value['requirement'])
    expected = path.read_bytes() if path.exists() else None
    try:
        confirm_source(project, value)
    except (KeyError, TypeError, AttributeError) as exc:
        raise ConfigurationError('Malformed review source events.') from exc
    with mutation_lock(project):
        if binding(project, config, change) != before:
            raise ConflictError('Review inputs changed during import.')
        encoded = json.dumps(value, ensure_ascii=False, indent=2) + '\n'
        if expected is not None:
            replace_file(project.root, path, encoded, expected)
        else:
            create_file(project.root, path, encoded)
    return {'receipt': path.relative_to(project.root).as_posix(), 'requirement': value['requirement']}


def status(project, config, change):
    if not config or not config.get('required_reviews'):
        return []
    current = binding(project, config, change) if change else None
    rows = []
    for requirement in config['required_reviews']:
        row = {'requirement': requirement, 'state': 'missing'}
        if change:
            path = path_for(project, change, requirement)
            if path.is_file():
                try:
                    value = load(path)
                    stamp = validate(value)
                    if value['requirement'] != requirement:
                        raise ValueError('Review requirement mismatch.')
                    materials = contained(project.root, value['source']['path'])
                    available = materials.is_file() and file_digest(materials) == value['source']['sha256']
                    state = 'satisfied'
                    if value['binding'] != current:
                        state = 'stale'
                    elif (datetime.now(timezone.utc) - stamp).total_seconds() > config.get('reuse_seconds', 3600):
                        state = 'expired'
                    elif any(f['severity'] == 'blocker' and f['disposition'] in ('open', 'deferred') for f in value['findings']):
                        state = 'changes-requested'
                    elif config.get('require_logs', False) and not available:
                        state = 'materials-missing'
                    row.update(state=state, receipt=path.relative_to(project.root).as_posix(), materials_available=available,
                               reviewer=value['reviewer'], summary=value['summary'], findings=value['findings'], limitations=value['limitations'])
                except (ValueError, KeyError, TypeError, AttributeError, OSError):
                    row['state'] = 'invalid'
        rows.append(row)
    return rows
