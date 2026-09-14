"""ADR source fields must remain distinguishable to Markdown readers."""

import re

import pytest

from taolib.documents import ASSETS, validate


def decision(locale="zh-Hans", context="**背景与备选：** 比较共享环境与独立环境。"):
    template = (ASSETS / "templates/decision.md").read_text()
    values = {
        "DOC_ID": "DOC_20260914_0000000000000001", "TITLE": "Runtime choice",
        "LOCALE": locale, "CREATED": "2026-09-14", "heading.decisions": "Decisions",
        "ADR_TITLE": "Isolate dependencies", "ADR_ID": "ADR_20260914_0000000000000001",
        "label.context": "Context", "ADR_CONTEXT": "Compare environments.",
        "label.decision": "Decision", "ADR_DECISION": "Use an isolated environment.",
        "label.consequences": "Consequences", "ADR_CONSEQUENCES": "Prepare dependencies separately.",
    }
    source = re.sub(r"\{\{([^}]+)\}\}", lambda match: values[match[1]], template)
    return source.replace("**Context:** Compare environments.", context)


@pytest.mark.parametrize("content", [
    "比较共享环境与独立环境。",
    "背景与备选：比较共享环境与独立环境。",
    "**背景与备选：**",
    "**：** 比较共享环境与独立环境。",
    "**背景与备选** 比较共享环境与独立环境。",
    "`**背景与备选：**` 比较共享环境与独立环境。",
    "**背景与备选：** <!-- Description is still missing. -->",
])
def test_adr_rejects_missing_label_or_description(tmp_path, content):
    path = tmp_path / "decision.md"
    path.write_text(decision(context=content))
    result = validate(tmp_path, [path])
    assert "TAO-ENTITY-001" in {item.rule_id for item in result.diagnostics}
    assert any("context" in item.message for item in result.diagnostics)


@pytest.mark.parametrize("locale,content", [
    ("zh-Hans", "**背景与备选：** 比较共享环境与独立环境。"),
    ("en", "**Context and alternatives:** Compare shared and isolated environments."),
    ("fr", "**Contexte et options** : Comparer les environnements."),
    ("zh-Hans", "__背景与备选__：比较共享环境与独立环境。"),
])
def test_adr_label_words_and_punctuation_are_localizable(tmp_path, locale, content):
    path = tmp_path / "decision.md"
    path.write_text(decision(locale, content))
    result = validate(tmp_path, [path])
    assert result.valid, result.to_dict()
