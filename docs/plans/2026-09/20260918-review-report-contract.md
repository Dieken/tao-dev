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
使用项目本地 Python 执行：专项回归 24 项通过，覆盖两种中英文模板、全部旧结果值及 unknown、非法结果拒绝、Markdown 报告不能替代必需审查回执，以及计划附件和工程目录两种批次位置。合成报告验证五个主题分组、八张表、段落、有序与无序列表、强调、代码、分隔线及 need／文件／跨报告章节链接的实际 HTML 输出。测试验证生成能力，不实现或宣称外部文档迁移无损。

完整维护回归 474 passed、5 skipped（670.58 秒）；5 项均为未启用的隔离原生客户端探针。Ruff 的配置致命规则无诊断，skill-creator 格式检查通过。日志在忽略的 tmp/tao/review-report-contract/，覆盖率产物在 tmp/tao/coverage/。

本次模板修改后的 45 份显式受管文档校验无 error，仅保留 [命令设计](../../engineering/cli-design.md) 中 handoff 命名示例的既有 TAO-LINK-002 warning；未提供历史删除基线，deletion_checked=false。HTML 构建完成，检查新计划到设计的 need 链接、模板及规程页面的实际目标。未部署，未进行原生客户端行为验收或独立模型审查，不声称满足完整独立审查门槛。

当前唯一既有 evidence 是 [共享规则与自举文档检查](20260914-shared-rules/evidence/shared-rules.md)。已检查元数据、五个固定章节、必需字段及引用，并与 Git 版本逐字节比较，内容、DOC／EVD 和记录时刻均未改变。其 passed 表示声明范围内的历史静态检查，partial 及正文明确排除了 AST、真实 CLI 和 HTML 验证；正文保留了 ID、模板、错误夹具及引用检查的具体观察，不只有退出码。仍符合扩充后的 schema，无须改成 unknown，也不作为当前版本通过证据。发布页中的 DOC／EVD 及五个章节锚点已核对。
<!-- /tao:results -->

<!-- tao:section questions -->
## 待确认事项

无。用户已批准实施，并要求不修改消费项目文件及核对当前项目既有 evidence。
