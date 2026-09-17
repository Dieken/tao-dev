"""Codex exec evidence must be a complete single review, not a success flag."""

import hashlib
import json

import pytest

from test_reviews import attestation, setup_review, submit
from test_relationships import CHG
from test_verification import report


def codex_attestation(root):
    value = attestation(root, model=True)
    value['reviewer'].update(model='unknown', provider='unknown')
    value['source']['format'] = 'codex-exec-jsonl'
    conclusion = {key: value[key] for key in ('binding', 'summary', 'findings', 'limitations')}
    events = [
        {'type': 'thread.started', 'thread_id': 'review-context'},
        {'type': 'turn.started'},
        {'type': 'item.completed', 'item': {'id': 'item_0', 'type': 'agent_message', 'text': 'Inspecting the inputs.'}},
        {'type': 'item.started', 'item': {'id': 'item_1', 'type': 'command_execution', 'status': 'in_progress'}},
        {'type': 'item.completed', 'item': {'id': 'item_1', 'type': 'command_execution', 'status': 'completed', 'exit_code': 0}},
        {'type': 'item.completed', 'item': {'id': 'item_2', 'type': 'agent_message', 'text': json.dumps(conclusion)}},
        {'type': 'turn.completed', 'usage': {'input_tokens': 12, 'cached_input_tokens': 0, 'output_tokens': 8}},
    ]
    return value, events


def save_source(root, value, events):
    path = root / value['source']['path']
    path.write_text('\n'.join(json.dumps(e) for e in events) + '\n', encoding='utf-8')
    value['source']['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()


def test_complete_codex_review_opens_gate(tmp_path):
    setup_review(tmp_path)
    value, events = codex_attestation(tmp_path)
    save_source(tmp_path, value, events)
    code, result = submit(tmp_path, value)
    assert code == 0, result
    code, result = report(tmp_path, 'verify', CHG)
    assert code == 0, result
    row, = result['outputs']['reviews']
    assert row['state'] == 'satisfied'
    assert row['reviewer']['model'] == row['reviewer']['provider'] == 'unknown'


@pytest.mark.parametrize('mutation', [
    'no-thread', 'wrong-thread', 'two-threads', 'no-start', 'two-turns',
    'truncated', 'failed', 'error', 'after-end', 'pending-item', 'duplicate-item',
    'bad-item-order', 'different-conclusion', 'no-final', 'duplicate-json',
    'duplicate-conclusion', 'model-claim', 'provider-claim', 'stale', 'tampered',
])
def test_codex_rejects_incomplete_or_unsubstantiated_source(tmp_path, mutation):
    setup_review(tmp_path)
    value, events = codex_attestation(tmp_path)
    if mutation == 'no-thread': events.pop(0)
    elif mutation == 'wrong-thread': events[0]['thread_id'] = 'someone-else'
    elif mutation == 'two-threads': events.insert(1, dict(events[0]))
    elif mutation == 'no-start': events.pop(1)
    elif mutation == 'two-turns': events += events[1:]
    elif mutation == 'truncated': events.pop()
    elif mutation == 'failed': events[-1] = {'type': 'turn.failed', 'error': {'message': 'failed'}}
    elif mutation == 'error': events.insert(3, {'type': 'error', 'message': 'lost stream'})
    elif mutation == 'after-end': events.append(events[-2])
    elif mutation == 'pending-item': events.pop(4)
    elif mutation == 'duplicate-item': events.insert(5, events[4])
    elif mutation == 'bad-item-order': events[3], events[4] = events[4], events[3]
    elif mutation == 'different-conclusion': value['summary'] = 'Edited after review'
    elif mutation == 'no-final': events.pop(-2)
    elif mutation == 'duplicate-conclusion':
        text = events[-2]['item']['text']
        events[-2]['item']['text'] = text[:-1] + ', "summary": "hidden override"}'
    elif mutation == 'model-claim': value['reviewer']['model'] = 'configured-model'
    elif mutation == 'provider-claim': value['reviewer']['provider'] = 'openai'
    elif mutation == 'stale': (tmp_path / 'check.py').write_text('print("changed")', encoding='utf-8')
    save_source(tmp_path, value, events)
    path = tmp_path / value['source']['path']
    if mutation == 'duplicate-json':
        path.write_text(path.read_text(encoding='utf-8').replace('"thread.started"', '"thread.started", "type": "thread.started"', 1), encoding='utf-8')
        value['source']['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    elif mutation == 'tampered': path.write_text(path.read_text(encoding='utf-8') + '{}\n', encoding='utf-8')
    code, result = submit(tmp_path, value)
    assert code != 0, result
    assert report(tmp_path, 'status', CHG)[1]['outputs']['reviews'][0]['state'] == 'missing'
