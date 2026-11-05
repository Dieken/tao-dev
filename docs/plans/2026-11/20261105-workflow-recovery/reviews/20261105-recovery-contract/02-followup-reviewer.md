---
schema: tao.project.evidence/v0.1
id: DOC_20261105_PP1WB7GCR9MRP1GG
title: 工作流迁移修订定向复核
locale: zh-Hans
status: draft
created: "2026-11-05"
evidence: EVD_20261105_FRHRYDXYD4AKDB1J
recorded_at: "2026-11-05T23:28:38.443413+08:00"
result: passed
coverage: partial
---

# 工作流迁移修订定向复核

<!-- tao:section scope -->
## 范围

对初审 A/B 的设计及计划修订作第二轮定向复核，核查迁移入口、unknown 表示及其恢复与校验影响；不扩展为实现验收。执行日期为 2026-11-05，记录时间取本机时钟。

<!-- tao:section inputs -->
## 输入与环境

<!-- tao:field fingerprint -->
**输入指纹：** bd22cc05a386af5ae2ba15cc8d6b46891eb539069d2d1b835677a60d0fae73aa；基础 186ae92c674ef4e4c604556c01682f2dac51f2d8，目标提交 79a249381f0c1b0da9b0319099bd8dd769c5b6c8 及预览固定的未提交设计与计划修订。快照 tmp/tao/review-inputs/64241fcf4d1c4419b651acefd63e6686.zip 及对应 -index.zip；源入口：[设计](../../../../../engineering/workflow-recovery.md)、[计划](../../../20261105-workflow-recovery.md)、[初审](01-contract-reviewer.md)。

<!-- tao:field environment -->
**环境：** OpenAI Codex 独立上下文子 agent document_review，同一审查者定向复核；实际模型未知。主 agent 负责核实与保存裁决，不计为第二审查者。本批第 2/2 轮。

<!-- tao:section checks -->
## 检查与结果

<!-- tao:field command -->
**方法：** 静态核对固定快照的设计契约、计划验收与初审发现，另运行 tao verify --only docs。

<!-- tao:field expected -->
**预期：** 旧 JSON 存在时有明确且保留源数据的迁移路径；旧计划可生成合法的 unknown 正式记录，后续查询和选择不伪造生命周期。

<!-- tao:field observed -->
**观察：** 定向文档复核通过，初审 A/B 已闭合；文档源检查通过，无诊断。没有实现、行为测试或出版验收结论。

<!-- tao:field reports -->
**报告：** [定向复核](02-followup-reviewer.md)与[复核裁决](03-followup-adjudication.md)。

<!-- tao:section findings -->
## 发现与限制

<!-- tao:field limits -->
**覆盖限制：** 仅审查本次修订及影响；首次报告保留原样。真实文件写入一致性与客户端行为仍须实施阶段验证。

### A — resolved

Original severity: P2, blocking. Residual severity: none.

`docs/engineering/workflow-recovery.md:85` and `:95-103` now define a separate `workflow migrate` path for readable existing JSON, including JSON-only and JSON+plan. Preview is read-only, and apply binds both revision and source digest. Lines 99-101 require lock-held rereading, original-byte comparison, preservation of unknown/local fields, record-first persistence, and explicit resume coordination after a second-write failure. Existing formal records do not trigger another migration. Thus users no longer need to remove the only legacy source to reach the defined migration operation, while recover retains its non-overwrite rule at line 111. The authorization sentence at line 101 also prevents ordinary continue from silently becoming migration authorization.

The plan includes the concrete migration cases and failure recovery in `docs/plans/2026-11/20261105-workflow-recovery.md:91-94` and `:133`; design line 163 adds stale-source/concurrency/repeated-migration and field-preservation checks. These are adequate commitments for the design-stage finding; actual behavior remains to be implemented and tested.

### B — resolved

Original severity: P2, blocking. Residual severity: none.

`docs/engineering/workflow-recovery.md:57` explicitly admits unknown for legacy imports and requires provenance identifying lifecycle as unknown; non-legacy unknown is rejected. Line 75 defines candidate retention, forbids equating unknown with active/ended, and requires an explicit decision for lifecycle conversion. Line 103 specifies the exact plan-only recovery result: unknown lifecycle, legacy provenance, empty closure, and spec as a coordination starting phase rather than approval. The fresh-directory read must retain unknown.

The plan adds schema-positive/schema-negative cases at `docs/plans/2026-11/20261105-workflow-recovery.md:74`, plan-only apply plus cross-directory rereading at `:94`, and the acceptance matrix at `:133`. Design line 163 makes the corresponding validation coverage explicit. This removes the original conflict between mandatory new-record creation and an unrepresentable lifecycle.

### Scope and limits

Examined the changes for conflicts with recovery non-overwrite guarantees, unknown-versus-ended semantics, existing-ID preservation, review/approval preservation, two-file write ordering, retry behavior, and plan coverage. No additional evidenced defect was established. No runtime, concurrent-write, client, publication, or source-schema tests were run by this reviewer. The parent reports revised source validation passed without diagnostics; that report does not establish runtime correctness. The author self-assessment subsection was excluded from the diff read. This is the final targeted round within the supplied two-round limit.


<!-- tao:section retention -->
## 保存

<!-- tao:field retention -->
**保存：** 随项目保存本批独立结论及处置，供后续实现和审计引用；快照与原始临时输出保持忽略，过期不改变历史结果。
