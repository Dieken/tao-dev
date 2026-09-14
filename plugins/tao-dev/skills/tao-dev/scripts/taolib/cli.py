"""Deterministic workflow operations; no model invocation or global setup."""

import argparse
from dataclasses import asdict
from datetime import date
import json
from importlib.util import find_spec
from pathlib import Path
import re
import sys
import time

from . import __version__
from .verification import policy, execute, evidence, file_digest, digest_json
from .measurements import usage
from . import reviews
from .documents import ASSETS, validate
from .identifiers import new_id
from .handoff import save as save_handoff
from .project import ConfigurationError, ConflictError, Project, create_file


CAPABILITIES = ["doctor", "id.new", "show", "new", "status", "handoff", "review", "retire", "verify.docs"]
if all(find_spec(module) for module in ("sphinx", "myst_parser", "sphinx_book_theme")):
    CAPABILITIES.append("docs.build")


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
    review = commands.add_parser("review", parents=[common])
    review.add_argument("change")
    review.add_argument("--from", dest="source")
    retirement = commands.add_parser("retire", parents=[common])
    retirement.add_argument("id")
    retirement.add_argument("--reason", required=True)
    retirement.add_argument("--replaced-by", action="append", default=[])
    retirement.add_argument("--apply", action="store_true")
    handoff = commands.add_parser("handoff", parents=[common])
    handoff.add_argument("change", nargs="?")
    handoff.add_argument("--from", dest="source", required=True)
    verify = commands.add_parser("verify", parents=[common])
    verify.add_argument("change", nargs="?")
    verify.add_argument("--only")
    verify.add_argument("--scope", choices=("changed", "all"), default="changed")
    verify.add_argument("--dry-run", action="store_true")
    docs = commands.add_parser("docs", parents=[common])
    docs.add_subparsers(dest="operation", required=True).add_parser("build", parents=[common])
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


def document_snapshot(project):
    paths = set(project.sources()) | set(project.output('retired').glob('*.jsonl'))
    from .project import contained
    return digest_json([(p.relative_to(project.root).as_posix(), file_digest(contained(project.root, p))) for p in sorted(paths)])


def verify(project, args, report):
    if args.only == "":
        raise ConfigurationError("--only must name at least one supported check category.")
    selected = args.only.split(",") if args.only else ["docs", "code", "evidence"]
    if not selected or len(set(selected)) != len(selected) or set(selected) - {"docs", "code", "evidence"}:
        raise ConfigurationError("--only accepts docs, code, evidence or a comma-separated combination.")
    config = policy(project)
    missing = [item for item in selected if item != "docs" and config is None]
    report.update(coverage="partial" if args.only else "unknown", readiness="not-evaluated" if args.only else "blocked",
                  scope="all", selection_reason="No verified impact baseline; include all configured checks and global relationships.",
                  checks=selected, missing_capabilities=missing, target=args.change)
    if args.dry_run:
        report.update(status="planned" if not missing else "not_run", coverage="unknown", readiness="not-evaluated")
        report["outputs"]["commands"] = config["checks"] if config and "code" in selected else []
        return report, 2 if missing else 0
    documents_before = document_snapshot(project) if "docs" in selected else None
    result = index(project) if "docs" in selected or args.change or not args.only else None
    if "docs" in selected:
        if not project.sources():
            raise ConfigurationError("No managed documents matched the configured scope.")
        report["outputs"]["documents"] = result.to_dict()
        report["diagnostics"] = [asdict(d) for d in result.diagnostics]
    if args.change and (args.change not in result.definitions or not args.change.startswith("CHG_")):
        raise ConfigurationError("Requested change is not in the managed index.")
    if missing:
        report["status"] = "not_run"
        return report, 2
    codes = [1] if result is not None and not result.valid else []
    if config and any(item in selected for item in ('code', 'evidence')):
        measurement = usage(project, config.get('usage_reports', []))
        report['outputs']['usage'] = measurement
        for key, observed in [('max_model_tokens', 'model_tokens'), ('max_estimated_usd', 'estimated_usd')]:
            if key in config:
                if measurement[observed] is None:
                    report.update(status='not_run')
                    report['outputs']['budget_reason'] = f'{key} cannot be checked: usage is unknown.'
                    return report, 2
                if measurement[observed] > config[key]:
                    report.update(status='failed')
                    report['outputs']['budget_reason'] = f'{key} exceeded before starting project checks.'
                    return report, 1
    if "code" in selected:
        execution = execute(project, config)
        report["outputs"]["execution"] = execution
        codes.append(0 if execution["status"] == "passed" else 2 if execution["status"] == "not_run" else 1)
    if "evidence" in selected:
        current = evidence(project, config)
        report["outputs"]["evidence"] = current
        codes.append(0 if current["state"] == "reusable" else 1 if current["state"] in ("stale", "failed") else 2)
    if documents_before is not None and documents_before != document_snapshot(project):
        report['outputs']['documents_changed_during_checks'] = True
        codes.append(1)
    if not args.only:
        changes = [d for d in result.documents.values() if d.metadata.get("schema") == "tao.project.change/v0.1"]
        if not args.change and len(changes) == 1:
            args.change = changes[0].metadata["change"]
        if not args.change:
            report["outputs"]["missing_target"] = "Select the active change when the index does not identify exactly one."
            codes.append(2)
        else:
            report["target"] = args.change
            tasks = [t for d in changes if d.metadata["change"] == args.change for t in d.tasks]
            pending = list(tasks)
            required = set(tasks)
            while pending:
                source = pending.pop()
                for reference in result.references:
                    if reference.source == source and reference.relation == 'depends_on' and reference.target not in required:
                        required.add(reference.target)
                        pending.append(reference.target)
            open_tasks = [t for t in sorted(required) if t not in result.definitions or result.definitions[t].status != "completed"]
            report["outputs"]["open_tasks"] = open_tasks
            if not tasks or open_tasks:
                codes.append(1)
        if config.get("required_reviews"):
            rows = reviews.status(project, config, args.change)
            report["outputs"]["reviews"] = rows
            codes.extend(0 if row['state'] == 'satisfied' else 1 if row['state'] in ('stale', 'changes-requested') else 2 for row in rows)
    code = max(codes, default=0)
    report["status"] = "passed" if code == 0 else "not_run" if code == 2 else "failed"
    if not args.only and code == 0:
        report.update(coverage="complete", readiness="checks-satisfied")
    return report, code


def dispatch(args):
    registry = json.loads((ASSETS / "document-profiles.json").read_text())
    report = dict(tool="tao-dev", protocol_version="0.1", tool_version=__version__, command=args.command,
                  status="passed", diagnostics=[], outputs={})
    if args.command == "doctor" and args.project is None and not any((p / ".tao/config.toml").is_file() for p in [Path.cwd(), *Path.cwd().parents]):
        report.update(capabilities=CAPABILITIES + ["setup"], schemas=list(registry["profiles"]))
        return report, 0
    project = Project(args.project)
    if args.command == "doctor":
        report.update(capabilities=CAPABILITIES + (["verify.code", "verify.evidence"] if policy(project) else []), schemas=list(registry["profiles"]))
        report["outputs"] = {"project": str(project.root), "python": sys.version.split()[0], "managed_sources": len(project.sources())}
        return report, 0
    if args.command == "docs":
        if "docs.build" not in CAPABILITIES:
            raise ConfigurationError("Publication dependencies are unavailable; consult requirements-publication.txt.")
        from .publication import build
        report["outputs"] = build(project)
        return report, 0
    if args.command == "verify":
        return verify(project, args, report)
    if args.command == "retire":
        from .retirement import retire
        outcome, code = retire(project, args.id, args.reason, args.replaced_by, apply=args.apply)
        report.update(outcome)
        return report, code
    result = index(project)
    if args.command == "review":
        config = policy(project)
        if not config or args.change not in result.definitions or not args.change.startswith('CHG_') or not result.valid:
            raise ConfigurationError('Review requires configured verification and a valid indexed change.')
        if args.source:
            report['outputs'] = reviews.import_review(project, config, args.change, args.source)
        else:
            report['outputs']['request'] = {'schema': 'tao.review/v0.1', 'binding': reviews.binding(project, config, args.change),
                                           'required_reviews': config.get('required_reviews', []),
                                           'instruction': 'Review fixed inputs independently; import the actual conclusion with its source. This request is not a review result.'}
        return report, 0
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
        current = evidence(project, policy(project)) if policy(project) else {"state": "not-evaluated"}
        report["outputs"] = {"tasks": tasks, "evidence_reusability": current["state"], "evidence": current,
                             "validation": "source diagnostics and receipt freshness only; no checks rerun"}
        target = args.change or (documents[0].metadata.get('change') if len(documents) == 1 else None)
        if target and (target not in result.definitions or not target.startswith('CHG_')):
            raise ConfigurationError('Requested change is not in the managed index.')
        report['outputs']['reviews'] = reviews.status(project, policy(project), target)
    report["diagnostics"] = [asdict(d) for d in result.diagnostics]
    if args.command in ("show", "status") and not result.valid:
        report["status"] = "failed"
        return report, 1
    return report, 0


def main(argv=None, runtime_context=None):
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
                      status="failed" if code == 1 else "not_run", diagnostics=[{"rule_id": "TAO-CLI-001", "severity": "error", "message": str(exc), "message_locale": "en"}], outputs={})
    report["duration_seconds"] = round(time.monotonic() - started, 6)
    if args.command == "doctor" and runtime_context:
        report["outputs"]["runtime"] = runtime_context
        if "setup" not in report.get("capabilities", []):
            report.setdefault("capabilities", []).append("setup")
        if runtime_context.get("publication", {}).get("state") == "ready" and "docs.build" not in report["capabilities"]:
            report["capabilities"].append("docs.build")
    if args.command == "verify" and "coverage" not in report:
        report.update(coverage="unknown", readiness="not-evaluated" if getattr(args, "only", None) else "blocked")
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
