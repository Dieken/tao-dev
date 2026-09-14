---
description: 核对当前变更的验证范围与完成条件。
argument-hint: [变更或目标]
---

读取本插件 [tao-dev 入口](${CLAUDE_PLUGIN_ROOT}/skills/tao-dev/SKILL.md)，按 [流程规程](${CLAUDE_PLUGIN_ROOT}/skills/tao-dev/references/workflow.md) 执行 verify。由上下文确定目标和必要范围；完整能力缺失时如实报告，不以局部通过宣称完成。用户补充：

$ARGUMENTS
