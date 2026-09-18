---
schema: tao.project.evidence/v0.1
id: "{{DOC_ID}}"
title: "{{TITLE}}"
locale: "{{LOCALE}}"
status: draft
created: "{{CREATED}}"
evidence: "{{EVD_ID}}"
recorded_at: "{{RECORDED_AT}}"
result: unknown
coverage: unknown
---

# {{TITLE}}

<!-- tao:section scope -->
## {{heading.scope}}

{{SCOPE}}

**{{label.review_time}}:** {{ACTUAL_REVIEW_TIME_WITH_SOURCE_OR_UNKNOWN}}

<!-- tao:section inputs -->
## {{heading.inputs}}

<!-- tao:field fingerprint -->
**{{label.fingerprint}}:** {{FINGERPRINT}}

<!-- tao:field environment -->
**{{label.environment}}:** {{REVIEWER_PROVIDER_MODEL_METHOD_EFFORT_INDEPENDENCE_ROUND_AND_ENVIRONMENT}}

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
**{{label.limits}}:** {{UNVERIFIED_SCOPE_AND_COVERAGE_LIMITS}}

### {{LOCAL_FINDING_ID_AND_TITLE}}

- **{{label.severity}}:** {{SEVERITY_AND_BLOCKING_CONDITION}}
- **{{label.location}}:** {{LOCATION_LINK_AND_LINE_OUTSIDE_LINK}}
- **{{label.constraint}}:** {{CONSTRAINT_WITH_NEED_REFERENCE_OR_SOURCE}}
- **{{label.trigger}}:** {{TRIGGER}}
- **{{label.evidence}}:** {{OBSERVED_EVIDENCE_OR_UNVERIFIED_HYPOTHESIS}}
- **{{label.impact}}:** {{IMPACT}}
- **{{label.remedy}}:** {{MINIMUM_REMEDY_OR_VERIFICATION}}

{{OTHER_FINDINGS_AND_UNRESOLVED_WORK_OR_NONE}}

**{{heading.next_impact}}:** {{IMPACT_ON_NEXT_ACTIONS_WITHOUT_INVENTING_AUTHORIZATION}}

<!-- tao:section retention -->
## {{heading.retention}}

<!-- tao:field retention -->
**{{label.retention}}:** {{RETENTION}}
