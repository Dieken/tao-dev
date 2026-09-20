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
    """Uncovered requirements, declared deferrals and malformed declarations."""
    if baseline is None:
        # No workflow record means no declared fork revision to compare against,
        # which is a condition, not an unfinished check; a recorded workflow
        # whose revision cannot be read is unfinished and says so.
        return {'state': 'not-applicable', 'reason': 'This change has no workflow record declaring a baseline revision.'}
    if not baseline:
        return {'state': 'not-evaluated', 'reason': 'The workflow record declares no baseline revision.'}
    changed = touched(project, index, baseline, read_baseline)
    carried = {reference.target for reference in index.references
               if reference.relation == 'relates' and reference.target.startswith('REQ_')
               and reference.source in {task for document in index.documents.values()
                                        if document.metadata.get('change') == change for task in document.tasks}}
    declared, faults = deferrals(project, index, change)
    uncovered = sorted(changed - carried - set(declared))
    return {'state': 'evaluated', 'baseline': baseline, 'changed': sorted(changed),
            'uncovered': uncovered, 'deferred': {k: declared[k] for k in sorted(declared)},
            'invalid_deferrals': [str(f) for f in faults]}
