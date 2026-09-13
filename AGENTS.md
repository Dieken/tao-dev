# Repository scope

This directory is an independent Git repository. Run Git commands from
this repository. Do not track it in the enclosing repository or register
it as a submodule.

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
