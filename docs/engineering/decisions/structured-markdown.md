---
schema: tao.project.decision/v0.1
id: DOC_20260914_ASJCKWCWGBA1EBCY
title: 正文保持 Markdown，机器读取明确结构
locale: zh-Hans
status: draft
created: "2026-09-14"
---

# 正文保持 Markdown，机器读取明确结构

<!-- tao:section decisions -->
## 决策

```{adr} 正文保持 Markdown，机器读取明确结构
:id: ADR_20260914_HHVX7YB5AG7J3TMT
:status: proposed
:links: REQ_20260914_42AXMZ2KH2RAZ8M3, REQ_20260914_NN0AEQ2E1GTVSMTV

<!-- tao:field context -->
**背景与备选：** 纯自由文本难稳定校验；全部改为 YAML 对人阅读不友好；维护并行 JSON 与正文会产生双份事实。

<!-- tao:field decision -->
**选择：** 采用受约束 Markdown：YAML 元数据、稳定章节键、MyST 风格条目块及固定任务列表。正文继续自然表达；机器数据从同一源文件提取。

<!-- tao:field consequences -->
**代价：** 需要 AST 级结构检查和少量扩展约定。JSON Schema 只负责提取后的数据，不声称能独自验证 Markdown 章节。具体字段见文档契约。
```
