"""Deterministic workflow operations; no model invocation or global setup."""

import argparse
from dataclasses import asdict
from datetime import date
import json
from pathlib import Path
import re
import sys

from . import __version__
from .documents import ASSETS, validate
from .identifiers import new_id
from .handoff import save as save_handoff
from .project import ConfigurationError, ConflictError, Project, create_file


CAPABILITIES = ["doctor", "id.new", "show", "new", "status", "handoff", "verify.docs"]


class ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise ConfigurationError(message)


def arguments(argv):
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--project", type=Path, default=argparse.SUPPRESS)
    common.add_argument("--format", choices=("text", "json"), default=argparse.SUPPRESS)
    parser = ArgumentParser(prog="tao", parents=[common])
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor", parents=[common])
    show = commands.add_parser("show", parents=[common])
    show.add_argument("id")
    identifier = commands.add_parser("id", parents=[common])
    generator = identifier.add_subparsers(dest="operation", required=True).add_parser("new", parents=[common])
    generator.add_argument("type", choices=("DOC", "REQ", "UC", "ADR", "TASK", "CHG", "EVD"))
    new = commands.add_parser("new", parents=[common])
    new.add_argument("--slug", required=True)
    new.add_argument("--locale")
    status = commands.add_parser("status", parents=[common])
    status.add_argument("change", nargs="?")
    handoff = commands.add_parser("handoff", parents=[common])
    handoff.add_argument("change", nargs="?")
    handoff.add_argument("--from", dest="source", required=True)
    verify = commands.add_parser("verify", parents=[common])
    verify.add_argument("change", nargs="?")
    verify.add_argument("--only")
    verify.add_argument("--scope", choices=("changed", "all"), default="changed")
    verify.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    args.project = getattr(args, "project", None)
    args.format = getattr(args, "format", "text")
    return args


def index(project):
    return validate(project.root, project.sources(), book_root=project.book_root,
                    retirement_directory=project.paths["retired"])


def skeleton(project, args, registry, result):
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", args.slug):
        raise ConfigurationError("--slug must contain lowercase ASCII words separated by hyphens.")
    locale = args.locale or project.locale
    if locale is None:
        locales = {doc.metadata["locale"] for doc in result.documents.values()}
        locale = next(iter(locales)) if len(locales) == 1 else None
    if locale not in ("en", "zh-Hans"):
        raise ConfigurationError("Choose an available document language once: en or zh-Hans.")
    day = date.today()
    path = project.output("changes", day.strftime("%Y-%m/%Y%m%d-") + args.slug + ".md")
    if path.exists() or path.with_suffix("").exists():
        raise ConflictError(f"Change or attachment path already exists: {path.relative_to(project.root)}")
    existing = set(result.definitions)
    ids = {}
    for kind in ("DOC", "CHG", "TASK"):
        ids[kind + "_ID"] = new_id(kind, registry, existing, today=day)
        existing.add(ids[kind + "_ID"])
    labels = json.loads((ASSETS / f"locales/{locale}.json").read_text())
    values = ids | labels | {"LOCALE": locale, "CREATED": day.isoformat()}
    template = (ASSETS / registry["profiles"]["tao.project.change/v0.1"]["template"]).read_text()
    rendered = re.sub(r"\{\{([^}]+)\}\}", lambda m: values.get(m[1], m[0]), template)
    # Template metadata remains a draft with a TITLE placeholder. No user
    # description is interpolated into YAML or a shell command.
    create_file(project.root, path, rendered)
    return {"path": path.relative_to(project.root).as_posix(), "ids": ids, "draft_complete": False}


def dispatch(args):
    project = Project(args.project)
    registry = json.loads((ASSETS / "document-profiles.json").read_text())
    report = dict(tool="tao-dev", protocol_version="0.1", tool_version=__version__, command=args.command,
                  status="passed", diagnostics=[], outputs={})
    if args.command == "doctor":
        report.update(capabilities=CAPABILITIES, schemas=list(registry["profiles"]))
        report["outputs"] = {"project": str(project.root), "python": sys.version.split()[0], "managed_sources": len(project.sources())}
        return report, 0
    if args.command == "verify":
        selected = args.only.split(",") if args.only else ["docs", "code", "evidence"]
        if not selected or len(set(selected)) != len(selected) or set(selected) - {"docs", "code", "evidence"}:
            raise ConfigurationError("--only accepts docs, code, evidence or a comma-separated combination.")
        missing = [item for item in selected if "verify." + item not in CAPABILITIES]
        report.update(coverage="partial" if args.only else "unknown", readiness="not-evaluated" if args.only else "blocked",
                      scope="all", selection_reason="No verified impact baseline; include all managed sources and global relationships.",
                      checks=selected, missing_capabilities=missing)
        if args.dry_run:
            report.update(status="planned" if not missing else "not_run", coverage="unknown", readiness="not-evaluated")
            return report, 2 if missing else 0
        result = index(project) if "docs" in selected else None
        if result is not None and not project.sources():
            raise ConfigurationError("No managed documents matched the configured scope.")
        if result is not None:
            report["outputs"]["documents"] = result.to_dict()
            report["diagnostics"] = [asdict(d) for d in result.diagnostics]
        if args.change and (result is None or args.change not in result.definitions or not args.change.startswith("CHG_")):
            raise ConfigurationError("Requested change is not in the managed index.")
        if missing:
            report["status"] = "not_run"
            return report, 2
        if result and not result.valid:
            report["status"] = "failed"
            return report, 1
        return report, 0
    result = index(project)
    if args.command in ("id", "new") and any(d.rule_id in ("TAO-DOC-001", "TAO-ID-002", "TAO-REF-004") for d in result.diagnostics):
        raise ConfigurationError("Cannot allocate IDs while the managed index has unreadable metadata, duplicate definitions or escaping paths.")
    if args.command == "show":
        target = result.definitions.get(args.id)
        if target is None:
            raise ConflictError("ID not found in the managed source and retirement index.")
        report["outputs"] = {"definition": asdict(target), "references": [asdict(r) for r in result.references if r.target == args.id], "url": None}
    elif args.command == "id":
        report["outputs"]["id"] = new_id(args.type, registry, result.definitions)
    elif args.command == "new":
        report["outputs"] = skeleton(project, args, registry, result)
    elif args.command == "handoff":
        report["outputs"] = save_handoff(project, args.source, args.change, result)
    elif args.command == "status":
        if args.change and (args.change not in result.definitions or not args.change.startswith("CHG_")):
            raise ConflictError("Change not found.")
        documents = list(result.documents.values())
        if args.change:
            documents = [d for d in documents if d.metadata.get("change") == args.change]
        tasks = [asdict(result.definitions[t]) for doc in documents for t in doc.tasks]
        report["outputs"] = {"tasks": tasks, "evidence_reusability": "not-evaluated", "validation": "source diagnostics only; no checks rerun"}
    report["diagnostics"] = [asdict(d) for d in result.diagnostics]
    if args.command in ("show", "status") and not result.valid:
        report["status"] = "failed"
        return report, 1
    return report, 0


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    output_format = "json" if any(argv[i:i + 2] == ["--format", "json"] for i in range(len(argv))) else "text"
    args = argparse.Namespace(command="unknown", format=output_format)
    try:
        args = arguments(argv)
        report, code = dispatch(args)
    except (OSError, ValueError) as exc:
        code = 1 if isinstance(exc, ConflictError) else 2
        report = dict(tool="tao-dev", protocol_version="0.1", tool_version=__version__, command=args.command,
                      status="failed" if code == 1 else "not_run", diagnostics=[{"rule_id": "TAO-CLI-001", "severity": "error", "message": str(exc), "message_locale": "en"}], outputs={})
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"tao {args.command}: {report['status']}")
        for diagnostic in report["diagnostics"]:
            print(f"{diagnostic['rule_id']}: {diagnostic['message']}")
        print(json.dumps(report["outputs"], ensure_ascii=False, indent=2))
        if "coverage" in report:
            print(f"coverage={report['coverage']} readiness={report['readiness']}")
    return code
