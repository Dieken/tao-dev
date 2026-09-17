"""A handoff is durable context, never a replay command or a consumed file."""
from pathlib import Path
from test_workflows import start, call


def handoff_source(root, change):
    source = f'''---
schema: tao.project.handoff/v0.1
id: DOC_20260914_0000000000000008
title: Continue the task
locale: en
status: draft
created: "2026-09-14"
change: {change}
---

# Continue the task
'''
    for section in ('scope', 'state', 'decisions', 'evidence', 'next'):
        source += f'\n<!-- tao:section {section} -->\n## {section}\n\nRead current files before proceeding.\n'
    (root / 'handoff-source.md').write_text(source, encoding='utf-8')


def test_handoff_before_plan_and_repeated_resume_preserves_new_progress(tmp_path, capsys):
    state = start(tmp_path, capsys)
    handoff_source(tmp_path, state['change'])
    code, report = call(tmp_path, capsys, 'handoff', state['change'], '--from', 'handoff-source.md')
    assert code == 0, report
    path = tmp_path / report['outputs']['path']
    assert path.is_file() and not (tmp_path / state['plan_path']).exists()
    code, report = call(tmp_path, capsys, 'workflow', 'status', state['change'])
    observed = report['outputs']['workflows'][0]
    assert observed['handoff_state'] == 'unread'
    code, report = call(tmp_path, capsys, 'workflow', 'resume', state['change'], '--expect', str(observed['revision']), '--handoff-digest', observed['handoff_digest'], '--decision', 'Checked files; remain in specification')
    assert code == 0, report
    assert path.is_file()
    from taolib.workflows import checkpoint
    from taolib.project import Project
    state = checkpoint(Project(tmp_path), state['change'], report['outputs']['revision'], {'next': 'Finish newly clarified acceptance criteria'})
    code, report = call(tmp_path, capsys, 'workflow', 'status', state['change'])
    observed = report['outputs']['workflows'][0]
    assert observed['handoff_state'] == 'resumed'
    assert observed['next'] == 'Finish newly clarified acceptance criteria'
    path.write_text(path.read_text(encoding='utf-8').replace('Read current files', 'Inspect new evidence'), encoding='utf-8')
    code, report = call(tmp_path, capsys, 'workflow', 'status', state['change'])
    assert report['outputs']['workflows'][0]['handoff_state'] == 'unread'
    assert path.is_file()


def test_resume_requires_current_checkpoint_and_does_not_advance_phase(tmp_path, capsys):
    state = start(tmp_path, capsys)
    code, report = call(tmp_path, capsys, 'workflow', 'resume', state['change'], '--expect', '1', '--decision', 'Reconciled actual files without handoff')
    assert code == 0, report
    assert report['outputs']['phase'] == 'spec'
    code, report = call(tmp_path, capsys, 'workflow', 'resume', state['change'], '--expect', '1', '--decision', 'Old session')
    assert code == 1


def test_resume_cannot_consume_handoff_changed_after_read(tmp_path, capsys):
    state = start(tmp_path, capsys)
    handoff_source(tmp_path, state['change'])
    code, report = call(tmp_path, capsys, 'handoff', state['change'], '--from', 'handoff-source.md')
    assert code == 0
    target = tmp_path / report['outputs']['path']
    _, report = call(tmp_path, capsys, 'workflow', 'status', state['change'])
    observed = report['outputs']['workflows'][0]
    target.write_text(target.read_text(encoding='utf-8')+'\nNew unresolved constraint.\n', encoding='utf-8')
    code, _ = call(tmp_path, capsys, 'workflow', 'resume', state['change'], '--expect', str(observed['revision']), '--handoff-digest', observed['handoff_digest'], '--decision', 'Read old version')
    assert code == 1
