# Repository scope

This directory is an independent Git repository. Run Git commands from
this repository. Do not track it in the enclosing repository or register
it as a submodule.

# Develop with tao-dev

Read `skills/tao-dev/SKILL.md` and its relevant bundled
references when developing this project. This is a project-local source
entry point. `CLAUDE.md` imports this guidance for the other target client.

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

The workflow is new (spec, design, plan), review doc, implement, review
code, with refine, status, continue and explicit handoff. Continue within
existing authorization; do not require step approvals, workflow
registration, review receipts or finish. The plan or its single task
attachment is the progress source. Checked tasks do not imply reviewed
or delivered; absent review evidence is unknown. Handoff replaces one
temporary Markdown summary and is not required to resume.

Use the bundled source validator and project-local Python environment
for explicitly requested checks. Local HTML publication and configured
code checks are separate from semantic review and actual client behavior.
Distribute the complete skill by project-local copying, or an optional
external skills tool. Document Claude, Codex, Cursor and Kiro discovery
paths; tao does not manage installation lifecycles or client configuration.
Report only exercised validation and its actual scope.
Prepare dependencies explicitly; reading or installing the skill must
not require publication dependencies or automatic environment setup.
Always pass `--no-config` to `uv`. This machine's global `uv.toml`
declares a mirror index, so a bare `uv run` or `uv lock` re-resolves and
rewrites every registry and wheel URL in `uv.lock`, producing a large
diff nobody asked for. The justfile and CI already pass it; the gap is
an ad-hoc command typed during a session. For one-off calls prefer
`.venv/bin/python` directly, which is what the justfile's own `tao` and
`python` variables do. If `uv.lock` shows unintended mass URL changes,
inspect the diff and preserve unrelated user changes when correcting it.

# CLI experiments

These constraints govern experiments on a maintainer machine, where they
exist to protect personal client state. Use the existing agent CLI commands
and their configured authentication; do not reinstall or reconfigure any
agent CLI for testing.

Enable tao-dev only inside an isolated experiment project, using a
verified project-local or invocation-local loading mechanism. Changing
the working directory alone does not establish installation scope.
Never install or register the test skill globally, or change global
client configuration. Pass these constraints to agents and scripts used
during the experiment.

Verify both activation inside the experiment and absence outside it.
Keep test configuration and cleanup within the experiment scope. If the
selected CLI cannot provide the required isolation, report that test as
blocked rather than falling back to a global installation.

CI file-deployment tests must remain project-scoped too. Real model
sessions require explicit authorization and a separately reported result;
file installation does not prove client discovery or agent behavior.

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
