"""Reference routing evidence extracted from real client event logs."""

import json

from acceptance import clients


def write_events(path, *events):
    path.write_text('\n'.join(json.dumps(event) for event in events) + '\n')


def test_claude_reads_come_only_from_executed_tool_inputs(tmp_path):
    log = tmp_path / 'claude.jsonl'
    write_events(
        log,
        {'type': 'assistant', 'message': {'content': [
            {'type': 'tool_use', 'name': 'Skill',
             'input': {'skill': 'tao-dev:tao-dev'}},
            {'type': 'tool_use', 'name': 'Read',
             'input': {'file_path': '/cache/skills/tao-dev/references/engineering.md'}},
            {'type': 'tool_use', 'name': 'Bash', 'input': {
                'command': "cat '/cache/skills/tao-dev/references/workflow.md' "
                           "'/cache/skills/tao-dev/references/engineering.md'"}},
        ]}},
        {'type': 'user', 'message': {'content': [{
            'type': 'tool_result',
            'content': 'A link to /cache/skills/tao-dev/references/documents.md',
        }]}},
    )

    result = clients.reference_reads(log, 'claude')

    assert result == {
        'skill_invoked': True,
        'resources': ['references/engineering.md', 'references/workflow.md'],
        'broad_scans': [],
    }


def test_codex_deduplicates_started_and_completed_commands(tmp_path):
    log = tmp_path / 'codex.jsonl'
    command = "/bin/zsh -lc 'cat .agents/skills/tao-dev/SKILL.md " \
              ".agents/skills/tao-dev/references/engineering.md'"
    write_events(
        log,
        {'type': 'item.started', 'item': {
            'type': 'command_execution', 'command': command}},
        {'type': 'item.completed', 'item': {
            'type': 'command_execution', 'command': command,
            'aggregated_output': 'references/documents.md appears in file text'}},
    )

    result = clients.reference_reads(log, 'codex')

    assert result == {
        'skill_invoked': True,
        'resources': ['references/engineering.md'],
        'broad_scans': [],
    }


def test_reference_parser_reports_broad_scans_and_ignores_partial_lines(tmp_path):
    log = tmp_path / 'partial.jsonl'
    log.write_text(
        '{not-json}\n' + json.dumps({'type': 'item.completed', 'item': {
            'type': 'command_execution',
            'command': "rg -n TODO .agents/skills/tao-dev/references",
        }}) + '\n')

    result = clients.reference_reads(log, 'codex')

    assert result['resources'] == []
    assert result['broad_scans'] == [
        'rg -n TODO .agents/skills/tao-dev/references',
    ]


def test_reference_parser_handles_a_probe_blocked_before_log_creation(tmp_path):
    assert clients.reference_reads(tmp_path / 'missing.jsonl', 'claude') == {
        'skill_invoked': False,
        'resources': [],
        'broad_scans': [],
    }


def test_routing_assessment_requires_core_refs_and_no_document_branch():
    passed = clients.assess_routing({
        'skill_invoked': True,
        'resources': ['references/engineering.md', 'references/workflow.md'],
        'broad_scans': [],
    })
    unexpected = clients.assess_routing({
        'skill_invoked': True,
        'resources': [
            'references/engineering.md',
            'references/workflow.md',
            'references/documents.md',
        ],
        'broad_scans': [],
    })
    unnecessary = clients.assess_routing({
        'skill_invoked': True,
        'resources': [
            'references/engineering.md',
            'references/runtime.md',
            'references/workflow.md',
        ],
        'broad_scans': [],
    })

    assert passed['status'] == 'passed'
    assert passed['unexpected_document_reads'] == []
    assert passed['unexpected_resource_reads'] == []
    assert unexpected['status'] == 'failed'
    assert unexpected['unexpected_document_reads'] == ['references/documents.md']
    assert unnecessary['status'] == 'failed'
    assert unnecessary['unexpected_resource_reads'] == ['references/runtime.md']
