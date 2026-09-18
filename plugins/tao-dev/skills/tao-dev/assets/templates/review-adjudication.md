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
**{{label.environment}}:** {{ADJUDICATOR_AND_ENVIRONMENT}}

| {{label.reports}} | {{label.focus}} | {{label.reviewer}} | {{label.method}} | {{label.independence}} | {{label.round}} |
|---|---|---|---|---|---|
| {{SOURCE_REPORT_LINK}} | {{REVIEW_FOCUS}} | {{REVIEWER_MODEL_PROVIDER}} | {{INVOCATION_AND_EFFORT}} | {{INDEPENDENCE}} | {{ROUND}} |

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

| {{label.finding}} | {{label.disposition}} | {{label.reason}} | {{label.followup}} |
|---|---|---|---|
| {{SOURCE_REPORT_LINK_AND_LOCAL_FINDING_ID}} | {{label.accepted}} / {{label.partial}} / {{label.deferred}} / {{label.rejected}} | {{RATIONALE}} | {{FOLLOWUP}} |

### {{heading.unresolved}}

{{UNRESOLVED}}

**{{label.next_impact}}:** {{NEXT_IMPACT}}

<!-- tao:section retention -->
## {{heading.retention}}

<!-- tao:field retention -->
**{{label.retention}}:** {{RETENTION}}
