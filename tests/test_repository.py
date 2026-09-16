"""Apply the distributed contract to the actual development documents.

Configured sources answer to the full document contract. The remaining
tracked pages carry ordinary links only, and a page shipped inside the
plugin may address just the files an installation actually receives.
"""

from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

from taolib.documents import validate
from taolib.git_workflow import run
from taolib.project import Project

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r'\[[^]]*\]\(([^)\s]+)(?:\s+"[^"]*")?\)')
PLUGIN_ROOT = '${CLAUDE_PLUGIN_ROOT}/'


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
    """Tracked Markdown the validator never reads; discovered, so no page name is fixed here."""
    managed = {path.resolve() for path in Project(ROOT).sources()}
    names = run(ROOT, 'ls-files', '-z', '*.md').split('\0')
    return [ROOT / name for name in names if name and (ROOT / name).resolve() not in managed]


def test_links_of_unmanaged_pages_stay_reachable():
    anchors = stable_anchors()
    pages = unmanaged_pages()
    placeholders = 0
    assert pages
    for page in pages:
        plugin = next((p for p in page.parents if (p / '.claude-plugin/plugin.json').is_file()), None)
        for target in LINK.findall(page.read_text(encoding='utf-8')):
            url = urlsplit(target)
            if url.scheme in ('http', 'https', 'mailto') or '{{' in target:
                continue  # Templates keep their placeholders until a project renders them.
            location = unquote(url.path)
            if location.startswith(PLUGIN_ROOT):
                # Clients expand this to the installed plugin directory.
                assert plugin is not None, (page, target)
                placeholders += 1
                resolved = (plugin / location[len(PLUGIN_ROOT):]).resolve()
            else:
                resolved = ((page.parent / location) if location else page).resolve()
            assert resolved.is_relative_to(plugin or ROOT), (page, target)
            assert resolved.exists(), (page, target)
            relative = resolved.relative_to(ROOT).as_posix()
            if url.fragment and relative in anchors:
                assert unquote(url.fragment) in anchors[relative], (page, target)
    assert placeholders, 'Plugin pages address bundled resources through the client placeholder.'
