---
description: 保存供后续会话恢复的简明交接。
argument-hint: [目标或补充说明]
---

先读取本插件 [工程规程](${CLAUDE_PLUGIN_ROOT}/skills/tao-dev/references/engineering.md) 与 [tao-dev 入口](${CLAUDE_PLUGIN_ROOT}/skills/tao-dev/SKILL.md)，按 [流程操作](${CLAUDE_PLUGIN_ROOT}/skills/tao-dev/references/workflow.md) 执行 handoff。用户补充作为目标与上下文处理，不直接拼接 shell 参数或推断额外权限：

$ARGUMENTS
