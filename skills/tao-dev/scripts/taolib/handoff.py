"""Save one explicit, disposable Markdown summary without changing the plan."""

from .project import (ConfigurationError, contained, create_file, mutation_lock,
                      relative_pattern, replace_file, select_plans)


def save(project, source_path, target, result):
    plan = select_plans(result, target, single=True)[0]
    if not relative_pattern(source_path):
        raise ConfigurationError("Handoff --from must be a project-relative Markdown path.")
    source = contained(project.root, source_path)
    if source.suffix.lower() != ".md":
        raise ConfigurationError("Handoff --from must be a Markdown file.")
    content = source.read_text(encoding="utf-8")
    if not content.strip():
        raise ConfigurationError("Handoff summary must not be empty.")
    identity = plan.metadata.get("change") or plan.metadata.get("id")
    definition = result.definitions.get(identity) if isinstance(identity, str) else None
    expected_kind = "CHG" if plan.metadata.get("change") else "DOC"
    if (definition is None or definition.path != plan.path or definition.kind != expected_kind
            or any(d.rule_id == "TAO-ID-002" and d.entity_id == identity for d in result.diagnostics)):
        raise ConfigurationError("The selected plan must have a valid, unique indexed CHG or DOC identity.")
    destination = project.output("temporary", f"handoffs/{identity}.md")
    if destination.is_symlink():
        raise ConfigurationError("Handoff destination must not be a symlink.")
    before = destination.read_bytes() if destination.exists() else None
    with mutation_lock(project):
        if before is None:
            create_file(project.root, destination, content)
        else:
            replace_file(project.root, destination, content, before)
    return {"path": destination.relative_to(project.root).as_posix(),
            "plan": plan.path, "temporary": True, "next_actions": ["continue", "status"]}
