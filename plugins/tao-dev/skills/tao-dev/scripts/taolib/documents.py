"""Validate Markdown nodes against the registry, then resolve their index.

Regular expressions recognize tao grammars inside parsed nodes only. Code
examples and quoted directives cannot register formal definitions.
"""

import json
import re
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from urllib.parse import unquote, urlsplit

import yaml
from markdown_it import MarkdownIt

from .model import Definition, Diagnostic, Document, Reference, Result
from . import relationships


ASSETS = Path(__file__).resolve().parents[2] / "assets"
SECTION = re.compile(r"<!-- tao:section ([a-z][a-z0-9-]*) -->\n?\Z")
FIELD = re.compile(r"<!-- tao:field ([a-z][a-z0-9-]*) -->\n?\Z")
PLACEHOLDER = re.compile(r"\{\{[A-Za-z][A-Za-z0-9_.]*\}\}")
LOCALE = re.compile(r"[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*\Z")


def need_role(state, silent):
    match = re.match(r"\{need\}`([^`\n]+)`", state.src[state.pos:])
    if not match:
        return False
    if not silent:
        token = state.push("tao_need", "", 0)
        token.content = match[1]
        token.meta["line_offset"] = state.src[:state.pos].count("\n")
    state.pos += len(match[0])
    return True


def parser():
    md = MarkdownIt("commonmark").enable("table")
    md.inline.ruler.before("text", "tao_need", need_role)
    # Preserve forbidden destinations for diagnostics instead of silently
    # rendering the entire link as ordinary text.
    md.validateLink = lambda _url: True
    return md


def valid_date(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return False
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def labelled_paragraph(token):
    children = [child for child in token.children or []
                if child.type != "text" or child.content.strip()]
    if [child.type for child in children[:3]] != ["strong_open", "text", "strong_close"]:
        return False
    label = children[1].content.strip()
    tail = children[3:]
    description = "".join(child.content for child in tail
                          if child.type in ("text", "code_inline", "tao_need")).strip()
    if label.endswith((":", "：")):
        label = label[:-1].strip()
    elif tail and tail[0].type == "text" and description.startswith((":", "：")):
        description = description[1:].strip()
    else:
        return False
    return bool(label and description)


class Validator:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.registry = json.loads((ASSETS / "document-profiles.json").read_text())
        self.result = Result()
        self.md = parser()
        self.file_links = []

    def error(self, rule, path, line, message, **kwargs):
        self.result.diagnostics.append(Diagnostic(
            rule, "error", path, max(1, line), message,
            "Correct the indicated field or relationship.", **kwargs))

    def identifier(self, value, prefix, path, line):
        valid = isinstance(value, str) and re.fullmatch(self.registry["id"]["pattern"], value)
        if valid:
            day = value.split("_")[1]
            valid = valid_date(f"{day[:4]}-{day[4:6]}-{day[6:]}")
        if valid and prefix:
            valid = value.startswith(prefix + "_")
        if not valid:
            self.error("TAO-ID-001", path, line, f"Invalid {prefix or 'entity'} ID: {value!r}.")
        return bool(valid)

    def define(self, value, path, line, status, title=""):
        if not self.identifier(value, None, path, line):
            return
        if value in self.result.definitions:
            old = self.result.definitions[value]
            self.error("TAO-ID-002", path, line, f"Duplicate definition: {value}.",
                       related_locations=[{"path": old.path, "line": old.line}], entity_id=value)
        else:
            self.result.definitions[value] = Definition(value, path, line, status, title)

    def reference(self, target, types, path, line, relation="links", source=None):
        if not self.identifier(target, None, path, line):
            return
        if types and target.split("_")[0] not in types:
            self.error("TAO-REF-002", path, line, f"{relation} requires {types}, received {target}.")
        self.result.references.append(Reference(target, path, line, relation, source))

    def metadata(self, source, path):
        lines = source.splitlines(keepends=True)
        if not lines or lines[0].rstrip("\r\n") != "---":
            self.error("TAO-DOC-001", path, 1, "YAML frontmatter must start the file.")
            return None
        end = next((i for i in range(1, len(lines)) if lines[i].rstrip("\r\n") == "---"), None)
        if end is None:
            self.error("TAO-DOC-001", path, 1, "Unclosed YAML frontmatter.")
            return None
        yaml_text = "".join(lines[1:end])
        try:
            tags = [t for t in yaml.scan(yaml_text) if isinstance(t, yaml.tokens.TagToken)]
            if tags:
                self.error("TAO-DOC-001", path, tags[0].start_mark.line + 2, "Explicit YAML tags are not allowed.")
                return None
            node = yaml.compose(yaml_text, Loader=yaml.SafeLoader)
        except yaml.YAMLError as exc:
            mark = getattr(exc, "problem_mark", None)
            self.error("TAO-DOC-001", path, mark.line + 2 if mark else 1, "Invalid YAML frontmatter.")
            return None
        if not isinstance(node, yaml.MappingNode):
            self.error("TAO-DOC-001", path, 2, "Frontmatter must be a mapping.")
            return None
        values, locations = {}, {}
        for key, value in node.value:
            line = key.start_mark.line + 2
            if not isinstance(key, yaml.ScalarNode) or key.tag != "tag:yaml.org,2002:str":
                self.error("TAO-DOC-001", path, line, "Metadata keys must be strings.")
                continue
            if key.value in values:
                self.error("TAO-DOC-001", path, line, f"Duplicate metadata: {key.value}.")
            if not isinstance(value, yaml.ScalarNode) or value.tag != "tag:yaml.org,2002:str":
                self.error("TAO-DOC-001", path, line, f"{key.value} must be a string; quote dates.")
                values[key.value] = None
            else:
                values[key.value] = value.value
            locations[key.value] = line
        profile = self.registry["profiles"].get(values.get("schema"))
        if profile is None:
            self.error("TAO-DOC-001", path, locations.get("schema", 2), f"Unsupported schema: {values.get('schema')!r}.")
            return None
        fields = self.registry["base_metadata"] | profile["metadata"]
        for key in values.keys() - fields.keys():
            self.error("TAO-DOC-001", path, locations[key], f"Unknown metadata: {key}.")
        for key, rule in fields.items():
            value, line = values.get(key), locations.get(key, 2)
            if key not in values and not rule.get("required"):
                continue
            if not isinstance(value, str) or not value.strip():
                self.error("TAO-DOC-001", path, line, f"{key} requires a nonempty string.")
                continue
            if rule.get("enum") and value not in rule["enum"]:
                self.error("TAO-DOC-001", path, line, f"{key} must be one of {rule['enum']}.")
            fmt = rule.get("format")
            if fmt == "date" and not valid_date(value):
                self.error("TAO-DOC-001", path, line, f"Invalid calendar date: {value}.")
            if fmt == "bcp47" and not LOCALE.fullmatch(value):
                self.error("TAO-DOC-001", path, line, f"Invalid locale tag: {value}.")
            if fmt == "rfc3339":
                try:
                    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})", value):
                        raise ValueError()
                    datetime.fromisoformat(value)
                except ValueError:
                    self.error("TAO-DOC-001", path, line, f"Invalid RFC 3339 timestamp: {value}.")
            if rule["type"] == "id" and self.identifier(value, rule["prefix"], path, line):
                if rule["role"] == "definition":
                    self.define(value, path, line, values.get("status", "draft"), values.get("title", ""))
                else:
                    self.reference(value, [rule["prefix"]], path, line)
        if valid_date(values.get("created")) and valid_date(values.get("updated")) and values["updated"] < values["created"]:
            self.error("TAO-DOC-001", path, locations["updated"], "updated precedes created.")
        return values, profile, "".join(lines[end + 1:]), end + 1

    def fields(self, tokens, expected, path, offset, label_style=None):
        found = []
        for index, token in enumerate(tokens):
            if token.level != 0 or token.type != "html_block":
                continue
            match = FIELD.fullmatch(token.content)
            if not match:
                continue
            found.append(match[1])
            following = tokens[index + 1:] or [None]
            if following[0] is None or following[0].type != "paragraph_open":
                self.error("TAO-ENTITY-001", path, offset + token.map[0] + 1, f"Field {match[1]} requires a nonempty paragraph.")
            elif label_style == "strong" and (len(following) < 2 or not labelled_paragraph(following[1])):
                self.error("TAO-ENTITY-001", path, offset + token.map[0] + 1,
                           f"Field {match[1]} requires a bold display label with ':' or '：', followed by a nonempty description.")
        if found != expected:
            self.error("TAO-ENTITY-001", path, offset + 1, f"Expected fields {expected}; found {found}.")

    def inline(self, tokens, path, offset):
        for token in tokens:
            if token.type != "inline":
                continue
            line = offset + token.map[0] + 1
            if PLACEHOLDER.search(token.content):
                self.error("TAO-ENTITY-001", path, line, "Unfilled template placeholder.")
            for child in token.children or []:
                if child.type == "tao_need":
                    self.reference(child.content, None, path, line + child.meta["line_offset"])
                elif child.type in ("link_open", "image"):
                    self.file_links.append((path, line, child.attrGet("href") or child.attrGet("src")))

    def entity(self, token, section, path, offset):
        match = re.fullmatch(r"\{(req|uc|adr)\}\s+(.+)", token.info.strip())
        line = offset + token.map[0] + 1
        if not match:
            self.error("TAO-ENTITY-001", path, line, "Formal blocks require a type and title.")
            return
        kind, title = match[1].upper(), match[2]
        rule = self.registry["entities"][kind]
        if token.markup != "```":
            self.error("TAO-ENTITY-001", path, line, "Formal blocks require three backticks.")
        if section not in self.registry["entity_sections"][kind]:
            self.error("TAO-ENTITY-001", path, line, f"{kind} is not allowed in section {section}.")
        lines = token.content.splitlines(keepends=True)
        options, positions = {}, {}
        pos = 0
        while pos < len(lines) and lines[pos].startswith(":"):
            option = re.fullmatch(r":([a-z][a-z_]*):\s*(.*?)\s*", lines[pos])
            if not option or option[1] in options:
                self.error("TAO-ENTITY-001", path, line + pos + 1, "Invalid or duplicate directive option.")
            else:
                options[option[1]], positions[option[1]] = option[2], line + pos + 1
            pos += 1
        if pos == len(lines) or lines[pos].strip():
            self.error("TAO-ENTITY-001", path, line + pos + 1, "Separate directive options and body with an empty line.")
        allowed = rule["required_options"] + rule["optional_options"]
        if set(options) - set(allowed) or set(rule["required_options"]) - set(options):
            self.error("TAO-ENTITY-001", path, line, f"Required options: {rule['required_options']}; allowed: {allowed}.")
        if options.get("status") not in rule["statuses"]:
            self.error("TAO-ENTITY-001", path, line, f"Invalid {kind} status.")
        identity = options.get("id")
        if self.identifier(identity, kind, path, positions.get("id", line)):
            self.define(identity, path, positions["id"], options.get("status", "proposed"), title)
        for key, types in rule["reference_types"].items():
            if key in options:
                members = [part.strip() for part in options[key].split(",")]
                if not all(members) or len(members) != len(set(members)):
                    self.error("TAO-ENTITY-001", path, positions[key], f"{key} requires distinct nonempty IDs.")
                for member in members:
                    self.reference(member, types, path, positions[key], key, identity)
        body_offset = line + pos
        body_tokens = self.md.parse("".join(lines[pos:]))
        self.fields(body_tokens, rule["fields"], path, body_offset, rule.get("field_label_style"))
        first_field = next((i for i, t in enumerate(body_tokens) if t.type == "html_block" and FIELD.fullmatch(t.content)), len(body_tokens))
        if kind == "REQ" and not any(t.type == "paragraph_open" for t in body_tokens[:first_field]):
            self.error("TAO-ENTITY-001", path, body_offset + 1, "REQ requires a behavior paragraph before its fields.")
        self.inline(body_tokens, path, body_offset)

    def document(self, source, path):
        parsed = self.metadata(source, path)
        if parsed is None:
            return
        metadata, profile, body, offset = parsed
        doc = Document(path, metadata)
        self.result.documents[path] = doc
        tokens = self.md.parse(body)
        body_lines = body.splitlines()
        navigation_count = 0
        sections, section, previous_heading = [], None, 0
        h1 = []
        for index, token in enumerate(tokens):
            line = offset + (token.map[0] if token.map else 0) + 1
            if token.type == "heading_open" and token.level == 0:
                depth = int(token.tag[1])
                if depth > previous_heading + 1:
                    self.error("TAO-DOC-002", path, line, "Heading levels must not skip a level.")
                previous_heading = depth
                if depth == 1:
                    h1.append(tokens[index + 1].content)
                if depth == 2:
                    prior = tokens[index - 1] if index else None
                    match = SECTION.fullmatch(prior.content) if prior and prior.type == "html_block" and prior.level == 0 else None
                    if not match or prior.map[1] != token.map[0]:
                        self.error("TAO-DOC-002", path, line, "H2 requires an immediately preceding section marker.")
                        section = None
                    else:
                        section = match[1]
                        sections.append(section)
                        doc.sections[section] = line
            if token.type == "fence" and token.level == 0:
                if re.match(r"\{(?:req|uc|adr)(?:\}|\s)", token.info):
                    self.entity(token, section, path, offset)
                elif re.match(r"\{(?:chg|evd)\}", token.info):
                    self.error("TAO-ENTITY-001", path, line, "CHG and EVD are defined only in frontmatter.")
                elif token.info.strip() == "{toctree}":
                    navigation_count += 1
                    relationships.navigation(self, token, section, doc, offset)
            if token.type == "list_item_open":
                relationships.task(self, token, section, doc, body_lines, offset)
        if profile.get("navigation") and navigation_count != profile["navigation"]["block_count"]:
            self.error("TAO-DOC-002", path, offset + 1, "Navigation requires exactly one toctree.")
        if h1 != [metadata.get("title")]:
            self.error("TAO-DOC-002", path, offset + 1, "Exactly one H1 matching metadata.title is required.")
        if sections != profile["sections"]:
            self.error("TAO-DOC-002", path, offset + 1, f"Expected sections {profile['sections']}; found {sections}.")
        for section_key in doc.sections:
            content_tokens = self.section_tokens(tokens, doc, section_key, offset)
            if not any(t.type in ("inline", "fence", "code_block") for t in content_tokens):
                self.error("TAO-DOC-002", path, doc.sections[section_key], f"Section {section_key} requires content or an explanation of non-applicability.")
        for section_key, required in profile.get("section_fields", {}).items():
            self.fields(self.section_tokens(tokens, doc, section_key, offset), required, path, offset)
        self.inline(tokens, path, offset)
        counts = Counter(d.kind for d in self.result.definitions.values() if d.path == path)
        for kind, count in profile.get("minimum_entities", {}).items():
            if counts[kind] < count:
                self.error("TAO-ENTITY-001", path, offset + 1, f"At least {count} {kind} required.")
        for kind, count in profile.get("maximum_entities", {}).items():
            if counts[kind] > count:
                self.error("TAO-ENTITY-001", path, offset + 1, f"At most {count} {kind} allowed.")

    def section_tokens(self, tokens, doc, section, offset):
        start = doc.sections.get(section, 0)
        end = min((line for line in doc.sections.values() if line > start), default=float("inf"))
        return [t for t in tokens if t.map and start < t.map[0] + offset + 1 < end]

    def resolve(self):
        definitions = self.result.definitions
        for ref in self.result.references:
            target = definitions.get(ref.target)
            if target is None:
                self.error("TAO-REF-001", ref.path, ref.line, f"Unresolved ID: {ref.target}.")
            elif target.status in ("retired", "superseded"):
                self.result.diagnostics.append(Diagnostic("TAO-REF-003", "warning", ref.path, ref.line,
                    f"Reference to {target.status} ID: {target.id}.", "Review the replacement or explain the historical use."))
        replaced = {r.target for r in self.result.references if r.relation == "supersedes"}
        for entity in definitions.values():
            if entity.status == "superseded" and entity.id not in replaced:
                self.error("TAO-REF-002", entity.path, entity.line, f"Superseded ID has no replacement: {entity.id}.")
        for relation in ("supersedes", "depends_on", "replaced_by"):
            graph = {}
            for ref in self.result.references:
                if ref.relation == relation and ref.source:
                    graph.setdefault(ref.source, []).append(ref.target)
            self.cycles(graph, relation)
        anchors = {}
        for path, doc in self.result.documents.items():
            anchors[path] = {d.id for d in definitions.values() if d.path == path}
            anchors[path].update(f"{doc.metadata.get('id')}--{section}" for section in doc.sections)
        for path, line, url in self.file_links:
            target = self.file_target(path, line, url)
            if target is None:
                continue
            destination, fragment = target
            if destination not in self.result.documents and not (self.root / destination).is_file():
                self.error("TAO-REF-001", path, line, f"Missing file: {url}.")
            elif fragment and destination in anchors and fragment not in anchors[destination]:
                self.error("TAO-LINK-001", path, line, f"Unknown stable anchor: {fragment}.")

    def file_target(self, path, line, url):
        try:
            parts = urlsplit(url)
            if parts.scheme in ("https", "http", "mailto"):
                return None
            decoded = unquote(parts.path)
            if parts.scheme or parts.netloc or decoded.startswith(("/", "\\")) or "\\" in decoded:
                raise ValueError()
            target = (self.root / path).parent / decoded if decoded else self.root / path
            relative = target.resolve().relative_to(self.root).as_posix()
            return relative, unquote(parts.fragment)
        except (ValueError, OSError, RuntimeError):
            self.error("TAO-REF-004", path, line, f"File link is outside the project or uses a forbidden scheme: {url}.")
            return None

    def cycles(self, graph, relation):
        finished = set()
        for start in graph:
            active, trail = set(), []
            stack = [(start, False)]
            while stack:
                node, leaving = stack.pop()
                if leaving:
                    active.remove(node)
                    trail.pop()
                    finished.add(node)
                elif node in active:
                    entity = self.result.definitions.get(node)
                    if entity:
                        self.error("TAO-REF-002", entity.path, entity.line, f"{relation} cycle: {' -> '.join(trail + [node])}.")
                elif node not in finished:
                    active.add(node)
                    trail.append(node)
                    stack.append((node, True))
                    stack.extend((target, False) for target in reversed(graph.get(node, [])))


def validate(root, paths, *, baseline_ids=None, book_root=None, retirement_directory="docs/retired", overrides=None):
    """Validate explicit managed sources. Historical deletion needs a baseline."""
    validator = Validator(root)
    overrides = overrides or {}
    for path in sorted(set(Path(p) for p in paths)):
        full = path if path.is_absolute() else validator.root / path
        try:
            relative = full.resolve().relative_to(validator.root).as_posix()
        except (ValueError, OSError, RuntimeError):
            validator.error("TAO-REF-004", str(path), 1, "Input document is outside the project.")
            continue
        try:
            source = overrides[relative] if relative in overrides else full.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            validator.error("TAO-DOC-001", relative, 1, f"Cannot read UTF-8 document: {type(exc).__name__}.")
            continue
        validator.document(source, relative)
    relationships.retirements(validator, retirement_directory)
    relationships.attachments(validator)
    relationships.book(validator, book_root)
    validator.resolve()
    if baseline_ids is not None:
        validator.result.deletion_checked = True
        for identity in sorted(set(baseline_ids) - validator.result.definitions.keys()):
            validator.error("TAO-ID-003", ".", 1, f"Baseline ID removed without retirement: {identity}.")
    return validator.result
