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


def policy(project):
    value = project.config.get('verification')
    if value is None:
        return None
    allowed = {'inputs', 'checks', 'budget_seconds', 'reuse_seconds', 'required_reviews', 'require_logs', 'environment', 'usage_reports', 'max_model_tokens', 'max_estimated_usd'}
    if not isinstance(value, dict) or value.keys() - allowed:
        raise ConfigurationError('Invalid verification configuration.')
    inputs = value.get('inputs')
    if not isinstance(inputs, list) or not inputs or any(not isinstance(p, str) or not p or Path(p).is_absolute() or '..' in Path(p).parts for p in inputs):
        raise ConfigurationError('verification.inputs must explicitly name project-relative input patterns.')
    checks = value.get('checks')
    if not isinstance(checks, list) or not checks:
        raise ConfigurationError('Configure at least one authorized verification check.')
    seen = set()
    for check in checks:
        if not isinstance(check, dict) or check.keys() - {'id', 'argv', 'timeout_seconds', 'metrics'}:
            raise ConfigurationError('Invalid check definition.')
        name = check.get('id', '')
        if not isinstance(name, str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', name) or name in seen:
            raise ConfigurationError('Check IDs must be unique lowercase words separated by hyphens.')
        seen.add(name)
        argv = check.get('argv')
        if not isinstance(argv, list) or not argv or any(not isinstance(s, str) or not s or '\0' in s for s in argv):
            raise ConfigurationError('Check argv must be a nonempty argument array; no implicit shell.')
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
            raise ConfigurationError(f'{key} must be a nonnegative integer.')
    for key in ('required_reviews', 'environment', 'usage_reports'):
        if not isinstance(value.get(key, []), list) or any(not isinstance(s, str) or not s for s in value.get(key, [])):
            raise ConfigurationError(f'{key} must be a string array.')
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
            raise ConfigurationError(f'{key} must be a finite nonnegative number.')
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


def snapshot(project, config):
    paths = set()
    temporary = project.output('temporary').resolve()
    for pattern in config['inputs']:
        for path in project.root.glob(pattern):
            contained(project.root, path)
            if path.is_file() and not path.resolve().is_relative_to(temporary) and not {'.git', '__pycache__'} & set(path.relative_to(project.root).parts):
                paths.add(path)
    if not paths:
        raise ConfigurationError('No verification inputs matched; an empty scope cannot pass.')
    config_path = contained(project.root, ".tao/config.toml")
    if config_path.is_file():
        paths.add(config_path)
    fingerprint = hashlib.sha256()
    # Keep only a combined digest, never a persistent per-file inventory.
    for path in sorted(paths):
        fingerprint.update(path.relative_to(project.root).as_posix().encode() + b'\0')
        fingerprint.update(file_digest(path).encode() + b'\0')
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
    result = {'source_digest': fingerprint.hexdigest(), 'input_count': len(paths),
              'policy_digest': digest_json(project.config), 'environment_digest': digest_json(environment),
              'input_ref': None, 'vcs_consistency': 'unavailable'}
    if shutil.which('git'):
        def git(*args):
            try:
                p = subprocess.run(['git', '-C', str(project.root), *args], capture_output=True, text=True, timeout=5)
            except (OSError, subprocess.TimeoutExpired):
                return None
            return p.stdout.strip() if p.returncode == 0 else None
        if git('rev-parse', '--show-toplevel') == str(project.root):
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
        if saved.get('receipt_version') != 1 or not isinstance(saved.get('checks'), list):
            raise ValueError('unsupported receipt')
        expected = {row['id']: row['argv'] for row in config['checks']}
        observed = {row['id']: row['argv'] for row in saved['checks']}
        if observed != expected or len(saved['checks']) != len(expected):
            raise ValueError('receipt check set mismatch')
        if saved['status'] == 'passed' and any(row['status'] != 'passed' or row['exit_code'] != 0 for row in saved['checks']):
            raise ValueError('inconsistent check outcome')
        if type(saved['recorded_epoch']) not in (int, float) or not math.isfinite(saved['recorded_epoch']) or saved['recorded_epoch'] > time.time() + 5:
            raise ValueError('invalid receipt timestamp')
        logs = all(contained(project.root, row['log']).is_file() for row in saved['checks'] if row.get('log'))
        now = current or snapshot(project, config)
        if saved['inputs']['fingerprint'] != now['fingerprint']:
            state = 'stale'
        elif saved['status'] != 'passed':
            state = 'failed' if saved['status'] == 'failed' else saved['status']
        elif time.time() - saved['recorded_epoch'] > config.get('reuse_seconds', 3600):
            state = 'expired'
        elif config.get('require_logs', False) and not logs:
            state = 'materials-missing'
        else:
            state = 'reusable'
        return {'state': state, 'logs_available': logs, 'receipt': path.relative_to(project.root).as_posix(), 'saved': saved}
    except (ValueError, KeyError, TypeError, OSError):
        return {'state': 'invalid', 'logs_available': False}


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
        for check in config['checks']:
            remaining = config.get('budget_seconds', 300) - (time.monotonic() - start)
            row = {'id': check['id'], 'argv': check['argv'], 'status': 'not_run', 'exit_code': None, 'elapsed_seconds': 0, 'log': None}
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
        receipt = {'receipt_version': 1, 'recorded_at': datetime.now(timezone.utc).isoformat(),
                   'recorded_epoch': time.time(), 'inputs': before, 'status': status,
                   'checks': rows, 'elapsed_seconds': round(time.monotonic() - start, 6),
                   'budget_seconds': config.get('budget_seconds', 300), 'reused': False,
                   'cost': {'billed_usd': None, 'model_tokens': None, 'source': 'no model invoked by verification'}}
        latest = receipt_path(project)
        pending = directory / ('receipt-' + str(time.time_ns()) + '.json')
        create_file(project.root, pending, json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
        os.replace(pending, latest)
        return receipt
