from html.parser import HTMLParser
import json
from pathlib import Path
import re
import pytest

from py_mini_racer import MiniRacer

from taolib.project import Project
from taolib.project import ConfigurationError
from taolib.publication import build
from test_documents import DOC, REQ, UC, spec
from test_relationships import CHANGE_DOC, navigation


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.ids = []
        self.links = []
        self.section_numbers = []
        self.current_link = None
        self.current_section_number = None
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "a":
            attrs["text"] = ""
            self.links.append(attrs)
            self.current_link = attrs
        if tag == "span" and "section-number" in attrs.get("class", "").split():
            self.current_section_number = ""

    def handle_data(self, data):
        if self.current_link is not None:
            self.current_link["text"] += data
        if self.current_section_number is not None:
            self.current_section_number += data

    def handle_endtag(self, tag):
        if tag == "a":
            self.current_link = None
        if tag == "span" and self.current_section_number is not None:
            self.section_numbers.append(self.current_section_number)
            self.current_section_number = None


def project(root):
    (root / ".tao").mkdir()
    (root / ".tao/config.toml").write_text('version = 1\nlocale = "en"\n[documents]\nbook_root = "docs/index.md"\n', encoding='utf-8')
    (root / "docs").mkdir()
    (root / "docs/index.md").write_text(navigation("spec.md"), encoding='utf-8')
    (root / "docs/spec.md").write_text(spec() + f'\n[Requirement section](#{DOC}--requirements)\n', encoding='utf-8')
    return Project(root)


def chinese_project(root):
    (root / ".tao").mkdir()
    (root / ".tao/config.toml").write_text(
        'version = 1\nlocale = "zh-Hans"\n[documents]\nbook_root = "docs/index.md"\n', encoding='utf-8')
    (root / "docs").mkdir()
    (root / "docs/index.md").write_text(navigation("spec.md"), encoding='utf-8')
    (root / "docs/spec.md").write_text(spec(), encoding='utf-8')
    return Project(root)


def test_chinese_book_search_loads_and_finds_body_text(tmp_path):
    """A published book whose script throws still renders its search box."""
    output = build(chinese_project(tmp_path))
    directory = tmp_path / output["directory"]

    with MiniRacer() as engine:
        engine.eval("var window = {};")
        engine.eval((directory / "_static/language_data.js").read_text(encoding='utf-8'))
        assert engine.eval("typeof window.Stemmer") == "function"
        query = engine.eval('JSON.stringify(splitQuery("\u4fdd\u7559\u5df2\u6709\u6587\u4ef6"))')

    payload = (directory / "searchindex.js").read_text(encoding='utf-8')
    terms = json.loads(payload[payload.index("(") + 1:payload.rindex(")")])["terms"]
    # The browser must ask for exactly the terms the index stored.
    assert json.loads(query) == ["\u4fdd\u7559", "\u7559\u5df2", "\u5df2\u6709", "\u6709\u6587", "\u6587\u4ef6"]
    assert all(term in terms for term in json.loads(query))


def test_book_has_stable_heading_and_entity_links_that_survive_moves(tmp_path):
    configured = project(tmp_path)
    output = build(configured)
    directory = tmp_path / output["directory"]
    page = Page((directory / "docs/spec.html").read_text(encoding='utf-8'))
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
    assert "../docs/spec.html#" + REQ in resolver.read_text(encoding='utf-8')
    (tmp_path / "docs/spec.md").rename(tmp_path / "docs/renamed.md")
    (tmp_path / "docs/index.md").write_text(navigation("renamed.md"), encoding='utf-8')
    build(configured)
    assert "../docs/renamed.html#" + REQ in resolver.read_text(encoding='utf-8')
    assert not (directory / "docs/spec.html").exists()


def test_book_numbers_sections_without_putting_numbers_in_permalinks(tmp_path):
    configured = project(tmp_path)
    second_doc = "DOC_20260914_0000000000000010"
    second_req = "REQ_20260914_0000000000000011"
    second_uc = "UC_20260914_0000000000000012"
    part_doc = "DOC_20260914_0000000000000013"
    second = spec().replace(DOC, second_doc).replace(REQ, second_req)
    second = second.replace(UC, second_uc)
    second = second.replace("文件导出", "文件导入")
    (tmp_path / "docs/second.md").write_text(second, encoding='utf-8')
    part = navigation("spec.md\nsecond.md").replace(CHANGE_DOC, part_doc)
    (tmp_path / "docs/part.md").write_text(part, encoding='utf-8')
    index = tmp_path / "docs/index.md"
    index.write_text(navigation("part.md"), encoding='utf-8')

    first_result = build(configured)
    directory = tmp_path / first_result["directory"]
    first = Page((directory / "docs/spec.html").read_text(encoding='utf-8'))
    second_page = Page((directory / "docs/second.html").read_text(encoding='utf-8'))
    part_html = (directory / "docs/part.html").read_text(encoding='utf-8')
    stable_href = f"../refs/{DOC}.html#{DOC}--requirements"
    assert first.section_numbers[:2] == ["1.1. ", "1.1.1. "]
    assert second_page.section_numbers[:2] == ["1.2. ", "1.2.1. "]
    assert stable_href in [link["href"] for link in first.links]
    local_toc = [link for link in first.links
                 if link.get("href") == f"#{DOC}--requirements"
                 and "nav-link" in link.get("class", "").split()]
    book_toc = [link for link in first.links
                if link.get("href") == "second.html"
                and {"reference", "internal"} <= set(link.get("class", "").split())]
    assert local_toc and all(link["text"].startswith("1.1.3. ") for link in local_toc)
    assert book_toc and all(link["text"].startswith("1.2. ") for link in book_toc)
    overview = re.search(fr'<section id="{part_doc}--overview">.*?<h2>(.*?)</h2>',
                         part_html, re.S)
    assert overview and "section-number" not in overview.group(1)

    (tmp_path / "docs/part.md").write_text(
        navigation("second.md\nspec.md").replace(CHANGE_DOC, part_doc)
    , encoding='utf-8')
    second_result = build(configured)
    reordered = Page((tmp_path / second_result["directory"] / "docs/spec.html").read_text(encoding='utf-8'))
    assert reordered.section_numbers[:2] == ["1.2. ", "1.2.1. "]
    assert stable_href in [link["href"] for link in reordered.links]


def test_retired_id_keeps_a_resolvable_explanation(tmp_path):
    configured = project(tmp_path)
    old = "REQ_20260914_0000000000000009"
    retired = tmp_path / "docs/retired"
    retired.mkdir()
    (retired / "20260914.jsonl").write_text(json.dumps({"id": old, "retired_on": "2026-09-14", "reason": "Merged into export protection.", "replaced_by": [REQ]}) + "\n", encoding='utf-8')
    result = build(configured)
    page = (tmp_path / result["directory"] / f"refs/{old}.html").read_text(encoding='utf-8')
    assert "Merged into export protection." in page
    assert REQ in page
    assert old in Page(page).ids
    replacement = next(a for a in Page(page).links
                       if a.get("href") == f"{REQ}.html#{REQ}")
    assert replacement["text"] == "拒绝覆盖"


def test_id_references_show_current_titles_without_changing_links(tmp_path):
    configured = project(tmp_path)
    source = tmp_path / "docs/spec.md"
    source.write_text(source.read_text(encoding='utf-8') + f'\n参见 {{need}}`{DOC}`、{{need}}`{REQ}`。\n', encoding='utf-8')
    for requirement_title in ("拒绝覆盖", "Protect <existing> & new files"):
        source.write_text(source.read_text(encoding='utf-8').replace("拒绝覆盖", requirement_title), encoding='utf-8')
        result = build(configured)
        page = Page((tmp_path / result["directory"] / "docs/spec.html").read_text(encoding='utf-8'))
        for identity, title in ((DOC, "Specification: 文件导出"), (REQ, "Requirement: "+requirement_title)):
            references = [a for a in page.links
                          if a.get("href") == f"../refs/{identity}.html#{identity}"
                          and "headerlink" not in a.get("class", "")]
            assert references and all(a["text"] == title for a in references)
        assert any(a["text"] == "Requirement section" for a in page.links)


def test_removed_published_id_requires_retirement_and_keeps_previous_book(tmp_path):
    configured = project(tmp_path)
    result = build(configured)
    old = "UC_20260914_0000000000000002"
    resolver = tmp_path / result["directory"] / f"refs/{old}.html"
    previous = resolver.read_bytes()
    source = tmp_path / "docs/spec.md"
    source.write_text(re.sub(r"```\{uc\}.*?```", "No active cases.", source.read_text(encoding='utf-8'), flags=re.S), encoding='utf-8')
    with pytest.raises(ConfigurationError, match="TAO-ID-003"):
        build(configured)
    assert resolver.read_bytes() == previous


def test_book_renders_typed_forward_backlinks_and_task_dependencies(tmp_path):
    from test_document_links import linked_plan, design, DESIGN
    from test_relationships import check_change, TASK, TASK_TWO
    (tmp_path/'.tao').mkdir()
    (tmp_path/'.tao/config.toml').write_text('version=1\nlocale="en"\n[documents]\ninclude=["docs/**/*.md"]\nbook_root="docs/index.md"\n', encoding='utf-8')
    content=linked_plan([DOC],[DESIGN])
    second=f'''- [ ] `{TASK_TWO}` Check error result
  - relates: ["{REQ}"]
  - depends_on: ["{TASK}"]
  - verify: Assert error.

'''
    check_change(tmp_path,content.replace('<!-- tao:section verification -->',second+'<!-- tao:section verification -->'))
    (tmp_path/'spec.md').rename(tmp_path/'docs/spec.md')
    (tmp_path/'docs/design.md').write_text(design(specs=[DOC]), encoding='utf-8')
    nav=navigation('spec.md\ndesign.md\nplans/2026-09/20260914-export.md').replace(CHANGE_DOC,'DOC_20260914_0000000000000090')
    (tmp_path/'docs/index.md').write_text(nav, encoding='utf-8')
    output=build(Project(tmp_path)); directory=tmp_path/output['directory']
    plan_html=(directory/'docs/plans/2026-09/20260914-export.html').read_text(encoding='utf-8')
    plan=Page(plan_html); spec_page=Page((directory/'docs/spec.html').read_text(encoding='utf-8'))
    assert 'tao-relations' in plan_html and '<table' in plan_html
    assert 'Specification' in plan_html and 'Design' in plan_html
    assert any(a['text']=='文件导出' and DOC in a.get('href','') for a in plan.links)
    assert any(a['text']=='Export design' and DESIGN in a.get('href','') for a in spec_page.links)
    assert any(a['text']=='导出检查' and CHANGE_DOC in a.get('href','') for a in spec_page.links)
    assert any(a['text']=='Task: 拒绝覆盖已有目标' and TASK in a.get('href','') for a in plan.links)
    assert any(a['text']=='Requirement: 拒绝覆盖' and REQ in a.get('href','') for a in plan.links)
    assert 'relates: [' not in plan_html and 'depends_on: [' not in plan_html
    assert any(CHANGE_DOC+'--tasks' in a.get('href','') and a['text']=='Tasks in this plan' for a in plan.links)


def test_term_definition_stages_its_local_attachment(tmp_path):
    from test_glossary import glossary
    configured=project(tmp_path)
    term=glossary('```{term} Export\n\nSee [local notes](notes.txt).\n```').replace(DOC,'DOC_20260914_0000000000000080')
    (tmp_path/'docs/terms.md').write_text(term, encoding='utf-8')
    (tmp_path/'docs/notes.txt').write_text('Important export constraints.\n', encoding='utf-8')
    (tmp_path/'docs/index.md').write_text(navigation('spec.md\nterms.md'), encoding='utf-8')
    output=build(configured); directory=tmp_path/output['directory']
    assert (directory/'docs/notes.txt').read_text(encoding='utf-8')=='Important export constraints.\n'
    assert any(a['text']=='local notes' for a in Page((directory/'docs/terms.html').read_text(encoding='utf-8')).links)
