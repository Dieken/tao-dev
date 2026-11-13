"""Write a temporary, machine-readable index of repository CI evidence."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/tao-dev/scripts"))

from taolib import __version__ as tao_version  # noqa: E402


STATUSES = {
    "passed": "passed",
    "success": "passed",
    "failed": "failed",
    "failure": "failed",
    "not_run": "not_run",
    "skipped": "not_run",
    "cancelled": "not_run",
    "unknown": "unknown",
}


def parse_check(value):
    name, separator, status = value.partition("=")
    if not separator or not name or status not in STATUSES:
        raise argparse.ArgumentTypeError(
            "checks must be NAME=STATUS with a supported status"
        )
    return name, STATUSES[status]


def project_path(value):
    supplied = Path(value)
    if supplied.is_absolute() or ".." in supplied.parts:
        raise ValueError(f"Evidence attachment must be project-relative: {value}")
    path = (ROOT / supplied).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError(f"Evidence attachment escapes the project: {value}")
    return supplied.as_posix(), path


def attachment(value):
    relative, path = project_path(value)
    if not path.is_file():
        return None
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return {"path": relative, "sha256": digest, "bytes": path.stat().st_size}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("tmp/tao/evidence.json"))
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--check", action="append", type=parse_check, required=True)
    parser.add_argument("--attachment", action="append", default=[])
    args = parser.parse_args(argv)
    if not args.run_id.strip() or not args.commit.strip():
        parser.error("--run-id and --commit must not be empty")
    names = [name for name, _ in args.check]
    if len(names) != len(set(names)):
        parser.error("check IDs must not be repeated")

    output_name, output = project_path(args.output.as_posix())
    temporary_root = (ROOT / "tmp/tao").resolve()
    if not output.is_relative_to(temporary_root):
        parser.error("--output must be inside tmp/tao")
    found = []
    missing = []
    for value in args.attachment:
        item = attachment(value)
        if item is None:
            missing.append(Path(value).as_posix())
        else:
            found.append(item)
    checks = [{"id": name, "status": status} for name, status in args.check]
    report = {
        "schema_version": "1",
        "run_id": args.run_id,
        "commit_sha": args.commit,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tool_versions": {"python": platform.python_version(), "tao-dev": tao_version},
        "environment": {
            "platform": sys.platform,
            "platform_release": platform.release(),
            "machine": platform.machine(),
            "runner_os": os.environ.get("RUNNER_OS"),
            "runner_arch": os.environ.get("RUNNER_ARCH"),
            "runner_image": os.environ.get("ImageOS"),
            "runner_image_version": os.environ.get("ImageVersion"),
        },
        "checks": checks,
        "attachments": found,
        "missing_attachments": missing,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".evidence-", dir=output.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.replace(temporary, output)
    finally:
        Path(temporary).unlink(missing_ok=True)
    print(output_name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
