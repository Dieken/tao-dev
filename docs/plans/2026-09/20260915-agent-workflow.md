---
schema: tao.project.plan/v0.1
id: DOC_20260915_SPNXNDTHJMFVSAN7
title: Agent 内开发工作流
locale: zh-Hans
status: draft
created: "2026-09-15"
change: CHG_20260915_0M6WRQNJ6CCANQ70
spec_docs: ["DOC_20260914_4C7N0XHQSP7CY69P"]
design_docs: ["DOC_20260914_AG3NSZ8RBSFA0YHW", "DOC_20260914_0VF190409FQCN197"]
updated: "2026-09-17"
---

# Agent 内开发工作流

> 历史计划：保留当时的目标、任务与实测范围，不作为当前操作规程；当前纯 skill 契约见 [项目级重构](../2026-11/20261108-project-skill.md)。旧机制的历史通过不证明当前版本通过。

<!-- tao:section scope -->
## 目标与边界

落实用户确认的 agent 内开发周期：可选项目接入、业务澄清、隔离工作副本、spec/design/plan 检查点、自动实现、有限审查、恢复交接与显式收尾。保持完整安装入口，Git 是完整流程的首个实现，不新增 VCS 框架或供应商。每个边界清楚的增量独立验证和提交。

若实现揭示需要扩大授权或改变已确认体验的重大问题，先报告具体影响。

<!-- tao:section references -->
## 规格依据

{need}`DOC_20260914_4C7N0XHQSP7CY69P`。

<!-- tao:section design -->
## 实施设计

设计依据：{need}`DOC_20260914_AG3NSZ8RBSFA0YHW`；{need}`DOC_20260914_0VF190409FQCN197`。

复用已有文档注册表、原子文件操作和配置检查执行层。阶段及批准版本存入项目内工作流状态；正式交接和项目知识保留为文档，日志与缓存留在忽略目录。命令包装只转发动作，共享规程是 agent 行为的唯一来源。审查默认初审加一次定向复核，输入变化后不复用旧结论。新 CLI 能力通过行为测试后才写成已支持。

<!-- tao:section tasks -->
## 任务

- [x] `TASK_20260915_50BX90SPVQNT4SH3` 迁移实施计划命名：迁移 plan profile、模板、目录、配置和所有引用，保留 CHG ID。
  - relates: ["CHG_20260915_0M6WRQNJ6CCANQ70"]
  - depends_on: []
  - verify: 文档/关系/CLI/出版回归和旧名称扫描。
  - evidence: [验证记录](#DOC_20260915_SPNXNDTHJMFVSAN7--verification)

- [x] `TASK_20260915_A06VK7REAK7AN8AS` 持久化工作流与 Git 隔离：增加阶段、批准版本、检查点、worktree/fork 绑定和只读恢复状态；兼容无配置起步。
  - relates: ["CHG_20260915_0M6WRQNJ6CCANQ70"]
  - depends_on: ["TASK_20260915_50BX90SPVQNT4SH3"]
  - verify: 中断恢复、过期批准、并发修改和 Git worktree 隔离测试。
  - evidence: [验证记录](#DOC_20260915_SPNXNDTHJMFVSAN7--verification)

- [x] `TASK_20260915_TCBW79Y67NJV58SM` 完善 handoff 与继续恢复：支持计划前交接；核对后标记接续版本，不删除正式交接文件。
  - relates: ["CHG_20260915_0M6WRQNJ6CCANQ70"]
  - depends_on: ["TASK_20260915_A06VK7REAK7AN8AS"]
  - verify: 计划前交接、重复恢复、新交接版本和旧状态冲突测试。
  - evidence: [验证记录](#DOC_20260915_SPNXNDTHJMFVSAN7--verification)

- [x] `TASK_20260915_EC0WZ5Z2TNFB3HR2` 实现项目接入与检查探测：提供只读技术栈/工具探测、最小配置写入及幂等接入；安装选择由 agent 执行。
  - relates: ["CHG_20260915_0M6WRQNJ6CCANQ70"]
  - depends_on: ["TASK_20260915_TCBW79Y67NJV58SM"]
  - verify: 空项目、已有配置、多技术栈及检查命令探测测试。
  - evidence: [验证记录](#DOC_20260915_SPNXNDTHJMFVSAN7--verification)

- [x] `TASK_20260915_VA29A39MM0VE0YG3` 实现审查范围与有界轮次：保存确认的审查范围、固定输入和轮次预算，支持串行/并行编排及停止条件。
  - relates: ["CHG_20260915_0M6WRQNJ6CCANQ70"]
  - depends_on: ["TASK_20260915_EC0WZ5Z2TNFB3HR2"]
  - verify: 多提交/脏工作区范围、全项目审查、恢复后轮次上限测试。
  - evidence: [验证记录](#DOC_20260915_SPNXNDTHJMFVSAN7--verification)

- [x] `TASK_20260915_0N10J9P66VNQ57SB` 更新 skill 与客户端动作：共享阶段规程；增加 setup/continue/refine/implement/review/debug/docs/finish 包装；分开文档职责。
  - relates: ["CHG_20260915_0M6WRQNJ6CCANQ70"]
  - depends_on: ["TASK_20260915_VA29A39MM0VE0YG3"]
  - verify: 分发包、链接、动作入口和情境行为检查。
  - evidence: [验证记录](#DOC_20260915_SPNXNDTHJMFVSAN7--verification)

- [x] `TASK_20260915_7762WHGSN8RDKHRC` 重写用户指南与集成验证：README 保留精简全周期；完整可复制流程写入 docs/user；更新维护文档和版本。
  - relates: ["CHG_20260915_0M6WRQNJ6CCANQ70"]
  - depends_on: ["TASK_20260915_0N10J9P66VNQ57SB"]
  - verify: 全量测试、两客户端隔离生命周期、Sphinx 构建、独立审查和差异检查。
  - evidence: [验证记录](#DOC_20260915_SPNXNDTHJMFVSAN7--verification)

<!-- tao:section verification -->
## 验证

历史收尾全量pytest为336 passed、0 failed、0 skipped（378.34秒），当时启用全部原生客户端探针。Ruff、依赖导出、32份受管理文档与导航、资源链接、Sphinx和稳定入口检查通过，doctor报告0.3.0；安装指南另20项相关检查通过。

已执行的关键边界包括：计划前CHG与handoff、产物变化使批准失效、检查点并发、真实Git worktree/fork、项目接入只读与摘要条件写入，以及审查工作区/暂存区快照和历史变化后的失败关闭。独立上下文复现暂存区遗漏及过度排除围栏内evidence示例，修复后均有回归。独立八个行为情境复测通过，不等同真实模型长期服从性。

Codex兼容包及Claude user/project/local四组隔离生命周期通过启停、0.3.0→0.3.1升级与移除，个人配置监测未变，未调用模型。原生Windows、全部动作真实长流程及跨供应商审查未在本次验收范围；未据此满足完整verify的必需审查记录门槛。执行时使用既有认证和独立实验项目，无全局配置变更；原始输出不长期保存。

<!-- tao:section questions -->
## 待确认事项

无。
