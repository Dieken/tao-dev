"""Build and inspect local HTML before replacing the last published output."""

import html
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import unquote, urlsplit

from .documents import parser, validate
from .project import ConfigurationError, ConflictError, contained, mutation_lock


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
        if tag == "a" and "href" in attrs:
            self.links.append(attrs)


def stage_sources(project, result, source):
    """Stage managed sources and explicitly linked local reading material."""
    pending = [project.root / p for p in result.documents]
    copied = set()
    raw_files = []
    md = parser()
    while pending:
        path = pending.pop()
        contained(project.root, path)
        relative = path.relative_to(project.root).as_posix()
        if relative in copied:
            continue
        copied.add(relative)
        destination = source / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix != ".md":
            shutil.copyfile(path, destination)
            raw_files.append(relative)
            continue
        text = path.read_text(encoding="utf-8")
        for token in md.parse(text):
            if token.type != "inline":
                continue
            for child in token.children or []:
                if child.type not in ("link_open", "image"):
                    continue
                url = child.attrGet("href") or child.attrGet("src")
                parts = urlsplit(url)
                if parts.scheme or parts.netloc or not parts.path:
                    continue
                target = (path.parent / unquote(parts.path)).resolve()
                contained(project.root, target)
                if target.is_file():
                    pending.append(target)
        if relative not in result.documents:
            if "templates" in path.parts:
                fence = "`" * max(4, max((len(x) for x in re.findall(r"`+", text)), default=0) + 1)
                text = f"# {path.name}\n\n{fence}markdown\n{text}\n{fence}\n"
            if text.startswith("---\n"):
                text = text.replace("---\n", "---\norphan: true\n", 1)
            else:
                text = "---\norphan: true\n---\n\n" + text
        # A source explicit label matching the generated section target
        # would duplicate it. Only remove this exact, validated ID form.
        text = re.sub(r"^\((DOC_[0-9]{8}_[0-9A-HJKMNP-TV-Z]{16}--[a-z-]+)\)=\n", "", text, flags=re.M)
        # MyST interprets fragment-only links as global label searches.
        # Make the source document explicit so its stable slug map applies.
        text = re.sub(r"\]\(#((?:DOC|REQ|UC|ADR|TASK|CHG|EVD)_[0-9]{8}_[0-9A-HJKMNP-TV-Z]{16}(?:--[a-z-]+)?)\)",
                      lambda m: "](" + path.name + "#" + m[1] + ")", text)
        destination.write_text(text, encoding="utf-8")
    return raw_files


def resolver_pages(result, output):
    directory = output / "refs"
    directory.mkdir()
    for identity, definition in result.definitions.items():
        if definition.path.endswith(".jsonl"):
            targets = [r.target for r in result.references if r.source == identity and r.relation == "replaced_by"]
            links = " ".join(f'<a href="{target}.html#{target}">{target}</a>' for target in targets)
            body = f'<h1 id="{identity}">{identity}</h1><p>Retired: {html.escape(definition.title)}</p>{links}'
        else:
            target = "../" + str(Path(definition.path).with_suffix(".html")) + "#" + identity
            # Preserve section fragments when the DOC resolver is used.
            base = target.split("#")[0]
            body = (f'<h1 id="{identity}">{html.escape(definition.title or identity)}</h1>'
                    f'<a href="{html.escape(target)}">Open definition</a>'
                    f'<script>location.replace({json.dumps(base)} + (location.hash || {json.dumps("#" + identity)}));</script>')
        (directory / f"{identity}.html").write_text('<!doctype html><meta charset="utf-8"><title>' + identity + '</title>' + body, encoding="utf-8")


def stable_links(result, output):
    for path, doc in result.documents.items():
        page_path = output / Path(path).with_suffix(".html")
        text = page_path.read_text(encoding="utf-8")
        prefix = os.path.relpath(output / "refs", page_path.parent).replace(os.sep, "/")

        def replace(match):
            anchor = html.unescape(match[2])
            identity = anchor.split("--", 1)[0]
            if identity in result.definitions:
                return match[1] + prefix + "/" + identity + ".html#" + anchor + match[3]
            return match[0]

        text = re.sub(r'(<a class="headerlink" href=")#([^"<>]+)(")', replace, text)
        page_path.write_text(text, encoding="utf-8")
        parsed = Page(text)
        required = {d.id for d in result.definitions.values() if d.path == path}
        required.update(doc.metadata["id"] + "--" + key for key in doc.sections)
        if not required <= set(parsed.ids) or len(parsed.ids) != len(set(parsed.ids)):
            raise ConfigurationError(f"Generated page has missing or duplicate stable IDs: {path}; missing {required - set(parsed.ids)}")
        permalinks = {a["href"] for a in parsed.links if "headerlink" in a.get("class", "")}
        for section in doc.sections:
            expected = f"{prefix}/{doc.metadata['id']}.html#{doc.metadata['id']}--{section}"
            if expected not in permalinks:
                raise ConfigurationError(f"Heading permalink is not stable: {path} section {section}")


def build(project):
    if not project.book_root:
        raise ConfigurationError("Configure documents.book_root before building a book.")
    destination = project.output("temporary", "book")
    if destination.exists() and not (destination / ".tao-book").is_file():
        raise ConflictError("Book output is not marked as generated by tao; choose an unused temporary directory.")
    baseline = {p.stem for p in (destination / "refs").glob("*.html")
                if re.fullmatch(r"(?:DOC|REQ|UC|ADR|TASK|CHG|EVD)_[0-9]{8}_[0-9A-HJKMNP-TV-Z]{16}", p.stem)}
    result = validate(project.root, project.sources(), baseline_ids=baseline or None,
                      book_root=project.book_root, retirement_directory=project.paths["retired"])
    if not result.valid:
        details = "; ".join(f"{d.path}:{d.line} {d.rule_id}: {d.message}" for d in result.diagnostics if d.severity == "error")
        raise ConfigurationError("Book sources are invalid: " + details)
    temporary_root = project.output("temporary")
    temporary_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="book-", dir=temporary_root) as working:
        work = Path(working)
        source, output = work / "source", work / "html"
        source.mkdir()
        raw_files = stage_sources(project, result, source)
        (source / "_tao-index.json").write_text(json.dumps(result.to_dict(), ensure_ascii=False), encoding="utf-8")
        title = result.documents[project.book_root].metadata["title"]
        conf = (f"import sys, json\nfrom pathlib import Path\nsys.path.insert(0, {str(Path(__file__).resolve().parents[1])!r})\n"
                "extensions = ['myst_parser', 'taolib.sphinx_ext']\n"
                "source_suffix = {'.md': 'markdown'}\nhtml_theme = 'sphinx_book_theme'\n"
                f"root_doc = {str(Path(project.book_root).with_suffix(''))!r}\n"
                f"project = {title!r}\nhtml_title = {title!r}\n"
                f"language = {'zh_CN' if project.locale == 'zh-Hans' else 'en'!r}\n"
                "myst_enable_extensions = ['colon_fence']\n"
                "html_copy_source = False\nhtml_show_sourcelink = False\n"
                "tao_index = json.loads(Path('_tao-index.json').read_text(encoding='utf-8'))\n")
        # Sphinx executes conf.py from its source directory.
        (source / "conf.py").write_text(conf, encoding="utf-8")
        completed = subprocess.run([sys.executable, "-m", "sphinx", "-W", "--keep-going", "-b", "html", str(source), str(output)], capture_output=True, text=True)
        if completed.returncode:
            log = project.output("temporary", "book-build.log")
            log.write_text(completed.stdout + completed.stderr, encoding="utf-8")
            raise ConfigurationError(f"Sphinx build failed; inspect {log.relative_to(project.root)}: {completed.stderr[-1500:]}")
        for relative in raw_files:
            target = output / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source / relative, target)
        resolver_pages(result, output)
        stable_links(result, output)
        (output / ".tao-book").write_text("generated\n")
        with mutation_lock(project):
            if destination.exists() and not (destination / ".tao-book").is_file():
                raise ConflictError("Book destination changed ownership during the build.")
            previous = work / "previous"
            if destination.exists():
                os.replace(destination, previous)
            try:
                os.replace(output, destination)
            except OSError:
                if previous.exists():
                    os.replace(previous, destination)
                raise
        return {"directory": destination.relative_to(project.root).as_posix(),
                "index": (destination / Path(project.book_root).with_suffix(".html")).relative_to(project.root).as_posix(),
                "definitions": len(result.definitions), "stable_links_checked": True}
