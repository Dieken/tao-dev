"""Validate an agent-written recovery summary before saving it atomically."""

from datetime import datetime
from pathlib import Path
import re

from .documents import Validator, validate
from . import workflows
from .project import ConfigurationError, ConflictError, contained, create_file, mutation_lock, replace_file
from tao_messages import Message


def save(project, source_path, change, result):
    source = contained(project.root, source_path)
    content = source.read_text(encoding="utf-8")
    reader = Validator(project.root)
    parsed = reader.metadata(content, str(source_path))
    if parsed is None or not reader.result.valid:
        raise ConfigurationError("Handoff input has invalid metadata.")
    metadata = parsed[0]
    if metadata["schema"] != "tao.project.handoff/v0.1":
        raise ConfigurationError("--from must use the handoff profile.")
    change = change or metadata.get("change")
    candidates = [d for d in result.documents.values() if d.metadata["schema"] == "tao.project.plan/v0.1"
                  and (d.metadata.get("change") == change if change else any(result.definitions[t].status == "pending" for t in d.tasks))]
    state = workflows.read(project, change) if change and workflows.state_path(project, change).is_file() else None
    if len(candidates) == 1:
        plan_path = candidates[0].path
        change = candidates[0].metadata['change']
    elif not candidates and state:
        plan_path = state['plan_path']
    else:
        raise ConfigurationError("Handoff requires one identifiable plan or workflow; supply its CHG ID.")
    if metadata.get("change") != change:
        raise ConfigurationError("Handoff change must match the selected workflow.")
    target = contained(project.root, Path(plan_path).with_suffix("") / "handoff.md")
    relative = target.relative_to(project.root).as_posix()
    sources = [p for p in project.sources() if p.resolve() not in (source.resolve(), target.resolve())] + [target]
    existing = result.documents.get(relative)
    if existing and existing.metadata["id"] != metadata["id"]:
        raise ConflictError("Preserve the existing handoff document ID when updating it.")
    tasks = [result.definitions[t] for d in result.documents.values() if d.metadata.get("change") == change for t in d.tasks]
    observation = {"recorded_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                   "completed": sum(t.status == "completed" for t in tasks),
                   "pending": sum(t.status != "completed" for t in tasks),
                   "evidence_reusability": "not-evaluated"}
    # The state observation is historical context, not another task tracker.
    stamp = (f"CLI observation ({observation['recorded_at']}): {observation['completed']} completed, "
             f"{observation['pending']} pending; evidence reusability not evaluated.\n\n")
    content = re.sub(r"^CLI observation \([^\n]+\): [^\n]*\n\n", "", content, flags=re.M)
    content = content.replace("<!-- tao:section decisions -->", stamp + "<!-- tao:section decisions -->")
    checked = validate(project.root, sources, retirement_directory=project.paths["retired"], overrides={relative: content},
                       section_redirects=project.section_redirects, diagnostic_locale=project.diagnostic_locale)
    if not checked.valid:
        errors = "; ".join(f"{d.path}:{d.line} {d.rule_id}" for d in checked.diagnostics if d.severity == "error")
        raise ConfigurationError(Message('Handoff would create invalid documents: {arg0}', errors))
    before = target.read_bytes() if target.exists() else None
    with mutation_lock(project):
        if before is None:
            create_file(project.root, target, content)
        else:
            replace_file(project.root, target, content, before)
    # Publish the readable document first. If a concurrent state update wins,
    # status can still discover this canonical path and reconcile it.
    if state:
        def link(owner, current):
            current['handoff'] = {'path': relative, 'digest': workflows.file_digest(target)}
        workflows.mutate(project, change, state['revision'], link)
    return {"path": relative, "id": metadata["id"], "observation": observation,
            "continue": "continue", "retained": True}
