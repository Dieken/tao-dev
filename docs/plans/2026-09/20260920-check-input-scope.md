---
schema: tao.project.plan/v0.1
id: "DOC_20260920_RYR02DHVTJJVR8DY"
title: "检查按自己的输入范围复用"
locale: "zh-Hans"
status: draft
created: "2026-09-20"
spec_docs: ["DOC_20260914_4C7N0XHQSP7CY69P"]
design_docs: ["DOC_20260914_0VF190409FQCN197"]
change: "CHG_20260920_Y0WCT88THT8JXXS2"
---

# 检查按自己的输入范围复用

<!-- tao:section scope -->
## 目标与边界

`[verification]` 的 `inputs` 是整个策略共用的一个输入范围，检查回执也整体复用：任一输入变化使整份回执过期，下次调用重新执行全部检查。项目要把文档类或数据类检查接入策略时因此两难——把这些输入纳入范围，改一行文档就要重跑全部长检查；不纳入，该检查的结果又不随它自己的真实输入过期。触发本次改动的实例是一个消费方项目要把任务图不变量检查接入 `[[verification.checks]]`，而同策略内另有一项耗时 1800 秒的模型验证。

本次给每项检查增加可选的输入范围声明，只决定本次是否重新执行该项；整份回执仍绑定全局输入全集。取舍与被否决的两个备选见 {need}`ADR_20260920_YB4X14PK7D277PS7`。

范围限于 `taolib/verification.py` 的策略校验、输入快照、执行与证据判定四处，检查回执格式，以及两份使用方参考页。不改文档校验器、不改工作流状态机、不改 `--only` 的分类划分，也不给文档分类引入可配置命令——PostToolUse hook 每次编辑后调用 `verify --only docs`，该路径不执行任何项目命令，这条边界本次保持不变。

本事项执行中确认了一项既有缺陷，经用户决定一并修复：`tao review` 的输入绑定把本轮声明的报告输出算进受检输入，而 {need}`REQ_20260914_0J68SDKV86ENKER2` 的验收要求「审查开始前明确的新报告输出不改变受检输入」。它与本次主题无关，但属于同一条需求的实现缺口、同一个模块家族，单独成任务、单独提交。

不做逐项过期判定：输入变化的过期判定仍然整体进行，只有复用时效按每项检查各自的实际执行时刻判定。理由见设计章节。

<!-- tao:section references -->
## 规格引用

本批不新增承诺，落在两条已有需求的实现层：

- {need}`REQ_20260914_0J68SDKV86ENKER2` 要求记录验证对象、执行条件、结果和适用范围，受影响输入变化后使相关证据过期。本次把「相关」从整个策略共用一个范围细化到每项检查可有自己的范围，并按本次修订的验收补上复用行的执行时刻与时效判据。
- {need}`REQ_20260914_4CS6P421MGW68PME` 要求分发的 skill 入口给出适用条件、具体动作和判断依据。使用方读的验证规程与工具规程须写明新声明的形状、约束与失效方式，否则声明完整性无从判断。

本次范围内的需求与设计决定到任务的覆盖对照（本计划覆盖全部，无延后项）：

| 左列条目 | 覆盖任务 |
|---|---|
| {need}`REQ_20260914_0J68SDKV86ENKER2` | {need}`TASK_20260920_6ACW0WPHCC3BQJKR`、{need}`TASK_20260920_6XJG8PTX00G5RQ9M`、{need}`TASK_20260920_3JT1MKMYG9Y95T9W`、{need}`TASK_20260920_R76R9DDKYGM4TM6C`、{need}`TASK_20260920_B66GBH9CSPTNYFBN` |
| {need}`REQ_20260914_4CS6P421MGW68PME` | {need}`TASK_20260920_W1QAW0FQS640CT22` |
| {need}`ADR_20260920_YB4X14PK7D277PS7` | {need}`TASK_20260920_6ACW0WPHCC3BQJKR`、{need}`TASK_20260920_6XJG8PTX00G5RQ9M`、{need}`TASK_20260920_3JT1MKMYG9Y95T9W` |

覆盖对照的 ADR 一行按人工核对，不是可由字段核实的链接：注册表 `tasks.relates_types` 只允许 `REQ` 与 `CHG`，任务的 `relates` 承载不了 ADR，写入会被校验器按 TAO-REF-002 拒绝。该限制是既有的格式契约，本次不改，此处写明以免该行被读作机械可核对的关系。

左列的设计决定按全部受管理设计文档相对事项基线修订 `c5a7255` 的正式条目差异枚举。实测差异只有一条新增 ADR，即上表第三行；[命令设计](../../engineering/cli-design.md) 本次的改动落在执行契约、回执格式与验收条目三处正文，不含 ADR 条目，其结论由该 ADR 承载，不重复列行。

<!-- tao:section design -->
## 设计

沿用 {need}`DOC_20260914_0VF190409FQCN197` 本次补入的执行契约与回执格式，以及 {need}`ADR_20260920_YB4X14PK7D277PS7` 的取舍。此处只记录本计划特有的实现安排。

### 两个维度分开：输入过期看整体，复用时效看逐行

输入变化的过期判定仍按全局指纹整体进行，保留「一份回执对应一个确定的输入全集」这条可一句话说明的性质。逐项过期判定需要另加「各项声明的并集必须覆盖输入全集」的约束才能堵住无人认领的输入文件，该约束的存在理由完全来自逐项过期本身，因此不引入。

复用时效则必须逐行判定，这不是可选的精确化，而是本次改动带来的新失效点：整份回执的 `recorded_epoch` 每次调用都会刷新，若时效仍按它判定，连续多日只改文档就会让一项久未真正执行的检查持续显示新鲜。回执因此逐行保存该项的输入摘要与实际执行时刻，`evidence` 只有在每一行距其自身执行时刻都未超过 `reuse_seconds` 时才报可复用。

### 子集约束挡的是越界，不是不全

声明匹配的文件集合须是全局输入范围匹配集合的子集，越界按配置错误拒绝。这条挡的是「声明到策略输入范围之外」，挡不住「声明得比真实依赖窄」——后者是逐项复用本身的代价，由 ADR 记录，工具不宣称能发现隐含依赖。作为补偿，策略、工具与环境指纹的变化仍使全部检查失效，不设逐项例外。

约束在输入快照阶段判定而非策略校验阶段，因为需要展开通配符才能比较文件集合；两者都以配置错误报告，退出码一致。

### 审查绑定排除本轮声明的输出

`reviews.binding()` 直接调用 `snapshot()`，结构上没有接收预留输出的途径，因此 `review-preview --output` 的预留只对 `workflow review-begin／end` 生效，对 `tao review` 与必需审查的时效判定不生效。后果不是理论的：本项目的 `verification.inputs` 含 `docs/**/*.md`，而文档组织规定审查报告放在计划的 reviews 附件目录，于是保存正式报告必然使它所记录的那次审查失效。

修法是给 `snapshot()` 增加一个排除集合参数，由 `reviews.binding()` 从工作流状态取各审查类别最近一轮声明的输出填入。只有最近一轮的声明输出被排除；更早轮次的报告是历史材料，继续参与摘要，与验收「历史报告变化仍使结果过期」一致。`execute()` 与 `evidence()` 不传排除集合——检查回执绑定的是完整输入范围，与审查绑定无关。工作流状态不可读时不排除任何文件，即退回当前行为：这一侧的失败使审查显示为过期，而不是显示为满足。

`reviews` 已引用 `verification`，而 `workflows` 引用 `reviews`，因此工作流状态在函数内延迟引入，沿用本仓库既有写法。

### 配置形状与回执版本

声明使用 `[[verification.checks]]` 下的 `inputs`，与全局 `inputs` 同名同形：项目相对模式数组，不接受绝对路径与 `..`，省略即沿用全局范围。同名同形是为了让读者不必记两套规则；代价是「同名不同作用域」可能被误读为覆盖全局，参考页须明确它只收窄本项的重跑判定。

回执新增逐行字段，`receipt_version` 由 1 升至 2。旧版本回执按无效处理并重新执行全部检查，不猜测其含义；这只影响一次本地缓存，回执本身不纳入 VCS。

<!-- tao:section tasks -->
## 任务

- [x] `TASK_20260920_6ACW0WPHCC3BQJKR` 策略接受逐项输入范围，快照按项计算摘要并拒绝越界声明
  - relates: ["REQ_20260914_0J68SDKV86ENKER2", "CHG_20260920_Y0WCT88THT8JXXS2"]
  - depends_on: []
  - verify: `policy()` 接受 `[[verification.checks]]` 的可选 `inputs`，非数组、空数组、含非字符串、含空串、绝对路径或 `..` 分量均报配置错误；`snapshot()` 为声明了该字段的检查按其模式计算输入摘要，未声明的沿用全局摘要，声明匹配到全局范围之外的文件时报配置错误并指出越界路径。以上各分支加回归用例，确认合法声明下改动该范围内文件使该项摘要变化、改动范围外文件使其不变，且两种情况下全局摘要均变化。运行 `tao verify --only docs` 无新增诊断。
  - evidence: [验证记录](#DOC_20260920_RYR02DHVTJJVR8DY--verification)
- [x] `TASK_20260920_6XJG8PTX00G5RQ9M` 回执升到版本 2，执行时逐行决定复用还是重新执行
  - relates: ["REQ_20260914_0J68SDKV86ENKER2", "CHG_20260920_Y0WCT88THT8JXXS2"]
  - depends_on: ["TASK_20260920_6ACW0WPHCC3BQJKR"]
  - verify: 回执 `receipt_version` 为 2，每行记录该项输入摘要、实际执行时刻与是否沿用上次结果；`execute()` 对声明范围内无变化、上次通过且未超时效的检查沿用上次行，其余重新执行。回归覆盖：只改动某一项声明范围内的文件后重新调用，只有该项新增日志文件，其余行的耗时与执行时刻保持原值且标记为沿用；改动全局范围内但不属任何声明的文件后整份回执过期，重新调用时各行按各自范围决定；把回执的 `receipt_version` 改为未知值或损坏其结构后全部重新执行。确认沿用行的耗时不计入本次 `duration_seconds`。
  - evidence: [验证记录](#DOC_20260920_RYR02DHVTJJVR8DY--verification)
- [x] `TASK_20260920_3JT1MKMYG9Y95T9W` 复用时效按每行自己的执行时刻判定
  - relates: ["REQ_20260914_0J68SDKV86ENKER2", "CHG_20260920_Y0WCT88THT8JXXS2"]
  - depends_on: ["TASK_20260920_6XJG8PTX00G5RQ9M"]
  - verify: `evidence()` 只有在全局输入指纹一致、全部行通过、且每一行距其自身执行时刻都未超过 `reuse_seconds` 时才报 reusable，否则报 expired。回归构造一份整体指纹一致、但某一行执行时刻早于 `reuse_seconds` 的回执，确认 `--only evidence` 报 expired 而非 reusable，且 `--only code` 随后重新执行该行、其余行仍沿用。确认整份回执的刷新不延长任何未重新执行行的时效。
  - evidence: [验证记录](#DOC_20260920_RYR02DHVTJJVR8DY--verification)
- [x] `TASK_20260920_W1QAW0FQS640CT22` 使用方契约写明新声明的形状、约束与失效方式
  - relates: ["REQ_20260914_4CS6P421MGW68PME", "CHG_20260920_Y0WCT88THT8JXXS2"]
  - depends_on: ["TASK_20260920_3JT1MKMYG9Y95T9W"]
  - verify: 核对验证规程写明逐项 `inputs` 的形状与省略含义、子集约束及越界后果、它只收窄本项的重跑判定而不改变整份回执的过期判定、时效按各行实际执行时刻判定，以及声明窄于真实依赖会使该项静默停止重跑这一后果；核对工具规程的 `--only code` 行说明存在沿用行。确认未把该字段描述为覆盖全局范围。运行 `tao verify --only docs` 与全仓相对链接解析，均无新增诊断。
  - evidence: [验证记录](#DOC_20260920_RYR02DHVTJJVR8DY--verification)
- [x] `TASK_20260920_R76R9DDKYGM4TM6C` 在本仓库自己的策略上实测一次逐项复用
  - relates: ["REQ_20260914_0J68SDKV86ENKER2", "CHG_20260920_Y0WCT88THT8JXXS2"]
  - depends_on: ["TASK_20260920_3JT1MKMYG9Y95T9W"]
  - verify: 给 `.tao/config.toml` 的 `python-lint` 声明其真实输入范围（该检查只读 `plugins/tao-dev/skills/tao-dev/scripts` 与 `tests` 两棵树，其工具版本由 `pyproject.toml` 与 `uv.lock` 固定，ruff 规则全部来自 argv，无独立配置文件）；`python-tests` 不声明，因其确实依赖受管理文档。执行一次完整 `tao verify --only code` 取得基线回执，随后只改动一份文档后重新执行，记录 `python-lint` 是否被沿用、其执行时刻是否保持原值、`python-tests` 是否重新执行，并写出两次调用的实际命令、改动的文件与观察到的回执内容。这是本次改动在真实策略上的端到端观察，不以回归用例顶替。
  - evidence: [验证记录](#DOC_20260920_RYR02DHVTJJVR8DY--verification)

- [x] `TASK_20260920_B66GBH9CSPTNYFBN` 审查绑定不再把本轮声明的报告输出算作受检输入
  - relates: ["REQ_20260914_0J68SDKV86ENKER2", "CHG_20260920_Y0WCT88THT8JXXS2"]
  - depends_on: ["TASK_20260920_6ACW0WPHCC3BQJKR"]
  - verify: `snapshot()` 接受排除集合参数，`reviews.binding()` 从工作流状态取各审查类别最近一轮的 `output_files` 填入，`execute()` 与 `evidence()` 不传。回归覆盖：预留输出存在与不存在时 `binding()` 的 `source_digest` 相同；更早轮次的报告变化仍使其变化；工作流状态缺失或不可读时不排除任何文件；排除后输入集合为空仍按空范围拒绝。在本仓库实测：实现阶段某一轮的 attestation 导入后，按三个时点观察 `tao status` 的该项必需审查——仅导入、本轮声明的报告落盘、加入批次导航——确认落盘那一步状态不退化为 stale，并写出三个时点的实测状态。`status()` 中 stale 的判定先于其余判定，因此该步保持其实质结论即为绑定未移动的证据。不断言该项必需审查达到 satisfied：本轮的发现处置与导航挂接各自独立决定该状态，而导航改动按审查调度规程属后续文档变更、不是声明输出。
  - evidence: [验证记录](#DOC_20260920_RYR02DHVTJJVR8DY--verification)

<!-- tao:section verification -->
## 验证

按任务的 verify 字段执行。源码改动的回归落在 `tests/test_verification.py`，按已记录的做法在全部编辑完成后运行一次完整回归，不在每个任务后重跑；上一批基线为 490 passed、5 skipped，跳过项是未启用的原生客户端安装探针，本次以实测结果为准，不沿用该数字作为通过依据。

文档改动后运行 `tao verify --only docs` 与全仓相对 Markdown 链接解析。本事项开始时全仓受管理文档诊断为 0 条，结束后应仍为 0 条。

{need}`TASK_20260920_R76R9DDKYGM4TM6C` 是本次唯一的端到端观察，其结果须写明两次调用的命令、改动的文件与实际读到的回执内容，不能以回归用例通过顶替——回归用例构造的是受控回执，证明不了真实策略下的复用路径。

本次不声称已验证「声明完整性」这一类人为约束：工具只能拒绝越界声明，不能发现声明不全，这一限制由 {need}`ADR_20260920_YB4X14PK7D277PS7` 记录，不在本计划的验证范围内。

<!-- tao:results -->
实现逐项inputs、版本2回执及逐行时效：单项范围只决定重跑选择，整份回执仍绑定全局输入；策略、工具或环境变化不沿用旧行。公开契约见[验证规程](../../../plugins/tao-dev/skills/tao-dev/references/verification.md)与[工具规程](../../../plugins/tao-dev/skills/tao-dev/references/tools.md)，声明不全的取舍见 {need}`ADR_20260920_YB4X14PK7D277PS7`。

### 真实复用观察

仅修改位于全局inputs内、python-lint范围外的本计划后，python-tests重新执行而lint沿用：

| 检查 | 基线 | 文档修改后 | 结论 |
|---|---|---|---|
| python-tests | 17:45:37执行，749.19秒，passed | 18:00:09执行，666.31秒，passed | 输入变化导致重跑 |
| python-lint | 原执行17:42:53，0.746秒 | 原时刻、耗时及输入摘要均不变 | 沿用行未伪装成新执行，也未计入本次耗时 |

文档修改后的整体耗时666.97秒，与测试耗时相差0.66秒。该项目实测只节省0.746秒，不代表长检查场景的收益量级；声明完整性仍由项目负责。

### 正确性与审查

回归覆盖非法/越界/空匹配范围、版本1回执拒绝复用、单行过期而其他行沿用、损坏缓存不得提取可用行，以及自身预留报告不移动审查绑定。范围子集判定使用排除前全集，摘要使用排除后集合，避免排除规则掩盖越界输入。

当时的审查观察为：有开放阻断时导入回执得到changes-requested；预留报告落盘后仍为changes-requested；未声明的父级导航变更后为stale。该结果说明绑定与结论各自独立，不能把无阻断的satisfied当作唯一正确结果；操作接口见[审查调度](../../../plugins/tao-dev/skills/tao-dev/references/review-runs.md)，后续批次记录排除规则见对应架构决定。

本事项三批正式审查及发现处置见[计划批次](20260920-check-input-scope/reviews/20260920-plan-review/index.md)、[实现批次](20260920-check-input-scope/reviews/20260920-implementation/index.md)和[加固复核](20260920-check-input-scope/reviews/20260920-implementation-followup/index.md)。模型为claude-sonnet-5，来源字段firstParty，未执行跨供应商审查；不从该字段另推供应商身份。

### 最终历史判定

合入前复核包含a6a93f5和27caa46的改动，固定审查树与文件范围以[加固复核报告](20260920-check-input-scope/reviews/20260920-implementation-followup/02-hardening-recheck-claude.md)为准。该回执导入后执行完整verify：passed／complete／checks-satisfied，任务无开放项，证据reusable，必需审查satisfied，诊断0。python-tests实际977.06秒、528 passed/5 skipped；lint实际0.25秒、0诊断。测试因逐行时效过期而重跑，证明整体记录刷新不能延长旧行时效。

此判定发生于该轮报告和父级导航落盘之前；按当时规则，导航落盘后审查为stale。历史判定保留，不作为当前代码的通过。此前507 passed/1 failed/5 skipped的完整检查因缺三条中文诊断失败，补齐后回归通过；不把该次失败改称单次全绿。原始回执和日志仅在忽略临时存储保留。

<!-- /tao:results -->

<!-- tao:section questions -->
## 待确认事项

无。配置键名、回执版本升级方式与子集约束的判定位置均已在设计章节定稿。
