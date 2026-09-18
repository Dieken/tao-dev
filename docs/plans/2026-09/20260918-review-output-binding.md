---
schema: tao.project.plan/v0.1
id: "DOC_20260918_CJ2ZGG2H578Z99AG"
title: "审查输入与本轮报告输出分离"
locale: "zh-Hans"
status: draft
created: "2026-09-18"
spec_docs: ["DOC_20260914_4C7N0XHQSP7CY69P"]
design_docs: ["DOC_20260914_Y5RR8BVF6065JTYP"]
change: "CHG_20260918_89X915GYHB63SCK4"
---

# 审查输入与本轮报告输出分离

<!-- tao:section scope -->
## 目标与边界

落实用户批准的 R1：正式报告保存到受管理目录后，不使其所属审查误判为输入过期。保留真实输入变化检测、旧轮次预算和机器审查回执边界。

<!-- tao:section references -->
## 规格引用

沿用 {need}`REQ_20260914_0J68SDKV86ENKER2` 的真实证据与输入变化约束。

<!-- tao:section design -->
## 设计

沿用 {need}`DOC_20260914_Y5RR8BVF6065JTYP`。预览用可重复的 --output 声明尚不存在的确切 Markdown 文件，开始前复查路径；重算时仅排除该轮输出，不排除历史报告、未声明新文件或已有导航。输出仍按文档契约单独校验；不增加通用忽略目录、模型调用或身份认证机制。

<!-- tao:section tasks -->
## 任务

- [x] `TASK_20260918_EGXHTS1BY0C7BV01` 分离本轮新输出并验证正式报告与输入变化的组合行为。
  - relates: ["REQ_20260914_0J68SDKV86ENKER2"]
  - depends_on: []
  - verify: 执行 feature/project 预览、登记、正式 evidence 与导航生成、文档校验及结束；确认源码、历史报告、新文件变化仍为 stale，已有或已删除输入不能预留为输出，CLI 参数与旧记录兼容。

  - evidence: [验证记录](#DOC_20260918_CJ2ZGG2H578Z99AG--verification)

<!-- tao:section verification -->
## 验证

<!-- tao:results -->
调查时已在隔离目录复现：规格无修改，临时报告记录 passed，合法正式报告记录 stale。修复后的审查批次、阶段与文档工作流回归共 28 项通过。feature/project 两种模式均实测正式 evidence 与新导航通过 schema 后可结束为 passed；源码、历史报告、未声明新文件变化仍为 stale。现有或已删除的跟踪文件不能预留，确认后提前创建输出会拒绝开始，CLI 参数传递与旧预算回归通过。

47 份显式受管理文档含书籍导航校验通过，保留 handoff 命名示例的一条既有 TAO-LINK-002 warning；deletion_checked=false。Ruff 配置致命规则与 diff 空白检查通过。未执行原生客户端、独立模型审查或本轮 HTML 构建，不声称完整交付门槛满足。
<!-- /tao:results -->

<!-- tao:section questions -->
## 待确认事项

无。用户已批准按审查建议实施。
