---
schema: tao.project.tasks/v0.1
id: "{{DOC_ID}}"
title: "{{TITLE}}"
locale: "{{LOCALE}}"
status: draft
created: "{{CREATED}}"
# This is the single task attachment referenced by its owning plan's tasks_doc.
# Use the owning plan's change; do not duplicate its task set.
change: "{{CHG_ID}}"
---

# {{TITLE}}

<!-- tao:section scope -->
## {{heading.scope}}

{{SCOPE}}

<!-- tao:section tasks -->
## {{heading.tasks}}

- [ ] `{{TASK_ID}}` {{TASK_TITLE}}
  - relates: ["{{CHG_ID}}"]
  - depends_on: []
  - verify: {{TASK_VERIFY}}
