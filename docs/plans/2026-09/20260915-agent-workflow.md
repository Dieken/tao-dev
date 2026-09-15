---
schema: tao.project.plan/v0.1
id: DOC_20260915_SPNXNDTHJMFVSAN7
title: Agent 内开发工作流
locale: zh-Hans
status: draft
created: "2026-09-15"
change: CHG_20260915_0M6WRQNJ6CCANQ70
---

# Agent 内开发工作流

<!-- tao:section scope -->
## 目标与边界

落实用户确认的 agent 内开发周期：可选项目接入、业务澄清、隔离工作副本、spec/design/plan 检查点、自动实现、有限审查、恢复交接与显式收尾。保持完整安装入口，Git 是完整流程的首个实现，不新增 VCS 框架或供应商。每个边界清楚的增量独立验证和提交。

<!-- tao:section references -->
## 依据

依据本会话已确认的九项设计决定，以及 [工程规程](../../../plugins/tao-dev/skills/tao-dev/references/engineering.md) 与 [现有流程](../../../plugins/tao-dev/skills/tao-dev/references/workflow.md)。用户已授权逐项实施；不再要求重复批准这份清单。

<!-- tao:section design -->
## 实施设计

复用已有文档注册表、原子文件操作和配置检查执行层。阶段及批准版本存入项目内工作流状态；正式交接和项目知识保留为文档，日志与缓存留在忽略目录。命令包装只转发动作，共享规程是 agent 行为的唯一来源。审查默认初审加一次定向复核，输入变化后不复用旧结论。新 CLI 能力通过行为测试后才写成已支持。

<!-- tao:section tasks -->
## 任务

- [x] `TASK_20260915_50BX90SPVQNT4SH3` 迁移实施计划命名：迁移 plan profile、模板、目录、配置和所有引用，保留 CHG 身份。
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

- [ ] `TASK_20260915_7762WHGSN8RDKHRC` 重写用户指南与集成验证：README 保留精简全周期；完整可复制流程写入 docs/user；更新维护文档和版本。
  - relates: ["CHG_20260915_0M6WRQNJ6CCANQ70"]
  - depends_on: ["TASK_20260915_0N10J9P66VNQ57SB"]
  - verify: 全量测试、两客户端隔离生命周期、Sphinx 构建、独立审查和差异检查。

<!-- tao:section verification -->
## 验证

每项提交前运行受影响的回归、文档校验及差异检查，完成后在此追加实际证据。最终运行完整测试与本地书籍构建。客户端模型调用仅使用既有客户端和授权配置，在隔离项目内执行；不更改全局配置。

命名迁移：先观察新增 plans 配置用例因旧键拒绝而失败，迁移后 109 项文档、CLI、关系、退役与出版回归全部通过。所有正式 ID 保持不变。

工作流状态：113 项阶段、CLI、文档、关系、退役和项目边界回归通过，Ruff 核心规则通过。覆盖无计划起步、内容变更使批准过期、检查点并发冲突、复用 CHG 与真实 Git worktree/fork。

交接恢复：29 项工作流、handoff 与 CLI 回归通过。计划前可保存正式交接；重复恢复保留新进度；读取后 handoff 变化会拒绝旧摘要接续；不自动删除文件。

项目接入：33 项探测、配置、项目边界、CLI 与 hook 测试通过。验证空项目只读、monorepo 候选命令不执行、同配置不改写、过期配置摘要拒绝覆盖，Ruff 核心规则通过。

有界审查：50 项审查范围、轮次、工作流、独立审查记录和验证回归通过。覆盖多提交/脏输入、实际 ZIP 快照、重载后轮次与时间预算、缺失报告及过期范围拒绝，Ruff 核心规则通过。

独立审查修复：审查者在隔离 Git 仓库复现暂存区遗漏与历史变化导致失败轮次无法结束。新增两项回归先失败，修复后 6 项审查运行测试全部通过；快照分别保存工作区和暂存区内容与模式，失败关闭保留输入错误。

53 项文档关系、工作流与分发测试通过；核心 Ruff 通过；独立 agent 的八个行为情境复测通过，并清理三处旧文档歧义。

53 项文档关系、工作流与分发测试通过；核心 Ruff 通过；独立 agent 的八个行为情境复测通过，并清理三处旧文档歧义。

<!-- tao:section questions -->
## 未决问题

当前无阻断决定。若实现揭示需要扩大授权或改变已确认体验的重大问题，先报告具体影响。
