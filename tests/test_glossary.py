from taolib.documents import validate
from test_documents import DOC
import pytest


def glossary(body):
    return f'''---
schema: tao.project.glossary/v0.1
id: {DOC}
title: Terms
locale: en
status: draft
created: "2026-09-14"
---
# Terms
<!-- tao:section terms -->
## Vocabulary
{body}
<!-- tao:section abbreviations -->
## Abbreviations
None.
'''


def check(tmp_path, body):
    path = tmp_path/'terms.md'
    path.write_text(glossary(body), encoding='utf-8')
    return validate(tmp_path, [path])


def test_controlled_terms_are_indexed_without_new_ids(tmp_path):
    result = check(tmp_path, '```{term} Identifier\n:english: Identifier\n:code: change_id\n:avoid: ["identity"]\n:scope: document IDs\n\nA stable value naming one object.\n```')
    assert result.valid, result.diagnostics
    term = result.documents['terms.md'].terms[0]
    assert term['preferred'] == 'Identifier'
    assert term['avoid'] == ['identity']
    assert set(result.definitions) == {DOC}


@pytest.mark.parametrize('body', [
    '```{term}\nA definition.\n```',
    '```{term} Identifier\n:english: Identifier\n```',
    '```{term} Identifier\n:unknown: value\n\nDefinition.\n```',
    '```{term} Identifier\n:avoid: ["Identifier"]\n\nDefinition.\n```',
    '```{term} Identifier\n:avoid: ["identity", "identity"]\n\nDefinition.\n```',
    '```{term} Identifier\n:scope: one\n:scope: two\n\nDefinition.\n```',
    '```{term} Identifier\nDefinition.\n```\n```{term} identifier\nOther definition.\n```',
])
def test_ambiguous_or_malformed_terms_are_rejected(tmp_path, body):
    assert not check(tmp_path, body).valid


def test_examples_are_not_terms_and_quoted_avoid_words_are_allowed(tmp_path):
    assert check(tmp_path, 'Do not use identity for an ID.\n\n````markdown\n```{term}\n```\n````').valid
