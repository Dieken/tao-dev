"""Parse controlled vocabulary without allocating entity IDs."""
import json
import re


def term(validator, token, section, doc, offset):
    rule = validator.registry['profiles'].get(doc.metadata['schema'], {}).get('terms')
    line = offset + token.map[0] + 1
    def error(message):
        validator.error('TAO-DOC-002', doc.path, line, message)
    if not rule or section != rule['section']:
        error('Controlled terms belong in the glossary terms section.')
        return
    preferred = token.info.removeprefix('{term}').strip()
    if not preferred:
        error('A controlled term requires a preferred name.')
        return
    options = {}
    lines = token.content.splitlines()
    pos = 0
    while pos < len(lines) and lines[pos].startswith(':'):
        match = re.fullmatch(r':([a-z_]+):\s*(.+)', lines[pos])
        if not match or match[1] not in rule['options'] or match[1] in options:
            error('Term options must be known, distinct and nonempty.')
            return
        options[match[1]] = match[2].strip()
        pos += 1
    definition = '\n'.join(lines[pos:]).strip()
    if not definition or not any(t.type == 'inline' and t.content.strip() for t in validator.md.parse(definition)):
        error('A controlled term requires a definition.')
        return
    avoid = []
    if 'avoid' in options:
        try:
            avoid = json.loads(options['avoid'])
        except ValueError:
            avoid = None
        if (not isinstance(avoid, list) or not avoid or
                any(not isinstance(x, str) or not x.strip() for x in avoid) or
                len({x.strip().casefold() for x in avoid}) != len(avoid) or
                preferred.casefold() in {x.strip().casefold() for x in avoid}):
            error('Avoided terms must be distinct nonempty strings excluding the preferred name.')
            return
    scope = options.get('scope', '').casefold()
    for previous in doc.terms:
        if previous.get('scope', '').casefold() == scope and previous['preferred'].casefold() == preferred.casefold():
            error('Define a preferred term only once per scope.')
            return
    doc.terms.append(options | {'preferred': preferred, 'definition': definition, 'avoid': avoid, 'line': line})
    validator.inline(validator.md.parse(definition), doc.path, line + pos, doc)
