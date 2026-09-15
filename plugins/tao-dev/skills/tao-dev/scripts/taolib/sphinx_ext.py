"""Render tao entities, stable targets, and book section numbers."""

from docutils import nodes
from . import publication_links as links
from docutils.parsers.rst import directives
from sphinx import addnodes
from sphinx.util.docutils import SphinxDirective


class Entity(SphinxDirective):
    required_arguments = 1
    final_argument_whitespace = True
    has_content = True
    option_spec = {key: directives.unchanged for key in ("id", "status", "links", "supersedes", "verifies")}

    def run(self):
        identity = self.options.get("id", "")
        if identity not in self.config.tao_index["definitions"]:
            return [nodes.literal_block(text="\n".join(self.content))]
        box = nodes.container(ids=[identity], classes=["tao-entity"])
        title = nodes.paragraph(classes=["rubric"])
        title += nodes.strong(text=self.arguments[0])
        title += nodes.reference("", " ¶", refuri="#" + identity, classes=["headerlink"])
        box += title
        box.extend(self.parse_content_to_nodes())
        for key in ("verifies", "links", "supersedes"):
            if self.options.get(key):
                box += links.relationship_paragraph(self.env.app, self.env.docname, key, [x.strip() for x in self.options[key].split(',')])
        return [box]


class Term(SphinxDirective):
    required_arguments = 1
    final_argument_whitespace = True
    has_content = True
    option_spec = {key: directives.unchanged for key in ("english", "code", "avoid", "scope")}

    def run(self):
        box = nodes.container(classes=["tao-term"])
        title = nodes.paragraph()
        title += nodes.strong(text=self.arguments[0])
        if self.options.get("english"):
            title += nodes.Text(" / " + self.options["english"])
        box += title
        box.extend(self.parse_content_to_nodes())
        for key in ("code", "scope", "avoid"):
            if key in self.options:
                box += nodes.paragraph(text=links.label(self.env.app, key) + ": " + self.options[key])
        return [box]


def need_role(name, rawtext, text, lineno, inliner, options=None, content=None):
    env = inliner.document.settings.env
    definition = env.config.tao_index["definitions"].get(text)
    if definition is None:
        return [nodes.literal(rawtext, text)], []
    return [links.reference(env.app, env.docname, text)], []


def _number_entries(node, prefix, numbers):
    position = 0
    for item in node.children:
        if not isinstance(item, nodes.list_item):
            continue
        paragraph = next((child for child in item.children
                          if isinstance(child, addnodes.compact_paragraph)), None)
        if paragraph is None or not paragraph.children:
            continue
        reference = paragraph.children[0]
        if not isinstance(reference, nodes.reference):
            continue
        anchor = reference.get("anchorname")
        if not anchor:
            continue
        position += 1
        number = prefix + (position,)
        numbers[anchor] = number
        for child in item.children:
            if isinstance(child, nodes.bullet_list):
                _number_entries(child, number, numbers)


def _document_numbers(env, docname, prefix):
    numbers = {"": prefix}
    toc = env.tocs.get(docname)
    if toc is None:
        return numbers
    for root in toc.children:
        if not isinstance(root, nodes.list_item):
            continue
        for child in root.children:
            if isinstance(child, nodes.bullet_list):
                _number_entries(child, prefix, numbers)
    return numbers


def section_numbers(app, env):
    index = app.config.tao_index
    documents = index.get("documents", {})
    root = app.config.root_doc + ".md"
    desired = {}

    def visit(parent, prefix):
        for position, target in enumerate(documents[parent].get("navigation", []), 1):
            number = prefix + (position,)
            document = documents[target]
            docname = target.removesuffix(".md")
            if document["metadata"]["schema"] == "tao.project.navigation/v0.1":
                identity = document["metadata"]["id"]
                desired[docname] = {
                    "": number,
                    **{f"#{identity}--{key}": () for key in document["sections"]},
                }
            else:
                desired[docname] = _document_numbers(env, docname, number)
            visit(target, number)

    visit(root, ())
    previous = env.toc_secnumbers
    env.toc_secnumbers = desired
    for toc in env.tocs.values():
        for reference in toc.findall(nodes.reference):
            reference.attributes.pop("secnumber", None)
            numbers = desired.get(reference.get("refuri", ""), {})
            number = numbers.get(reference.get("anchorname", ""))
            if number:
                reference["secnumber"] = number
    for title in env.titles.values():
        title.attributes.pop("secnumber", None)
    for docname, numbers in desired.items():
        if docname in env.titles:
            env.titles[docname]["secnumber"] = numbers[""]
    return sorted(docname for docname in set(previous) | set(desired)
                  if previous.get(docname) != desired.get(docname))


def targets(app, doctree):
    docname = app.env.docname
    index = app.config.tao_index
    doc = index["documents"].get(docname + ".md")
    if doc is None:
        return
    if docname == app.config.root_doc:
        for tree in doctree.findall(addnodes.toctree):
            tree["numbered"] = 999
    identity = doc["metadata"]["id"]
    sections = list(doctree.findall(nodes.section))
    if sections:
        sections[0]["ids"] = [identity]
    h2_sections = [node for node in sections[0].children if isinstance(node, nodes.section)] if sections else []
    for section, key in zip(h2_sections, doc["sections"], strict=True):
        section["ids"] = [identity + "--" + key]
    # Metadata CHG/EVD and task checkboxes are definitions too. Their
    # anchors are attached to real nodes without inventing new source IDs.
    for key in ("change", "evidence"):
        item = doc["metadata"].get(key)
        if item and index["definitions"].get(item, {}).get("path") == docname + ".md":
            doctree.insert(0, nodes.target(ids=[item]))
    for task in doc["tasks"]:
        for item in doctree.findall(nodes.list_item):
            if task in item.astext().splitlines()[0]:
                item["ids"] = [task]
                item.children[0] += nodes.reference("", " ¶", refuri="#" + task, classes=["headerlink"])
                links.task_relationships(app, docname, item, task)
                break
    table = links.related_table(app, docname, doc)
    if table is not None and sections:
        sections[0].insert(1, table)
    # MyST/Sphinx resolves source Markdown fragments through this map.
    anchors = {value: (node.line, value, value) for node in doctree.findall(nodes.Element) for value in node.get("ids", [])}
    app.env.metadata[docname]["myst_slugs"] = anchors
    for node in doctree.findall(nodes.Element):
        for anchor in node.get("ids", []):
            if anchor.split("--", 1)[0] in index["definitions"]:
                node["names"] = [anchor.lower()]
                doctree.note_explicit_target(node)


def missing_reference(app, env, node, contnode):
    target = node.get("reftarget", "")
    fragment = target.rsplit("#", 1)[-1]
    identity = fragment.split("--", 1)[0]
    if identity in app.config.tao_index["definitions"]:
        uri = app.builder.get_relative_uri(env.docname, "refs/" + identity) + "#" + fragment
        return nodes.reference("", "", contnode, refuri=uri)
    return None


def setup(app):
    app.add_config_value("tao_index", {}, "env")
    for kind in ("req", "uc", "adr"):
        app.add_directive(kind, Entity)
    app.add_directive("term", Term)
    app.add_role("need", need_role)
    app.connect("doctree-read", targets, priority=400)
    app.connect("env-get-updated", section_numbers, priority=600)
    app.connect("missing-reference", missing_reference)
    return {"version": "0.1", "parallel_read_safe": True, "parallel_write_safe": True}
