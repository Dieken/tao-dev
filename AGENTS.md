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
their scope and implementation rationale are in `docs/document-contract.md`.
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
Full delivery verification, publication and dual-client behavioral
acceptance remain incomplete; source checks do not establish them.

# CLI experiments

Use the existing `claude` and `codex` commands and their configured
authentication. Do not reinstall or reconfigure either CLI for testing.

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
