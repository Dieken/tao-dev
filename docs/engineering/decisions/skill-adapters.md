---
schema: tao.project.decision/v0.1
id: DOC_20260914_YQSPSWMMX08JRR2B
title: 共享技能与项目客户端适配分层
locale: zh-Hans
status: draft
---

# 共享技能与项目客户端适配分层

<!-- tao:section decisions -->
## 决策

```{adr} 共享技能与项目客户端适配分层
:id: ADR_20260914_J5N1H8WPZZ4MNR04
:status: proposed
:links: REQ_20260914_BWAY1ZF6HNPM855Y, REQ_20260914_95193C19C90NRXV4

<!-- tao:field context -->
**背景与备选：** 为每个客户端维护独立文档契约与进度来源，容易产生不一致；把某个客户端的扩展当作公共标准，会导致未经验证的兼容性声明。

<!-- tao:field decision -->
**选择：** 共享完整的文档与知识管理技能（Agent Skill）；接入指南记录 Claude Code、Codex、Cursor、Kiro 的原生项目级技能路径，不提供安装适配层，用户级配置保持不变。项目文档与持久计划不依赖客户端临时状态。分发与依赖见 [打包设计](../skill-design.md)。

<!-- tao:field consequences -->
**影响与后果：** 保持一份规则与模板，降低平台耦合；文件部署、实际发现和模型行为分别验收，官方目录依据不替代真实运行。客户端自身可能发现同项目的其他原生目录，不保证客户端独占。
```
