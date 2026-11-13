"""Export a versioned document ID baseline for repository CI."""

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/tao-dev/scripts"))

from taolib.documents import validate  # noqa: E402
from taolib.project import Project  # noqa: E402


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--source-revision", required=True)
    args = parser.parse_args(argv)
    if not args.source_revision.strip():
        parser.error("--source-revision must not be empty")

    project = Project(args.project)
    result = validate(
        project.root,
        project.sources(),
        book_root=project.book_root,
        retirement_directory=project.paths["retired"],
        section_redirects=project.section_redirects,
        diagnostic_locale=project.diagnostic_locale,
    )
    if not result.valid:
        print(json.dumps({"diagnostics": [asdict(item) for item in result.diagnostics]},
                         ensure_ascii=False, indent=2), file=sys.stderr)
        return 1
    manifest = {
        "schema_version": "1",
        "source_revision": args.source_revision,
        "ids": sorted(result.definitions),
    }
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
