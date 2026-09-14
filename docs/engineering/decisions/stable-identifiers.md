---
schema: tao.project.decision/v0.1
id: DOC_20260914_HSQGY4BRYYMA3693
title: 日期与随机串组成的标识符保持稳定
locale: zh-Hans
status: draft
created: "2026-09-14"
---

# 日期与随机串组成的标识符保持稳定

<!-- tao:section decisions -->
## 决策

```{adr} 日期与随机串组成的标识符保持稳定
:id: ADR_20260914_5R9RWAZTTBX9X86G
:status: proposed
:links: REQ_20260914_5Y6CWDE3MFMKJXSB

<!-- tao:field context -->
**背景与备选：** UUIDv4 不直观表达日期；ULID 更紧凑，但其时间需要解码。日期＋三位流水号便于阅读，却需要协调跨分支和离线分配。条目需要兼顾时间识别度、独立生成与稳定引用。

<!-- tao:field decision -->
**选择：** 正式 ID 使用 `类型_YYYYMMDD_16位随机串`，日期为分配时的本地日期，随机部分为 80 位安全随机数据的 Crockford Base32 编码。生成后完整 ID 固定；日期纠正、改名和移动不重新编号。标题用于显示，代码与跨文档引用保存完整 ID。

<!-- tao:field consequences -->
**代价：** 这是项目自定义格式，需要日期与编码校验；概率唯一仍须查重，正式删除保留小型退役记录。内嵌日期是分配日线索，不代替精确时间戳或内容版本。变更文件名的日期与 slug 可读，正式 ID 独立生成，不依赖文件名。
```
