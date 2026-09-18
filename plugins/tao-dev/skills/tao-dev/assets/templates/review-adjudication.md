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
**{{label.environment}}:** {{ADJUDICATOR_AND_ENVIRONMENT}}

| {{label.reports}} | {{label.focus}} | {{label.reviewer}} | {{label.method}} | {{label.independence}} | {{label.round}} |
|---|---|---|---|---|---|
| {{SOURCE_REPORT_LINK}} | {{REVIEW_FOCUS}} | {{ACTUAL_REVIEWER_MODEL_PROVIDER_OR_UNKNOWN}} | {{ACTUAL_INVOCATION_AND_EFFORT_OR_UNKNOWN}} | {{ACTUAL_INDEPENDENCE_OR_UNKNOWN}} | {{ACTUAL_ROUND_OR_UNKNOWN}} |

<!-- tao:section checks -->
## {{heading.checks}}

<!-- tao:field command -->
**{{label.command}}:** {{ACTUAL_CHECKS_AND_ADJUDICATION_METHOD}}

<!-- tao:field expected -->
**{{label.expected}}:** {{ADJUDICATION_CRITERIA_AND_DECISION_RULES}}

<!-- tao:field observed -->
**{{label.observed}}:** {{CHECK_RESULTS_AND_SEPARATE_REVIEW_VERDICT}}

<!-- tao:field reports -->
**{{label.reports}}:** {{SOURCE_REPORT_LINKS_OR_NO_SEPARATE_REPORTS}}

<!-- tao:section findings -->
## {{heading.findings}}

<!-- tao:field limits -->
**{{label.limits}}:** {{UNVERIFIED_SCOPE_AND_COVERAGE_LIMITS}}

### {{heading.accepted}}

| {{label.finding}} | {{label.disposition}} | {{label.reason}} | {{label.followup}} |
|---|---|---|---|
| {{ACCEPTED_SOURCE_REPORT_LINK_AND_LOCAL_FINDING_ID}} | {{ACCEPTED_DISPOSITION_SCOPE}} | {{ACCEPTED_RATIONALE_WITH_EVIDENCE}} | {{ACCEPTED_REMAINING_WORK_OR_REVISIT_CONDITION_OR_NONE}} |

### {{heading.partial}}

| {{label.finding}} | {{label.disposition}} | {{label.reason}} | {{label.followup}} |
|---|---|---|---|
| {{PARTIAL_SOURCE_REPORT_LINK_AND_LOCAL_FINDING_ID}} | {{PARTIAL_DISPOSITION_SCOPE}} | {{PARTIAL_RATIONALE_WITH_EVIDENCE}} | {{PARTIAL_REMAINING_WORK_OR_REVISIT_CONDITION_OR_NONE}} |

### {{heading.deferred}}

| {{label.finding}} | {{label.disposition}} | {{label.reason}} | {{label.followup}} |
|---|---|---|---|
| {{DEFERRED_SOURCE_REPORT_LINK_AND_LOCAL_FINDING_ID}} | {{DEFERRED_DISPOSITION_SCOPE}} | {{DEFERRED_RATIONALE_WITH_EVIDENCE}} | {{DEFERRED_REMAINING_WORK_OR_REVISIT_CONDITION_OR_NONE}} |

### {{heading.rejected}}

| {{label.finding}} | {{label.disposition}} | {{label.reason}} | {{label.followup}} |
|---|---|---|---|
| {{REJECTED_SOURCE_REPORT_LINK_AND_LOCAL_FINDING_ID}} | {{REJECTED_DISPOSITION_SCOPE}} | {{REJECTED_RATIONALE_WITH_EVIDENCE}} | {{REJECTED_REMAINING_WORK_OR_REVISIT_CONDITION_OR_NONE}} |

### {{heading.unresolved}}

{{UNRESOLVED_ISSUES_AND_UNCERTAINTIES_OR_NONE}}

### {{heading.next_impact}}

{{IMPACT_ON_NEXT_ACTIONS_WITHOUT_INVENTING_AUTHORIZATION}}

<!-- tao:section retention -->
## {{heading.retention}}

<!-- tao:field retention -->
**{{label.retention}}:** {{RETENTION}}
