"""Decode observed review output without inventing client identity claims."""

import json


def decode(text):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate JSON key.')
            result[key] = value
        return result
    return json.loads(text, object_pairs_hook=unique)


def confirm_codex(events, reviewer, conclusion):
    # exec JSONL has thread identity and messages, but no attested model/provider.
    if reviewer['model'] != 'unknown' or reviewer['provider'] != 'unknown':
        raise ValueError('Codex exec does not attest model or provider; use unknown.')
    if (len(events) < 4 or events[0].get('type') != 'thread.started'
            or events[0].get('thread_id') != reviewer['context']
            or events[1].get('type') != 'turn.started'
            or events[-1].get('type') != 'turn.completed'):
        raise ValueError('A Codex review requires one observed thread and successful turn.')
    pending, completed = {}, set()
    final = None
    for event in events[2:-1]:
        kind = event.get('type')
        if kind not in ('item.started', 'item.updated', 'item.completed'):
            raise ValueError('Unexpected, failed or additional Codex review turn.')
        item = event['item']
        identifier, item_type = item['id'], item['type']
        if not isinstance(identifier, str) or not identifier or not isinstance(item_type, str):
            raise ValueError('Invalid Codex item identity.')
        if identifier in completed or (identifier in pending and pending[identifier] != item_type):
            raise ValueError('Inconsistent or repeated Codex item.')
        if kind == 'item.started':
            if identifier in pending:
                raise ValueError('Repeated Codex item start.')
            pending[identifier] = item_type
        elif kind == 'item.updated':
            if identifier not in pending:
                raise ValueError('Codex item update has no start.')
        else:
            pending.pop(identifier, None)
            completed.add(identifier)
            if item_type == 'agent_message':
                final = item['text']
    if pending or final is None:
        raise ValueError('Codex review has unfinished items or no conclusion.')
    if decode(final) != conclusion:
        raise ValueError('Codex output does not match the recorded conclusion and dispositions.')
