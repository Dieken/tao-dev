---
schema: tao.project.decision/v0.1
id: DOC_20260914_1WXV6YGDHFAZBWHA
title: 出版层优先验证 Sphinx 组合，执行核心保持独立
locale: zh-Hans
status: draft
created: "2026-09-14"
---

# 出版层优先验证 Sphinx 组合，执行核心保持独立

<!-- tao:section decisions -->
## 决策

```{adr} 出版层优先验证 Sphinx 组合，执行核心保持独立
:id: ADR_20260914_ZJWEM2FQCMF5G4KJ
:status: proposed
:links: REQ_20260914_3JQXRKWXKAZSNJ5R, REQ_20260914_95193C19C90NRXV4

<!-- tao:field context -->
**背景与备选：** mdBook 简洁，但语义追踪需补充；Antora 适合多仓库版本聚合，当前负担偏大。

<!-- tao:field decision -->
**选择：** 采用 MyST、Sphinx 与 sphinx-book-theme，薄扩展复用源校验器的显式 ID、关系索引与永久链接；文档检查和普通开发命令可独立运行。

<!-- tao:field consequences -->
**代价：** 需要可选的 Python 构建依赖和小型 Sphinx 扩展。现有校验器已覆盖任务、元数据与章节键，引入 Sphinx-Needs 会重复建立索引，因此当前直接复用既有索引；不宣称已验收 Sphinx-Needs 或 PDF。HTML 的固定入口、侧栏锚点、改名及退役由实际构建回归测试检查。
```
