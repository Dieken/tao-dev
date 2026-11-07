---
schema: tao.project.decision/v0.1
id: DOC_20260914_YWCGBAJWE648CM8S
title: 开发锁定与显式项目运行环境
locale: zh-Hans
status: draft
---

# 开发锁定与显式项目运行环境

<!-- tao:section decisions -->
## 决策

```{adr} 开发锁定与显式项目运行环境
:id: ADR_20260914_Z19W6HRG4MWQM97A
:status: accepted
:links: REQ_20260914_W1NDXAS6DMV7D7HH, REQ_20260914_GH69P66HSM6HDZXF, REQ_20260914_WAHF2CDHEJFSBGDC, REQ_20260914_5PFGD8NJKSAVG2NT

<!-- tao:field context -->
**背景与备选：** 开发使用 uv 不应要求使用者安装 uv；自动向用户或业务环境安装依赖会造成耦合。内置 Python 或维护环境选择数据库增加平台和维护成本。

<!-- tao:field decision -->
**选择：** pyproject.toml/uv.lock 锁定开发，导出带哈希的运行与出版依赖清单。读取和复制 skill 无需 Python；辅助入口的帮助与版本查询只用标准库；文档命令使用调用者显式选择的项目 .venv。没有 env prepare、自动下载或全局环境发现。

<!-- tao:field consequences -->
**影响与后果：** 保留可复现清单和明确缺依赖诊断；用户需要辅助工具时显式准备 Python 3.11–3.14 与依赖。项目文件部署不证明真实客户端兼容，出版依赖只为出版操作准备。
```
