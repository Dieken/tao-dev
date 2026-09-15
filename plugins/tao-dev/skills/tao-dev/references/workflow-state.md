# 工作流状态接口

创建隔离任务、保存检查点、恢复会话或记录阶段决定时读取。用户动作与提问规则见 [流程操作](workflow.md)；下列是 agent 调用的底层接口，不要求用户逐个输入。

## 开始与定位

确认澄清完成并获准开始写 spec 后，agent 选择项目约定的语言和简短 slug：

```text
tao --project <root> workflow start --slug <slug> --summary <目标> --locale <语言> --decision <用户决定> --worktree
```

完整隔离流程要求 Git 已有初始提交、跟踪文件无未提交修改，且 `/.worktrees/` 已被忽略。默认创建 `.worktrees/<slug>` 和 `tao/<slug>` 分支，记录基础分支和完整 fork commit；已经位于宿主创建的 worktree 时复用当前副本。未跟踪的项目配置可复制到新副本，不复制未提交源码。冲突先调查，不能覆盖已有目录。没有 Git 时仍可使用文档与检查功能；省略 --worktree 可在明确选定的现有目录保存状态，但不代表提供了隔离。

返回 CHG ID、当前阶段 spec 和预留计划路径。开始不生成占位计划。正式状态位于 `.tao/workflows/<CHG-ID>.json`，只维护协调信息，文档正文和任务进度仍以正式文档为准。状态属于可保留的项目控制信息，不放临时复现或日志。它记录决定，不认证用户身份，也不授予客户端权限。

`tao workflow status [CHG-ID]` 只读列出状态，主项目可通过 Git 已登记的 worktree 发现任务。多个目标由 agent 根据当前上下文选择，仍不明确时请用户选择。跨项目操作显式传 --project，不依赖会话是否已切换 cwd。无法读取状态时保留现场并恢复，不能静默新建同名任务。

## 检查点与阶段

`tao workflow checkpoint <CHG-ID> --expect <revision> --from <项目相对 JSON>` 接受以下字段：

- summary、next：简短实际状态及下一步。
- blockers、operations：未解决问题及仍需核对的进程、任务、日志入口；字符串数组。记录不代表进程仍活着。
- artifacts：spec、design、plan 到现有项目相对文档路径数组的映射。只存入口，不复制正文。

更新采用项目写锁和原子替换；revision 不一致时拒绝覆盖，先读取最新状态再协调。每次有意义的进展都保存检查点，不能只在 handoff 时保存。

`tao workflow advance <CHG-ID> --expect <revision> --decision <用户决定>` 记录批准当前产物并进入下一阶段：spec → design → plan → implement → review → finish → complete。前三阶段需要已关联且通过源校验的对应文档；批准绑定实际内容摘要。计划的任务勾选、evidence 行及显式 tao:results 块属于执行记录，不使计划批准失效；任务正文、依赖、验证办法与方案变化仍会失效，不能把这些内容藏进结果块。计划进入实现还需 `--doc-review completed|skipped` 记录真实文档审查或用户跳过决定，不能以参数代替实际审查。

`tao workflow revise <CHG-ID> --expect <revision> --phase spec|design|plan --decision <用户决定>` 回到指定已到达阶段，撤销该阶段及下游的旧批准，不删除产物或代码。批准后的文档变化会由 status 标记 stale_approvals；不得继续沿用过期批准。纯文档排版也会触发保守失效，agent 解释实际影响并取得相称决定。

阶段推进只是协调记录，不证明测试通过、审查完成、提交或发布。实现阶段内按已批准计划自主推进，检查与交付门槛仍由 verify 和项目规则决定。结束前核实真实产物、运行中的操作以及用户对合并、推送和清理的选择。

## 与计划的关系

创建计划时使用 `tao new --slug <原 slug> --change <CHG-ID>`，沿用开发事项的 CHG ID、日期、语言和预留路径。已有设计附件不阻止本事项创建计划；已有计划一律不覆盖。未使用工作流状态的已有计划仍可直接使用原 CLI。

CHG 表示开发事项，plan 表示实施计划。计划出现前，状态提供 CHG 引用目标；计划出现后，正式文档中的定义成为展示入口。不能用是否存在 plan.md 来推断整个任务是否存在或已获准实现。

## handoff 与 continue

`tao handoff <CHG-ID> --from <摘要文件>` 接受 handoff profile，计划前也可保存到预留计划的同名附件目录。返回可点击路径，由 agent 提示在对应项目内用 `continue` 恢复；多个任务时附上这个实际路径。正式 handoff 默认随项目保留，不加入忽略规则，不复制完整会话，也不自动提交或传送未提交源码。

continue 先读取 status、对应产物及 handoff，核对当前进度、批准时效、未完成修改、测试证据和记录的运行中操作。不能仅凭旧摘要重做已完成任务或重新启动仍活跃的进程。确认核对完成后：

```text
tao workflow resume <CHG-ID> --expect <revision> --decision <核对结果> --handoff-digest <status 返回的摘要>
```

不存在 handoff 时省略 --handoff-digest。此操作只记录恢复检查点，保留当前阶段、下一步和任务进度，不删除 handoff、不自动批准下一阶段。文件在核对后改变会拒绝接续；新版本显示 unread，已接续版本显示 resumed。再次 continue 从新检查点继续，旧摘要只作背景。保存 handoff 后如状态更新冲突，文档仍保留，status 可按固定位置重新发现。

没有 handoff 时仍从状态及实际产物恢复；缺少的会话讨论不能凭空还原。状态文件也丢失时先调查现有分支和文档，向用户列出能确认的阶段与缺失决定，不能用文件存在推断批准。整个机制不提供进程保活、文件备份或跨机器传输。
