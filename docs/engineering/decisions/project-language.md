---
schema: tao.project.decision/v0.1
id: DOC_20260914_A8HNABEBDYE68NF2
title: 中文规范、英文机器标识，显示语言独立选择
locale: zh-Hans
status: draft
created: "2026-09-14"
---

# 中文规范、英文机器标识，显示语言独立选择

<!-- tao:section decisions -->
## 决策

```{adr} 中文规范、英文机器标识，显示语言独立选择
:id: ADR_20260914_WX7BFBRXENPN4CT7
:status: proposed
:links: REQ_20260914_GDY8F3KPE6XBGWGD, REQ_20260914_42AXMZ2KH2RAZ8M3

<!-- tao:field context -->
**背景与备选：** 项目主要维护者阅读中文更方便；全英文便于更广泛协作，但会增加当前审阅负担；同步维护两套全文容易发生语义漂移。不同模型和任务的语言表现需要实测，通用知识问答成绩不能直接证明 skill 的执行效果。

<!-- tao:field decision -->
**选择：** tao-dev 的需求、设计及维护说明以简体中文为权威正文；代码标识、注释、文件名和机器协议使用英文，必要术语保留英文原名。后续 skill 入口初期沿用中文，保持单一规范来源；若目标模型的配对评测显示英文入口有明确收益，再形成可追溯的英文执行版本。模板本地化只替换人读文字，稳定键和 ID 不变；使用方的语言独立选择。

<!-- tao:field consequences -->
**影响与后果：** 要把显示标签从解析逻辑中移出，并测试中英文及 Unicode 边界。初版验证简体中文与英文，不宣称完整支持所有语言。未来译文记录源版本及审校状态，过期译文不能成为新的权威规则。
```
