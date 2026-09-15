---
schema: tao.project.plan/v0.1
id: DOC_20260916_M4PCSTFN67XY86TX
title: 文档关联与工作流使用体验
locale: zh-Hans
status: draft
created: "2026-09-16"
change: CHG_20260916_4ZTBQCAS0SR9KGTY
---

# 文档关联与工作流使用体验

<!-- tao:section scope -->
## 目标与边界

补齐规格、设计、计划和任务的可追溯关系与 HTML 阅读入口，改善自然语言分派、术语约束和审查预算。保持 skill 精炼，不新增经验文档类型，不扩展 VCS 或客户端安装范围。

<!-- tao:section references -->
## 规格依据

规格见 [协作开发协议](../../product/protocol.md)，设计见 [文档契约](../../engineering/documentation/contract.md) 与 [命令设计](../../engineering/cli-design.md)。本计划记录已批准的实施范围；具体契约与关系在相应权威文档维护。

<!-- tao:section design -->
## 设计引用

文档关系由 profile 定义并校验，出版层生成可读链接及反向关系；复用已有术语表类型。审查批次独立保存预算与历史，续审保持原预算。动作分派与写入批准统一在流程规程维护。

<!-- tao:section tasks -->
## 任务

- [x] `TASK_20260916_S7FNTDFB8HP2DBW3` 修正标识符误译与过时术语。
  - relates: ["CHG_20260916_4ZTBQCAS0SR9KGTY"]
  - depends_on: []
  - verify: 全仓用词核查与受管理文档校验。
  - evidence: [验证记录](#DOC_20260916_M4PCSTFN67XY86TX--verification)

- [ ] `TASK_20260916_R23QAC7XE5A3B9Z4` 约束项目术语条目及按需读取。
  - relates: ["CHG_20260916_4ZTBQCAS0SR9KGTY"]
  - depends_on: []
  - verify: 术语结构、重复项与反例回归。

- [ ] `TASK_20260916_NASWY0MW29RN8B55` 精简 skill 并优先固化可执行经验。
  - relates: ["CHG_20260916_4ZTBQCAS0SR9KGTY"]
  - depends_on: []
  - verify: 情景演练、入口读取范围与文档校验。

- [ ] `TASK_20260916_3R6KR1TV9MW0VVXJ` 隔离新审查批次与续审预算。
  - relates: ["CHG_20260916_4ZTBQCAS0SR9KGTY"]
  - depends_on: []
  - verify: 跨会话续审、新阶段审查及预算耗尽反例。

- [ ] `TASK_20260916_D0XMQ8AB9DWAC60R` 补齐类型化文档关系及现有依据。
  - relates: ["CHG_20260916_4ZTBQCAS0SR9KGTY"]
  - depends_on: []
  - verify: 引用类型、多目标、阶段完整性与现有文档校验。

- [ ] `TASK_20260916_6HZF4R0B3VK98K33` 生成可读的文档与任务关联链接。
  - relates: ["CHG_20260916_4ZTBQCAS0SR9KGTY"]
  - depends_on: []
  - verify: 实际 Sphinx HTML 中的标题、类型、前向与反向链接。

- [ ] `TASK_20260916_DB1X5G163G6C2ZRV` 完善自然语言分派并验证整体行为。
  - relates: ["CHG_20260916_4ZTBQCAS0SR9KGTY"]
  - depends_on: []
  - verify: 自然语言情景复核、完整回归及书籍构建。

<!-- tao:section verification -->
## 验证记录

逐项记录实际执行结果；原始报告放入忽略的 tmp/tao/。

术语核查：修正六处把标识符称为“身份”的用法，保留认证含义；同步计划、产物和 Git 术语。受管理文档校验通过。

<!-- tao:section questions -->
## 未决问题

无。用户已批准本计划范围内的修改、验证和独立提交；合并与推送不在本次范围。
