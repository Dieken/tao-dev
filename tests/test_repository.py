"""The book and shipped skill must not contain broken local links."""

from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

from taolib.documents import validate
from taolib.project import Project

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r'\[[^]]*\]\(([^)\s]+)(?:\s+"[^"]*")?\)')


def test_development_documents_use_the_shared_runtime_contract():
    result = validate(ROOT, list((ROOT / "docs").rglob("*.md")))
    assert result.valid, result.to_dict()


def stable_anchors():
    """Managed documents publish entity IDs and section markers; plain headings are not link targets."""
    result = validate(ROOT, [str(path) for path in Project(ROOT).sources()])
    anchors = {}
    for path, document in result.documents.items():
        anchors[path] = {d.id for d in result.definitions.values() if d.path == path}
        anchors[path].update(document.metadata['id'] + '--' + section for section in document.sections)
    return anchors


def unmanaged_pages():
    """Read shipped skill pages and maintained repository entry points."""
    skill = ROOT / 'skills/tao-dev'
    return [*skill.rglob('*.md'), *(ROOT / name for name in
            ('AGENTS.md', 'CLAUDE.md', 'README.md', 'tests/acceptance/README.md')
            if (ROOT / name).is_file())]


def test_links_of_unmanaged_pages_stay_reachable():
    anchors = stable_anchors()
    pages = unmanaged_pages()
    for page in pages:
        skill = ROOT / 'skills/tao-dev'
        boundary = skill if page.is_relative_to(skill) else ROOT
        # A link inside a fenced example is sample syntax, not a shipped resource.
        prose = re.sub(r'^```.*?^```', '', page.read_text(encoding='utf-8'), flags=re.S | re.M)
        for target in LINK.findall(prose):
            url = urlsplit(target)
            if url.scheme in ('http', 'https', 'mailto') or '{{' in target:
                continue  # Templates keep their placeholders until a project renders them.
            location = unquote(url.path)
            resolved = ((page.parent / location) if location else page).resolve()
            assert resolved.is_relative_to(boundary), (page, target)
            assert resolved.exists(), (page, target)
            relative = resolved.relative_to(ROOT).as_posix()
            if url.fragment and relative in anchors:
                assert unquote(url.fragment) in anchors[relative], (page, target)
