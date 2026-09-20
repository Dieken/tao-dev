"""Bounded project checks and temporary, input-bound execution receipts."""

from datetime import datetime, timezone
import hashlib
from importlib.metadata import distributions
import json
import math
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import subprocess
import sys
import time

from .project import ConfigurationError, contained, mutation_lock, create_file
from tao_messages import Message


def patterns(value):
    """A declared input scope: nonempty, project-relative, no traversal."""
    return (isinstance(value, list) and bool(value)
            and not any(not isinstance(p, str) or not p or Path(p).is_absolute() or '..' in Path(p).parts for p in value))


def policy(project):
    value = project.config.get('verification')
    if value is None:
        return None
    allowed = {'inputs', 'checks', 'budget_seconds', 'reuse_seconds', 'required_reviews', 'require_logs', 'environment', 'usage_reports', 'max_model_tokens', 'max_estimated_usd'}
    if not isinstance(value, dict) or value.keys() - allowed:
        raise ConfigurationError('Invalid verification configuration.')
    inputs = value.get('inputs')
    if not patterns(inputs):
        raise ConfigurationError('verification.inputs must explicitly name project-relative input patterns.')
    checks = value.get('checks')
    if not isinstance(checks, list) or not checks:
        raise ConfigurationError('Configure at least one authorized verification check.')
    seen = set()
    for check in checks:
        if not isinstance(check, dict) or check.keys() - {'id', 'argv', 'timeout_seconds', 'metrics', 'inputs'}:
            raise ConfigurationError('Invalid check definition.')
        name = check.get('id', '')
        if not isinstance(name, str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', name) or name in seen:
            raise ConfigurationError('Check IDs must be unique lowercase words separated by hyphens.')
        seen.add(name)
        argv = check.get('argv')
        if not isinstance(argv, list) or not argv or any(not isinstance(s, str) or not s or '\0' in s for s in argv):
            raise ConfigurationError('Check argv must be a nonempty argument array; no implicit shell.')
        if 'inputs' in check and not patterns(check['inputs']):
            raise ConfigurationError('Check inputs must name project-relative input patterns; omit the key to use the whole policy scope.')
        metric = check.get('metrics')
        if metric is not None:
            if not isinstance(metric, dict) or set(metric) != {'format', 'path'} or metric['format'] not in ('coverage-json', 'ruff-json') or not isinstance(metric['path'], str):
                raise ConfigurationError('Metrics require format coverage-json or ruff-json and an output path.')
            output = contained(project.root, metric['path']).resolve()
            if not output.is_relative_to(project.output('temporary').resolve()):
                raise ConfigurationError('Metric outputs must be inside the configured temporary directory.')
        if type(check.get('timeout_seconds', 60)) is not int or check.get('timeout_seconds', 60) <= 0:
            raise ConfigurationError('Check timeout must be a positive integer.')
    for key, default in [('budget_seconds', 300), ('reuse_seconds', 3600)]:
        if type(value.get(key, default)) is not int or value.get(key, default) < 0:
            raise ConfigurationError(Message('{arg0} must be a nonnegative integer.', key))
    for key in ('required_reviews', 'environment', 'usage_reports'):
        if not isinstance(value.get(key, []), list) or any(not isinstance(s, str) or not s for s in value.get(key, [])):
            raise ConfigurationError(Message('{arg0} must be a string array.', key))
    reviews = value.get('required_reviews', [])
    if len(set(reviews)) != len(reviews) or any(not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', name) for name in reviews):
        raise ConfigurationError('Review IDs must be unique lowercase words separated by hyphens.')
    reports = value.get('usage_reports', [])
    if len(reports) != len({str(contained(project.root, name).resolve()) for name in reports}):
        raise ConfigurationError('Usage report paths must be unique.')
    for name in reports:
        if Path(name).is_absolute():
            raise ConfigurationError('Usage reports must use project-relative paths.')
        contained(project.root, name)
    for key in ('max_model_tokens', 'max_estimated_usd'):
        if key in value and (type(value[key]) not in (int, float) or not math.isfinite(value[key]) or value[key] < 0):
            raise ConfigurationError(Message('{arg0} must be a finite nonnegative number.', key))
    if type(value.get('require_logs', False)) is not bool:
        raise ConfigurationError('require_logs must be boolean.')
    return value


def digest_json(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def file_digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def matched(project, declared):
    """Files a declared input scope actually resolves to right now."""
    paths = set()
    temporary = project.output('temporary').resolve()
    for pattern in declared:
        for path in project.root.glob(pattern):
            contained(project.root, path)
            if path.is_file() and not path.resolve().is_relative_to(temporary) and not {'.git', '__pycache__'} & set(path.relative_to(project.root).parts):
                paths.add(path)
    return paths


def combined(project, paths, digests):
    """Keep only a combined digest, never a persistent per-file inventory."""
    fingerprint = hashlib.sha256()
    for path in sorted(paths):
        if path not in digests:
            digests[path] = file_digest(path)
        fingerprint.update(path.relative_to(project.root).as_posix().encode() + b'\0')
        fingerprint.update(digests[path].encode() + b'\0')
    return fingerprint.hexdigest()


def scopes(project, config, paths, allowed, digests):
    """A digest per check: its own declared scope, or the whole policy scope.

    A declaration may only narrow, so it is validated against the whole policy
    scope; `paths` then decides what actually contributes a digest, which is
    the policy scope minus whatever the caller excluded.
    """
    whole = combined(project, paths, digests)
    result = {}
    for check in config['checks']:
        declared = check.get('inputs')
        if declared is None:
            result[check['id']] = whole
            continue
        subset = matched(project, declared)
        outside = sorted(path.relative_to(project.root).as_posix() for path in subset - allowed)
        if outside:
            raise ConfigurationError(Message(
                'Check {arg0} declares inputs outside verification.inputs: {arg1}.', check['id'], ', '.join(outside[:5])))
        contributing = subset & paths
        if not contributing:
            raise ConfigurationError(Message('Check {arg0} matched no inputs; an empty scope cannot pass.', check['id']))
        result[check['id']] = combined(project, contributing, digests)
    return whole, result


def snapshot(project, config, exclude=()):
    """`exclude` drops project-relative paths a caller declared in advance as
    its own new outputs, so writing them cannot change what was examined. Only
    review binding passes it; a check receipt binds the whole input scope."""
    allowed = matched(project, config['inputs'])
    config_path = contained(project.root, ".tao/config.toml")
    if config_path.is_file():
        allowed.add(config_path)
    excluded = {contained(project.root, name).resolve() for name in exclude}
    paths = {path for path in allowed if path.resolve() not in excluded}
    if not paths:
        raise ConfigurationError('No verification inputs matched; an empty scope cannot pass.')
    digests = {}
    source_digest, check_digests = scopes(project, config, paths, allowed, digests)
    runtime = {p.name: file_digest(p) for p in Path(__file__).parent.glob('*.py')}
    executables = {}
    for check in config['checks']:
        program = check['argv'][0]
        resolved = str((project.root / program).resolve()) if '/' in program and not Path(program).is_absolute() else shutil.which(program)
        executables[check['id']] = {'path': resolved, 'sha256': file_digest(Path(resolved)) if resolved and Path(resolved).is_file() else None}
    environment = {'python': sys.version, 'platform': platform.platform(),
                   'packages': sorted((d.metadata['Name'], d.version) for d in distributions()),
                   'variables': {k: os.environ.get(k) for k in ['PATH', 'LANG', 'LC_ALL', *config.get('environment', [])]},
                   'executables': executables, 'runtime': runtime}
    result = {'source_digest': source_digest, 'input_count': len(paths), 'check_digests': check_digests,
              'policy_digest': digest_json(project.config), 'environment_digest': digest_json(environment),
              'input_ref': None, 'vcs_consistency': 'unavailable'}
    if shutil.which('git'):
        def git(*args):
            try:
                p = subprocess.run(['git', '-C', str(project.root), *args], capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=5)
            except (OSError, subprocess.TimeoutExpired):
                return None
            return p.stdout.strip() if p.returncode == 0 else None
        # Git reports a posix path even on Windows, and a temporary root may
        # arrive in its short form, so compare resolved paths, not strings.
        toplevel = git('rev-parse', '--show-toplevel')
        if toplevel and Path(toplevel).resolve() == project.root.resolve():
            revision = git('rev-parse', 'HEAD')
            state = git('status', '--porcelain', '--untracked-files=all')
            result['input_ref'] = 'git:' + revision if revision else None
            result['vcs_consistency'] = 'unavailable' if state is None or not revision else 'clean' if state == '' else 'dirty'
    result['fingerprint'] = digest_json({key: result[key] for key in ('source_digest', 'policy_digest', 'environment_digest')})
    return result


def receipt_path(project):
    return project.output('temporary', 'verification/latest.json')


def evidence(project, config, current=None):
    path = receipt_path(project)
    if not path.is_file():
        return {'state': 'missing', 'logs_available': False}
    try:
        saved = json.loads(path.read_text(encoding='utf-8'))
        if saved.get('receipt_version') != 2 or not isinstance(saved.get('checks'), list):
            raise ValueError('unsupported receipt')
        expected = {row['id']: row['argv'] for row in config['checks']}
        observed = {row['id']: row['argv'] for row in saved['checks']}
        if observed != expected or len(saved['checks']) != len(expected):
            raise ValueError('receipt check set mismatch')
        if saved['status'] == 'passed' and any(row['status'] != 'passed' or row['exit_code'] != 0 for row in saved['checks']):
            raise ValueError('inconsistent check outcome')
        for stamp in [saved['recorded_epoch'], *(row.get('recorded_epoch') for row in saved['checks'])]:
            if type(stamp) not in (int, float) or not math.isfinite(stamp) or stamp > time.time() + 5:
                raise ValueError('invalid receipt timestamp')
        logs = all(contained(project.root, row['log']).is_file() for row in saved['checks'] if row.get('log'))
        now = current or snapshot(project, config)
        # A carried row was executed earlier than this receipt was written, so
        # each row ages from its own execution; refreshing the receipt after an
        # unrelated input change must not present a stale execution as fresh.
        limit = config.get('reuse_seconds', 3600)
        expired = sorted(row['id'] for row in saved['checks'] if time.time() - row['recorded_epoch'] > limit)
        if saved['inputs']['fingerprint'] != now['fingerprint']:
            state = 'stale'
        elif saved['status'] != 'passed':
            state = 'failed' if saved['status'] == 'failed' else saved['status']
        elif expired or time.time() - saved['recorded_epoch'] > limit:
            state = 'expired'
        elif config.get('require_logs', False) and not logs:
            state = 'materials-missing'
        else:
            state = 'reusable'
        return {'state': state, 'logs_available': logs, 'expired_checks': expired,
                'receipt': path.relative_to(project.root).as_posix(), 'saved': saved}
    except (ValueError, KeyError, TypeError, OSError):
        return {'state': 'invalid', 'logs_available': False}


def carried(project, config, current, existing):
    """Previous rows still standing on their own scope, tools and freshness.

    Only rows of a receipt the reader could interpret qualify: a corrupted
    cache is re-run, never mined for the parts that still look plausible.
    Policy and environment changes invalidate every row, because a
    declaration narrows which sources a check watches, never which toolchain
    produced its result.
    """
    saved = existing['saved'] if existing['state'] not in ('missing', 'invalid') else None
    if not saved:
        return {}
    if saved['inputs']['policy_digest'] != current['policy_digest'] or saved['inputs']['environment_digest'] != current['environment_digest']:
        return {}
    limit = config.get('reuse_seconds', 3600)
    now = time.time()
    rows = {}
    for row in saved['checks']:
        if row['status'] != 'passed' or now - row['recorded_epoch'] > limit:
            continue
        if row.get('inputs_digest') != current['check_digests'].get(row['id']):
            continue
        if config.get('require_logs', False) and not (row.get('log') and contained(project.root, row['log']).is_file()):
            continue
        rows[row['id']] = row
    return rows


def execute(project, config):
    with mutation_lock(project):
        before = snapshot(project, config)
        existing = evidence(project, config, before)
        if existing['state'] == 'reusable':
            return existing['saved'] | {'reused': True, 'logs_available': existing['logs_available']}
        start = time.monotonic()
        directory = project.output('temporary', 'verification')
        directory.mkdir(parents=True, exist_ok=True)
        rows = []
        previous = carried(project, config, before, existing)
        for check in config['checks']:
            prior = previous.get(check['id'])
            if prior is not None and prior.get('argv') == check['argv']:
                # Keep the original elapsed time and execution moment; this run
                # did not produce them and must not claim them as its own.
                rows.append(prior | {'reused': True})
                continue
            remaining = config.get('budget_seconds', 300) - (time.monotonic() - start)
            row = {'id': check['id'], 'argv': check['argv'], 'status': 'not_run', 'exit_code': None,
                   'elapsed_seconds': 0, 'log': None, 'reused': False,
                   'inputs_digest': before['check_digests'][check['id']], 'recorded_epoch': time.time()}
            if remaining <= 0:
                row['reason'] = 'budget-exhausted'
                rows.append(row)
                continue
            log = directory / (str(time.time_ns()) + '-' + check['id'] + '.log')
            row['log'] = log.relative_to(project.root).as_posix()
            began = time.monotonic()
            try:
                metric = check.get('metrics')
                if metric:
                    metric_path = contained(project.root, metric['path'])
                    metric_path.parent.mkdir(parents=True, exist_ok=True)
                    metric_path.unlink(missing_ok=True)
                with log.open('x', encoding='utf-8') as stream:
                    process = subprocess.Popen(check['argv'], cwd=project.root, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
                    try:
                        process.wait(timeout=min(remaining, check.get('timeout_seconds', 60)))
                        row.update(status='passed' if process.returncode == 0 else 'failed', exit_code=process.returncode)
                    except subprocess.TimeoutExpired:
                        if os.name == 'posix':
                            os.killpg(process.pid, signal.SIGKILL)
                        else:
                            process.kill()
                        process.wait()
                        row.update(reason='timeout', exit_code=process.returncode)
            except OSError as exc:
                row['reason'] = str(exc)
            if check.get('metrics') and row['status'] in ('passed', 'failed'):
                try:
                    value = json.loads(contained(project.root, check['metrics']['path']).read_text(encoding='utf-8'))
                    if check['metrics']['format'] == 'coverage-json':
                        totals = value['totals']
                        percent = totals['percent_covered']
                        if type(percent) not in (int, float) or not math.isfinite(percent) or not 0 <= percent <= 100:
                            raise ValueError('invalid coverage percentage')
                        row['metrics'] = {k: totals[k] for k in ('percent_covered', 'covered_lines', 'num_statements', 'covered_branches', 'num_branches') if k in totals}
                    else:
                        if not isinstance(value, list) or any(not isinstance(d, dict) or 'code' not in d for d in value):
                            raise ValueError('invalid Ruff diagnostics')
                        row['metrics'] = {'diagnostics': len(value)}
                except (OSError, ValueError, KeyError, TypeError) as exc:
                    row.update(status='not_run', reason='Required metric output unavailable or invalid: ' + str(exc))
            row['elapsed_seconds'] = round(time.monotonic() - began, 6)
            rows.append(row)
        after = snapshot(project, config)
        status = 'stale' if before['fingerprint'] != after['fingerprint'] else 'not_run' if any(r['status'] == 'not_run' for r in rows) else 'failed' if any(r['status'] == 'failed' for r in rows) else 'passed'
        receipt = {'receipt_version': 2, 'recorded_at': datetime.now(timezone.utc).isoformat(),
                   'recorded_epoch': time.time(), 'inputs': before, 'status': status,
                   'checks': rows, 'elapsed_seconds': round(time.monotonic() - start, 6),
                   'budget_seconds': config.get('budget_seconds', 300), 'reused': False,
                   'cost': {'billed_usd': None, 'model_tokens': None, 'source': 'no model invoked by verification'}}
        latest = receipt_path(project)
        pending = directory / ('receipt-' + str(time.time_ns()) + '.json')
        create_file(project.root, pending, json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
        os.replace(pending, latest)
        return receipt
