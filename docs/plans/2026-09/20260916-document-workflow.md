---
schema: tao.project.plan/v0.1
id: DOC_20260916_M4PCSTFN67XY86TX
title: 文档关联与工作流使用体验
locale: zh-Hans
status: draft
created: "2026-09-16"
change: CHG_20260916_4ZTBQCAS0SR9KGTY
spec_docs: ["DOC_20260914_4C7N0XHQSP7CY69P"]
design_docs: ["DOC_20260914_P1G9T0KSCC0FTBM1", "DOC_20260914_0VF190409FQCN197"]
updated: "2026-09-17"
---

# 文档关联与工作流使用体验

<!-- tao:section scope -->
## 目标与边界

补齐规格、设计、计划和任务的可追溯关系与 HTML 阅读入口，改善自然语言分派、术语约束和审查预算。保持 skill 精炼，不新增经验文档类型，不扩展 VCS 或客户端安装范围。

用户已批准本计划范围内的修改、验证和独立提交；合并与推送不在本次范围。

<!-- tao:section references -->
## 规格依据

{need}`DOC_20260914_4C7N0XHQSP7CY69P`。

<!-- tao:section design -->
## 设计引用

设计依据：{need}`DOC_20260914_P1G9T0KSCC0FTBM1`；{need}`DOC_20260914_0VF190409FQCN197`。

文档关系由 profile 定义并校验，出版层生成可读链接及反向关系；复用已有术语表类型。审查批次独立保存预算与历史，续审保持原预算。动作分派与写入批准统一在流程规程维护。

<!-- tao:section tasks -->
## 任务

- [x] `TASK_20260916_S7FNTDFB8HP2DBW3` 修正标识符误译与过时术语。
  - relates: ["CHG_20260916_4ZTBQCAS0SR9KGTY"]
  - depends_on: []
  - verify: 全仓用词核查与受管理文档校验。
  - evidence: [验证记录](#DOC_20260916_M4PCSTFN67XY86TX--verification)

- [x] `TASK_20260916_R23QAC7XE5A3B9Z4` 约束项目术语条目及按需读取。
  - relates: ["CHG_20260916_4ZTBQCAS0SR9KGTY"]
  - depends_on: []
  - verify: 术语结构、重复项与反例回归。
  - evidence: [验证记录](#DOC_20260916_M4PCSTFN67XY86TX--verification)

- [x] `TASK_20260916_NASWY0MW29RN8B55` 精简 skill 并优先固化可执行经验。
  - relates: ["CHG_20260916_4ZTBQCAS0SR9KGTY"]
  - depends_on: []
  - verify: 情景演练、入口读取范围与文档校验。
  - evidence: [验证记录](#DOC_20260916_M4PCSTFN67XY86TX--verification)

- [x] `TASK_20260916_3R6KR1TV9MW0VVXJ` 隔离新审查批次与续审预算。
  - relates: ["CHG_20260916_4ZTBQCAS0SR9KGTY"]
  - depends_on: []
  - verify: 跨会话续审、新阶段审查及预算耗尽反例。
  - evidence: [验证记录](#DOC_20260916_M4PCSTFN67XY86TX--verification)

- [x] `TASK_20260916_D0XMQ8AB9DWAC60R` 补齐类型化文档关系及现有依据。
  - relates: ["CHG_20260916_4ZTBQCAS0SR9KGTY"]
  - depends_on: []
  - verify: 引用类型、多目标、阶段完整性与现有文档校验。
  - evidence: [验证记录](#DOC_20260916_M4PCSTFN67XY86TX--verification)

- [x] `TASK_20260916_6HZF4R0B3VK98K33` 生成可读的文档与任务关联链接。
  - relates: ["CHG_20260916_4ZTBQCAS0SR9KGTY"]
  - depends_on: []
  - verify: 实际 Sphinx HTML 中的标题、类型、前向与反向链接。
  - evidence: [验证记录](#DOC_20260916_M4PCSTFN67XY86TX--verification)

- [x] `TASK_20260916_DB1X5G163G6C2ZRV` 完善自然语言分派并验证整体行为。
  - relates: ["CHG_20260916_4ZTBQCAS0SR9KGTY"]
  - depends_on: []
  - verify: 自然语言情景复核、完整回归及书籍构建。
  - evidence: [验证记录](#DOC_20260916_M4PCSTFN67XY86TX--verification)

<!-- tao:section verification -->
## 验证记录

历史全量pytest覆盖356项：355 passed、1旧版本常量断言 failed、0 skipped（593.19秒）。断言改为核对pyproject.toml声明版本后单项复测通过，不能把已加载旧测试的全量报告改称单次全绿。0.4.0中文书籍、33份受管理文档、Ruff及skill入口检查通过。

| 覆盖面 | 实际观察 |
|---|---|
| 文档关系 | 规格、设计、计划与任务附件的结构化依据校验；tasks契约变化使批准过期；93项相关回归通过 |
| 出版 | 20项真实Sphinx、标题转义、稳定入口、章节重定向与模板检查通过，102个定义入口有效 |
| 审查与恢复 | 15项相关回归确认续审不重置、新批次须显式选择、运行中批次不可覆盖；独立审查发现的术语附件复制遗漏已复现并复核修复 |
| 指导与术语 | 新需求、修订、歧义归属、只读status及知识保留情境核对；45项术语/格式/关系检查通过，正文可出版且不新增正式ID |

原生Windows及完整产品发布就绪不在本次结论内。情境复核不能代替原生模型行为；[工程规程](../../../plugins/tao-dev/skills/tao-dev/references/engineering.md)的按需读取仅在已说明场景观察。原始报告在忽略临时存储，不保证长期可还原。

<!-- tao:section questions -->
## 待确认事项

无。
