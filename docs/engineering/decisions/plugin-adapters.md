---
schema: tao.project.decision/v0.1
id: DOC_20260914_YQSPSWMMX08JRR2B
title: 公共插件结构与客户端适配分层
locale: zh-Hans
status: draft
created: "2026-09-14"
---

# 公共插件结构与客户端适配分层

<!-- tao:section decisions -->
## 决策

```{adr} 公共插件结构与客户端适配分层
:id: ADR_20260914_J5N1H8WPZZ4MNR04
:status: proposed
:links: REQ_20260914_BWAY1ZF6HNPM855Y, REQ_20260914_95193C19C90NRXV4

<!-- tao:field context -->
**背景与备选：** 各自维护两套流程会漂移；把某个客户端的 agent、command 和 hook 当作公共标准则会产生虚假兼容。

<!-- tao:field decision -->
**选择：** 使用标准公共 manifest 和共享 skills，平台专用配置遵循官方扩展；首批同时验收 Codex CLI 与 Claude Code CLI。目录、定义边界和验收矩阵集中维护于 [插件打包与运行环境](../plugin-design.md)。

<!-- tao:field consequences -->
**影响与后果：** 需要维护少量适配配置并运行两套客户端验收；兼容元数据采用派生与一致性检查，运行材料保持独立于内部开发文档。
```
