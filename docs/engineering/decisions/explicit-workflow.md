---
schema: tao.project.decision/v0.1
id: DOC_20260914_F1ZWHX2HJN02WP01
title: 文档管理、持久计划与确定性工具
locale: zh-Hans
status: draft
---

# 文档管理、持久计划与确定性工具

<!-- tao:section decisions -->
## 决策

```{adr} 文档管理、持久计划与确定性工具
:id: ADR_20260914_V3NMPG25YZT8WQJA
:status: proposed
:links: REQ_20260914_95193C19C90NRXV4, REQ_20260914_6YZ1XE1GC369655H

<!-- tao:field context -->
**背景与备选：** 全靠口头上下文会丢失知识；多个持久进度源会增加同步和维护成本。需要让长期知识与执行进度各有唯一位置，并区分 agent 判断与确定性工具职责。

<!-- tao:field decision -->
**选择：** skill 负责文档语义与知识生命周期，不编排实现或代码审查阶段。agent 自行管理执行，依据实际成果回写持久 plan/tasks；客户端任务仅作临时步骤。CLI 只处理文档、ID、计划骨架、只读查询与显式检查，不推荐流程动作。跨会话、协作或跟踪工作维护项目计划，小改动复用现有材料，不强制规格、设计、计划序列。

<!-- tao:field consequences -->
**影响与后果：** plan/tasks 成为可跨客户端移植的唯一项目进度源；查询不执行检查，任务进度不认证验证、审查或交付。新会话从计划与实际产物核对事实，无需独立交接机制。完成计划保留变更历史，长期当前事实更新规格、设计和 ADR；重要授权仍由用户决定。
```
