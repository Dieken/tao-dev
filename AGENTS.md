# Repository scope

This directory is an independent Git repository. Run Git commands from
this repository. Do not track it in the enclosing repository or register
it as a submodule.

# Develop with tao-dev

Read `plugins/tao-dev/skills/tao-dev/SKILL.md` and its relevant bundled
references when developing this project. This is a project-local source
entry point; it does not install or register a plugin. `CLAUDE.md` imports
this guidance for the other target client.

Use the bundled document profiles and templates for new delivery
documents. Bundle a resource only when a consuming project's LLM reads
it as instructions or a runtime component loads, executes, renders, or
validates with it. Reusability and self-hosting alone do not justify
distribution. Keep documentation used only to develop or maintain
tao-dev in top-level `docs/`, including CLI implementation design and
project requirements, tasks, and test reports. Split mixed-purpose
documents and identify each bundled resource's reader or runtime caller.
Development documents use the same shared profiles as consuming projects;
their scope and implementation rationale are in `docs/engineering/documentation/contract.md`.
Check each document against its declared schema and report the actual
validation scope. Preserve existing IDs and references when editing.

Keep maintained documentation focused on current behavior, constraints
and useful design rationale. Leave superseded arrangements and routine
relocation history in Git rather than repeating them in active guidance.

Keep routine validation summaries in the change plan. Raw command output
and detailed reports belong in ignored temporary storage or CI artifacts
by default. Retain separate evidence documents or raw data only when
independent references or explicit retention needs justify them. Log
expiry alone does not reverse historical results or task completion.

The bundled source validator and maintained regression tests are available.
Run the repository tests with the project-local Python environment and
validate only explicitly managed sources against supported profiles.
Use the bundled tao.py doctor output to identify available CLI commands.
Local HTML publication, configured code checks and evidence freshness
checks are available. Input-bound review imports are available. Native macOS client acceptance is recorded for the tested versions and
package formats. CI runs the maintained regression on Linux, macOS and
Windows across Python 3.11 to 3.14, and the native install probes with
the current Claude Code and Codex CLIs on the same three platforms.
Those probes drive installation, scope and removal only: no model call,
no client credential and no PowerShell launcher. Native Windows client
behavior acceptance and the current independent review therefore remain
incomplete; partial checks do not establish delivery readiness.

Always pass `--no-config` to `uv`. This machine's global `uv.toml`
declares a mirror index, so a bare `uv run` or `uv lock` re-resolves and
rewrites every registry and wheel URL in `uv.lock`, producing a large
diff nobody asked for. The justfile and CI already pass it; the gap is
an ad-hoc command typed during a session. For one-off calls prefer
`.venv/bin/python` directly, which is what the justfile's own `tao` and
`python` variables do. If `uv.lock` shows a mass URL change nobody
intended, it came from a bare `uv` invocation: restore it with
`git checkout uv.lock`.

# CLI experiments

These constraints govern experiments on a maintainer machine, where they
exist to protect personal client state. Use the existing `claude` and
`codex` commands and their configured authentication; do not reinstall
or reconfigure either CLI for testing.

Enable tao-dev only inside an isolated experiment project, using a
verified project-local or invocation-local loading mechanism. Changing
the working directory alone does not establish installation scope.
Never install or register the test skill or plugin globally, or change
global plugin, skill, marketplace, or hook configuration. Pass these
constraints to agents and scripts used during the experiment.

Verify both activation inside the experiment and absence outside it.
Keep test configuration and cleanup within the experiment scope. If the
selected CLI cannot provide the required isolation, report that test as
blocked rather than falling back to a global installation.

An ephemeral CI runner starts with neither CLI installed and holds no
personal state or credentials, so these constraints do not bind it. Its
workflow installs both CLIs and defines its own scope.

# Commits

Commit each completed, cohesive, independently reviewable change. Keep
unrelated work and incomplete changes out of the commit.

Always write commit messages in English. Use a concise summary, a blank
line, and a descriptive body explaining the context, resulting behavior,
implementation, and relevant validation or limitations. Use paragraphs
where helpful; do not reduce the message to a one-line summary.

Hard-wrap every body line at no more than 72 characters. Preserve actual
newlines. When using a message file, pass it with `git commit --file`.
Check the saved message's formatting before committing.
