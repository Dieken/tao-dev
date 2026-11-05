# 工作流状态接口

创建隔离任务、记录阶段决定、保存检查点或恢复会话时读取对应小节。授权与讨论见 [流程操作](workflow.md)，动作步骤见 [开发动作](workflow-actions.md)。

## 开始与定位

获准开始 spec 后，按项目约定选择语言和 slug：

```text
tao --project <root> workflow start --slug <slug> --summary <目标> --locale <语言> --decision <用户决定> --worktree
```

--worktree 要求 Git 有初始提交、跟踪文件无未提交修改，且 `/.worktrees/` 已忽略。默认创建 `.worktrees/<slug>` 与 `tao/<slug>`，记录基础分支和 fork commit；已位于宿主 worktree 时复用。可复制未跟踪项目配置，不复制未提交源码；冲突时先调查，不覆盖目录。无 Git 仍可用文档和检查，省略 --worktree 在选定目录保存状态不提供隔离。

返回 CHG、spec 阶段与预留计划路径，不生成计划。`docs/workflows/<CHG-ID>.md` 从开始保存可提交的生命周期与关键决定，`.tao/workflows/<CHG-ID>.json` 保存忽略的本地协调信息，正式文档维护正文和任务进度；状态记录不授予客户端权限。

`tao workflow status [CHG-ID]` 只读查询，主项目可发现已登记 worktree。根据上下文选事项，无法确定再询问；跨项目显式 --project。状态缺失时输出预期绝对路径和 recover 命令；损坏时保留现场，不覆盖或静默新建同名事项。

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

实现期的文档细化可自评恢复：把已实现的技术选择补进设计、把实测结论写回文档、修补任务 verify 的措辞或登记例外，这类修订不改变承诺、需求与任务范围，agent 可自行 revise 并重新批准回到 implement，决定文字须写明是自评、被修订的具体内容，以及它为何不落入下列任何一条。仍须停下取得用户批准的是：改变产品承诺或验收实质、增删需求、改变任务范围、自己判断不准或存在两种合理改法。自评不适用于阶段首次批准，只用于已获批准阶段内的回补。

阶段批准、撤销、审查尝试和生命周期决定先保存正式记录，再同步本地 JSON；普通 checkpoint 只更新本地。不同步时先 resume，不能重复事件。交付检查按 [验证规程](verification.md) 执行。finish → complete 使用 workflow finish 并提供结构化收尾依据。

## 创建计划

`tao new --slug <原 slug> --change <CHG-ID>` 沿用事项的 ID、日期、语言和预留路径，已有本事项设计附件不阻止创建，已有计划不覆盖。CHG 可先由状态提供引用目标，计划出现后以文档定义为展示入口；已有无状态计划仍可用原 CLI。

## handoff 与恢复

`tao handoff <CHG-ID> --from <摘要文件>` 接受 handoff profile，保存到计划或预留计划的同名附件目录；给出返回路径、实际 worktree／branch 和 continue 输入。摘要保留目标、决定、现状、证据、阻断与下一步，链接权威材料。正式 handoff 随项目保留，不自动提交、停止会话或传输源码。

continue 先读 status、产物及 handoff，核对副本、有效批准、任务进度、未提交修改、证据时效和实际运行中的操作，避免重复执行；按 [流程操作](workflow.md) 展示进度与下一步建议。核对后记录：

```text
tao workflow resume <CHG-ID> --expect <revision> --decision <核对结果> --handoff-digest <status 摘要>
```

无 handoff 时省略 --handoff-digest；resume 保留当前阶段与任务，不批准下一阶段。核对后文件变化会拒绝接续，新摘要为 unread，已接续版本为 resumed；再次恢复从新检查点继续。handoff 已保存而状态更新冲突时，status 可重新发现文件。

无 handoff 时仍可从状态和产物接续。本地状态缺失时执行：

```text
tao --project <root> workflow recover <CHG-ID>
tao --project <root> workflow recover <CHG-ID> --apply --expect-source <预览摘要>
```

默认只读预览；应用保留 CHG、文档与任务勾选，缺失批准、基准、轮次和运行操作保持未知或待核对。现有或损坏 JSON 不覆盖。仅有旧 plan 时新正式记录保存 legacy 来源和 lifecycle=unknown；没有权威记录或唯一计划时报告不足，不靠正文 CHG 字符串猜测。

可读旧 JSON 尚无正式记录时，不删除 JSON：先 `workflow migrate <CHG-ID>`，再传 `--apply --expect <revision> --expect-source <预览摘要>`。迁移保留旧字段、检查点和完整本地审查上下文，正式记录只保存精简持久信息；第二次写入失败后按提示 resume。来源变化时重新预览。审查历史未知时默认 review-begin 被拒绝；只有用户明确授权新批次和额度，才能同时提供 --new-batch 与 --max-rounds，决定持久保留，不能借恢复清零旧尝试。

### 自动调用与多个事项

status 只读发现并列出事项，不自动恢复。continue 已明确 CHG、有继续授权且来源无冲突时，可以预览并携带摘要应用 recover；迁移已有 JSON 需已有迁移授权。其他状态依赖写命令缺文件时提示恢复，不隐式重试。无状态的普通文档检查仍可运行。

依次采用显式 CHG、当前会话选择、当前 worktree 唯一可信归属、当前范围唯一未结束候选。unknown 不当作已结束排除，定位不构成继续授权。仍有歧义时列出标题、CHG、生命周期、阶段与目录，请用户选择；不使用最近修改时间或项目全局 active 指针。写命令传明确 CHG，跨目录传 --project。

同一 CHG 出现在多个 worktree 时，查询列出来源及冲突，显式 --project 选择现存状态副本；当前目录仅有文档时先定位唯一持有本地状态的 worktree，recover 不会在另一 worktree 已有 JSON 时静默创建第二份。

切换只改变会话目标，不自动 git switch、结束原事项或停止其进程；必要时保存检查点并提示待核对操作。unknown 转 active/paused 需明确决定，用 `workflow resume <CHG-ID> --expect <revision> --decision <决定> --lifecycle active|paused`。已结束事项不能借 resume 重新打开。

### 结束与保留

交付检查和审查条件满足时建议 finish，不因为切换、时间经过或勾选全部任务就自动结束。调用 `workflow finish <CHG-ID> --expect <revision> --decision <决定> --outcome completed|cancelled --from <项目相对 JSON>`；JSON 仅含 evidence 和 unfinished 两个非空字符串数组（数组本身可空），cancelled 必须填写 unfinished 的处置。completed 运行完整交付门禁。

只有旧 JSON、尚无正式记录时，finish 会拒绝并提供 migrate 预览命令；显式迁移后再按新 revision 收尾。正式记录损坏时诊断指向该 Markdown，不会误称本地 JSON 损坏或建议覆盖恢复。

正式 closure 保存时间、结果、依据及未完成事项处置，先落盘再同步本地；同一收尾重试不产生第二次结束。已结束事项可直接从 docs 查询，历史结束不因证据过期消失。合入、推送和清理仍分别需要授权。

正式 workflow profile 由 CLI 与校验器读取，记录目录可通过 paths.workflows 配置且须纳入管理、不能被忽略。配置 book_root 时未手工编入导航的记录由出版器附加到书根隐藏目录。正式记录不保活进程、不备份未提交文件或跨机器传输。
