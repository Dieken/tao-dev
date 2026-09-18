---
name: tao-debug
description: 调查缺陷并按授权复现或修复。
argument-hint: [目标或补充说明]
---

读取本插件 [tao-dev 入口](${CLAUDE_PLUGIN_ROOT}/skills/tao-dev/SKILL.md)，按 [开发动作](${CLAUDE_PLUGIN_ROOT}/skills/tao-dev/references/workflow-actions.md) 执行 debug。用户补充作为目标与上下文处理，不直接拼接 shell 参数或推断额外权限：

$ARGUMENTS
