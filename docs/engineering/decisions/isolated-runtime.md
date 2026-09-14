---
schema: tao.project.decision/v0.1
id: DOC_20260914_YWCGBAJWE648CM8S
title: 开发依赖与插件运行环境
locale: zh-Hans
status: draft
created: "2026-09-14"
---

# 开发依赖与插件运行环境

<!-- tao:section decisions -->
## 决策

```{adr} 开发锁定与插件运行环境分离
:id: ADR_20260914_Z19W6HRG4MWQM97A
:status: accepted
:links: REQ_20260914_W1NDXAS6DMV7D7HH, REQ_20260914_GH69P66HSM6HDZXF, REQ_20260914_WAHF2CDHEJFSBGDC, REQ_20260914_5PFGD8NJKSAVG2NT

<!-- tao:field context -->
**背景与备选：** 开发使用 uv 不应要求插件使用者也安装 uv；向系统或业务环境安装依赖会产生版本耦合。把所有依赖内置或打包 Python 会增加发布平台和维护负担。

<!-- tao:field decision -->
**选择：** 以 pyproject.toml 和 uv.lock 管理开发，导出带哈希的 pip 清单。标准库启动层负责 setup、doctor 和环境选择；CLI、hook 共用。插件根只读，依赖保存于客户端数据目录，可显式覆盖到隔离试验目录。新环境在最终路径创建，验证后才可选，不能移动 venv。

<!-- tao:field consequences -->
**代价：** 需要维护小型启动层和发布同步检查。使用方须提供受支持的 Python；首次准备依赖需要网络或明确提供的离线包。客户端 scope 与运行数据归属独立，具体能力必须逐端验收，不将模拟结果记为真实兼容。
```
