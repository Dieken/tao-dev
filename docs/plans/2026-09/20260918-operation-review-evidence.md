---
schema: tao.project.plan/v0.1
id: "DOC_20260918_JBRE6CXEJK6RMS2A"
title: "操作状态核验与审查文档管理"
locale: "zh-Hans"
status: draft
created: "2026-09-18"
spec_docs: ["DOC_20260914_4C7N0XHQSP7CY69P"]
design_docs: ["DOC_20260914_P1G9T0KSCC0FTBM1", "DOC_20260914_Y5RR8BVF6065JTYP"]
change: "CHG_20260918_TZG032GMJ2B1S07P"
---

# 操作状态核验与审查文档管理

> 历史计划：保留当时的目标、任务与实测范围，不作为当前操作规程；当前纯 skill 契约见 [项目级重构](../2026-11/20261108-project-skill.md)。旧机制的历史通过不证明当前版本通过。

<!-- tao:section scope -->
## 目标与边界

补足命令报告成功与目标状态完成的区别，统一正式审查报告的 schema、归属与引用。检查本仓库 Markdown 管理边界及外部消费项目的报告样例；外部项目仅只读调查，不修改其文件。本次为用户直接授权的局部规程与校验器修复，复用已有规格与设计。

<!-- tao:section references -->
## 规格引用

沿用 {need}`DOC_20260914_4C7N0XHQSP7CY69P` 的协作与文档约束。

<!-- tao:section design -->
## 设计

沿用 {need}`DOC_20260914_P1G9T0KSCC0FTBM1` 与 {need}`DOC_20260914_Y5RR8BVF6065JTYP`。正式审查复用 evidence profile，审查模板由报告作者读取；不新建实体或机器回执格式。校验器提示正文中未链接的完整 ID 与明确的 Markdown 文件代码片段，代码示例不自动注册引用；无法可靠识别的缩写与任意路径由内容审查负责。

<!-- tao:section tasks -->
## 任务

- [x] `TASK_20260918_WZXHY67Z5RM4CEBC` 完善状态核验、审查模板及引用诊断，核对文档管理范围并验证。
  - relates: ["CHG_20260918_TZG032GMJ2B1S07P"]
  - depends_on: []
  - verify: 运行项目回归、显式受管理源校验和 HTML 构建；检查生成报告页面的实际 href 与目标锚点；核对工作区和每项预期改动。
  - evidence: [验证记录](#DOC_20260918_JBRE6CXEJK6RMS2A--verification)

<!-- tao:section verification -->
## 验证

历史检查确认项目正式文档均声明受支持schema，范围外入口、运行参考与模板有明确消费职责；维护回归459 passed、5原生安装探针 skipped（594.00秒），相关模板、引用、管理范围与本地化33项定向检查通过。43份受管理文档无error，Ruff无诊断；当时保留[命令设计](../../engineering/cli-design.md)的一个命名示例warning，deletion_checked=false。

真实HTML检查覆盖契约与计划的稳定入口、报告夹具的need/文件/章节href及目标锚点，两种语言的evidence结构与非法引用边界。外部消费项目仅只读调查：四份报告缺schema且在管理范围外，其中一份含15个不存在的临时快照链接；133处未链接完整ID、96处代码形式文件引用仅为AST调查信号，未据此验证或改写外部报告。

状态回读与批量核对规则经过文本和情境自查，没有模型服从性实验；未运行原生客户端模型或独立实现审查，不声明完整交付。原始日志和HTML保存在忽略临时存储，无部署；原DOC/EVD及来源事实保持。

<!-- tao:section questions -->
## 待确认事项

无。独立审查与原生客户端验收不由本次本地检查替代。
