---
schema: tao.project.change/v0.1
id: "DOC_20260914_0SHBPV8YQFQFQN8X"
title: "篇章层级与统一目录页"
locale: "zh-Hans"
status: draft
created: "2026-09-14"
change: "CHG_20260914_AR8DMCNHNEHNGWWV"
---

# 篇章层级与统一目录页

<!-- tao:section scope -->
## 目标与边界

为使用方文档增加篇、章与内容页的组织规则及统一目录模板，保持阅读顺序、正文位置和全局标识符的单一来源。本次不实现出版器，不迁移本项目现有长期文档。

<!-- tao:section references -->
## 规格引用

需求依据见 [协作开发协议](../../protocol.md) 中的信息单一来源、统一文档格式及持续成书要求；实现取舍见 [组织设计](../../document-layout.md)。

<!-- tao:section design -->
## 设计

篇按读者与职责分组，章按能力、子系统或操作主题分组；小章保持单页，多页章使用 navigation 目录页。MyST toctree 唯一维护父子关系与顺序；机器注册表定义相应语法，显示文字使用同套中英文资源。正式 ID 不包含章节号；变更文档按年份分组但保留全局当天的文件序号。

<!-- tao:section tasks -->
## 任务

- [x] `TASK_20260914_W3Z533KR48C4EBVH` 补齐篇章组织、目录模板及静态验收
  - relates: ["CHG_20260914_AR8DMCNHNEHNGWWV"]
  - depends_on: []
  - verify: 注册表、模板和双语资源一致；嵌套导航、Unicode 路径及重排保持 ID 的夹具通过；缺页、循环、重复主位置和非法导航被拒绝；独立包引用闭合。
  - evidence: [静态检查记录](20260914-002-book-navigation/evidence/checks.json)

<!-- tao:section verification -->
## 验证

执行模板正反例、目录图正反例、已有文档与独立包检查，以及 skill 元数据和差异空白检查。结果只覆盖相应静态条件，不构成完整 AST、Sphinx HTML、PDF 或真实 CLI 验收。

<!-- tao:section questions -->
## 未决问题

Sphinx 主题、PDF 篇章映射和正式导航检查器尚待实现；现有内部格式文档仍按单独迁移范围报告。
