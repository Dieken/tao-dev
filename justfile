# Deterministic project helpers; no global setup or workflow registration.
uvrun := "uv run --no-config --locked --extra publication"
tao := "uv run --no-config --locked --extra publication python skills/tao-dev/scripts/tao.py"

default:
    @just --list

# Run configured code checks and verify the distributed dependency inventory.
check:
    {{ tao }} verify --only code --no-reuse --format json
    {{ uvrun }} python scripts/export_dependencies.py --check

# Validate the managed book, then build it explicitly.
docs:
    {{ tao }} verify --only docs --simplified --format json
    {{ tao }} docs build --format json

# Choose a fresh output directory; never overwrite an existing package.
package output:
    {{ uvrun }} python scripts/package_skill.py --output {{ quote(output) }}

# Set the release version; dryrun reports without writing.
bump-version version="" dryrun="":
    {{ uvrun }} python scripts/bump_version.py {{ version }} {{ if dryrun == "" { "" } else { "--dry-run" } }}

tao *arguments:
    {{ tao }} {{ arguments }}
