from html.parser import HTMLParser
import json
from pathlib import Path
import re
import pytest

from taolib.project import Project
from taolib.project import ConfigurationError
from taolib.publication import build
from test_documents import DOC, REQ, spec
from test_relationships import CHANGE_DOC, navigation


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.ids = []
        self.links = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "a":
            self.links.append(attrs)


def project(root):
    (root / ".tao").mkdir()
    (root / ".tao/config.toml").write_text('version = 1\nlocale = "en"\n[documents]\nbook_root = "docs/index.md"\n')
    (root / "docs").mkdir()
    (root / "docs/index.md").write_text(navigation("spec.md"))
    (root / "docs/spec.md").write_text(spec() + f'\n[Requirement section](#{DOC}--requirements)\n')
    return Project(root)


def test_book_has_stable_heading_and_entity_links_that_survive_moves(tmp_path):
    configured = project(tmp_path)
    output = build(configured)
    directory = tmp_path / output["directory"]
    page = Page((directory / "docs/spec.html").read_text())
    assert DOC in page.ids and REQ in page.ids
    assert DOC + "--requirements" in page.ids
    assert len(page.ids) == len(set(page.ids))
    for link in page.links:
        href = link.get("href", "")
        if href.startswith("#") and len(href) > 1:
            assert href[1:] in page.ids
    links = [a["href"] for a in page.links if "headerlink" in a.get("class", "")]
    assert f"../refs/{DOC}.html#{DOC}--requirements" in links
    resolver = directory / f"refs/{REQ}.html"
    assert "../docs/spec.html#" + REQ in resolver.read_text()
    (tmp_path / "docs/spec.md").rename(tmp_path / "docs/renamed.md")
    (tmp_path / "docs/index.md").write_text(navigation("renamed.md"))
    build(configured)
    assert "../docs/renamed.html#" + REQ in resolver.read_text()
    assert not (directory / "docs/spec.html").exists()


def test_retired_id_keeps_a_resolvable_explanation(tmp_path):
    configured = project(tmp_path)
    old = "REQ_20260914_0000000000000009"
    retired = tmp_path / "docs/retired"
    retired.mkdir()
    (retired / "20260914.jsonl").write_text(json.dumps({"id": old, "retired_on": "2026-09-14", "reason": "Merged into export protection.", "replaced_by": [REQ]}) + "\n")
    result = build(configured)
    page = (tmp_path / result["directory"] / f"refs/{old}.html").read_text()
    assert "Merged into export protection." in page
    assert REQ in page
    assert old in Page(page).ids


def test_removed_published_id_requires_retirement_and_keeps_previous_book(tmp_path):
    configured = project(tmp_path)
    result = build(configured)
    old = "UC_20260914_0000000000000002"
    resolver = tmp_path / result["directory"] / f"refs/{old}.html"
    previous = resolver.read_bytes()
    source = tmp_path / "docs/spec.md"
    source.write_text(re.sub(r"```\{uc\}.*?```", "No active cases.", source.read_text(), flags=re.S))
    with pytest.raises(ConfigurationError, match="TAO-ID-003"):
        build(configured)
    assert resolver.read_bytes() == previous
