import json
from taolib.measurements import usage
from taolib.project import Project


def test_different_client_cache_accounting_does_not_double_count(tmp_path):
    (tmp_path / 'claude.jsonl').write_text(json.dumps({'type':'result', 'usage':{'input_tokens':10, 'cache_read_input_tokens':20, 'cache_creation_input_tokens':30, 'output_tokens':4}, 'total_cost_usd':0.25})+'\n')
    (tmp_path / 'codex.jsonl').write_text(json.dumps({'type':'turn.completed', 'usage':{'input_tokens':60, 'cached_input_tokens':20, 'output_tokens':5}})+'\n')
    result = usage(Project(tmp_path), ['claude.jsonl','codex.jsonl'])
    assert result['model_tokens'] == 129
    assert result['estimated_usd'] is None
    assert result['billed_usd'] is None
    assert result['runs'][0]['estimated_usd'] == 0.25


def test_incomplete_or_missing_usage_stays_unknown(tmp_path):
    (tmp_path / 'partial.jsonl').write_text('{"type":"thread.started"}\n')
    assert usage(Project(tmp_path), ['partial.jsonl'])['model_tokens'] is None
    assert usage(Project(tmp_path), ['missing.jsonl'])['estimated_usd'] is None


def test_claude_model_usage_includes_auxiliary_model_tokens(tmp_path):
    event = {'type':'result', 'usage':{'input_tokens':10,'output_tokens':4}, 'total_cost_usd':0.3,
             'modelUsage':{'main':{'inputTokens':10,'outputTokens':4}, 'auxiliary':{'inputTokens':3,'outputTokens':1}}}
    (tmp_path / 'usage.jsonl').write_text(json.dumps(event)+'\n')
    assert usage(Project(tmp_path), ['usage.jsonl'])['model_tokens'] == 18
