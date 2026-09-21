"""Which requirements this change touched, and whether tasks carry them."""

import re

from .project import contained
from tao_messages import Message

DEFERRAL = re.compile(r"- deferred: (REQ_[0-9A-HJKMNP-TV-Z_]+) — (\S.*)")


def entities(text):
    """Formal requirement entries keyed by ID, with the body they declare."""
    found = {}
    for block in re.finditer(r"^```\{req\}[^\n]*\n(.*?)^```", text, re.S | re.M):
        body = block[1]
        identity = re.search(r"^:id: (REQ_\S+)", body, re.M)
        if identity:
            found[identity[1]] = body
    return found


def touched(project, index, baseline, read_baseline):
    """Requirements this change added or changed, by comparing entries.

    Enumerating from the baseline difference keeps the left column out of the
    author's memory and out of optional metadata: a scan driven by a declared
    field silently shrinks when the field is forgotten.
    """
    changed = set()
    for path, document in index.documents.items():
        if document.metadata.get('schema') != 'tao.project.spec/v0.1':
            continue
        current = entities(contained(project.root, path).read_text(encoding='utf-8'))
        previous = entities(read_baseline(baseline, path) or '')
        for identity, body in current.items():
            if previous.get(identity) != body:
                changed.add(identity)
    return changed


def carried(index, change):
    """Requirements the tasks of this change relate to."""
    tasks = {task for document in index.documents.values()
             if document.metadata.get('change') == change for task in document.tasks}
    return {reference.target for reference in index.references
            if reference.relation == 'relates' and reference.target.startswith('REQ_')
            and reference.source in tasks}


def specifications(index, change):
    """Paths of the specifications this change's plan declares in spec_docs."""
    declared = {identity for document in index.documents.values()
                if document.metadata.get('schema') == 'tao.project.plan/v0.1'
                and document.metadata.get('change') == change
                for identity in document.metadata.get('spec_docs', [])}
    return {path for path, document in index.documents.items()
            if document.metadata.get('id') in declared
            and document.metadata.get('schema') == 'tao.project.spec/v0.1'}


def scope(index, change, held, deferred):
    """The whole declared range, against the requirements tasks carry.

    The baseline difference asks what this change touched; this asks what the
    change said it would deliver. They separate once the requirements reach a
    baseline: from then on the difference is empty while the range still holds
    every requirement the plan named. The range is the plan's own spec_docs,
    so a project neither repeats the list nor teaches tao where specs live; a
    plan declaring none states no range, and the comparison stays silent
    instead of guessing from the document tree.
    """
    paths = specifications(index, change)
    if not paths:
        return {'state': 'not-declared',
                'reason': 'The plan of this change declares no spec_docs, so it states no requirement range.'}
    ranged = {identity for identity, definition in index.definitions.items()
              if identity.startswith('REQ_') and definition.path in paths}
    # An unresolved ID is the reference resolver's finding; reporting it here
    # as well would name the wrong cause.
    resolved = {identity for identity in held if identity in index.definitions}
    return {'state': 'evaluated', 'specifications': sorted(paths), 'requirements': len(ranged),
            'uncovered': sorted(ranged - held - set(deferred)),
            'out_of_scope': sorted(resolved - ranged)}


def deferrals(project, index, change):
    """Deferral lines a plan declares, keyed by requirement.

    The declaration is an exemption, so forgetting it fails the check instead
    of quietly narrowing what is compared.
    """
    declared, faults = {}, []
    for path, document in index.documents.items():
        if document.metadata.get('schema') != 'tao.project.plan/v0.1' or document.metadata.get('change') != change:
            continue
        text = contained(project.root, path).read_text(encoding='utf-8')
        section = text.split('<!-- tao:section questions -->')[-1]
        for line in section.splitlines():
            if line.startswith('- deferred:'):
                match = DEFERRAL.fullmatch(line.rstrip())
                if not match:
                    faults.append(Message('Deferral needs a requirement ID and a trigger: {arg0}', line.strip()))
                else:
                    declared[match[1]] = match[2]
    return declared, faults


def report(project, index, change, baseline, read_baseline):
    """Uncovered requirements, declared deferrals and malformed declarations.

    The declared range is reported whatever the baseline, because it needs no
    revision to compare against; it is exactly the angle that still holds when
    the baseline one cannot run or has nothing left to say.
    """
    declared, faults = deferrals(project, index, change)
    held = carried(index, change)
    summary = {'scope': scope(index, change, held, declared),
               'deferred': {key: declared[key] for key in sorted(declared)},
               'invalid_deferrals': [str(fault) for fault in faults]}
    if baseline is None:
        # No workflow record means no declared fork revision to compare against,
        # which is a condition, not an unfinished check; a recorded workflow
        # whose revision cannot be read is unfinished and says so.
        summary.update(state='not-applicable',
                       reason='This change has no workflow record declaring a baseline revision.')
        return summary
    if not baseline:
        summary.update(state='not-evaluated', reason='The workflow record declares no baseline revision.')
        return summary
    changed = touched(project, index, baseline, read_baseline)
    summary.update(state='evaluated', baseline=baseline, changed=sorted(changed),
                   uncovered=sorted(changed - held - set(declared)))
    return summary
