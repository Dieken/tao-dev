---
schema: tao.project.evidence/v0.1
id: "DOC_20260914_8YCWJXDGRT728KXD"
title: "共享规则与自举文档检查"
locale: "zh-Hans"
status: draft
created: "2026-09-14"
evidence: "EVD_20260914_6M5WB4VYYSZ4BM89"
change: "CHG_20260914_MPNFR3H9WQ7KHFAD"
recorded_at: "2026-09-14T11:50:51+08:00"
result: passed
coverage: partial
---

# 共享规则与自举文档检查

<!-- tao:section scope -->
## 目标与边界

本次规则归位、包内引用与新增自举文档的静态检查。完整 AST、HTML 出版和双 CLI 行为不在本记录的覆盖范围。

<!-- tao:section inputs -->
## 输入与环境

<!-- tao:field fingerprint -->
**受检输入:** 本仓库版本 `1a22ec3beb311be6d3abba49c28167419be654c5` 的文档、入口及插件源码，排除证据目录；原清单 39 个文件均已核对与该版本相同，不表示执行时已提交。

<!-- tao:field environment -->
**环境:** Darwin 24.6.0、Python 3.14.7、PyYAML 6.0.3。

<!-- tao:section checks -->
## 检查记录

<!-- tao:field command -->
**命令:** `python3 tao-doc-review-check.py`、`python3 tao-runtime-contract-check.py`、`python3 tao-shared-package-check.py`、`python3 quick_validate.py plugins/tao-dev/skills/tao-dev`、`git diff --check`。

<!-- tao:field expected -->
**预期:** ID 稳定、文档与模板格式正确、包内引用完整，错误夹具被拒绝。

<!-- tao:field observed -->
**结果:** 均退出 0；37 个原有及 5 个新增 ID 唯一；10 种模板、2 种语言、16 个错误夹具符合预期；36 个包内引用可解析，包外依赖被拒绝。

<!-- tao:field reports -->
**报告:** 结果保存在本摘要，详细输出不在当前目录保留。

<!-- tao:section findings -->
## 发现与限制

<!-- tao:field limits -->
**限制:** 临时检查脚本未作为维护工具交付，不能仅凭本记录重放。开发文档与共享 profile 分别检查；未验证完整 AST、真实 CLI、跨模型审查或 HTML 构建；历史结果不证明当前版本通过。

<!-- tao:section retention -->
## 证据保存

<!-- tao:field retention -->
**保存:** 保留本摘要及其 DOC／EVD 标识符，随项目 VCS 保存，不随 skill 发布。
