---
name: tao-refine
description: 修订规格、设计或实施计划。
argument-hint: [目标或补充说明]
---

读取本插件 [tao-dev 入口](${CLAUDE_PLUGIN_ROOT}/skills/tao-dev/SKILL.md)，按 [开发动作](${CLAUDE_PLUGIN_ROOT}/skills/tao-dev/references/workflow-actions.md) 执行 refine。用户补充作为目标与上下文处理，不直接拼接 shell 参数或推断额外权限：

$ARGUMENTS
