---
schema: tao.project.plan/v0.1
id: "DOC_20260918_43XCMZ4WYWEFAR7Q"
title: "审查报告模板、结果语义与命名"
locale: "zh-Hans"
status: draft
created: "2026-09-18"
spec_docs: ["DOC_20260914_4C7N0XHQSP7CY69P"]
design_docs: ["DOC_20260914_P1G9T0KSCC0FTBM1"]
change: "CHG_20260918_HHSEC6GB903A90EV"
---

# 审查报告模板、结果语义与命名

> 历史计划：保留当时的目标、任务与实测范围，不作为当前操作规程；当前纯 skill 契约见 [项目级重构](../2026-11/20261108-project-skill.md)。旧机制的历史通过不证明当前版本通过。

<!-- tao:section scope -->
## 目标与边界

按已确认方案补齐 evidence 的未知结论语义、独立审查与主审裁决模板、审查批次命名与填写规程。复用既有 schema，保留五个固定二级章节；不新增发现实体，不改变 JSON 审查回执。仅修改 tao-dev，不改写消费项目文件；skill 聚焦按规范生成文档，不提供外部报告迁移流程。

<!-- tao:section references -->
## 规格引用

沿用 {need}`DOC_20260914_4C7N0XHQSP7CY69P` 的真实证据与共享文档要求，以及 {need}`DOC_20260914_P1G9T0KSCC0FTBM1` 的文档管理边界。

<!-- tao:section design -->
## 设计

复用 {need}`DOC_20260914_P1G9T0KSCC0FTBM1`。evidence.result 仅扩充 unknown；两种写作变体沿用解析器与出版器，子章节容纳完整发现及裁决。命名由文档规程约束，语义与内容完整性由作者核对确认，不把 schema 通过当作内容完整或审查通过。

<!-- tao:section tasks -->
## 任务

- [x] `TASK_20260918_HCV3T9XN7VR01ER6` 补齐结果契约、两种模板、命名与填写规程，并验证旧 evidence、链接和 HTML 兼容性。
  - relates: ["CHG_20260918_HHSEC6GB903A90EV"]
  - depends_on: []
  - verify: 检查中英模板、六种合法结果与非法结果、未知结论不满足必需审查；使用合成报告验证表格、列表与引用发布；检查当前全部受管文档及既有 evidence 内容，运行维护回归。

  - evidence: [验证记录](#DOC_20260918_43XCMZ4WYWEFAR7Q--verification)

<!-- tao:section verification -->
## 验证

<!-- tao:results -->
专项回归24项通过，覆盖两种双语模板、旧结果与unknown、非法枚举拒绝、Markdown不能代替必需机器回执，以及报告在计划附件和工程目录的布局。合成报告实测MyST/HTML可表达发现分组、表格、段落、列表、强调、代码及跨报告章节链接；不表示外部报告迁移无损。

完整维护回归474 passed、5原生安装探针 skipped（670.58秒）；Ruff及skill元数据检查通过。45份显式受管理文档无error，当时保留[命令设计](../../engineering/cli-design.md)的一条命名示例warning，deletion_checked=false；HTML及稳定入口检查通过，原DOC/EVD和引用保持。

既有[共享规则与自举检查](20260914-shared-rules/evidence/shared-rules.md)已与Git字节核对：原passed仅表示其partial静态检查范围，仍符合扩充后的schema，无须改成unknown，也不作为当前版本通过依据。未执行本次原生客户端或独立语义审查；原始输出和覆盖率仅在忽略临时存储。

<!-- /tao:results -->

<!-- tao:section questions -->
## 待确认事项

无。用户已批准实施，并要求不修改消费项目文件及核对当前项目既有 evidence。
