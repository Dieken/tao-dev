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

逐项记录实际执行结果；原始报告放入忽略的 tmp/tao/。

最终验证：启用全部原生客户端探针的全量 pytest 覆盖 356 项，355 项通过、1 项旧版本常量断言失败、0 跳过（593.19 秒）。该断言改为核对 pyproject.toml 的声明版本，修正后单项复测通过（41.23 秒）；全量运行已加载旧测试代码，不能把该报告改称单次全绿。0.4.0 中文书籍、33 份受管理文档、Ruff 错误规则及 skill 入口校验通过。独立只读代码审查发现的术语附件复制遗漏已复现、修复并复核；新诊断翻译目录检查通过。自然语言新需求、修订、含糊归属、只读状态和经验保留情景复核通过。本次不宣称 Windows 验收或完整产品发布就绪。

出版关联：20 项真实 Sphinx、标题转义、稳定入口、章节重定向与模板回归通过；项目中文书籍构建通过，102 个定义的永久链接检查通过。静态错误检查无诊断。

文档关系：93 项源格式、关系、阶段与项目契约回归通过；33 份实际文档校验通过。六份设计和七份计划补齐结构化依据，独立任务附件的契约变化会使计划批准过期。

审查预算：15 项审查与工作流回归通过。新增反例确认独立新批次重置预算并保留旧记录；续审不重置，仍在运行的批次不能被新批次覆盖。

Skill 精简：入口校验与受管理文档校验通过。独立只读情景复核确认 `status` 不读取完整的 [工程规程](../../../plugins/tao-dev/skills/tao-dev/references/engineering.md)，经验保留优先可执行约束，不新增重复总结或修改全局 skill。

术语条目：45 项术语、文档与项目契约回归通过；新增结构反例先失败后通过。实际 Sphinx 构建通过，术语正文可出版且不新增正式 ID。

术语核查：修正六处把标识符称为“身份”的用法，保留认证含义；同步计划、产物和 Git 术语。受管理文档校验通过。

<!-- tao:section questions -->
## 待确认事项

无。
