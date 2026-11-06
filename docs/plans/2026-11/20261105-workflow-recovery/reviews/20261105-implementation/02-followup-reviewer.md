---
schema: tao.project.evidence/v0.1
id: DOC_20261106_FGYW2BP2SF6K11KG
title: 工作流恢复实现定向复核
locale: zh-Hans
status: draft
created: "2026-11-06"
evidence: EVD_20261106_4W03KCNMK4NJDC5P
recorded_at: "2026-11-06T00:19:01.124258+08:00"
result: failed
coverage: partial
---

# 工作流恢复实现定向复核

<!-- tao:section scope -->
## 范围

本事项累计实现、相关设计和测试的独立实现定向复核；聚焦恢复、迁移、持久记录和收尾的一致性。批次开始于 2026-11-05，报告保存时间取本机时钟。

<!-- tao:section inputs -->
## 输入与环境

<!-- tao:field fingerprint -->
**输入指纹：** 1ae14a8f7e36b942469bf349e52a657e2aa5a15e124f9e7d49c9ea79cf546120；基础 186ae92c674ef4e4c604556c01682f2dac51f2d8，目标 381130f1447c0b66d8d2f4046ab84ef015139ca3 加固定的工作区与暂存区内容。工作区快照 tmp/tao/review-inputs/c4c3fd1e2ae4495bb6dbd7bc4ebc3fad.zip 及对应 -index.zip；本批报告不计入输入。需求入口为[规格](../../../../../product/workflow-recovery.md)，实施范围见[计划](../../../20261105-workflow-recovery.md)。

<!-- tao:field environment -->
**环境：** 独立上下文子 agent implementation_review，供应商 OpenAI，实际模型未知；主 agent 核实并保存报告。串行一人，代码批次第 2/2 轮，未修改源代码，复现使用隔离临时目录。

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

Verdict: changes requested for the remaining portion of I4. I1, I2 and I3 are resolved in the reviewed scope; I4 is partially resolved. No additional independent round is authorized or implied by this report.

### Inputs and method

Fixed snapshot: `tmp/tao/review-inputs/c4c3fd1e2ae4495bb6dbd7bc4ebc3fad.zip` and matching `-index.zip`. The five primary changed modules, including new frontmatter.py, were byte-compared against the live files and matched. Tests and the extra probe imported extracted snapshot code under `tmp/tao/implementation-followup-snapshot/`. This follows the first report `tmp/tao/implementation-review.md` and reviews I1-I4 fixes and their directly affected behavior, not a new broad review.

Actual execution: 2026-11-06, Asia/Singapore. Reviewer: independent-context OpenAI agent, actual model identifier unknown, delegated read-only call. No source edits, model dispatch, global configuration changes or client installation. Test runtime preparation and reproduction data were isolated temporary artifacts.

### Verification

Ran project-local Python with the repository's existing offline wheelhouse against extracted tests:

`TAO_TEST_WHEELHOUSE=/Users/liuyubao/home/tao-dev/.worktrees/workflow-recovery/tmp/tao/wheels /Users/liuyubao/home/tao-dev/.venv/bin/python -m pytest -q tmp/tao/implementation-followup-snapshot/tests/test_workflow_recovery.py tmp/tao/implementation-followup-snapshot/tests/test_review_runs.py tmp/tao/implementation-followup-snapshot/tests/test_workflows.py --basetemp=tmp/tao/implementation-followup-pytest`

Result: **53 passed, 2 warnings in 33.00s**. Actual log: `tmp/tao/implementation-followup-tests-retry.txt`. An initial attempt omitted the wheelhouse environment override and produced 53 fixture-setup errors; no product tests ran in that attempt. Its raw log remains `tmp/tao/implementation-followup-tests.txt`.

Also ran `/Users/liuyubao/home/tao-dev/.venv/bin/python tmp/tao/implementation-followup-probe.py`. Actual output: `tmp/tao/implementation-followup-probe.txt`.

### Findings disposition

| Finding | Disposition | Independent evidence |
|---|---|---|
| I1 | Resolved | finish now rechecks scheduler code-review currentness under mutation; actual configured verification tests cover unchanged-code completion and changed-code rejection. Phase normalization keeps the legitimate transition current. |
| I2 | Resolved | Missing review history persists as an unknown allowance marker; default begin and new_batch without explicit max_rounds fail. Explicit new allowance persists and clears only its corresponding review kind. Targeted tests pass. |
| I3 | Resolved | Shared frontmatter extraction recognizes standalone delimiter lines. Embedded triple hyphens in summaries, artifact titles and approval decisions round-trip; binding and recovery tests pass. Duplicate/alias rejection was inspected. |
| I4 | Partially resolved, remains blocking | Original incomplete batch/request fixture is rejected before recovery, but required request fields still lack type checks and an accepted malformed record still crashes its consumer. Reproduction below. |

#### I4 remaining — Medium, blocking: request base_commit type is not validated

- Location: `plugins/tao-dev/skills/tao-dev/scripts/taolib/workflow_records.py:110-118` (validate_batch request validation), consumed by `review_runs.py:78-80` and the repreview call in review finish.
- Constraint: the formal profile must reject nested type errors before creating recoverable local state; malformed formal sources must produce an actionable validation boundary rather than a traceback during reconciliation.
- Trigger: start an actual review in an isolated Git project; in its formal record, set the running request's `scope` to `feature` and `base_commit` to the YAML list `['invalid type']`; remove local state and recover. This represents a malformed edited/merged source, not a supported alternative base representation.
- Actual evidence: source validation prints `malformed request validates True`; recovery applies; actual `review_runs.finish(..., outcome='failed', reports=[], summary='Interrupted review reconciliation')` raises `AttributeError: 'list' object has no attribute 'startswith'`. No product functions were mocked. All writes were in an ignored isolated probe directory. The probe script and raw output are retained above.
- Root cause: required_request enforces key presence and validates scope/kind/input_digest/list filters, but does not check the types of base_commit, target_commit or change. The consumer treats a nonempty base as a string and calls startswith before the failed-run reconciliation can finish. Its catch covers OSError/ValueError, not this type error.
- Consequence: validator-approved formal metadata can still reconstruct a local running-review state that cannot record its failed result, retaining the unrecoverable-state failure class from I4.
- Minimal remedy: validate all required request values according to their actual producer/consumer contract (including nullable string commit references and CHG identity), and reject malformed nested records before recovery. Cover this running-review failure path and a legitimate null-base project review. Do not merely catch the AttributeError and accept malformed data as current-schema history.

### Limits

This final review does not certify full-suite, native client, concurrency stress or overall delivery readiness. The targeted tests are real deterministic coverage, not a replacement for pending native checks. No additional speculative issues are reported. This is a temporary raw review report, not a managed evidence document; no document-schema validation was applied to this report itself.

<!-- tao:section retention -->
## 保存

<!-- tao:field retention -->
**保存：** 报告作为发现处置与复核依据随项目保存；快照和原始复现输出留在忽略的临时目录。报告登记后不改写原发现。
