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
documents. Keep reusable rules in the skill and project-specific
requirements, implementation design, and tasks in `docs/`. Existing
internal document profiles remain a separately reported migration scope;
do not use them as templates for new documents or claim they already
pass the shared format. Preserve existing IDs and content when migrating.

The product CLI and complete AST validator are not implemented. Report
the actual scope of manual or temporary checks without claiming product
CLI, publication, or dual-client behavioral acceptance.

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
