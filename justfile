# Deterministic project helpers; no global setup or workflow registration.
python := if os() == "windows" { ".venv/Scripts/python.exe" } else { ".venv/bin/python" }
tao := python + " skills/tao-dev/scripts/tao.py"

default:
    @just --list

# Project checks own their commands and artifacts; prepare the environment first.
check: test lint
    {{ python }} scripts/export_dependencies.py --check

test:
    {{ python }} tests/acceptance/quality.py

lint:
    {{ python }} -c "from pathlib import Path; Path('tmp/tao').mkdir(parents=True, exist_ok=True)"
    {{ python }} -m ruff check --select E9,F63,F7,F82 --output-format json --output-file tmp/tao/ruff.json skills/tao-dev/scripts scripts tests

# Validate the managed book, then build it explicitly.
docs:
    {{ tao }} verify --simplified --format json
    {{ tao }} docs build --format json

# Choose a fresh output directory; never overwrite an existing package.
package output:
    {{ python }} scripts/package_skill.py --output {{ quote(output) }}

# Set the release version; dryrun reports without writing.
bump-version version="" dryrun="":
    {{ python }} scripts/bump_version.py {{ version }} {{ if dryrun == "" { "" } else { "--dry-run" } }}

tao *arguments:
    {{ tao }} {{ arguments }}
