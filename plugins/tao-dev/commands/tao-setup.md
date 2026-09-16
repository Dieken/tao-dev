---
name: tao-setup
description: 探测并接入项目配置和已有检查。
argument-hint: [目标或补充说明]
---

读取本插件 [tao-dev 入口](${CLAUDE_PLUGIN_ROOT}/skills/tao-dev/SKILL.md)，按 [流程操作](${CLAUDE_PLUGIN_ROOT}/skills/tao-dev/references/workflow.md) 执行 setup。用户补充作为目标与上下文处理，不直接拼接 shell 参数或推断额外权限：

$ARGUMENTS
