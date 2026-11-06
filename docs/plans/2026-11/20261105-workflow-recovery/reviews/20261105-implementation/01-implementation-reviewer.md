---
schema: tao.project.evidence/v0.1
id: DOC_20261105_51AYAVQFYPJCP00B
title: 工作流恢复实现独立审查
locale: zh-Hans
status: draft
created: "2026-11-06"
evidence: EVD_20261105_MT80SY41XDZYF3JH
recorded_at: "2026-11-06T00:04:59.046493+08:00"
result: failed
coverage: partial
---

# 工作流恢复实现独立审查

<!-- tao:section scope -->
## 范围

本事项累计实现、相关设计和测试的独立实现初审；聚焦恢复、迁移、持久记录和收尾的一致性。批次开始于 2026-11-05，报告保存时间取本机时钟。

<!-- tao:section inputs -->
## 输入与环境

<!-- tao:field fingerprint -->
**输入指纹：** 7efd25ccfa38c223591ed3839cff4ed92c9a4590cd45bee942211927c7553183；基础 186ae92c674ef4e4c604556c01682f2dac51f2d8，目标 381130f1447c0b66d8d2f4046ab84ef015139ca3 加固定的工作区与暂存区内容。工作区快照 tmp/tao/review-inputs/ad9a3fa16fd74a229fb6847f5a272a25.zip 及对应 -index.zip；本批报告不计入输入。需求入口为[规格](../../../../../product/workflow-recovery.md)，实施范围见[计划](../../../20261105-workflow-recovery.md)。

<!-- tao:field environment -->
**环境：** 独立上下文子 agent implementation_review，供应商 OpenAI，实际模型未知；主 agent 核实并保存报告。串行一人，代码批次第 1/2 轮，未修改源代码，复现使用隔离临时目录。

<!-- tao:section checks -->
## 检查与结果

<!-- tao:field command -->
**方法：** 阅读固定代码及契约、追踪调用与失败序列，并在隔离目录复现确认；确定性检查由主 agent 执行。

<!-- tao:field expected -->
**预期：** 恢复不新增批准或审查额度，收尾满足当前门禁，合法文档能读回，迁移和同步不丢失持久事实。

<!-- tao:field observed -->
**观察：** 独立实现审查要求修改。确定性检查已覆盖核心回归及 15 次真实 CLI 调用（包括出版）；维护全量首轮 652 通过、12 失败、2 跳过，失败项重跑中。不能以部分通过宣称交付就绪。

<!-- tao:field reports -->
**报告：** [独立报告](01-implementation-reviewer.md)和[裁决](00-adjudication.md)。

<!-- tao:section findings -->
## 发现与限制

<!-- tao:field limits -->
**覆盖限制：** 本轮是独立模型上下文审查，不是受支持 CLI 原始回执；不冒充已满足 required_reviews 的机器证据。平台与真实客户端未覆盖项仍需单独报告。

Verdict: changes requested. Four confirmed defects: two high severity and two medium severity. No reviewed source files were edited.

### Scope and inputs

Reviewed fixed working snapshot `tmp/tao/review-inputs/ad9a3fa16fd74a229fb6847f5a272a25.zip` and the provided index snapshot. Baseline is `186ae92c674ef4e4c604556c01682f2dac51f2d8`; supplied target is `381130f` plus the implementation snapshot. The four primary live modules were byte-compared with the snapshot and matched. Reproductions import extracted snapshot modules, not mutable working files.

Read repository AGENTS.md, local skill workflow, engineering, review and report guidance, approved product specification and engineering design. Did not read author self-assessment or other reviewer findings. Scope includes new persistence/recovery modules and workflow, review, document validation integration. This is independent-context read-only code review via a delegated agent; supplier OpenAI, actual model identifier unknown. Execution: 2026-11-06, Asia/Singapore. No model dispatch or global/client configuration changes were performed.

### Checks

Executed `/Users/liuyubao/home/tao-dev/.venv/bin/python tmp/tao/repro-implementation.py` against fixed snapshot code. Reproductions and isolated fixtures are entirely under ignored `tmp/tao/`. Actual output is `tmp/tao/implementation-repro-output.txt`; the script preserves reproducible setup and calls. Full repository regression was not rerun by this reviewer; author-provided test summaries are contextual, not independently verified results.

### Findings

#### I1 — High, blocking: completion accepts code changed after its passed review

- Location: `plugins/tao-dev/skills/tao-dev/scripts/taolib/workflows.py:445-464`, particularly line 456.
- Contract: completed must satisfy current delivery and review conditions, not merely an earlier transition into finish.
- Trigger: finish-phase workflow previously passed scheduler code review; code changes before `workflow finish`; project has ordinary deterministic checks but no separately configured imported-review requirement.
- Evidence: isolated fixture used actual review preview/begin/finish, obtained `review_runs.passed(..., 'code') == True`, advanced to finish, changed `check.py`, and observed passed become False. Actual finish then executed its real configured check and persisted `lifecycle=completed`. No verification or review function was mocked. The fixture uses the internal mutation helper solely to establish a pre-review phase and known Git baseline; review, transition, changed input, and completion use actual public functions. Closure accepted empty evidence and unfinished arrays.
- Root cause: finish calls general verify, whose independent imports are optional policy, and checks document snapshot/phase/blockers/stale approvals, but never checks the scheduler code-review binding. The former passed review is not a permanent authorization for subsequently changed code.
- Consequence: durable completion can assert delivery after unreviewed changes. After copying formal records this invalid closure survives loss of local state.
- Minimal remedy: recheck the applicable review requirement at completion against current code/input state. Preserve the intended valid transition across phase bookkeeping without treating changed code as equivalent. Add a positive finish case plus a changed-code-after-review rejection case; checking only phase or only deterministic verification cannot satisfy this boundary.

#### I2 — High, blocking: unknown historical review budget resets to round 1 of 2

- Location: `workflow_recovery.py:63-65,83-85` and `review_runs.py:183-191` under the same taolib directory.
- Contract: missing review history must remain unknown; recovery must not reset remaining attempts and permit dispatch under an invented budget.
- Trigger: recover a valid legacy plan with no local JSON, then call review preview/begin without an explicit replacement budget decision.
- Evidence: actual recover writes provenance `unknown_fields: [lifecycle, approvals, baseline, review_batches]`, with an empty reviews mapping. Actual begin, with default max_rounds and new_batch=False, succeeds and creates `max_rounds=2`, round=1. Reproduction output records both facts. Recovery's generic blocker and unknown lifecycle do not stop review-begin.
- Root cause: unknown and known-empty review histories share `{}`; begin interprets absence of a series as a fresh allowance and does not consult durable unknown provenance.
- Consequence: exhausted/lost rounds can be silently replenished; a scheduler can dispatch more model calls without the required reconciliation or explicit additional-budget decision.
- Minimal remedy: carry the unknown-history marker into review scheduling; refuse default begin until explicit budget/history reconciliation establishes a new allowance, and persist that decision. Cover legacy recovery and migration with genuinely missing history, plus known fresh start as a valid counterexample.

#### I3 — Medium, blocking: valid triple-hyphen text makes newly generated records unreadable

- Location: `workflow_records.py:80`; same delimiter pattern also appears at lines 102 and in review_contract, and in workflows.artifact_digest.
- Contract: generated valid formal records must remain readable; normal text must not be confused with frontmatter delimiters.
- Trigger: start with summary `Support --- separators` (also applies to decisions/text containing three hyphens).
- Evidence: actual start succeeds; the generated record passes managed source validation (`True`), but immediate records.read raises ConfigurationError for that very record. No malformed input was injected.
- Root cause: `content.split('---', 2)[1]` closes frontmatter at any substring, including plain or quoted YAML values, instead of only a standalone delimiter line.
- Consequence: status, mutation and recovery encounter a corrupt-record failure on tool-generated valid content. The same parsing shortcut can break artifact binding or review normalization.
- Minimal remedy: share a line-delimited frontmatter extraction routine with the validator, applying it at all new occurrences; add records containing embedded `---` values and a real closing delimiter as regressions.

#### I4 — Medium, blocking: nested review record validation accepts unrecoverable state

- Location: `workflow_records.py:63-68`, consumed by `workflow_recovery.py:64-65` and `review_runs.py:198`.
- Contract: new formal profile rejects unknown fields, nested type errors and incomplete review attempts before recovery; persistent records must contain interpretable review history.
- Trigger: formal record has review_batches.code = `{max_rounds: 2, runs: [{id: arbitrary, outcome: passed}]}`. This can arise from a manual edit or merge dropping the request/timing/batch identity fields.
- Evidence: managed document validation returns True for this record; deleting local state and applying recovery also succeeds. Review preview then begin raises uncaught `KeyError: 'request'`. The reproduction uses actual source validator and recovery.
- Root cause: validation checks only max_rounds/list and per-run id/outcome, while downstream code assumes substantially more structure. Nested batch/run/closure/baseline mappings also lack the stated strict field contracts.
- Consequence: validator-approved formal sources can create a local state unusable by its next relevant operation, losing the actionable corruption boundary the recovery feature promises.
- Minimal remedy: validate the actual compact persisted representation recursively, including required batch/run request fields and types used by consumers; explicitly represent unsupported legacy facts as unknown rather than accepting incomplete current records. Add malformed nested examples and valid compact recovered-record counterexamples.

### Limitations

No separate stress/concurrency campaign or native client acceptance was conducted. Read-only code inspection covered locking and two-file write/reconcile paths but does not establish their fault tolerance. This review does not certify the broader release or model/client behavior. The reproduction's malformed baseline observation was exploratory and is not an additional finding. This temporary raw report is not a managed evidence document and was not passed through the document schema validator.

<!-- tao:section retention -->
## 保存

<!-- tao:field retention -->
**保存：** 报告作为发现处置与复核依据随项目保存；快照和原始复现输出留在忽略的临时目录。报告登记后不改写原发现。
