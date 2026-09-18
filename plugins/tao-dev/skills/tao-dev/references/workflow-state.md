# 工作流状态接口

创建隔离任务、记录阶段决定、保存检查点或恢复会话时读取对应小节。授权与讨论见 [流程操作](workflow.md)，动作步骤见 [开发动作](workflow-actions.md)。

## 开始与定位

获准开始 spec 后，按项目约定选择语言和 slug：

```text
tao --project <root> workflow start --slug <slug> --summary <目标> --locale <语言> --decision <用户决定> --worktree
```

--worktree 要求 Git 有初始提交、跟踪文件无未提交修改，且 `/.worktrees/` 已忽略。默认创建 `.worktrees/<slug>` 与 `tao/<slug>`，记录基础分支和 fork commit；已位于宿主 worktree 时复用。可复制未跟踪项目配置，不复制未提交源码；冲突时先调查，不覆盖目录。无 Git 仍可用文档和检查，省略 --worktree 在选定目录保存状态不提供隔离。

返回 CHG、spec 阶段与预留计划路径，不生成计划。`.tao/workflows/<CHG-ID>.json` 随项目保留协调信息，正式文档维护正文和任务进度；状态记录不授予客户端权限。

`tao workflow status [CHG-ID]` 只读查询，主项目可发现已登记 worktree。根据上下文选事项，无法确定再询问；跨项目显式 --project。状态不可读时保留现场恢复，不静默新建同名事项。

## 检查点与阶段

`tao workflow checkpoint <CHG-ID> --expect <revision> --from <项目相对 JSON>` 接受：

| 字段 | 内容 |
|---|---|
| summary、next | 简短状态和下一步 |
| blockers、operations | 阻断与待核对操作／日志入口，字符串数组 |
| artifacts | spec、design、plan 到现有项目相对文档路径数组的映射 |

有意义进展后保存检查点；revision 冲突时读最新状态再协调。operations 是记录，恢复时须查实际进程。

`tao workflow advance <CHG-ID> --expect <revision> --decision <决定>` 按 spec → design → plan → implement → review → finish → complete 推进。前三阶段须关联通过源检查的对应文档，批准绑定内容；任务勾选、evidence 行及 tao:results 内执行记录不使计划批准失效。任务正文、依赖、验证办法或方案发生变化，仍会使计划批准失效，不能藏进结果块。进入 implement 还须用 `--doc-review completed|skipped` 记录实际审查决定。

`tao workflow revise <CHG-ID> --expect <revision> --phase spec|design|plan --decision <决定>` 返回已到达阶段并撤销该阶段及下游批准，保留产物。status 的 stale_approvals 不能继续沿用；即使只改排版，系统也可能出于谨慎将原批准标为失效；说明实际影响并重新取得批准。

阶段推进只保存协调记录，交付检查按 [验证规程](verification.md) 另行执行。

## 创建计划

`tao new --slug <原 slug> --change <CHG-ID>` 沿用事项的 ID、日期、语言和预留路径，已有本事项设计附件不阻止创建，已有计划不覆盖。CHG 可先由状态提供引用目标，计划出现后以文档定义为展示入口；已有无状态计划仍可用原 CLI。

## handoff 与恢复

`tao handoff <CHG-ID> --from <摘要文件>` 接受 handoff profile，保存到计划或预留计划的同名附件目录；给出返回路径、实际 worktree／branch 和 continue 输入。摘要保留目标、决定、现状、证据、阻断与下一步，链接权威材料。正式 handoff 随项目保留，不自动提交、停止会话或传输源码。

continue 先读 status、产物及 handoff，核对副本、有效批准、任务进度、未提交修改、证据时效和实际运行中的操作，避免重复执行；按 [流程操作](workflow.md) 展示进度与下一步建议。核对后记录：

```text
tao workflow resume <CHG-ID> --expect <revision> --decision <核对结果> --handoff-digest <status 摘要>
```

无 handoff 时省略 --handoff-digest；resume 保留当前阶段与任务，不批准下一阶段。核对后文件变化会拒绝接续，新摘要为 unread，已接续版本为 resumed；再次恢复从新检查点继续。handoff 已保存而状态更新冲突时，status 可重新发现文件。

无 handoff 时从状态和产物恢复；状态也丢失时调查分支与文档，列出可确认阶段和缺失决定，不从文件存在推断批准。此机制不保活进程、不备份文件或跨机器传输。
