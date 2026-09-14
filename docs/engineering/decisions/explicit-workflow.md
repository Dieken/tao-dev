---
schema: tao.project.decision/v0.1
id: DOC_20260914_F1ZWHX2HJN02WP01
title: 显式操作推进流程，hook 执行短小的辅助动作
locale: zh-Hans
status: draft
created: "2026-09-14"
---

# 显式操作推进流程，hook 执行短小的辅助动作

<!-- tao:section decisions -->
## 决策

```{adr} 显式操作推进流程，hook 执行短小的辅助动作
:id: ADR_20260914_V3NMPG25YZT8WQJA
:status: proposed
:links: REQ_20260914_95193C19C90NRXV4, REQ_20260914_6YZ1XE1GC369655H

<!-- tao:field context -->
**背景与备选：** 全靠提示容易遗漏检查；每次事件启动完整流程会增加延迟和失控循环。将文档检查、行为验证和收尾条件各设一个命令，会把工具内部分类变成用户必须选择的步骤。

<!-- tao:field decision -->
**选择：** 流程使用 specify、plan、implement、review、verify，澄清、设计及任务划分融入相关阶段，不强制逐步调用。工具以 `tao verify` 统一文档检查、行为验证和收尾判定，agent 按时机选择局部反馈，交付前完整验证；创建用 new，展示用 show，交接用 handoff。先实现 doctor、id new、show 和 verify 的文档子集。接口与默认选择见命令专篇；hook 仅做有预算的短检查。

<!-- tao:field consequences -->
**代价：** 工具需报告能力、选择原因和完整／局部覆盖，不能把局部通过冒充交付通过。无可靠基线时扩大检查；缺少必要能力时明确未完成。hook 须有超时、幂等性及并发保护，CI 复核完整条件。核心文档命令已实现，其余能力由 doctor 明确报告。
```
