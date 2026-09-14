#!/usr/bin/env python3
"""Read-only document validator; the workflow CLI consumes the same API."""

import argparse
import json
from pathlib import Path
import sys

from taolib.documents import validate
from tao_messages import configured_locale


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--book-root", type=Path)
    parser.add_argument("--diagnostic-locale")
    parser.add_argument("paths", nargs="+", help="Explicit managed Markdown paths relative to the project.")
    args = parser.parse_args(argv)
    if not args.project.is_dir():
        parser.error("--project must be an existing directory")
    try:
        result = validate(args.project, args.paths, book_root=args.book_root,
                          diagnostic_locale=configured_locale(sys.argv[1:] if argv is None else argv))
    except (OSError, ValueError) as exc:
        print(f"Cannot load validator resources: {exc}", file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        for item in result.diagnostics:
            print(f"{item.path}:{item.line}:{item.column}: {item.severity} {item.rule_id}: {item.message}")
        print(f"{'Passed' if result.valid else 'Failed'}: {len(result.documents)} documents, {len(result.definitions)} definitions.")
        print("Scope: source format and relationships; no historical deletion, generated HTML, semantic or execution acceptance.")
    return 0 if result.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
