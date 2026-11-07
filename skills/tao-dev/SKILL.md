---
name: tao-dev
description: 项目级文档驱动开发 skill；用于需求、设计、计划、实现、文档与代码审查，以及 refine、status、continue 和显式 handoff。
---

# tao-dev · 协作开发之道

围绕可验收的用户结果，选择简单方案，用结构化文档保存长期知识，以 plan/tasks 表达真实进度。

## 开始

先读 [流程操作](references/workflow.md)，再按当前动作读取 [开发动作](references/workflow-actions.md)。主线为 **new（spec → design → plan）→ review doc → implement → review code**；已有授权内连续推进，不要求逐步批准、workflow 注册或 finish。每个动作说明实际结果与下一步选项，选项不是强制停止关卡。

## 按需读取

| 当前工作 | 参考 |
|---|---|
| 需求、设计、实现、调试 | [工程规程](references/engineering.md) 及相关专题 |
| 编写或审查长期文档 | [文档规程](references/documents.md) 与当前 profile 模板 |
| 文档或代码审查 | [审查方法](references/review.md) |
| status、continue、显式 handoff | [开发动作](references/workflow-actions.md) 对应小节 |
| CLI、可选项目配置与安装 | [工具入口](references/tools.md)、[运行环境](references/runtime.md) |
| 术语有歧义 | [术语](references/glossary.md) 与项目定义 |

长期结论直接更新 spec/design/ADR 等权威文档，计划只保留当前结果摘要。详细 review/evidence 默认留对话或临时目录，不自动建档或提交。handoff 仅显式写一份临时 Markdown，不是恢复前置条件。任务全勾选不代表审查通过，未知就是未知。

相对链接以当前文件为基准；资源全在本 skill 内。读取无需安装 Python 依赖，不注册 hook、插件或用户级配置。
