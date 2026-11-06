"""The authority needed after losing local review execution history."""
from copy import deepcopy
import math

from .project import ConfigurationError
from .verification import digest_json


def invalid():
    raise ConfigurationError('Invalid workflow review batch.')


def validate_limits(limits):
    if limits is None:
        return  # Unknown, not unlimited.
    if (not isinstance(limits, dict) or set(limits) != {'timeout_seconds', 'cost_limit_usd'}
            or type(limits['timeout_seconds']) is not int or limits['timeout_seconds'] < 1):
        invalid()
    cost = limits['cost_limit_usd']
    if cost is not None:
        try:
            valid = type(cost) in (int, float) and math.isfinite(cost) and cost > 0
        except OverflowError:
            valid = False
        if not valid:
            invalid()


def used(series):
    count = series.get('used_rounds', 0)
    if type(count) is not int or count < 0:
        invalid()
    rounds = [r.get('round', 0) for r in series['runs']]
    if any(type(n) is not int or n < 1 for n in rounds):
        invalid()
    return max(count, len(rounds), max(rounds, default=0))


def running(series):
    pending = series.get('pending')
    if pending:
        return pending
    runs = series['runs']
    if runs and runs[-1]['outcome'] == 'running':
        return {key: runs[-1][key] for key in ('id', 'round')}
    return None


def project(reviews):
    controls = {}
    for kind, series in reviews.items():
        decisions = series.get('round_decisions', [])
        controls[kind] = {
            'batch': series['id'], 'phase': series['phase'],
            'used': used(series), 'limit': series['max_rounds'],
            'decision': series.get('control_decision', decisions[-1]['decision'] if decisions else series['decision']),
            'limits': deepcopy(series.get('limits')),
            'in_flight': running(series),
            'local_digest': digest_json(series),
        }
    validate(controls)
    return controls


def validate(controls):
    if not isinstance(controls, dict) or controls.keys() - {'docs', 'code'}:
        invalid()
    active = 0
    for control in controls.values():
        if (not isinstance(control, dict) or set(control) != {
                'batch', 'phase', 'used', 'limit', 'decision', 'limits', 'in_flight', 'local_digest'}
                or any(not isinstance(control[k], str) or not control[k].strip() for k in ('batch', 'decision'))
                or control['phase'] not in ('spec', 'design', 'plan', 'implement', 'review', 'finish', 'complete')
                or type(control['used']) is not int or control['used'] < 0
                or type(control['limit']) is not int or control['limit'] < 1):
            invalid()
        digest = control['local_digest']
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
            invalid()
        validate_limits(control['limits'])
        pending = control['in_flight']
        if pending is not None:
            if (not isinstance(pending, dict) or set(pending) != {'id', 'round'}
                    or not isinstance(pending['id'], str) or not pending['id'].strip()
                    or type(pending['round']) is not int or pending['round'] != control['used']
                    or pending['round'] < 1):
                invalid()
            active += 1
    if active > 1:
        invalid()


def restore(controls):
    validate(controls)
    return {kind: {
        'id': c['batch'], 'phase': c['phase'], 'decision': c['decision'],
        'max_rounds': c['limit'], 'used_rounds': c['used'],
        'limits': deepcopy(c['limits']), 'pending': deepcopy(c['in_flight']),
        'runs': [], 'round_decisions': [],
    } for kind, c in controls.items()}
