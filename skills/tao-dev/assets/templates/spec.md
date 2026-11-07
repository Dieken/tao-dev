---
schema: tao.project.spec/v0.1
id: "{{DOC_ID}}"
title: "{{TITLE}}"
locale: "{{LOCALE}}"
status: draft
created: "{{CREATED}}"
---

# {{TITLE}}

<!-- tao:section scope -->
## {{heading.scope}}

{{SCOPE}}

<!-- tao:section terms -->
## {{heading.terms}}

{{TERMS}}

<!-- tao:section requirements -->
## {{heading.requirements}}

```{req} {{REQ_TITLE}}
:id: {{REQ_ID}}
:status: proposed

{{REQ_BODY}}

<!-- tao:field acceptance -->
**{{label.acceptance}}:** {{REQ_ACCEPTANCE}}

<!-- tao:field source -->
**{{label.source}}:** {{REQ_SOURCE}}
```

<!-- tao:section cases -->
## {{heading.cases}}

```{uc} {{UC_TITLE}}
:id: {{UC_ID}}
:status: proposed
:verifies: {{REQ_ID}}

<!-- tao:field given -->
**{{label.given}}:** {{UC_GIVEN}}

<!-- tao:field when -->
**{{label.when}}:** {{UC_WHEN}}

<!-- tao:field then -->
**{{label.then}}:** {{UC_THEN}}
```

<!-- tao:section questions -->
## {{heading.questions}}

{{QUESTIONS}}
