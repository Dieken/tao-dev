---
schema: tao.project.evidence/v0.1
id: DOC_20261105_6E2FNYAW0QTE4MQJ
title: 工作流迁移修订复核裁决
locale: zh-Hans
status: draft
created: "2026-11-05"
evidence: EVD_20261105_ZH8098BTQSNH6J5J
recorded_at: "2026-11-05T23:28:38.443413+08:00"
result: passed
coverage: partial
---

# 工作流迁移修订复核裁决

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

| 原发现 | 复核处置 | 核实依据 |
|---|---|---|
| [A](01-contract-reviewer.md) | 已解决 | migrate 显式预览及应用，绑定 revision/源摘要，保留 JSON 扩展字段并定义正式成功本地失败后的 resume；计划覆盖 JSON-only/JSON+plan。 |
| [B](01-contract-reviewer.md) | 已解决 | legacy 正式记录明确允许 unknown 并要求来源，禁止推断 active；计划覆盖合法/非法 schema 和 plan-only 恢复后跨目录读取。 |

[独立复核](02-followup-reviewer.md)逐项判定 A/B 闭合，主 agent 核对对应条款与验收任务后一致采用，无未解决项或额外新增发现。结论针对工作区快照的修订内容；暂存区仍是旧内容，两者不宣称相同。文档复核通过不批准修订设计或计划、不授权实现。批次两轮已用完。


<!-- tao:section retention -->
## 保存

<!-- tao:field retention -->
**保存：** 随项目保存本批独立结论及处置，供后续实现和审计引用；快照与原始临时输出保持忽略，过期不改变历史结果。
