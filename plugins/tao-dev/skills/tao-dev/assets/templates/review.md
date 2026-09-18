---
schema: tao.project.evidence/v0.1
id: "{{DOC_ID}}"
title: "{{TITLE}}"
locale: "{{LOCALE}}"
status: draft
created: "{{CREATED}}"
evidence: "{{EVD_ID}}"
recorded_at: "{{RECORDED_AT}}"
result: "{{RESULT}}"
coverage: "{{COVERAGE}}"
---

# {{TITLE}}

<!-- tao:section scope -->
## {{heading.scope}}

{{SCOPE}}

**{{label.review_time}}:** {{REVIEW_TIME_AND_SOURCE}}

<!-- tao:section inputs -->
## {{heading.inputs}}

<!-- tao:field fingerprint -->
**{{label.fingerprint}}:** {{FINGERPRINT}}

<!-- tao:field environment -->
**{{label.environment}}:** {{REVIEWER_AND_ENVIRONMENT}}

<!-- tao:section checks -->
## {{heading.checks}}

<!-- tao:field command -->
**{{label.command}}:** {{COMMAND}}

<!-- tao:field expected -->
**{{label.expected}}:** {{EXPECTED}}

<!-- tao:field observed -->
**{{label.observed}}:** {{OBSERVED}}

<!-- tao:field reports -->
**{{label.reports}}:** {{REPORTS}}

<!-- tao:section findings -->
## {{heading.findings}}

<!-- tao:field limits -->
**{{label.limits}}:** {{LIMITS}}

### {{heading.defects}}

#### {{LOCAL_FINDING_ID_AND_TITLE}}

- **{{label.severity}}:** {{SEVERITY}}
- **{{label.location}}:** {{LOCATION}}
- **{{label.constraint}}:** {{CONSTRAINT}}
- **{{label.trigger}}:** {{TRIGGER}}
- **{{label.evidence}}:** {{EVIDENCE}}
- **{{label.impact}}:** {{IMPACT}}
- **{{label.remedy}}:** {{REMEDY}}

### {{heading.risks}}

{{RISKS}}

### {{heading.suggestions}}

{{SUGGESTIONS}}

### {{heading.accepted_limits}}

{{ACCEPTED_LIMITS}}

### {{heading.unresolved}}

{{UNRESOLVED}}

**{{label.next_impact}}:** {{NEXT_IMPACT}}

<!-- tao:section retention -->
## {{heading.retention}}

<!-- tao:field retention -->
**{{label.retention}}:** {{RETENTION}}
