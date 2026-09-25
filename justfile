# Maintainer entry points. Checks come from the policy in .tao/config.toml so
# this file, `tao verify` and CI cannot describe different checks.

set shell := ["bash", "-euo", "pipefail", "-c"]

uvrun := "uv run --no-config --locked --extra publication"
python := ".venv/bin/python"
tao := ".venv/bin/python plugins/tao-dev/skills/tao-dev/scripts/tao.py"

# Keep the bootstrapped runtime inside the project temporary root.
export TAO_RUNTIME_DIR := justfile_directory() / "tmp/tao/runtime"
export TAO_PYTHON := justfile_directory() / ".venv/bin/python"

# Show the available recipes.
default:
    @just --list

# Sync the locked environment, fetch the hash-pinned wheels and build the runtime.
[private]
prepare:
    {{ uvrun }} --help > /dev/null
    {{ uvrun }} python tests/acceptance/runtime.py --download
    {{ tao }} env prepare --wheelhouse tmp/tao/wheels --format json

# Run every maintainer check: the configured policy, the dependency export and the native client probes.
check: prepare
    {{ tao }} verify --only code --format json
    {{ uvrun }} python scripts/export_dependencies.py --check
    # Native probes auto-skip any of claude/codex/cursor that is missing or not
    # logged in. CI sets TAO_TEST_NATIVE_CLIENTS=1 to require only the CLI.
    {{ uvrun }} python -m pytest tests/test_install_clients.py -k native -q

# Check every managed document, then build the book and print its entry point.
docs: prepare
    {{ tao }} verify --only docs --format json
    {{ tao }} docs build --format json

# Build both plugin package formats; the outputs are regenerated each time.
package: prepare
    rm -rf tmp/tao/public-plugin tmp/tao/codex-plugin
    {{ python }} scripts/package_plugin.py --format public --output tmp/tao/public-plugin
    {{ python }} scripts/package_plugin.py --format codex-legacy --output tmp/tao/codex-plugin

# Set the release version; empty means the next minor, `dryrun` reports only.
bump-version version="" dryrun="":
    {{ uvrun }} python scripts/bump_version.py {{ version }} {{ if dryrun == "" { "" } else { "--dry-run" } }}

# Run the source-local tao entry point, e.g. `just tao status`.
tao *arguments: prepare
    {{ tao }} {{ arguments }}
