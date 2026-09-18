---
schema: tao.project.evidence/v0.1
id: "{{DOC_ID}}"
title: "{{TITLE}}"
locale: "{{LOCALE}}"
status: draft
created: "{{CREATED}}"
evidence: "{{EVD_ID}}"
recorded_at: "{{RECORDED_AT}}"
result: not_run
coverage: unknown
---

# {{TITLE}}

<!-- tao:section scope -->
## {{heading.scope}}

{{SCOPE}}

<!-- tao:section inputs -->
## {{heading.inputs}}

<!-- tao:field fingerprint -->
**{{label.fingerprint}}:** {{FINGERPRINT}}

<!-- tao:field environment -->
**{{label.environment}}:** {{REVIEWER_PROVIDER_MODEL_METHOD_INDEPENDENCE_AND_ENVIRONMENT}}

<!-- tao:section checks -->
## {{heading.checks}}

<!-- tao:field command -->
**{{label.command}}:** {{ACTUAL_CHECK_COMMANDS_AND_REVIEW_METHOD}}

<!-- tao:field expected -->
**{{label.expected}}:** {{REVIEW_CRITERIA}}

<!-- tao:field observed -->
**{{label.observed}}:** {{CHECK_RESULTS_AND_SEPARATE_REVIEW_VERDICT}}

<!-- tao:field reports -->
**{{label.reports}}:** {{SOURCE_REPORT_LINKS_OR_NO_SEPARATE_REPORTS}}

<!-- tao:section findings -->
## {{heading.findings}}

<!-- tao:field limits -->
**{{label.limits}}:** {{UNVERIFIED_SCOPE_AND_OPEN_ISSUES}}

{{FINDINGS_WITH_LOCATION_CONSTRAINT_TRIGGER_EVIDENCE_IMPACT_AND_MINIMUM_REMEDY}}

{{DISPOSITIONS_WITH_SOURCE_REPORT_LINKS_AND_REASONS_OR_NOT_YET_ADJUDICATED}}

<!-- tao:section retention -->
## {{heading.retention}}

<!-- tao:field retention -->
**{{label.retention}}:** {{RETENTION}}
