---
schema: tao.project.evidence/v0.1
id: "DOC_20260921_8V3SEHB25G48XM0V"
title: "必需审查裁决"
locale: "zh-Hans"
status: draft
created: "2026-09-21"
evidence: "EVD_20260921_K72DT1NBM6YWMJ4E"
change: "CHG_20260921_Y6MW6AX39S9RJHGZ"
recorded_at: "2026-09-21T11:05:00+08:00"
result: "passed"
coverage: "partial"
---

# 必需审查裁决

<!-- tao:section scope -->
## 目标与边界

由用户明确发起的新批次，承担本事项的必需审查 `independent-implementation-review`。前一批次两轮均未产出可导入的记录：第 1 轮的 attestation 因记述错误实际未导入，发现时输入已过期；第 2 轮未取得机器可校验的 attestation。

本文件在本轮开始前建立，使批次导航页及其父级入口属于受检版本——这是前一批次实测得出的前置条件。两轮结论已落定，result 与 coverage 据实订正。

**审查执行时间与依据:** 第 1 轮实测 96.446 秒，第 2 轮实测 102.729 秒，均来源于调度脚本记录。

<!-- tao:section inputs -->
## 输入与环境

<!-- tao:field fingerprint -->
**受检输入引用:** 第 1 轮为提交 `4b9d604` 的树，第 2 轮为提交 `9615314` 的树（树对象 `2a88127`），基准均为 `d8b599d`。

<!-- tao:field environment -->
**环境:** 主审为本事项作者 agent，不具备独立性。

| 报告 | 关注点 | 审查者、模型与供应商 | 独立性 | 轮次 |
|---|---|---|---|---|
| [第 1 轮](01-required-claude.md) | 实现与回归 | `claude-sonnet-5`，firstParty | 独立上下文 | 第 1 轮 |
| [第 2 轮](02-required-recheck-claude.md) | F1 的处置 | `claude-sonnet-5`，firstParty，另一会话 | 独立上下文 | 第 2 轮 |

两轮派发均包含 `project.py`。此前三轮各提出一条「某异常不在捕获元组内」的发现且均不成立，成因都是审查者看不到异常类层次；包含该文件后未再出现同类发现，第 1 轮转而提出一条成立的阻断。

<!-- tao:section checks -->
## 检查记录

<!-- tao:field command -->
**命令或观察步骤:** 核实第 1 轮 F1 的前提，并在第 2 轮导入 attestation 后执行完整 `tao verify`。

<!-- tao:field expected -->
**预期:** F1 若成立则修复并复核；取得对应最终受检树的 attestation 并当场导入。

<!-- tao:field observed -->
**实际观察:** F1 成立并已复现——登记前的报告校验取诊断于受管理文档集合，管理范围外的报告不被分析。第 2 轮 0 发现，attestation 已实际导入。完整验证返回 passed／complete／checks-satisfied，必需审查 satisfied，诊断 0 条。

<!-- tao:field reports -->
**报告:** 见上表两份链接。

<!-- tao:section findings -->
## 发现与限制

<!-- tao:field limits -->
**限制:** 被调用模块不在受检范围，两轮均如此。

| 来源发现 | 处置与范围 | 依据与理由 | 剩余工作或复查条件 |
|---|---|---|---|
| [第 1 轮 F1](01-required-claude.md) 登记前校验对管理范围外的报告不生效 | 采用，但不采用其首选补救 | 已复现：诊断取自受管理文档集合，范围外文件不被分析，`faults` 恒为空。首选补救是直接按报告路径校验，试行后被既有测试挡下——审查规程允许用户指定其他格式并说明未做校验，强制全部为 tao 文档会推翻该允许。改为逐份记录是否校验：范围内校验并拒绝不合格报告，范围外保留其格式并标明未校验 | 已完成并经第 2 轮复核，契约页、设计与任务 verify 同步订正 |

### 未解决事项

无阻断。

**对下一步的影响:** 必需审查已取得对应受检树 `2a88127` 的记录并实际导入，完整交付判定成立。本裁决不代表交付授权。

<!-- tao:section retention -->
## 证据保存

<!-- tao:field retention -->
**保存位置与期限:** 随事项长期保留。
