---
schema: tao.project.decision/v0.1
id: DOC_20260920_A73MEQTXF57YRFTM
title: 项目检查与缓存由项目原生工具管理
locale: zh-Hans
status: draft
---

# 项目检查与缓存由项目原生工具管理

<!-- tao:section decisions -->
## 决策

```{adr} 项目检查与缓存由项目原生工具管理
:id: ADR_20260920_YB4X14PK7D277PS7
:status: proposed
:links: REQ_20260914_0J68SDKV86ENKER2

<!-- tao:field context -->
**背景与备选：** 项目已有 justfile、Makefile、项目清单或 CI 来定义测试、代码静态检查、构建及缓存。在 tao 再保存命令参数、超时、输入范围、环境指纹与执行回执会形成第二套配置；输入声明不完整还可能把过时结果当作通过。备选是在 tao 维护通用执行器，或由项目工具独立执行、文档只记录可核对的结果。

<!-- tao:field decision -->
**选择：** 项目原生工具管理检查命令、超时、依赖、缓存与报告；`.tao/config.toml` 仅保存文档配置。`tao verify` 只校验受管理文档，不发现、执行或缓存项目代码检查。tao-dev 自身通过 justfile 的 `test`、`lint`、`check` 执行检查并保留原报告路径。

<!-- tao:field consequences -->
**影响与后果：** tao 不维护重复命令或跨工具的回执协议，也不提供统一的代码检查 JSON 输出。项目按实际工具定义退出码、缓存有效性与超时，智能体记录真实命令、输入、结果和限制；旧结果不能因摘要更新而变成新结果。计划的 `verification` 是持久结果摘要而非执行配置。没有运行或无法核对的检查明确记为未知，不推断完成或交付。
```
