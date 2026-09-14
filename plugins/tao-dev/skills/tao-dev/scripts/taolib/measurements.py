"""Normalize observed CLI usage without inferring prices or billed costs."""

import json
import math
from .project import ConfigurationError, contained
from tao_messages import Message


def counters(value, input_key, output_key, cache_keys=()):
    if not isinstance(value, dict) or input_key not in value or output_key not in value:
        raise ConfigurationError('Usage counters are missing or malformed.')
    items = [value[input_key], value[output_key], *(value.get(k, 0) for k in cache_keys)]
    if any(type(n) is not int or n < 0 for n in items):
        raise ConfigurationError('Usage counters must be nonnegative integers.')
    return value[input_key] + sum(value.get(k, 0) for k in cache_keys), value[output_key]


def usage(project, paths):
    runs = []
    for name in paths:
        path = contained(project.root, name)
        try:
            events = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
        except (OSError, ValueError):
            runs.append({'source': name, 'status': 'unknown', 'reason': 'missing or invalid event report'})
            continue
        final = [e for e in events if isinstance(e, dict) and e.get('type') in ('result', 'turn.completed')]
        if not final:
            runs.append({'source': name, 'status': 'unknown', 'reason': 'no completed usage event'})
            continue
        if sum(e['type'] == 'result' for e in final) > 1:
            runs.append({'source': name, 'status': 'unknown', 'reason': 'multiple Claude results may contain cumulative usage'})
            continue
        totals = {'input_tokens': 0, 'output_tokens': 0, 'estimated_usd': 0.0}
        cost_known = True
        for event in final:
            value = event.get('usage', {})
            if event['type'] == 'result':
                # Claude reports uncached, cache-read and cache-create inputs
                # separately. Its cost is a CLI estimate, not an invoice.
                inputs, output = counters(value, 'input_tokens', 'output_tokens', ('cache_read_input_tokens', 'cache_creation_input_tokens'))
                cost = event.get('total_cost_usd')
            else:
                # Codex input_tokens already includes cached_input_tokens.
                inputs, output = counters(value, 'input_tokens', 'output_tokens')
                cost = None
            if event['type'] == 'result' and event.get('modelUsage'):
                if not isinstance(event['modelUsage'], dict):
                    raise ConfigurationError('modelUsage must be an object.')
                models = [counters(m, 'inputTokens', 'outputTokens', ('cacheReadInputTokens', 'cacheCreationInputTokens')) for m in event['modelUsage'].values()]
                inputs, output = sum(m[0] for m in models), sum(m[1] for m in models)
            if type(inputs) is not int or inputs < 0 or type(output) is not int or output < 0:
                raise ConfigurationError(Message('Invalid token counters in {arg0}.', name))
            totals['input_tokens'] += inputs
            totals['output_tokens'] += output
            if cost is None:
                cost_known = False
            elif type(cost) not in (int, float) or not math.isfinite(cost) or cost < 0:
                raise ConfigurationError(Message('Invalid cost counter in {arg0}.', name))
            else:
                totals['estimated_usd'] += cost
        if not cost_known:
            totals['estimated_usd'] = None
        runs.append({'source': name, 'status': 'observed', 'completed_events': len(final), **totals,
                     'billed_usd': None, 'cost_basis': 'CLI-reported estimate; billing unknown'})
    known = bool(runs) and all(r['status'] == 'observed' for r in runs)
    return {'runs': runs,
            'model_tokens': sum(r['input_tokens'] + r['output_tokens'] for r in runs) if known else None,
            'estimated_usd': sum(r['estimated_usd'] for r in runs) if known and all(r['estimated_usd'] is not None for r in runs) else None,
            'billed_usd': None, 'scope': 'explicitly supplied completed CLI reports only; not account-wide usage'}
