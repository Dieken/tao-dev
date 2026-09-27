# Maintainer entry points. Checks come from the policy in .tao/config.toml so
# this file, `tao verify` and CI cannot describe different checks.

uvrun := "uv run --no-config --locked --extra publication"
tao := "uv run --no-config --locked --extra publication python plugins/tao-dev/skills/tao-dev/scripts/tao.py"

# Keep the bootstrapped runtime inside the project temporary root.
export TAO_RUNTIME_DIR := justfile_directory() / "tmp/tao/runtime"

# Show the available recipes.
default:
    @just --list

# Sync the locked environment, fetch the hash-pinned wheels and build the runtime.
[private]
prepare:
    {{ uvrun }} --help
    {{ uvrun }} python tests/acceptance/runtime.py --download
    {{ tao }} env prepare --wheelhouse tmp/tao/wheels --format json

# Run every maintainer check: configured policy, full pytest acceptance, and dependencies.
check: prepare
    {{ tao }} verify --only code --no-reuse --format json
    {{ uvrun }} python scripts/export_dependencies.py --check

# Check every managed document, then build the book and print its entry point.
docs: prepare
    {{ tao }} verify --only docs --format json
    {{ tao }} docs build --format json

# Build both plugin package formats; the outputs are regenerated each time.
package: prepare
    {{ uvrun }} python -c "import shutil; from pathlib import Path; [shutil.rmtree(Path(path), ignore_errors=True) for path in ('tmp/tao/public-plugin', 'tmp/tao/codex-plugin')]"
    {{ uvrun }} python scripts/package_plugin.py --format public --output tmp/tao/public-plugin
    {{ uvrun }} python scripts/package_plugin.py --format codex-legacy --output tmp/tao/codex-plugin

# Set the release version; empty means the next minor, `dryrun` reports only.
bump-version version="" dryrun="":
    {{ uvrun }} python scripts/bump_version.py {{ version }} {{ if dryrun == "" { "" } else { "--dry-run" } }}

# Run the source-local tao entry point, e.g. `just tao status`.
tao *arguments: prepare
    {{ tao }} {{ arguments }}
