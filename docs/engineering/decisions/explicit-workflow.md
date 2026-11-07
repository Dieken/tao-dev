---
schema: tao.project.decision/v0.1
id: DOC_20260914_F1ZWHX2HJN02WP01
title: 显式 skill 动作与确定性工具
locale: zh-Hans
status: draft
created: "2026-09-14"
---

# 显式 skill 动作与确定性工具

<!-- tao:section decisions -->
## 决策

```{adr} 显式 skill 动作与确定性工具
:id: ADR_20260914_V3NMPG25YZT8WQJA
:status: proposed
:links: REQ_20260914_95193C19C90NRXV4, REQ_20260914_6YZ1XE1GC369655H

<!-- tao:field context -->
**背景与备选：** 全靠口头上下文会丢失知识，但把协作拆成持久阶段、审批与事件 hook 会增加重复状态和维护成本。

<!-- tao:field decision -->
**选择：** skill 指导 new（spec → design → plan）、review doc、implement、review code，以及 refine/status/continue/handoff；CLI 只处理文档、ID、查询、临时交接和显式检查。已有授权内连续推进，没有 workflow 注册、审批或 finish。

<!-- tao:field consequences -->
**影响与后果：** plan/tasks 成为唯一任务源；查询不执行检查，任务进度不认证审查或交付。恢复从真实文档与代码出发，交接可选；重要授权仍由用户决定。
```
