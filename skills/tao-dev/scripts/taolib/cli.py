"""Deterministic document and persistent project progress helpers."""

import argparse
from dataclasses import asdict
from datetime import date
from importlib.util import find_spec
import json
from pathlib import Path
import re
import sys
import time

from . import __version__
from .documents import ASSETS, validate
from .identifiers import new_id, new_ids
from .project import (ConfigurationError, ConflictError, Project, contained,
                      create_file, mutation_lock, select_plans)
from tao_messages import configured_locale, diagnostic, valid_locale, Message


CAPABILITIES = ["doctor", "id.new", "show",
                "new", "status", "retire", "verify.docs",
                "project.inspect", "project.configure"]
if all(find_spec(module) for module in ("sphinx", "myst_parser", "sphinx_book_theme")):
    CAPABILITIES.append("docs.build")


class ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise ConfigurationError(message)


def arguments(argv):
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--project", type=Path, default=argparse.SUPPRESS)
    common.add_argument("--format", choices=("text", "json"), default=argparse.SUPPRESS)
    common.add_argument("--diagnostic-locale", default=argparse.SUPPRESS)
    parser = ArgumentParser(prog="tao", parents=[common])
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor", parents=[common])
    show = commands.add_parser("show", parents=[common])
    show.add_argument("id")
    identifier = commands.add_parser("id", parents=[common])
    generator = identifier.add_subparsers(dest="operation", required=True).add_parser("new", parents=[common])
    generator.add_argument("type", choices=("DOC", "REQ", "UC", "ADR", "TASK", "CHG", "EVD"))
    generator.add_argument("--count", type=int, default=1)
    new = commands.add_parser("new", parents=[common])
    new.add_argument("--slug", required=True)
    new.add_argument("--locale")
    setup = commands.add_parser("project", parents=[common])
    setup_commands = setup.add_subparsers(dest="operation", required=True)
    setup_commands.add_parser("inspect", parents=[common])
    configure = setup_commands.add_parser("configure", parents=[common])
    configure.add_argument("--from", dest="source", required=True)
    configure.add_argument("--expect")
    status = commands.add_parser("status", parents=[common])
    status.add_argument("target", nargs="?", help="Plan CHG, DOC or project-relative path; omit to list plans.")
    status.add_argument("--simplified", action="store_true", help="Omit completed task details.")
    retirement = commands.add_parser("retire", parents=[common])
    retirement.add_argument("id")
    retirement.add_argument("--reason", required=True)
    retirement.add_argument("--replaced-by", action="append", default=[])
    retirement.add_argument("--apply", action="store_true")
    verify_parser = commands.add_parser("verify", parents=[common])
    verify_parser.add_argument("--dry-run", action="store_true")
    verify_parser.add_argument("--simplified", action="store_true")
    docs = commands.add_parser("docs", parents=[common])
    docs.add_subparsers(dest="operation", required=True).add_parser("build", parents=[common])
    args = parser.parse_args(argv)
    args.project = getattr(args, "project", None)
    args.format = getattr(args, "format", "text")
    args.diagnostic_locale = getattr(args, "diagnostic_locale", None)
    if args.diagnostic_locale is not None and not valid_locale(args.diagnostic_locale):
        raise ConfigurationError('--diagnostic-locale must be a language tag.')
    return args


def index(project):
    return validate(project.root, project.sources(), book_root=project.book_root,
                    retirement_directory=project.paths["retired"], section_redirects=project.section_redirects,
                    diagnostic_locale=project.diagnostic_locale)


def reserved_ids(project, registry):
    """Reserve even IDs in unfinished drafts without requiring valid documents."""
    pattern = re.compile(registry["id"]["pattern"].removeprefix("^").removesuffix("$"))
    paths = set(project.sources()) | set(project.output("retired").glob("*.jsonl"))
    identities = set()
    for path in paths:
        with contained(project.root, path).open(encoding="utf-8") as stream:
            for line in stream:
                identities.update(match[0] for match in pattern.finditer(line))
    return identities


def skeleton(project, args, registry, existing):
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", args.slug):
        raise ConfigurationError("--slug must contain lowercase ASCII words separated by hyphens.")
    locale = args.locale or project.locale
    if locale not in ("en", "zh-Hans"):
        raise ConfigurationError("Choose an available document language once: en or zh-Hans.")
    day = date.today()
    path = project.output("plans", day.strftime("%Y-%m/%Y%m%d-") + args.slug + ".md")
    if path.exists() or path.with_suffix("").exists():
        raise ConflictError(Message('Change or attachment path already exists: {arg0}', path.relative_to(project.root)))
    ids = {}
    for kind in ("DOC", "CHG", "TASK"):
        ids[kind + "_ID"] = new_id(kind, registry, existing, today=day)
        existing.add(ids[kind + "_ID"])
    labels = json.loads((ASSETS / f"locales/{locale}.json").read_text(encoding="utf-8"))
    values = ids | labels | {"LOCALE": locale}
    template = (ASSETS / registry["profiles"]["tao.project.plan/v0.1"]["template"]).read_text(encoding="utf-8")
    rendered = re.sub(r"\{\{([^}]+)\}\}", lambda m: values.get(m[1], m[0]), template)
    create_file(project.root, path, rendered)
    return {"path": path.relative_to(project.root).as_posix(), "ids": ids,
            "draft_complete": False}


def section_summary(project, document, section):
    start = document.sections.get(section)
    if start is None:
        return None
    lines = contained(project.root, document.path).read_text(encoding="utf-8").splitlines()
    end = min((line - 1 for line in document.sections.values() if line > start), default=len(lines))
    return re.sub(r"<!-- tao:section [^>]+ -->", "", "\n".join(lines[start:end])).strip()


def plan_status(project, result, target=None, *, simplified=False):
    plans = select_plans(result, target)
    rows = []
    linked = set()
    for plan in plans:
        for key in ("spec_docs", "design_docs"):
            values = plan.metadata.get(key)
            if isinstance(values, list):
                linked.update(value for value in values if isinstance(value, str))
        task_source = plan
        attachment = plan.metadata.get("tasks_doc")
        if attachment:
            definition = result.definitions.get(attachment) if isinstance(attachment, str) else None
            task_source = result.documents.get(definition.path) if definition else None
        task_paths = {plan.path, task_source.path if task_source else None}
        task_set_valid = task_source is not None and (
            not attachment or (
                task_source.metadata.get("schema") == "tao.project.tasks/v0.1"
                and task_source.metadata.get("change") == plan.metadata.get("change")
                and not plan.tasks))
        structural_rules = {"TAO-TASK-001", "TAO-DOC-001", "TAO-DOC-002", "TAO-ID-001", "TAO-ID-002"}
        if any(d.severity == "error" and d.rule_id in structural_rules
               and (d.path in task_paths or any(location["path"] in task_paths for location in d.related_locations))
               for d in result.diagnostics):
            task_set_valid = False
        tasks = [asdict(result.definitions[t]) for t in task_source.tasks
                 if t in result.definitions] if task_source else []
        pending = [task for task in tasks if task["status"] != "completed"]
        completed = len(tasks) - len(pending)
        progress = ("unavailable" if not task_set_valid else "planning" if not tasks
                    else "tasks_complete" if not pending else "in_progress" if completed else "pending")
        rows.append({"id": plan.metadata.get("id"), "change": plan.metadata.get("change"),
                     "path": plan.path, "title": plan.metadata.get("title", plan.path),
                     "progress": progress, "progress_basis": "inferred_from_tasks" if task_set_valid else "unavailable",
                     "task_source": task_source.path if task_source else None,
                     "task_set_valid": task_set_valid,
                     "task_counts": {"total": len(tasks), "completed": completed, "pending": len(pending)} if task_set_valid else None,
                     "tasks": pending if simplified else tasks, "pending_tasks": pending,
                     "verification_summary": section_summary(project, plan, "verification"),
                     "review": "unknown"})
    planning = [{"id": doc.metadata.get("id"), "path": doc.path, "title": doc.metadata.get("title", doc.path),
                 "progress": "planning", "review": "unknown"}
                for doc in result.documents.values()
                if target is None and doc.metadata.get("schema") in ("tao.project.spec/v0.1", "tao.project.design/v0.1")
                and (not isinstance(doc.metadata.get("id"), str) or doc.metadata["id"] not in linked)]
    return {"plans": rows, "planning": planning,
            "validation": "Read-only document diagnostics; task progress is not review or delivery certification.",
            "output_mode": "simplified" if simplified else "full"}


def verify(project, args, report):
    if args.dry_run:
        report["status"] = "planned"
        return report, 0
    if not project.sources():
        raise ConfigurationError("No managed documents matched the configured scope.")
    result = index(project)
    report["outputs"]["documents"] = result.to_dict()
    report["diagnostics"] = [asdict(d) for d in result.diagnostics]
    report["status"] = "passed" if result.valid else "failed"
    return report, 0 if result.valid else 1


def dispatch(args):
    registry = json.loads((ASSETS / "document-profiles.json").read_text(encoding="utf-8"))
    report = dict(tool="tao-dev", protocol_version="0.1", tool_version=__version__, command=args.command,
                  status="passed", diagnostics=[], outputs={})
    project = Project(args.project)
    project.diagnostic_locale = args.diagnostic_locale or project.diagnostic_locale
    if args.command == "doctor":
        report.update(capabilities=CAPABILITIES, schemas=list(registry["profiles"]))
        report["outputs"] = {"project": str(project.root), "python": sys.version.split()[0], "managed_sources": len(project.sources())}
        return report, 0
    if args.command == "project":
        from . import project_setup
        report["outputs"] = project_setup.inspect(project) if args.operation == "inspect" else project_setup.configure(project, args.source, args.expect)
        return report, 0
    if args.command == "docs":
        if "docs.build" not in CAPABILITIES:
            raise ConfigurationError("Publication dependencies are unavailable; consult requirements-publication.txt.")
        from .publication import build
        report["outputs"] = build(project)
        return report, 0
    if args.command == "verify":
        report, code = verify(project, args, report)
        return (simplified_verification(report), code) if args.simplified else (report, code)
    if args.command == "retire":
        from .retirement import retire
        outcome, code = retire(project, args.id, args.reason, args.replaced_by, apply=args.apply)
        report.update(outcome)
        return report, code
    if args.command == "id":
        report["outputs"]["ids"] = new_ids(args.type, args.count, registry, reserved_ids(project, registry))
        return report, 0
    if args.command == "new":
        # Check arguments before creating even a temporary lock.
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", args.slug):
            raise ConfigurationError("--slug must contain lowercase ASCII words separated by hyphens.")
        locale = args.locale or project.locale
        if locale is None:
            locales = {doc.metadata.get("locale") for doc in index(project).documents.values()}
            locale = next(iter(locales)) if len(locales) == 1 else None
        if locale not in ("en", "zh-Hans"):
            raise ConfigurationError("Choose an available document language once: en or zh-Hans.")
        args.locale = locale
        with mutation_lock(project):
            report["outputs"] = skeleton(project, args, registry, reserved_ids(project, registry))
        return report, 0
    result = index(project)
    if args.command == "show":
        target = result.definitions.get(args.id)
        if target is None:
            raise ConflictError("ID not found in the managed source and retirement index.")
        report["outputs"] = {"definition": asdict(target), "references": [asdict(r) for r in result.references if r.target == args.id], "url": None}
    elif args.command == "status":
        report["outputs"] = plan_status(project, result, args.target, simplified=args.simplified)
    report["diagnostics"] = [asdict(d) for d in result.diagnostics]
    if args.command in ("show", "status"):
        report["outputs"]["documents_valid"] = result.valid
        if not result.valid:
            report["status"] = "partial"
    return report, 0


def simplified_verification(report):
    """Keep document counts and actionable diagnostics, omit the full index."""
    outputs = report.get("outputs", {})
    docs = outputs.get("documents")
    if isinstance(docs, dict):
        outputs["documents"] = {"valid": docs.get("valid"), "counts": {
            "definitions": len(docs.get("definitions", {})), "references": len(docs.get("references", [])),
            "documents": len(docs.get("documents", {})), "section_redirects": len(docs.get("section_redirects", {}))},
            "deletion_checked": docs.get("deletion_checked")}
    report["output_mode"] = "simplified"
    return report


def main(argv=None):
    started = time.monotonic()
    argv = sys.argv[1:] if argv is None else argv
    output_format = "json" if "--format=json" in argv or any(argv[i:i + 2] == ["--format", "json"] for i in range(len(argv))) else "text"
    args = argparse.Namespace(command="unknown", format=output_format)
    try:
        args = arguments(argv)
        report, code = dispatch(args)
    except (OSError, ValueError) as exc:
        code = 1 if isinstance(exc, ConflictError) else 2
        report = dict(tool="tao-dev", protocol_version="0.1", tool_version=__version__, command=args.command,
                      status="failed" if code == 1 else "not_run", diagnostics=[{
                          "rule_id": "TAO-CLI-001", "severity": "error", **diagnostic(exc, configured_locale(argv))}], outputs={})
    report["duration_seconds"] = round(time.monotonic() - started, 6)
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"tao {args.command}: {report['status']}")
        for item in report["diagnostics"]:
            print(f"{item['rule_id']}: {item['message']}")
        print(json.dumps(report["outputs"], ensure_ascii=False, indent=2))
    return code
