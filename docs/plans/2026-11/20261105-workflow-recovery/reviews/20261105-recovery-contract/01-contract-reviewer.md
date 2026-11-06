---
schema: tao.project.evidence/v0.1
id: DOC_20261105_QBWN2J1BNFCXKB5X
title: 工作流恢复独立文档审查
locale: zh-Hans
status: draft
created: "2026-11-05"
evidence: EVD_20261105_K46D4XFWHSXP3SGK
recorded_at: "2026-11-05T23:15:26.241398+08:00"
result: failed
coverage: partial
---

# 工作流恢复独立文档审查

<!-- tao:section scope -->
## 范围

本事项 spec、design、plan/tasks 及累计文档改动的第一轮正式文档审查。结论针对设计可实现性和契约一致性，不要求当前实现已满足未来设计。尚未修订受检文档。

**执行时间：** 本轮于 2026-11-05 执行，保存时间取本机时钟。

<!-- tao:section inputs -->
## 输入与环境

<!-- tao:field fingerprint -->
**输入指纹：** 基础提交 186ae92c674ef4e4c604556c01682f2dac51f2d8，目标提交 2cd1cdeb2e31723d7e3d16a29c6bd79437c38a5a，输入摘要 092f34ee82bf1e3e069fe150bc348e715585acbd5d4bd0a9254456834304cbff。固定工作区快照 tmp/tao/review-inputs/9fd6096b9f6845998a93c1a54fc354b8.zip，暂存区快照为同名 -index.zip；批次自身报告目录不参与输入。当前源入口为[规格](../../../../../product/workflow-recovery.md)、[设计](../../../../../engineering/workflow-recovery.md)与[计划](../../../20261105-workflow-recovery.md)。

<!-- tao:field environment -->
**环境：** 独立 Codex 子 agent document_review；供应商 OpenAI，实际模型未知；独立上下文、串行一人，第一轮。未读取作者自评段落，未修改源文档，未调用外部 CLI 或其他供应商。

<!-- tao:section checks -->
## 检查与结果

<!-- tao:field command -->
**方法：** 读取固定文档、相关实现与约束，追踪迁移、恢复、批准和收尾的可达操作序列；源格式另用 tao verify --only docs 检查。

<!-- tao:field expected -->
**预期：** 各受支持旧资料均有保留真实信息的迁移路径，恢复不会制造授权或生命周期事实，设计足以支撑计划任务。

<!-- tao:field observed -->
**观察：** 受检 spec/design/plan 源检查通过；语义审查要求修改。报告与导航另做源校验，格式通过不代表缺陷已消除。未执行新功能行为测试或 HTML 出版。

<!-- tao:field reports -->
**报告：** [独立报告](01-contract-reviewer.md)和[逐项裁决](00-adjudication.md)共同保留来源与处置。

<!-- tao:section findings -->
## 发现与限制

<!-- tao:field limits -->
**覆盖限制：** 一名独立上下文审查者，第一轮，默认最多两轮。静态契约审查不证明并发或运行时正确性；本报告不替代必需实现审查的机器回执。

### A — readable legacy JSON has no defined migration application path

Severity: medium (P2). Blocking: yes, for implementing the promised selected legacy-state migration; not a present-code regression.

Primary location: `docs/engineering/workflow-recovery.md:82-85`, `:100`, `:109`. Supporting commitment: `:75`, `docs/product/workflow-recovery.md:135-138`, and plan `:91-94`.

Trigger: an existing pre-feature CHG has a readable `.tao/workflows/<CHG>.json` but no formal workflow record (including the expressly supported JSON-only, pre-plan case). The user previews and requests migration of that selected CHG.

Evidence: line 75 makes readable JSON the migration source. The only defined record-creating migration operation is `recover --apply` (line 83), but its contract is exclusive local-state creation and line 100 rejects every existing local file. `resume` only reconciles existing state (line 85); its described synchronization path presupposes an existing formal record (line 109). The design gives no existing-JSON migration branch in resume, a separate migration command, or an explicit source-file argument. Moving/deleting the only JSON to satisfy recover's absence prerequisite also removes its described discoverable migration source, losing approvals, baseline, and consumed review attempts. This is especially consequential for the JSON-only case.

Consequence: the implementation cannot satisfy both “use the readable legacy state as migration evidence” and “recover never changes an existing state” through the declared interface. An implementer must invent an additional migration behavior, or users must manually disturb the only source of unpersisted decisions.

Minimum remedy: define one explicit, previewable migration path for an existing valid legacy JSON, such as a selected-CHG resume migration branch or a dedicated migration operation. Specify source digest/revision checks, preservation of the existing JSON and unknown fields, record-first/local-sync failure behavior, and tests for JSON-only and JSON+plan inputs. Keep missing-state recovery's non-overwrite guarantee intact. This does not require a broad migration framework.

### B — new migrated records cannot encode an unknown legacy lifecycle

Severity: medium (P2). Blocking: yes, for the plan-only migration contract.

Primary location: `docs/engineering/workflow-recovery.md:57`, `:75`, `:83`, `:99`. Supporting commitment: `docs/product/workflow-recovery.md:135-138`, plan `:74`, `:94`, `:133`.

Trigger: a project has a legacy plan and no JSON or formal workflow record; there is no recorded decision proving whether the matter is active, paused, completed, or cancelled. The user applies recovery, which must also create a new formal record.

Evidence: line 75 requires lifecycle `unknown` for this exact source combination. Line 57 restricts persisted lifecycle to active/paused/completed/cancelled and explicitly does not put unknown in that enum; its missing-field fallback is described only for old records. Line 83 requires creating a new formal record on legacy recovery. Line 99 defines a conservative `spec` coordination phase but does not resolve the independent lifecycle field. No valid new-record representation or explicit lifecycle-decision input is specified for this case.

Consequence: a new migrated record either guesses a lifecycle, violating the unknown-versus-ended boundary, omits a field without a defined new-profile exception, or rejects a promised recovery case. Treating all such plans as active would recreate the explicitly prohibited misclassification of historical matters.

Minimum remedy: specify a schema-valid representation for unknown lifecycle in newly imported records (for example, an explicitly permitted absent lifecycle with legacy provenance), or require and record an explicit lifecycle decision before persisting that field. Define how recovery/status/selection handle it and test plan-only migration through apply and a subsequent fresh-directory read. Do not infer the decision from task checkboxes or current phase.

No additional substantive findings established. The record-per-CHG architecture and ordered two-file write strategy are reasonable within the stated scope; their eventual correctness still requires the planned failure-injection and integration checks. Review-binding normalization, finish retry ordering, and concurrency were examined as design risks, but this report does not assert unproven implementation defects in those areas.


<!-- tao:section retention -->
## 保存与后续

<!-- tao:field retention -->
**保存：** 报告作为本批发现与后续复核的正式依据随项目保存；原始快照和临时输出保持忽略，不要求提交。快照过期不改变本次审查历史结论。
