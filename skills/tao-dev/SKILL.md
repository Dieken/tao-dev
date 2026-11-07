---
name: tao-dev
description: 项目文档与知识管理 skill；用于查找、创建、更新、语义审查、校验、出版和退役文档，以及持久计划与任务的读取、核对和结果回写。
---

# tao-dev · 项目文档与知识管理

用结构化文档保存可追溯的项目知识，用持久 plan/tasks 保存跨会话、跨客户端的项目进度。文档是需求、边界、决定和验收的语义契约，不只是格式正确的文件。

## 开始

先识别用户需要查找或改变的知识、文档或项目进度，定位项目根及现有权威文档，再读 [文档规程](references/documents.md)。只处理当前需要：小改动复用已有文档，不要求每次先创建 spec、design、plan。需要跨会话、协作或明确跟踪的工作，读取 [持久计划](references/planning.md)。

执行策略由 agent 根据用户授权和实际任务决定，tao 不编排实现、代码审查或会话阶段。agent 在实际工作后把结果写回项目文档；客户端原生任务只作临时执行步骤，不另立项目进度来源。

## 按需读取

| 当前需要 | 参考 |
|---|---|
| 创建、更新、查找长期知识 | [文档规程](references/documents.md)、对应 profile 模板与 [正文写法](references/document-content.md) |
| 记录、读取、核对和回写项目进度 | [持久计划](references/planning.md) |
| 审查文档的语义、依据与一致性 | [文档审查](references/review.md) |
| 校验源文档、区分项目检查与文档检查结果 | [确定性检查](references/verification.md) |
| 组织、出版、翻译或退役文档 | [组织](references/document-layout.md)、[出版](references/publication.md)、[本地化](references/localization.md)、[退役](references/retirement.md) |
| CLI、可选项目配置与依赖准备 | [工具入口](references/tools.md)、[运行环境](references/runtime.md) |
| 术语有歧义 | [术语](references/glossary.md) 与项目定义 |

长期当前事实维护在 spec/design/ADR 等权威文档；计划完成后保留为变更记录。任务全勾选不代表已验证、已审查或已交付，未知就说明未知。各原生 CLI 的任务持久化能力不同，便携的仓库文档而非私有会话状态才是项目进度依据。

相对链接以当前文件为基准；资源全在本 skill 内。读取无需安装 Python 依赖，也不修改用户级配置。
