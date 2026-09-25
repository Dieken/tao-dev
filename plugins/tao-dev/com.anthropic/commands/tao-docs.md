---
name: tao-docs
description: 构建本地文档书籍并返回入口。
argument-hint: [可选补充要求]
---

读取本插件 [tao-dev 入口](${CLAUDE_PLUGIN_ROOT}/skills/tao-dev/SKILL.md)，按 [开发动作](${CLAUDE_PLUGIN_ROOT}/skills/tao-dev/references/workflow-actions.md) 执行 docs。可选补充作为目标与上下文处理，不直接拼接 shell 参数或推断额外权限：

$ARGUMENTS
