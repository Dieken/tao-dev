---
schema: tao.project.design/v0.1
id: DOC_20261105_0H6V7T4BYCRJW79H
title: 工作流恢复与持久生命周期设计
locale: zh-Hans
status: draft
created: "2026-11-05"
spec_docs: [DOC_20261105_27RJ5NTQG9BNBJHX]
---

# 工作流恢复与持久生命周期设计

<!-- tao:section overview -->
## 概述

本设计实现[工作流状态恢复与事项生命周期规格](../product/workflow-recovery.md)，供 tao-dev 维护者实现 CLI、校验器及 skill 使用。以下接口与新 profile 是待实现契约，不表示当前版本已提供。当前阶段仅形成设计，不生成计划、运行记录格式或实现代码。

正式文档保留跨机器不可丢失的决定，本地 JSON 保留高频执行协调。恢复重建后者，不从文件存在推断授权。每个事项独立存储，会话选择不写入全项目活动指针。

<!-- tao:section architecture -->
## 边界与架构

### 数据归属与方案选择

采用每个 CHG 一份 Markdown 正式记录，默认位于 `docs/workflows/<CHG-ID>.md`，使用新增 `tao.project.workflow/v0.1` profile。目录可通过项目路径配置映射，必须处于受管理源范围且不能被忽略。正文供用户阅读，结构化元数据供 CLI 恢复；禁止正文再维护一份独立阶段或批准事实。记录从 start 创建，覆盖没有 plan 的阶段。

| 方案 | 判断 |
|---|---|
| 提交完整 workflow JSON | 体积与更新频率违背用户要求，不采用 |
| 仅靠现有 plan 元数据恢复 | 无法覆盖计划前事项，也没有批准绑定和审查预算，不采用 |
| 单份全项目事项台账 | 并行分支经常争用同一文件，不采用 |
| 每事项正式记录加本地 JSON | 仅重要事件更新，天然按 CHG 隔离，采用 |

正式记录不保存完整文件清单、快照内容、进程日志或完整 review request。spec/design/plan/tasks 仍拥有正文和任务事实，review 报告拥有审查发现。正式记录保存文档 ID、摘要和绑定，不复制上述正文。

### 模块职责

- 新增持久记录模块负责 profile 数据归一、事件转换、摘要、校验和原子写入；复用现有项目路径约束、锁及比较后替换，不新增数据库或服务。
- workflows 负责本地执行状态、恢复和跨 worktree 定位。所有依赖状态的入口统一使用定位结果和诊断，禁止各命令吞掉定位歧义后自行猜测。
- documents/relationships 的正式索引先解析 docs，不依赖本地 JSON 可读；只读旧状态是兼容补充，其错误不能阻止独立文档检查。
- review_runs 负责将尝试占用、结束标记及当前额度决定写入持久记录；输入归一规则继续由现有审查实现维护。
- skill 负责会话中选择事项、在已有授权内调用 recover，以及展示缺口和 finish 建议；CLI 不保存全局会话指针。

分发的 workflow profile、模板和写法由消费项目的 LLM 与源校验器读取，恢复模块在运行时读取正式记录，因此随 skill 打包。本设计与本项目的规格、计划留在顶层 docs/，不随包分发。

<!-- tao:section contracts -->
## 接口与数据契约

### 正式记录

新记录使用现有 DOC 元数据与固定正文节 `overview`，只展示当前生命周期及阶段；兼容读取带 `review_batches` 和三节正文的旧记录。文档 status 仍为 draft/accepted/retired，与事项生命周期分开。新增结构化字段如下；未知字段、类型错误、重复身份和无效关系均报错。

| 字段 | 契约 |
|---|---|
| change、slug、title、locale、created | 原事项身份和基本信息；CHG 与 DOC 独立 |
| record_revision | 从 1 递增，只在持久事件变化时更新 |
| lifecycle | active、paused、completed、cancelled、unknown；新建事项 start 为 active，legacy 导入无法证实时必须显式保存 unknown，并附 provenance.unknown_fields 包含 lifecycle；非 legacy 记录不允许 unknown |
| phase | 已记录的 spec/design/plan/implement/review/finish/complete；不能表示推测的批准 |
| artifacts | 各角色的 DOC ID 数组，按正式索引解析路径；任务通过 tasks_doc 关系解析 |
| plan_path | 尚无计划时预留的项目相对路径；已有计划时核对同一 CHG |
| approvals | 阶段键表示批准事实，值保存绑定摘要及算法；完整决定文字留本地或已有正式决定，缺失表示未证实 |
| baseline | 经确认的原始 commit、分支说明与决定依据；不可用时为未知，不能用 HEAD 填充 |
| review_control | 每类仅保留当前批次 ID、阶段、已用次数、上限、当前授权、调用限制、未结束尝试及完整本地批次摘要；不保存逐轮列表或历史批次 |
| closure | 结束操作 ID、时间、结果、决定、验证/审查引用和未完成事项处置；未结束时为空 |
| provenance | 保留无法确认的字段；迁移未协调时保留来源摘要，协调后的后续持久事件去除该临时来源信息；不保存机器绝对路径 |

批准摘要引入有版本的规范化算法，按 DOC 身份绑定内容。spec/design 对内容做摘要；plan 继续排除任务勾选、evidence 行和合法结果块，并纳入独立 tasks 契约。记录原算法版本，不能将旧路径摘要悄悄改写为新算法。文件迁移后可按 DOC 找到产物；不能确认旧绑定时报告待核对。

审查摘要必须绑定受检输入、范围、模式及必要的 Git index 信息；输出排除规则复用已有批次自身输出规则。正式 workflow 记录中本批次运行元数据也必须按字段归一排除，不能排除整个文件而放过生命周期、批准或范围的变化。缺少摘要重算所需上下文时，只恢复历史结果，不认定当前 passed。快照过期不撤销历史结束，但重放旧现场可能不可用。

当前审查控制不表示历史结论或当前通过。恢复的本地批次保存 used_rounds，轮次分配及额度门禁按已用次数计算；不为满足旧列表长度而补造历史尝试。未结束尝试先占用次数，恢复后缺少现场时只能核对并登记失败，不允许直接派发或补登记通过。调用限制为结构化 timeout_seconds 与 cost_limit_usd；limits 整体为空表示未知，cost_limit_usd 单项为空才表示无 CLI 费用阈值，不从自然语言推断数值。完整本地批次摘要只用于在恢复写入中断时核对已有现场；不相符的本地资料保存在忽略状态的 recovery_local_reviews，不充当当前通过。已结束且无未结束尝试时不再保存审查控制；历史结果由正式报告及 Git 历史维护。

### CHG 定义与兼容

存在正式 workflow 记录时由它定义 CHG，plan 的 change 成为对同一 CHG 的关联；没有正式记录时保留旧 plan 定义 CHG 的行为。解析分两步收集候选再确定定义，不依赖文件遍历顺序。同一 CHG 最多一份正式记录、一个主计划；多个正式记录、多个主计划或身份不一致都报告冲突，不能借兼容规则隐藏重复。

新记录产生前，已有 JSON 与 plan 继续可用。生命周期 unknown 的正式导入记录是合法状态：查询和候选选择始终保留，不能按 active 或已结束解释；即使只剩它一个候选也仅可定位，不自动取得继续开发授权。只有明确的生命周期决定才能通过 resume 转为 active/paused，或通过 finish 的相应条件结束；清除 unknown_fields 中的 lifecycle 并保存决定，不从 phase、勾选或迁移动作推断。对于只有旧 plan 的事项，生命周期 unknown；对于只有旧 JSON 的事项，以可读取记录为迁移依据，不能自动声称其决定已跨机器持久化。仅正文引用不创建事项。旧 CHG 不重新分配。

### 命令与选择

| 入口 | 行为 |
|---|---|
| workflow status [CHG]、status [CHG] | 合并正式记录、旧计划和本地状态的只读观察，输出来源、生命周期、阶段、工作区、状态路径及恢复可用性 |
| workflow recover CHG | 只读生成恢复候选、已知事实、冲突和待核对项 |
| workflow recover CHG --apply | 重新核对资料后排他创建本地状态；兼容旧事项时同时建立选定事项的正式记录，不改其他事项 |
| recover 的 --expect-source 参数 | 可选预览摘要；skill 自动应用时必须携带，材料改变则拒绝应用并重新预览 |
| workflow migrate CHG [--apply --expect REV --expect-source DIGEST] | 为现存可读旧 JSON 显式迁移；默认只读预览，应用须同时绑定本地 revision 和来源摘要，不复用 recover 的缺失状态创建分支 |
| workflow resume | 核对现有状态、handoff 与实际操作，不负责缺失文件创建 |
| workflow finish CHG --expect REV --decision TEXT --outcome completed或cancelled | 保存结构化结束结果；completed 检查交付条件，cancelled 要求未完成事项处置；保留独立的合入、推送、清理授权 |

finish 的结构化依据通过 `--from` 项目相对 JSON 输入，内容含验证/审查引用及未完成事项处置，不接受任意 state 字段。advance 的 finish → complete 分支调用同一收尾实现；没有有效收尾输入时给出 finish 指引，不再只修改 phase。暂停/恢复生命周期沿用明确决定的转换，不由切换事项触发；具体通过 resume 的生命周期选项表达，仍须 revision 检查。cancelled 保留结束时的 phase，completed 才设置 complete。

无 CHG 的 status 列出事项，不强制选一个。需要目标的 CLI 写命令保留显式 CHG。skill 依次采用用户显式目标、会话选择、worktree 唯一可信关联、唯一未结束事项；unknown 生命周期不能当作已结束排除。只要剩余候选仍有歧义就展示标题、身份、生命周期、阶段和位置。分支名称匹配仅用于提示，不证明归属；跨 worktree 的同一身份多副本必须显式选择项目。

切换只更新会话目标，不隐式执行 git switch、不结束原事项、不停止原进程。已完成事项直接读取正式记录；后续独立需求建立新 CHG，恢复不会重新打开旧事项。

### 现存旧 JSON 的迁移

`workflow migrate CHG` 只处理本地 JSON 可读、身份匹配而尚无正式记录的选定事项，支持 JSON-only 和 JSON+plan。预览列出原始 revision、源摘要、可导入字段、未知信息和正式记录目标路径；摘要包含旧 JSON 原始字节及本次读取的文档内容与关系。损坏 JSON 不迁移，已有正式记录指向 resume 协调；不得要求先删除或移走唯一旧 JSON。

`--apply` 必须携带预览的 `--expect` 和 `--expect-source`。锁内重读旧 JSON 与相关文档，任一版本或摘要不符均拒绝，不新建记录也不改本地文件。正式记录只复制可解释的持久依据，保留旧批准算法与实际已用审查轮次；没有明确生命周期事实时写入合法的 unknown 和来源说明。旧 phase=complete 可以作为历史阶段事实保留，但不能补造新格式所需的交付或 closure 依据；生命周期仍待明确核对。不能解析的扩展字段不进入正式 schema，原 JSON 的该字段及其值原样保留。

应用按既定顺序先排他创建正式记录，再以原字节作比较条件更新 JSON 的同步标记及 revision。所有原有字段，包括未知扩展、检查点、完整旧审查请求、基准和操作信息均保留，不能用精简投影覆盖原 JSON。首次迁移的 provenance 保存原 JSON 摘要和 revision；本地同步失败时正式记录已存在，重试 migrate 不再次创建或重复迁移，返回 resume 协调指引。resume 核对 provenance 和当前 JSON 后完成同步：原始字节仍匹配时只补标记及 revision；内容已变则展示冲突，不用正式记录覆盖较新本地事实。正式写入失败时旧 JSON 字节不变。skill 不把普通 continue 隐式升级为迁移写入，先展示选定事项迁移预览，在用户已授权迁移的范围内应用。

仅有旧 plan、没有 JSON 的情况仍走 recover；创建正式记录时写入 lifecycle=unknown、legacy 来源及缺失字段，closure 为空，phase=spec 仅表示待核对协调起点。完成后再复制正式资料到新目录查询，必须仍显示 unknown；既不伪装为 active，也不丢失候选。迁移与恢复不补造批准、审查预算或结束决定。

### 恢复过程

1. 在显式项目范围及登记 worktree 中发现来源；解析正式定义与直接关系，不遍历整个引用图。
2. 区分 missing、corrupt、ambiguous、legacy、available、closed。状态缺失时返回绝对预期路径，命令建议对含空格路径正确引用；JSON 结果另给参数数组供调用者执行。
3. 校验适用资料，计算包含文档内容及关系的 source_digest；读取任务事实，验证批准绑定和审查依据，重新观察当前 Git 环境。旧基准与当前环境分别保存。
4. 有正式记录时恢复其已记录阶段；缺批准或绑定失效时列为阻断。只有旧文档时从 spec 作为待核对协调起点，单独展示候选进度；不把任务全部完成提升为 complete。
5. 应用前在锁内重新读取并比较摘要、目标文件存在性、正式记录 revision。已有或损坏本地文件均不覆盖。恢复写入新的本地 revision、持久 revision/source digest 和已知字段，未知运行操作设为待核对阻断，不假设已停止。
6. skill continue 自动应用只限目标明确、已有继续授权且无来源冲突；恢复后仍报告缺失批准或操作核对项，不能自动推进阶段。status 和其他命令不暗中调用写入恢复。

### 两类写入与中断

checkpoint 等高频操作只更新本地 JSON。阶段批准、revise、审查尝试与额度决定、生命周期转换是持久事件，必须同时更新正式记录和本地投影。

每次持久事件在现有项目 mutation_lock 内读取两个版本，验证前置条件，生成 operation_id，先原子保存正式记录，再原子替换本地状态；本地保存最后同步的 record_revision 和 operation_id。正式记录保存最后事件 ID 和当前恢复依据，未结束审查尝试及 closure 保留稳定身份。第二次写入失败时返回明确的“正式记录已保存，本地待同步”，不撤销已持久结果。

后续写命令发现 revision 不一致时停止原动作；resume 在核对后仅同步持久字段，保留本地未冲突的检查点和操作信息。若本地文件缺失则 recover 重建。重复 finish 发现相同 closure 返回已结束结果，不增加第二次结束事件；不同结束决定必须报告冲突，不能覆盖。

start 同样先创建正式记录再创建 JSON，第二步失败时返回原 CHG 和 recover 命令，不能重试生成另一 CHG。创建 worktree 已成功但后续失败时保留工作区并指出位置。计划生成通过正式记录关联原 CHG，禁止提前生成空计划充当身份记录。

项目锁只协调本机同一工作区。不同机器或 worktree 合并发生正式记录冲突时依赖 Git 显式解决；不做最后写入者获胜。相同 record_revision 而内容不同由 source digest 检出。

<!-- tao:section invariants -->
## 不变量与正确性

- 一个 CHG 在选定工作区有且仅有一个正式身份入口，旧 plan 的兼容定义不能重复注册。
- 恢复、切换和本地 revision 重建不产生新的批准、审查额度或结束决定。
- 未知和失败不等于通过；历史结束事实与当前证据时效分别展示。
- 正式记录写入失败时本地持久投影不得前进；正式写入成功而本地失败时不得重新执行该持久事件。
- 普通检查点不修改正式记录；审查开始必须先持久计入尝试，之后才能派发，即使派发失败该尝试也不消失。
- 任务进度只来自计划或 tasks，恢复不改勾选，批准只绑定适用的契约内容。
- completed 必须满足现有交付策略及审查条件，不能因 phase 为 finish 就跳过检查；cancelled 不能显示为交付成功。

这些不变量用状态转换和故障注入测试验证；计划阶段再评估是否需要短小状态模型来挑战两文件写入协议，不预先引入长期维护的形式化工具。

<!-- tao:section errors -->
## 失败处理

| 情况 | 输出及下一步 |
|---|---|
| JSON 缺失 | 精确绝对路径、文档来源、recover 预览和应用命令 |
| 可读旧 JSON 且无正式记录 | 输出 migrate 预览入口；应用需 revision 与 source digest，不提示删除 JSON 后 recover |
| JSON 损坏 | 路径、解析原因、保留现场；用户先移走或修复损坏文件，再恢复，CLI 不提供隐式覆盖 |
| 正式记录损坏或有合并冲突 | 指出源文件和字段，阻止相关恢复与写入，不以本地副本反向覆盖 |
| DOC 引用缺失、重复定义、越界路径 | 输出具体来源与引用，不猜测替代文档 |
| 批准失效、轮次未知、原基准缺失 | 展示已知进度和待决定项，仅阻断依赖该依据的操作 |
| 预览后资料变化 | 拒绝应用，重新预览，不使用旧候选 |
| 本地和正式记录不同步 | status 只读显示差异；resume/recover 按文件是否存在完成显式协调 |
| 项目配置不纳入正式记录目录 | 创建前报告配置缺口，不写入校验器看不见的记录 |

共享诊断提供稳定 rule_id、CHG、expected_path、candidate_sources、recovery_commands 和冲突原因；文本中实际路径和命令可复制。纯文档校验不把丢失本地状态当成文档错误，正式引用缺失仍是错误。

<!-- tao:section verification -->
## 验证

实施阶段对照规格九组场景建立 CLI 和 skill 行为回归：跨目录仅复制受跟踪资料、计划前恢复、多 CHG 与共享文档、两个会话独立选择、切换期间仍有操作、损坏及重复状态、旧计划 unknown、结束结果跨机器读取。检查既有合法反例，避免将没有 workflow 的普通文档项目变成错误。

在持久写入前后及本地替换前后分别注入失败，验证 start、advance、review-begin、finish 重试不重复事件；并发恢复仅允许一个创建者，预览后修改和相同 revision 内容分歧均可发现。审查测试覆盖自己的记录写入不使输入失效、修改批准或范围仍使绑定失效，以及未知尝试不重置额度。

校验器测试覆盖新增 profile、嵌套字段类型与枚举、CHG 定义优先级、DOC 关系、重复主计划、目录配置与出版锚点。检查迁移保持 ID，不批量修改未选择的历史事项。对 JSON-only 与 JSON+plan 执行 migrate 预览和应用，比较未知字段、批准、轮次、基准和任务未丢失；覆盖摘要过期、并发写入、正式成功本地失败后 resume、已有记录重复迁移。对 plan-only 执行 recover 应用、profile 校验及跨目录查询，确认 unknown 可持久化且不自动选成 active；缺少 legacy 来源的 unknown 必须被校验拒绝。分发测试验证新增 profile、模板、运行模块实际被打包，内部设计未被打包。

本设计阶段只执行受管理文档的源结构、ID、关系和导航检查；不把该结果视为恢复功能、并发协议或客户端行为验收。实现后按项目测试策略执行适用回归并汇总在变更计划，原始输出留在忽略的临时目录。
