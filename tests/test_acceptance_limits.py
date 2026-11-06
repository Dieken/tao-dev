"""Operators select paid experiment limits without changing unrelated defaults."""
import pytest
from acceptance import limits
from acceptance.behavior_clients import adapter_for


@pytest.fixture(autouse=True)
def default_environment(monkeypatch):
    monkeypatch.delenv('TAO_ACCEPTANCE_MODEL_TIMEOUT', raising=False)
    monkeypatch.delenv('TAO_CLAUDE_MAX_BUDGET_USD', raising=False)


def test_explicit_unlimited_mode_preserves_default_budget_otherwise(tmp_path, monkeypatch):
    monkeypatch.setattr('acceptance.behavior_clients.cli_executable', lambda client: client)
    assert limits.model_timeout() == 600
    assert limits.claude_budget(4) == 4
    request = adapter_for('claude').request('', tmp_path, tmp_path/'turn', 1, None)
    assert request.command[request.command.index('--max-budget-usd')+1] == '2'
    monkeypatch.setenv('TAO_CLAUDE_MAX_BUDGET_USD', 'none')
    for turn, session in [(1, None), (2, 'same-session')]:
        request = adapter_for('claude').request('', tmp_path, tmp_path/f'turn-{turn}', turn, session)
        assert '--max-budget-usd' not in request.command
    monkeypatch.setenv('TAO_CLAUDE_MAX_BUDGET_USD', '1.25')
    request = adapter_for('claude').request('', tmp_path, tmp_path/'limited', 1, None)
    assert request.command[request.command.index('--max-budget-usd')+1] == '1.25'


@pytest.mark.parametrize('value', ['0', '-1', 'nan', 'inf', '', 'invalid'])
def test_invalid_fee_override_is_rejected(monkeypatch, value):
    monkeypatch.setenv('TAO_CLAUDE_MAX_BUDGET_USD', value)
    with pytest.raises(ValueError):
        limits.claude_budget(4)


@pytest.mark.parametrize('value', ['0', '-1', '1.5', '', 'invalid'])
def test_invalid_timeout_is_rejected(monkeypatch, value):
    monkeypatch.setenv('TAO_ACCEPTANCE_MODEL_TIMEOUT', value)
    with pytest.raises(ValueError):
        limits.model_timeout()


def test_pytest_runner_and_inner_session_share_operator_timeout(tmp_path, monkeypatch):
    import test_live_acceptance as live
    monkeypatch.setenv('TAO_ACCEPTANCE_MODEL_TIMEOUT', '1200')
    monkeypatch.setattr(live, '_require_model_session', lambda client: None)
    calls=[]
    monkeypatch.setattr(live, '_run', lambda args, **kw: calls.append((args, kw)))
    live.test_documented_claude_acceptance('plan', 'local', (), tmp_path)
    live.test_documented_codex_acceptance('recover', (), tmp_path)
    live.test_documented_behavior_acceptance('claude', tmp_path)
    assert len(calls) == 3
    for args, options in calls:
        assert args[args.index('--timeout')+1] == '1200'
        assert options['timeout'] == 1320
        assert options['environment']['TAO_ACCEPTANCE_MODEL_TIMEOUT'] == '1200'
