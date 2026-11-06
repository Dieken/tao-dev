"""Explicit operator limits for authenticated maintenance experiments."""

import math
import os


def budget_limit(value):
    """`none` removes the CLI fee threshold only when explicitly selected."""
    if str(value).strip().lower() == 'none':
        return None
    budget = float(value)
    if not math.isfinite(budget) or budget <= 0:
        raise ValueError('Claude budget must be positive and finite, or none.')
    return budget


def claude_budget(default):
    return budget_limit(os.environ.get('TAO_CLAUDE_MAX_BUDGET_USD', str(default)))


def model_timeout():
    try:
        seconds = int(os.environ.get('TAO_ACCEPTANCE_MODEL_TIMEOUT', '600'))
    except ValueError as exc:
        raise ValueError('TAO_ACCEPTANCE_MODEL_TIMEOUT must be a positive integer.') from exc
    if seconds <= 0:
        raise ValueError('TAO_ACCEPTANCE_MODEL_TIMEOUT must be a positive integer.')
    return seconds
