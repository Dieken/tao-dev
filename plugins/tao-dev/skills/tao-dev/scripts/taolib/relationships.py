"""Task, attachment, retirement and book relationships."""

import json
import re
from pathlib import Path
from tao_messages import Message


def task(validator, token, section, doc, body_lines, offset):
    raw = body_lines[token.map[0]:token.map[1]]
    first = raw[0] if raw else ""
    # A checkbox follows the list marker and is neither inline nor reference link
    # syntax; its content is left to the strict match below, so a malformed mark
    # still reaches the error.
    if "`TASK_" not in first or not re.match(r"\s*(?:[-*+]|\d+[.)])\s+\[[^]]*\](?![(\[])", first):
        return
    line = offset + token.map[0] + 1
    rule = validator.registry["tasks"]
    match = re.fullmatch(r"- \[([ x])\] `(TASK_[^`]+)` (\S.*)", first)
    if not match or token.level != 1 or section != rule["section"]:
        validator.error("TAO-TASK-001", doc.path, line, "TASK must be a flat checkbox in the tasks section.")
        return
    completed, identity, title = match.groups()
    if validator.identifier(identity, "TASK", doc.path, line):
        validator.define(identity, doc.path, line, "completed" if completed == "x" else "pending", title)
        doc.tasks.append(identity)
    fields, positions = {}, {}
    for number, text in enumerate(raw[1:], 1):
        if not text.strip():
            continue
        field = re.fullmatch(r"  - ([a-z_]+): (.*)", text)
        if not field or field[1] in fields:
            validator.error("TAO-TASK-001", doc.path, line + number, "Invalid indentation, duplicate field or task continuation.")
            continue
        fields[field[1]], positions[field[1]] = field[2], line + number
    required = rule["required_fields"] + (rule["completed_requires"] if completed == "x" else [])
    expected = [key for key in rule["field_order"] if key in fields]
    if set(required) - fields.keys() or list(fields) != expected:
        validator.error("TAO-TASK-001", doc.path, line, Message('Required fields: {arg0}; order: {arg1}.', required, rule['field_order']))
    if not fields.get("verify", "").strip():
        validator.error("TAO-TASK-001", doc.path, line, "verify must describe a nonempty check.")
    for key, types in (("relates", rule["relates_types"]), ("depends_on", rule["depends_on_types"])):
        try:
            members = json.loads(fields.get(key, "null"))
            if not isinstance(members, list) or any(not isinstance(x, str) for x in members):
                raise ValueError()
            if len(set(members)) != len(members) or (key == "relates" and not members):
                raise ValueError()
        except (ValueError, TypeError):
            validator.error("TAO-TASK-001", doc.path, positions.get(key, line), Message('{arg0} requires a unique JSON string array.', key))
            continue
        for member in members:
            validator.reference(member, types, doc.path, positions[key], key, identity)
    if "evidence" in fields:
        parsed = validator.md.parseInline(fields["evidence"])[0].children or []
        if (not parsed or parsed[0].type != "link_open" or parsed[-1].type != "link_close"
                or sum(t.type == "link_open" for t in parsed) != 1):
            validator.error("TAO-TASK-001", doc.path, positions["evidence"], "evidence must contain exactly one Markdown link.")


def navigation(validator, token, section, doc, offset):
    line = offset + token.map[0] + 1
    profile = validator.registry["profiles"][doc.metadata["schema"]]
    rule = profile.get("navigation")
    if not rule or section != rule["section"] or token.markup != "```":
        validator.error("TAO-DOC-002", doc.path, line, "toctree is only allowed in navigation.contents.")
        return
    lines = token.content.splitlines()
    expected = [f":{key}: {value}".rstrip() for key, value in rule["options"].items()]
    if lines[:len(expected)] != expected or len(lines) <= len(expected) or lines[len(expected)].strip():
        validator.error("TAO-DOC-002", doc.path, line, Message('toctree requires options {arg0} and an empty separator line.', expected))
        return
    entries = [value for value in lines[len(expected) + 1:] if value.strip()]
    if len(entries) < rule["minimum_entries"] or len(entries) != len(set(entries)):
        validator.error("TAO-DOC-002", doc.path, line, "toctree requires distinct, nonempty entries.")
    for value in entries:
        if not value.endswith(".md") or re.search(r"[#*?<>]|://", value) or value != value.strip():
            validator.error("TAO-DOC-002", doc.path, line, Message('Invalid navigation entry: {arg0}.', value))
            continue
        resolved = validator.file_target(doc.path, line, value)
        if resolved:
            target, _ = resolved
            if target == doc.path:
                validator.error("TAO-DOC-002", doc.path, line, "Navigation cannot include itself.")
            doc.navigation.append(target)


def attachments(validator):
    documents = validator.result.documents
    by_id = {doc.metadata.get("id"): doc for doc in documents.values()}
    for doc in documents.values():
        profile = validator.registry["profiles"][doc.metadata["schema"]]
        if len(doc.tasks) < profile.get("minimum_tasks", 0):
            validator.error("TAO-TASK-001", doc.path, 1, "This profile requires at least one task.")
        total_tasks = len(doc.tasks)
        for key, rule in profile['metadata'].items():
            if not rule.get('target_profile'):
                continue
            targets = doc.metadata.get(key, []) if rule['type'] == 'array' else [doc.metadata.get(key)]
            for identity in targets:
                target = by_id.get(identity)
                if target is None:
                    continue
                if target.metadata['schema'] != rule['target_profile']:
                    validator.error('TAO-REF-002', doc.path, 1, Message('{arg0} must select the matching profile and change back-reference.', key))
                if key == 'design_docs' and target.metadata.get('change') not in (None, doc.metadata.get('change')):
                    validator.error('TAO-REF-002', doc.path, 1, 'A dedicated design must belong to the same change; shared designs omit change.')
        for key, rule in profile.get("attachments", {}).items():
            if key not in doc.metadata:
                continue
            target = by_id.get(doc.metadata[key])
            if target is None:
                continue  # The reference resolver reports this root error.
            if target.metadata["schema"] != rule["profile"] or target.metadata.get("change") != doc.metadata.get("change"):
                validator.error("TAO-REF-002", doc.path, 1, Message('{arg0} must select the matching profile and change back-reference.', key))
            if key == "tasks_doc":
                total_tasks += len(target.tasks)
                if doc.tasks:
                    validator.error("TAO-TASK-001", doc.path, doc.sections.get("tasks", 1), "Split tasks must have a single authoritative task set.")
        if profile.get("requires_task_set") and total_tasks == 0:
            validator.error("TAO-TASK-001", doc.path, 1, "Change and its task attachment require at least one task.")
        if profile.get("requires_task_set"):
            created = doc.metadata.get("created", "")
            filename = Path(doc.path).name
            match = re.fullmatch(r"(\d{8})-[a-z0-9]+(?:-[a-z0-9]+)*\.md", filename)
            if not match or match[1] != created.replace("-", "") or Path(doc.path).parent.name != created[:7]:
                validator.error("TAO-DOC-002", doc.path, 1, "Change path must end in <yyyy-mm>/<yyyymmdd>-<slug>.md and match created.")


def book(validator, book_root):
    documents = validator.result.documents
    parents = {}
    graph = {}
    for doc in documents.values():
        for target in doc.navigation:
            if target not in documents:
                validator.error("TAO-DOC-002", doc.path, 1, Message('Navigation target is outside the declared sources: {arg0}.', target))
            if target in parents:
                validator.error("TAO-DOC-002", doc.path, 1, Message('Navigation target has multiple parents: {arg0}.', target))
            parents[target] = doc.path
            graph.setdefault(doc.path, []).append(target)
    # Detect cycles even when no book root is supplied.
    for start in graph:
        seen, current = set(), start
        while current in parents:
            if current in seen:
                validator.error("TAO-DOC-002", start, 1, "Navigation contains a cycle.")
                break
            seen.add(current)
            current = parents[current]
    if book_root is not None:
        path = Path(book_root)
        path = path if path.is_absolute() else validator.root / path
        try:
            root = path.resolve().relative_to(validator.root).as_posix()
        except ValueError:
            validator.error("TAO-REF-004", str(book_root), 1, "Book root is outside the project.")
            return
        if root not in documents or documents[root].metadata["schema"] != "tao.project.navigation/v0.1":
            validator.error("TAO-DOC-002", root, 1, "Book root must be a managed navigation document.")
        seen, pending = set(), [root]
        while pending:
            item = pending.pop()
            if item not in seen:
                seen.add(item)
                pending.extend(graph.get(item, []))
        for missing in documents.keys() - seen:
            validator.error("TAO-DOC-002", missing, 1, "Document is not reachable from the book root.")


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(Message('Duplicate key: {arg0}', key))
        value[key] = item
    return value


def section_redirects(validator, redirects):
    location = '.tao/config.toml'
    documents = {doc.metadata.get('id'): doc for doc in validator.result.documents.values()}
    for source, target in redirects.items():
        parsed = []
        for value in (source, target):
            match = re.fullmatch(r'(.+)--([a-z][a-z0-9-]*)', value)
            if not match or not validator.identifier(match[1], 'DOC', location, 1):
                validator.error('TAO-LINK-001', location, 1, 'Section redirects require DOC_ID--section keys and targets.')
                break
            parsed.append(match.groups())
        if len(parsed) != 2:
            continue
        (old_doc, _), (new_doc, section) = parsed
        if old_doc not in validator.result.definitions:
            validator.error('TAO-LINK-001', location, 1, Message('Redirect source document is unknown: {arg0}.', old_doc))
        elif target in redirects:
            validator.error('TAO-LINK-001', location, 1, 'Section redirects must point directly to a current section, without redirect chains.')
        elif new_doc not in documents or section not in documents[new_doc].sections:
            validator.error('TAO-LINK-001', location, 1, Message('Redirect destination section is unknown: {arg0}.', target))
        else:
            validator.result.section_redirects[source] = target


def retirements(validator, directory, overrides=None):
    from .documents import valid_date

    rule = validator.registry["retirement_records"]
    path = validator.root / directory
    try:
        path.resolve().relative_to(validator.root)
    except ValueError:
        validator.error("TAO-REF-004", str(directory), 1, "Retirement directory is outside the project.")
        return
    overrides = overrides or {}
    files = set(path.glob("*.jsonl"))
    files.update(validator.root / name for name in overrides
                 if Path(name).parent == Path(directory) and Path(name).suffix == '.jsonl')
    for full in sorted(files):
        relative = full.relative_to(validator.root).as_posix()
        try:
            full.resolve().relative_to(validator.root)
            if not re.fullmatch(rule["filename_pattern"], full.name):
                raise ValueError("Invalid retirement filename.")
            content = overrides[relative] if relative in overrides else full.read_text(encoding="utf-8")
            if content is None:
                continue
            lines = content.splitlines()
        except (ValueError, OSError, UnicodeError) as exc:
            validator.error("TAO-DOC-001", relative, 1, Message('Cannot read retirement file: {arg0}.', type(exc).__name__))
            continue
        for number, line in enumerate(lines, 1):
            try:
                item = json.loads(line, object_pairs_hook=unique_object)
                if not isinstance(item, dict) or set(item) != set(rule["fields"]):
                    raise ValueError()
                if not valid_date(item["retired_on"]) or item["retired_on"].replace("-", "") != full.stem:
                    raise ValueError()
                if not isinstance(item["reason"], str) or not item["reason"].strip():
                    raise ValueError()
                targets = item["replaced_by"]
                if not isinstance(targets, list) or any(not isinstance(t, str) for t in targets) or len(set(targets)) != len(targets):
                    raise ValueError()
            except (ValueError, TypeError):
                validator.error("TAO-DOC-001", relative, number, "Invalid retirement record: check keys, date, reason and replacement array.")
                continue
            identity = item["id"]
            if validator.identifier(identity, None, relative, number):
                validator.define(identity, relative, number, "retired", item["reason"])
                for target in targets:
                    # A replacement supersedes the retired source; use the
                    # same graph direction as directive supersedes options.
                    validator.reference(target, [identity.split("_")[0]], relative, number, "replaced_by", identity)
