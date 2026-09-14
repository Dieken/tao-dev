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

为使用方文档增加篇、章与内容页的组织规则及统一目录模板，保持阅读顺序、正文位置和全局标识符的单一来源。本次范围为组织规则、目录模板与静态验收，不包含出版器实现。

<!-- tao:section references -->
## 规格引用

需求依据见 [协作开发协议](../../product/protocol.md) 中的信息单一来源、统一文档格式及持续成书要求；实现取舍见 [组织设计](../../engineering/documentation/layout.md)。

<!-- tao:section design -->
## 设计

篇按读者与职责分组，章按能力、子系统或操作主题分组；小章保持单页，多页章使用 navigation 目录页。MyST toctree 唯一维护父子关系与顺序；机器注册表定义相应语法，显示文字使用同套中英文资源。正式 ID 不包含章节号；变更文档按创建月份分组，文件名使用创建日期与语义 slug。

<!-- tao:section tasks -->
## 任务

- [x] `TASK_20260914_W3Z533KR48C4EBVH` 补齐篇章组织、目录模板及静态验收
  - relates: ["CHG_20260914_AR8DMCNHNEHNGWWV"]
  - depends_on: []
  - verify: 注册表、模板和双语资源一致；嵌套导航、Unicode 路径及重排保持 ID 的夹具通过；缺页、循环、重复主位置和非法导航被拒绝；独立包引用闭合。
  - evidence: [本计划验证记录](20260914-book-navigation.md#DOC_20260914_0SHBPV8YQFQFQN8X--verification)

(DOC_20260914_0SHBPV8YQFQFQN8X--verification)=
<!-- tao:section verification -->
## 验证

受检输入为本仓库版本 `f49159f305c9a495480b38366fdcd716c10ce119` 的文档与运行源码，排除证据和生成输出；原报告中 41 个输入摘要均已核对与该版本相同，不表示执行时已提交。记录时间为 `2026-09-14T12:04:07+08:00`，环境为 Darwin、Python 3.14.7。

| 检查命令 | 历史结果 |
|---|---|
| `python3 tao-navigation-template-check.py` | 退出 0；11 种模板、2 种语言、16 个错误用例符合预期 |
| `python3 tao-navigation-check.py` | 退出 0；嵌套导航、Unicode、稳定 ID 及 12 个错误用例符合预期 |
| `python3 tao-doc-review-check.py`、`python3 tao-navigation-package-check.py` | 均退出 0；文档结构、ID、引用与独立包检查通过 |
| `python3 quick_validate.py plugins/tao-dev/skills/tao-dev`、`git diff --check` | 均退出 0 |

覆盖为 partial；未验证完整 AST、Sphinx HTML、PDF 或真实 CLI 行为。上述临时脚本未作为维护工具交付，不能仅凭记录重放检查。摘要随计划保留，详细输出不在当前目录保留；这记录当时的结果，不证明当前版本通过。


<!-- tao:section questions -->
## 未决问题

Sphinx 主题、PDF 篇章映射和正式导航检查器尚待实现。
