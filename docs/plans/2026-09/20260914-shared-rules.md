---
schema: tao.project.plan/v0.1
id: "DOC_20260914_ZTVP0B3S9N1JQ7X8"
title: "共享文档规则归位"
locale: "zh-Hans"
status: draft
created: "2026-09-14"
change: "CHG_20260914_MPNFR3H9WQ7KHFAD"
spec_docs: ["DOC_20260914_4C7N0XHQSP7CY69P"]
design_docs: ["DOC_20260914_P1G9T0KSCC0FTBM1", "DOC_20260914_Y5RR8BVF6065JTYP"]
---

# 共享文档规则归位

<!-- tao:section scope -->
## 目标与边界

把通用文档规则作为 skill 的权威分发内容，让本项目从源码入口和 skill 提供的模板开始自举。保持项目内容与标识符稳定；正式校验器和平台行为验收不属于本次交付。

<!-- tao:section references -->
## 规格依据

{need}`DOC_20260914_4C7N0XHQSP7CY69P`。

<!-- tao:section design -->
## 设计

设计依据：{need}`DOC_20260914_P1G9T0KSCC0FTBM1`；{need}`DOC_20260914_Y5RR8BVF6065JTYP`。

文档组织、术语、诊断、本地化及出版规则的权威文本位于 skill 的 references，开发文档引用这些规则。按任务读取参考；仅复制插件根也可访问完整规则。项目需求、实现理由和开发任务仍留在 docs。AGENTS 指向本仓库 skill 源码，CLAUDE 导入同一入口，不进行安装或注册。交付文件采用共享 change／evidence profile；检查结论明确实际覆盖的格式。

<!-- tao:section tasks -->
## 任务

- [x] `TASK_20260914_VDJ82NS26W4AESFH` 完成规则归位与项目局部自举入口
  - relates: ["CHG_20260914_MPNFR3H9WQ7KHFAD"]
  - depends_on: []
  - verify: 包内引用闭合且无项目专用标识符；原有正式 ID 保留；本计划与证据符合 skill 提供的 profile；中英文模板及既有结构检查无新增错误，报告明确未覆盖的行为验收。
  - evidence: [检查记录](20260914-shared-rules/evidence/shared-rules.md)

<!-- tao:section verification -->
## 验证

执行现有临时文档检查、共享模板正反例检查、skill 元数据检查、独立复制包的引用与边界检查，以及 git diff --check。检查记录引用已有独立摘要，保留受检版本与关键结果，不保留详细输出；临时检查不冒充正式 AST 或真实 CLI 验收。

<!-- tao:section questions -->
## 未决问题

源格式校验、本地 HTML 出版及相关自动检查已有实现；完整双 CLI 行为仍待验收。当前进展与限制见 [交付记录](20260914-bootstrap.md)，上节仅记录本计划当时的检查结果。
