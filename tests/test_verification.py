"""Run real bounded check processes against independent project fixtures."""

import json
import sys

import pytest

from test_cli import run
from test_relationships import change, CHG
from test_documents import spec


def configured(root, body='print("checked")', *, timeout=5, budget=20):
    (root / 'docs').mkdir()
    (root / 'docs/spec.md').write_text(spec())
    (root / 'docs/changes/2026-09').mkdir(parents=True)
    (root / 'docs/changes/2026-09/20260914-export.md').write_text(change().replace('- [x]', '- [ ]'))
    (root / 'check.py').write_text(body)
    (root / '.tao').mkdir()
    (root / '.tao/config.toml').write_text(f'''version = 1
[verification]
inputs = ["check.py", "docs/**/*.md"]
budget_seconds = {budget}
reuse_seconds = 3600
[[verification.checks]]
id = "tests"
argv = [{json.dumps(sys.executable)}, "check.py"]
timeout_seconds = {timeout}
''')


def report(root, *arguments):
    p = run(root, *arguments)
    return p.returncode, json.loads(p.stdout)


def test_real_checks_are_partial_and_reused_without_reexecution(tmp_path):
    configured(tmp_path, 'from pathlib import Path\np=Path("tmp/tao/calls")\np.write_text(p.read_text()+"x" if p.exists() else "x")')
    code, first = report(tmp_path, 'verify', '--only', 'code')
    assert code == 0, first
    assert first['coverage'] == 'partial'
    assert first['outputs']['execution']['checks'][0]['status'] == 'passed'
    assert first['outputs']['execution']['checks'][0]['elapsed_seconds'] >= 0
    code, second = report(tmp_path, 'verify', '--only', 'code')
    assert code == 0
    assert second['outputs']['execution']['reused'] is True
    assert (tmp_path / 'tmp/tao/calls').read_text() == 'x'
    assert not list(tmp_path.rglob('inputs.sha256'))


def test_status_detects_changed_and_new_inputs_without_running_checks(tmp_path):
    configured(tmp_path)
    assert report(tmp_path, 'verify', '--only', 'code')[0] == 0
    assert report(tmp_path, 'status')[1]['outputs']['evidence_reusability'] == 'reusable'
    (tmp_path / 'check.py').write_text('raise Exception("changed")')
    status = report(tmp_path, 'status')[1]
    assert status['outputs']['evidence_reusability'] == 'stale'
    assert report(tmp_path, 'verify', '--only', 'code')[0] == 1


def test_mutation_during_check_cannot_produce_valid_evidence(tmp_path):
    configured(tmp_path, 'from pathlib import Path\nPath("check.py").write_text("print(1)")')
    code, result = report(tmp_path, 'verify', '--only', 'code')
    assert code == 1
    assert result['outputs']['execution']['status'] == 'stale'


@pytest.mark.parametrize('body,timeout,budget', [('import time; time.sleep(5)', 1, 10), ('print(1)', 5, 0)])
def test_timeout_or_exhausted_budget_is_not_run(tmp_path, body, timeout, budget):
    configured(tmp_path, body, timeout=timeout, budget=budget)
    code, result = report(tmp_path, 'verify', '--only', 'code')
    assert code == 2
    assert result['outputs']['execution']['checks'][0]['status'] == 'not_run'


def test_missing_executable_and_missing_policy_cannot_pass(tmp_path):
    configured(tmp_path)
    config = tmp_path / '.tao/config.toml'
    config.write_text(config.read_text().replace(json.dumps(sys.executable), '"tao-deliberately-missing-tool"'))
    assert report(tmp_path, 'verify', '--only', 'code')[0] == 2


def test_log_expiry_does_not_reverse_history_or_force_reexecution(tmp_path):
    configured(tmp_path)
    code, result = report(tmp_path, 'verify', '--only', 'code')
    assert code == 0
    log = tmp_path / result['outputs']['execution']['checks'][0]['log']
    log.unlink()
    status = report(tmp_path, 'status')[1]['outputs']
    assert status['evidence_reusability'] == 'reusable'
    assert status['evidence']['logs_available'] is False
    assert report(tmp_path, 'verify', '--only', 'code')[1]['outputs']['execution']['reused']


def test_full_verification_requires_closed_target_tasks(tmp_path):
    configured(tmp_path)
    code, result = report(tmp_path, 'verify', CHG)
    assert code == 1 and result['readiness'] == 'blocked'
    path = tmp_path / 'docs/changes/2026-09/20260914-export.md'
    text = path.read_text().replace('- [ ]', '- [x]')
    path.write_text(text)
    code, result = report(tmp_path, 'verify', CHG)
    assert code == 0, result
    assert result['coverage'] == 'complete'
    assert result['readiness'] == 'checks-satisfied'


def test_dry_run_does_not_execute_or_save_receipts(tmp_path):
    configured(tmp_path)
    code, result = report(tmp_path, 'verify', CHG, '--dry-run')
    assert code == 0, result
    assert result['coverage'] == 'unknown'
    assert not (tmp_path / 'tmp').exists()


def test_new_input_and_required_log_are_not_silently_ignored(tmp_path):
    configured(tmp_path)
    assert report(tmp_path, 'verify', '--only', 'code')[0] == 0
    (tmp_path / 'docs/extra.md').write_text('new untracked input')
    assert report(tmp_path, 'status')[1]['outputs']['evidence_reusability'] == 'stale'


def test_unknown_review_requirements_and_empty_input_scope_fail_closed(tmp_path):
    configured(tmp_path)
    config = tmp_path / '.tao/config.toml'
    config.write_text(config.read_text().replace('[verification]', '[verification]\nrequired_reviews = ["independent"]'))
    code, result = report(tmp_path, 'verify', CHG)
    assert code == 2 and result['readiness'] == 'blocked'


def test_corrupt_or_empty_pass_receipt_is_not_reused(tmp_path):
    configured(tmp_path)
    assert report(tmp_path, 'verify', '--only', 'code')[0] == 0
    receipt = tmp_path / 'tmp/tao/verification/latest.json'
    saved = json.loads(receipt.read_text())
    saved['checks'] = []
    receipt.write_text(json.dumps(saved))
    assert report(tmp_path, 'status')[1]['outputs']['evidence_reusability'] == 'invalid'


def test_policy_can_require_logs_for_reuse(tmp_path):
    configured(tmp_path)
    config = tmp_path / '.tao/config.toml'
    config.write_text(config.read_text().replace('[verification]', '[verification]\nrequire_logs = true'))
    _, result = report(tmp_path, 'verify', '--only', 'code')
    (tmp_path / result['outputs']['execution']['checks'][0]['log']).unlink()
    assert report(tmp_path, 'status')[1]['outputs']['evidence_reusability'] == 'materials-missing'


def test_expiry_and_environment_change_prevent_reuse(tmp_path, monkeypatch):
    configured(tmp_path)
    config = tmp_path / '.tao/config.toml'
    config.write_text(config.read_text().replace('[verification]', '[verification]\nenvironment = ["TAO_TEST_DATASET"]'))
    assert report(tmp_path, 'verify', '--only', 'code')[0] == 0
    monkeypatch.setenv('TAO_TEST_DATASET', 'changed')
    assert report(tmp_path, 'status')[1]['outputs']['evidence_reusability'] == 'stale'
    assert report(tmp_path, 'verify', '--only', 'code')[0] == 0
    receipt = tmp_path / 'tmp/tao/verification/latest.json'
    saved = json.loads(receipt.read_text())
    saved['recorded_epoch'] -= 3601
    receipt.write_text(json.dumps(saved))
    assert report(tmp_path, 'status')[1]['outputs']['evidence_reusability'] == 'expired'


def test_same_vcs_revision_with_dirty_inputs_is_stale(tmp_path):
    import subprocess
    configured(tmp_path)
    def git(*args):
        return subprocess.run(['git', '-C', str(tmp_path), *args], check=True, capture_output=True, text=True)
    git('init')
    (tmp_path / '.gitignore').write_text('tmp/\n')
    git('add', '.')
    git('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-m', 'Fixture')
    _, first = report(tmp_path, 'verify', '--only', 'code')
    assert first['outputs']['execution']['inputs']['vcs_consistency'] == 'clean'
    revision = first['outputs']['execution']['inputs']['input_ref']
    (tmp_path / 'check.py').write_text('print("different")')
    _, second = report(tmp_path, 'verify', '--only', 'code')
    assert second['outputs']['execution']['reused'] is False
    assert second['outputs']['execution']['inputs']['input_ref'] == revision
    assert second['outputs']['execution']['inputs']['vcs_consistency'] == 'dirty'


def test_missing_metric_report_is_not_a_pass_and_report_values_are_observed(tmp_path):
    configured(tmp_path)
    config = tmp_path / '.tao/config.toml'
    config.write_text(config.read_text() + 'metrics = {format="coverage-json", path="tmp/tao/coverage.json"}\n')
    assert report(tmp_path, 'verify', '--only', 'code')[0] == 2
    (tmp_path / 'check.py').write_text('from pathlib import Path\nPath("tmp/tao/coverage.json").write_text(\'{"totals":{"percent_covered":75,"covered_lines":3,"num_statements":4}}\')')
    code, result = report(tmp_path, 'verify', '--only', 'code')
    assert code == 0
    assert result['outputs']['execution']['checks'][0]['metrics']['percent_covered'] == 75


def test_unknown_or_exceeded_model_budget_does_not_start_checks(tmp_path):
    configured(tmp_path, 'from pathlib import Path\nPath("ran").touch()')
    config = tmp_path / '.tao/config.toml'
    config.write_text(config.read_text().replace('[verification]', '[verification]\nmax_model_tokens = 5\nusage_reports = ["tmp/tao/usage.jsonl"]'))
    code, result = report(tmp_path, 'verify', '--only', 'code')
    assert code == 2
    assert not (tmp_path / 'ran').exists()
    (tmp_path / 'tmp/tao').mkdir(parents=True, exist_ok=True)
    (tmp_path / 'tmp/tao/usage.jsonl').write_text(json.dumps({'type':'turn.completed','usage':{'input_tokens':6,'output_tokens':1}})+'\n')
    assert report(tmp_path, 'verify', '--only', 'code')[0] == 1
    assert not (tmp_path / 'ran').exists()


def test_check_cannot_close_tasks_while_full_verification_is_running(tmp_path):
    configured(tmp_path, 'from pathlib import Path\np=Path("docs/changes/2026-09/20260914-export.md")\np.write_text(p.read_text().replace("- [ ]", "- [x]"))')
    config = tmp_path / '.tao/config.toml'
    config.write_text(config.read_text().replace('"check.py", "docs/**/*.md"', '"check.py"'))
    code, result = report(tmp_path, 'verify', CHG)
    assert code == 1 and result['readiness'] == 'blocked'
    assert result['outputs']['documents_changed_during_checks'] is True


def test_committing_identical_inputs_does_not_rerun_checks(tmp_path):
    import subprocess
    configured(tmp_path)
    def git(*args):
        return subprocess.run(['git', '-C', str(tmp_path), *args], check=True, capture_output=True)
    git('init')
    (tmp_path / '.gitignore').write_text('tmp/\n')
    git('add', '.')
    git('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-m', 'Fixture')
    assert report(tmp_path, 'verify', '--only', 'code')[0] == 0
    git('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '--allow-empty', '-m', 'Metadata only')
    assert report(tmp_path, 'status')[1]['outputs']['evidence_reusability'] == 'reusable'
