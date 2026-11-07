---
schema: tao.project.plan/v0.1
id: "{{DOC_ID}}"
title: "{{TITLE}}"
locale: "{{LOCALE}}"
status: draft
# Link existing spec_docs/design_docs only when relevant; neither is a prerequisite.
# Use inline tasks by default, or tasks_doc for one attachment with the same change.
change: "{{CHG_ID}}"
---

# {{TITLE}}

<!-- tao:section scope -->
## {{heading.scope}}

{{SCOPE}}

<!-- tao:section references -->
## {{heading.references}}

{{REFERENCES}}

<!-- tao:section design -->
## {{heading.design}}

{{DESIGN_REFERENCE}}

<!-- tao:section tasks -->
## {{heading.tasks}}

- [ ] `{{TASK_ID}}` {{TASK_TITLE}}
  - verify: {{TASK_VERIFY}}

<!-- tao:section verification -->
## {{heading.verification}}

{{VERIFICATION}}

<!-- tao:section questions -->
## {{heading.questions}}

{{QUESTIONS}}
