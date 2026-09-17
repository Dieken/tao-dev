"""Readable links derived from the validated source index, never written back."""
from functools import lru_cache
import json
from pathlib import Path
from docutils import nodes


@lru_cache(maxsize=2)
def catalog(locale):
    return json.loads((Path(__file__).resolve().parents[2]/'assets/locales'/f'{locale}.json').read_text(encoding='utf-8'))


def label(app, key):
    locale = 'zh-Hans' if (app.config.language or '').startswith('zh') else 'en'
    return catalog(locale).get('publication.'+key, key)


def kind(app, identity):
    index = app.config.tao_index
    definition = index['definitions'].get(identity.split('--', 1)[0], {})
    prefix = identity.split('_', 1)[0]
    if prefix == 'DOC':
        doc = index['documents'].get(definition.get('path'), {})
        return doc.get('metadata', {}).get('schema', 'tao.project.document/v0.1').split('/')[0].rsplit('.', 1)[-1]
    return {'REQ': 'requirement', 'UC': 'case', 'ADR': 'decision', 'TASK': 'task', 'CHG': 'change', 'EVD': 'evidence'}.get(prefix, 'document')


def reference(app, docname, identity, *, typed=True, title=None):
    definition = app.config.tao_index['definitions'].get(identity.split('--', 1)[0])
    if definition is None:
        return nodes.literal(text=identity)
    title = title or definition.get('title') or identity
    if typed:
        title = label(app, 'type.'+kind(app, identity)) + ': ' + title
    uri = app.builder.get_relative_uri(docname, 'refs/'+identity.split('--', 1)[0])+'#'+identity
    return nodes.reference('', title, refuri=uri, reftitle=identity, classes=['tao-reference'])


def relationship_paragraph(app, docname, key, targets):
    paragraph = nodes.paragraph()
    paragraph += nodes.strong(text=label(app, key)+': ')
    for pos, identity in enumerate(targets):
        if pos:
            paragraph += nodes.Text('; ')
        paragraph += reference(app, docname, identity)
    if not targets:
        paragraph += nodes.Text(label(app, 'none'))
    return paragraph


def related_table(app, docname, doc):
    index = app.config.tao_index
    identity = doc['metadata']['id']
    rows = []
    for ref in index['references']:
        relation, source, target = ref['relation'], ref.get('source'), ref['target']
        if relation not in ('spec_docs', 'design_docs', 'tasks_doc'):
            continue
        if source == identity:
            rows.append((relation, kind(app, target), target, None))
        if target == identity and source:
            relation = 'related_design' if kind(app, source) == 'design' else 'implementation'
            if ref['relation'] == 'tasks_doc':
                relation = 'owner'
            rows.append((relation, kind(app, source), source, None))
    if doc['tasks'] and doc['metadata']['schema'] == 'tao.project.plan/v0.1':
        rows.append(('tasks_doc', 'tasks', identity+'--tasks', label(app, 'inline_tasks')))
    if not rows:
        return None
    table = nodes.table(ids=['tao-related-'+identity], classes=['tao-relations'])
    table += nodes.title(text=label(app, 'related'))
    group = nodes.tgroup(cols=3)
    table += group
    for width in (20, 20, 60):
        group += nodes.colspec(colwidth=width)
    head = nodes.thead(); group += head
    heading = nodes.row(); head += heading
    for name in ('relationship', 'type', 'document'):
        entry = nodes.entry(); entry += nodes.paragraph(text=label(app, name)); heading += entry
    body = nodes.tbody(); group += body
    for relation, category, target, title in dict.fromkeys(rows):
        row = nodes.row(); body += row
        for value in (label(app, relation), label(app, 'type.'+category)):
            entry = nodes.entry(); entry += nodes.paragraph(text=value); row += entry
        entry = nodes.entry(); row += entry
        paragraph = nodes.paragraph(); entry += paragraph
        paragraph += reference(app, docname, target, typed=False, title=title)
    return table


def task_relationships(app, docname, item, identity):
    refs = [r for r in app.config.tao_index['references'] if r.get('source') == identity]
    for paragraph in list(item.findall(nodes.paragraph)):
        text = paragraph.astext()
        for key in ('relates', 'depends_on'):
            if text.startswith(key+': '):
                targets = [r['target'] for r in refs if r['relation'] == key]
                paragraph.replace_self(relationship_paragraph(app, docname, key, targets))
                break
