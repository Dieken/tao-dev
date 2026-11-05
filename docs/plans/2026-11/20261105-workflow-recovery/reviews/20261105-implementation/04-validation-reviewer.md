---
schema: tao.project.evidence/v0.1
id: DOC_20261106_CSRFYPEMPNV048TC
title: 恢复审查请求校验独立复核
locale: zh-Hans
status: draft
created: "2026-11-06"
evidence: EVD_20261106_GE319F37MSATWR3C
recorded_at: "2026-11-06T01:22:57.706751+08:00"
result: passed
coverage: partial
---

# 恢复审查请求校验独立复核

<!-- tao:section scope -->
## 范围

用户批准的额外一轮定向复核：此前 I4 的最终请求类型校验、身份绑定及直接影响。代码批次第 3/3 轮。

<!-- tao:section inputs -->
## 输入与环境

<!-- tao:field fingerprint -->
**输入指纹：** 7d0ed12a63cb45fb1b72b2eab618a5a0539e42dda0ec460f1b40681b7b16d3da；固定快照 tmp/tao/review-inputs/55e433f56e284bbb91bcc8f1b5734bb7.zip，SHA256 3a4c9e9124f5b1ddf92edece45c30400bbfce9b3abc2cd45927d679e38e6a45d；目标提交 cdcabdcc6747929c626d8b820b6504611ad6f3f7。

<!-- tao:field environment -->
**环境：** 独立上下文 implementation_review；OpenAI，实际模型未知，串行一人；主 agent 保存报告与裁决。未调用原生客户端，未安装测试包或修改全局配置。

<!-- tao:section checks -->
## 检查与结果

<!-- tao:field command -->
**方法：** 只读固定快照，追踪校验与恢复调用，隔离临时目录执行回归和反例。

<!-- tao:field expected -->
**预期：** 非法审查请求在源校验及恢复前被拒绝；合法 nullable 提交号不破坏失败登记。

<!-- tao:field observed -->
**观察：** 本轮结论 passed；实际执行与覆盖见下文。原有确定性回归 656 passed、2 skipped，最终定向 43 passed。

<!-- tao:field reports -->
**报告：** [前次发现与复核](02-followup-reviewer.md)；[本轮独立报告](04-validation-reviewer.md)。

<!-- tao:section findings -->
## 发现与限制

<!-- tao:field limits -->
**覆盖限制：** 本轮报告不是受支持 CLI 原始回执，不满足 required_reviews 的机器证据；原生客户端隔离异常与未完成的多会话验收仍阻断整体交付。

VERDICT: PASSED

### Extra targeted independent review: final I4 request validation

### Scope

**Verdict: passed within the authorized targeted scope.** The remaining I4 request-validation defect is resolved in this fixed snapshot. No new blocking findings were identified in the request type checks, CHG binding, nullable commit references, or the directly affected recovery/failure-recording path.

This is the explicitly authorized third round, limited to the final I4 repair and its effects. It is not a new comprehensive implementation review or delivery-readiness conclusion.

**Review time and source:** executed 2026-11-06, Asia/Singapore, using the project-local Python interpreter and the fixed input archives identified below.

### Inputs

**Fingerprint:** `tmp/tao/review-inputs/55e433f56e284bbb91bcc8f1b5734bb7.zip`, SHA-256 `3a4c9e9124f5b1ddf92edece45c30400bbfce9b3abc2cd45927d679e38e6a45d`. Matching index archive: `tmp/tao/review-inputs/55e433f56e284bbb91bcc8f1b5734bb7-index.zip`, SHA-256 `a1b8d24804a0f9e4298258550103658b8b9c6360bf9094f1d5ce2534c840e18c`. Both hashes were independently recomputed and matched the registered round.

Extracted implementation and tests to ignored `tmp/tao/extra-validation-snapshot/`; all reviewed code and executed test imports came from that fixed extraction. Inspected `workflow_records.validate_batch`, its top-level and archived-history callers, and the recovered running-review failure path. Compared the remaining I4 reproduction from the previous independent report with the new behavior.

**Environment:** independent-context delegated OpenAI reviewer; actual model identifier unknown. Invocation: agent tool/API session. Interpreter: `/Users/liuyubao/home/tao-dev/.venv/bin/python`. Offline wheelhouse: `/Users/liuyubao/home/tao-dev/tmp/tao/wheels`. No native agent client invocation, installation, global configuration reads/writes, source changes, or additional agent dispatch. Test runtime preparation used an isolated temporary tool runtime; it did not install any native client.

### Checks

**Commands:**

```text
TAO_TEST_WHEELHOUSE=/Users/liuyubao/home/tao-dev/tmp/tao/wheels /Users/liuyubao/home/tao-dev/.venv/bin/python -m pytest -q tmp/tao/extra-validation-snapshot/tests/test_workflow_recovery.py tmp/tao/extra-validation-snapshot/tests/test_review_runs.py tmp/tao/extra-validation-snapshot/tests/test_workflow_documents.py --basetemp=tmp/tao/extra-validation-pytest
/Users/liuyubao/home/tao-dev/.venv/bin/python tmp/tao/extra-validation-probe.py
```

**Expected:** malformed required request values and foreign CHG bindings are rejected at the formal source boundary before recovery creates state. Legitimate project-review requests with null commit references remain recoverable, and their interrupted running review can record a failed outcome. Existing affected workflow/document/review regressions remain passing.

**Observed:** **59 passed, 2 warnings in 23.87 seconds.** The tests include malformed values across every required request field, foreign CHG, optional output-file values, the original incomplete-record rejection, and the valid null-commit recovery path.

The separate independently assembled probe replayed the prior I4 trigger against the new snapshot:

```text
malformed request validates False
recovery rejected ConfigurationError
no local state created True
null commit recovered failure persisted failed
archived request CHG mismatch rejected True
```

Code inspection confirmed that required request keys are enforced, schema/kind use exact matching, scope is checked as a string before enum membership, change is a CHG-shaped string matching its owning workflow, both commit references are null or 40/64-character hexadecimal strings, input_digest is a 64-character hexadecimal string, and list-valued request fields contain nonempty strings. The owning CHG is passed through both current and archived batch validation.

**Reports:** raw deterministic output `tmp/tao/extra-validation-tests.txt`; independent probe source `tmp/tao/extra-validation-probe.py`; actual probe output `tmp/tao/extra-validation-probe.txt`. These remain ignored temporary artifacts.

### Findings

**I4 disposition:** resolved for the remaining request-validation defect. The prior accepted-list base_commit case now fails managed validation and recovery before any local state is created. The positive null-commit counterexample completes failure reconciliation and saves the failed outcome in the formal record. A foreign CHG in archived history is also rejected.

No additional confirmed defect or unproven risk is reported within this targeted change scope.

**Limits:** only the authorized I4 repair and directly affected regressions were independently checked. This result does not rerun or certify the entire maintained suite, native clients, concurrency stress, broader end-to-end acceptance, or overall delivery readiness. Prior I1-I3 dispositions remain those in the preceding report; this round does not expand their validation claims. The two pytest warnings do not change the passing test count.

**Next impact:** this review no longer blocks on I4. Any broader delivery or acceptance blockers remain for the primary agent to assess; this result grants no additional implementation, client-experiment, or integration authorization.

### Retention

**Retention:** temporary raw report follows the five-section review template. The primary agent assigns formal DOC/EVD identities, archives the actual report and performs managed document/schema validation. This raw report itself has no formal metadata and was not submitted to the document validator.


<!-- tao:section retention -->
## 保存

<!-- tao:field retention -->
**保留：** 本报告随事项保存，原始输出和固定快照位于忽略的 tmp/tao。历史报告保持原样。
