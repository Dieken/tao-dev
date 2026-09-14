"""Render tao entities and attach exact, case-preserving stable targets."""

from docutils import nodes
from docutils.parsers.rst import directives
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
        return [box]


def need_role(name, rawtext, text, lineno, inliner, options=None, content=None):
    env = inliner.document.settings.env
    definition = env.config.tao_index["definitions"].get(text)
    if definition is None:
        return [nodes.literal(rawtext, text)], []
    # Permanent entry points also work for retired definitions.
    target = "refs/" + text
    uri = env.app.builder.get_relative_uri(env.docname, target) + "#" + text
    return [nodes.reference(rawtext, text, refuri=uri)], []


def targets(app, doctree):
    docname = app.env.docname
    index = app.config.tao_index
    doc = index["documents"].get(docname + ".md")
    if doc is None:
        return
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
                break
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
    app.add_role("need", need_role)
    app.connect("doctree-read", targets, priority=400)
    app.connect("missing-reference", missing_reference)
    return {"version": "0.1", "parallel_read_safe": True, "parallel_write_safe": True}
