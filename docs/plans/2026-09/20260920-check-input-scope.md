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
{need}`TASK_20260920_6ACW0WPHCC3BQJKR`：`policy()` 接受 `[[verification.checks]]` 的可选 `inputs`，形状校验与全局 `inputs` 共用新的 `patterns()`。`snapshot()` 拆出 `matched()`、`combined()` 与 `scopes()`：`matched()` 把一组模式解析为当前文件集合，`combined()` 算合并摘要并用一个逐文件哈希缓存避免同一文件在多个范围里重复读取，`scopes()` 为每项检查产出一个摘要——声明了就用自己的范围，没声明就用全局摘要——并在此判定子集约束。快照结果新增 `check_digests`；`fingerprint` 仍只由 source、policy、environment 三个摘要构成，整份回执的过期判定因此未变。

检查：新增 7 个参数化回归用例覆盖空数组、非数组、空串、绝对路径、`..` 分量、越界声明与匹配不到文件七种情形，全部返回退出码 2 且不启动任何检查子进程。

{need}`TASK_20260920_6XJG8PTX00G5RQ9M`：回执 `receipt_version` 升至 2，每行新增 `inputs_digest`、`recorded_epoch` 与 `reused`。新增 `carried()` 挑出仍站得住的上次行：状态为 passed、自身摘要未变、未超时效、`argv` 未变，且回执的 `policy_digest` 与 `environment_digest` 与本次一致——策略、工具或环境变化时一行都不沿用。`execute()` 沿用时把上次的行原样带过去，只加 `reused: True`，不改写执行时刻、耗时与日志位置。

检查：回归确认只改动某一项声明范围内的文件后，只有该项重新执行，另一项的 `recorded_epoch` 与 `elapsed_seconds` 与上次逐字相等且被观察的副作用文件计数不增；把回执的 `receipt_version` 改成 1 后全部重新执行。

{need}`TASK_20260920_3JT1MKMYG9Y95T9W`：`evidence()` 改为按每行自己的 `recorded_epoch` 判 `reuse_seconds`，并返回 `expired_checks` 列出超时的检查；回执整体的记录时刻仍一并检查，但不再是唯一依据。

检查：回归构造一份整体输入指纹一致、记录时刻新鲜、但某一行执行时刻早于 `reuse_seconds` 的回执，`--only evidence` 报 expired 且 `expired_checks` 恰为该行；随后的 `--only code` 只重新执行该行，另一项仍沿用。

{need}`TASK_20260920_W1QAW0FQS640CT22`：[验证规程](../../../plugins/tao-dev/skills/tao-dev/references/verification.md) 补入逐项 `inputs` 的配置示例、形状与省略含义、子集约束与越界后果、「只收窄本项重跑判定而不改变整份回执过期判定」这一句，以及声明窄于真实依赖会使该项静默停止重跑的后果与补偿；复用一节补入沿用行的记录要求与逐行时效。[工具规程](../../../plugins/tao-dev/skills/tao-dev/references/tools.md) 的 `--only code` 与 `--only evidence` 行相应更新。

检查：`tao verify --only docs` 通过，72 份受管理文档、0 条诊断。

**回归与一处遗漏。** 第一次完整执行 `tao verify --only code` 时 `python-tests` 失败：`tests/test_diagnostics_locale.py` 遍历源码 AST，要求每条字面诊断消息在 `assets/locales/diagnostics.zh-Hans.json` 有对应条目，而本次新增的三条消息都未登记（507 passed、1 failed、5 skipped，692.11 秒）。补齐三条中文条目后重跑为 508 passed、5 skipped、746.02 秒。三条条目按该文件有序段中 Check 家族的位置插入，最终差异为 3 行新增。

{need}`TASK_20260920_R76R9DDKYGM4TM6C`：`.tao/config.toml` 的 `python-lint` 声明 `inputs = ["plugins/tao-dev/skills/tao-dev/scripts/**/*", "tests/**/*", "pyproject.toml", "uv.lock"]`。核实依据：该检查的 argv 只对这两棵树运行 ruff，全部规则来自 argv 的 `--select`，`pyproject.toml` 无 `[tool.ruff]` 节，工具版本由 `pyproject.toml` 的版本区间与 `uv.lock` 固定。`python-tests` 不声明，因为它运行整套回归，`tests/test_repository.py` 确实读取受管理文档。

端到端观察取三次完整执行。基线为第二次执行（全部通过），随后只改动一份受管理文档——本计划正文的验证记录与任务勾选——再执行第三次。`docs/**/*.md` 在全局 `inputs` 之内，在 `python-lint` 声明的范围之外。

| 检查 | 第二次（基线） | 第三次（只改一份文档后） | 输入摘要 |
|---|---|---|---|
| python-tests | 17:45:37 执行，749.19 秒，passed | 18:00:09 重新执行，666.31 秒，passed | `e0637b92…` → `cd1a60e0…` 变化 |
| python-lint | 沿用，原执行 17:42:53、0.746 秒 | 仍沿用，执行时刻与耗时不变 | `a96339b1…` → `a96339b1…` 不变 |

第三次回执整体耗时 666.97 秒，与 `python-tests` 单项的 666.31 秒相差 0.66 秒，沿用行的 0.746 秒未计入本次执行。

`python-lint` 连续两次被沿用，其执行时刻始终停在 17:42:53，而整份回执的记录时刻在这期间刷新了两次。这正是 {need}`REQ_20260914_0J68SDKV86ENKER2` 本次修订的验收所禁止的情形的反面证据：若时效仍按整份回执的记录时刻判定，这一行会一直显示新鲜；按其自身执行时刻判定，它在 `reuse_seconds` 到期后会被重新执行。

第一次与第二次执行之间还有一次同形观察，改动的是 `plugins/tao-dev/skills/tao-dev/assets/locales/diagnostics.zh-Hans.json`——同样在全局 `plugins/**/*` 之内、在声明范围之外，`python-lint` 同样被沿用。两次观察的区别只是改动的文件类别，结论一致。

本项目省下的是 0.746 秒，收益量级不具代表性：`python-tests` 确实依赖受管理文档，无法收窄，而真正的目标场景是长检查与文档类检查混在同一策略里。机制在真实策略上跑通，收益量级须在消费方项目上观察，本计划不声称已验证后者。

{need}`TASK_20260920_B66GBH9CSPTNYFBN`：`snapshot()` 增加 `exclude` 参数，排除调用方预先声明的自身新输出；`scopes()` 相应拆成两个集合——子集约束对**排除前**的完整策略范围判定，摘要只由**排除后**的集合贡献，因此排除不会把越界声明变成合法声明。`reviews.binding()` 新增 `declared_outputs()`，从工作流状态取各审查类别最近一轮的 `output_files`；`workflows` 引用 `reviews`，故在函数内延迟引入。`execute()` 与 `evidence()` 不传排除集合。

修复前后在本仓库实测，控制导航不变、只增删本轮三份预留输出：修复前 `binding()` 的 `source_digest` 为 `a2b23e4d62df66b3…`（有输出）对 `1ebbc73dd7b36b31…`（无输出）；修复后两种状态同为 `2bb170e327e30ea0…`，排除项计 4 份，即 docs 批次最近一轮 1 份加 code 批次最近一轮 3 份。

检查：`tests/test_reviews.py` 增三项回归——本轮声明输出写入或改写均不移动绑定而更早轮次的报告改动仍移动它；无工作流状态、状态不可解析时都不排除任何文件，此时新报告按普通输入处理；排除掉全部输入后仍按空范围拒绝。`test_reviews.py` 21 项、`test_verification.py`、`test_review_runs.py`、`test_workflows.py` 合计 60 项全部通过。

本次同时修正了 F1 处置中发现的另一处缺陷：`carried()` 原先在 `require_logs` 为假时不校验日志路径，于是一份 `evidence()` 已判为 invalid 的损坏回执仍会被逐行挖出可用的部分，违反验证规程「缓存损坏或清空后须重跑」。改为由 `execute()` 把已算出的 `evidence()` 结果传入，状态为 invalid 或 missing 时一行都不沿用，同时删去重复的解析与校验。`tests/test_verification.py` 增一项回归，对含遍历分量的日志路径断言 `evidence()` 返回 invalid 且重跑时无任何沿用行。

**审查绑定修复的实测（{need}`TASK_20260920_B66GBH9CSPTNYFBN` 的第五项检查）。** 实现阶段第 2 轮复核后按三个时点观察 `tao status` 的该项必需审查：

| 时点 | 状态 | 说明 |
|---|---|---|
| A 导入本轮 attestation，尚无报告落盘 | changes-requested | 该轮有阻断级发现且处置为 open |
| B 本轮声明的报告已落盘 | changes-requested | 状态未退化为 stale，即绑定未因保存本轮报告而移动 |
| C 加入批次导航条目之后 | stale | 导航不是声明输出，按审查调度规程属后续文档变更 |

`status()` 中 stale 的判定先于 changes-requested，因此 B 点仍为 changes-requested 就是绑定未移动的直接证据，这正是本次修复要达到的效果。

该项检查原写为「由 stale 回到 satisfied」。实测表明那个字面结果达不到，原因有二且都不是修复失效：其一，当轮存在未处置的阻断级发现，状态本就不应显示满足；其二，新报告必须进入批次导航才能从书入口可达，而导航改动按审查调度规程是后续文档变更、不是声明输出。原措辞把两个各自独立的因素当成了修复本身的效果，因此经用户批准改写为上表的三时点观察，以 B 点不退化为 stale 作为绑定未移动的判据。

**完整交付判定。** 在实现审查新批次第 1 轮的 attestation 导入之后、本轮报告落盘之前，执行 `tao verify CHG_20260920_Y0WCT88THT8JXXS2`：退出码 0，status passed，coverage complete，readiness checks-satisfied，目标任务开放项为空，当前证据可复用，必需审查 `independent-implementation-review` 为 satisfied，诊断 0 条，耗时 3.0 秒。该耗时来自整份回执复用，其中各检查行的执行属于此前的实际运行，不是本次重新执行。

该判定的观察时点在本轮审查报告与其批次导航落盘之前。落盘后必需审查因导航改动显示为过期：批次导航不是声明输出，按 [审查调度](../../../plugins/tao-dev/skills/tao-dev/references/review-runs.md) 属后续文档变更。这与上文三时点观察一致，不改写该判定在其时点上的结论。

**审查执行汇总。** 本事项共五轮独立审查，分属三个批次：计划阶段批次两轮（1 条建议，采用）、实现阶段批次两轮（1 条建议部分采用、1 条阻断采用并修复）、用户明确发起的复核批次一轮（1 条建议，记为后续加固）。五轮均为模型审查，`claude-sonnet-5`，供应商 firstParty，五个互不相同的会话上下文，均与作者上下文不同；同供应商，未使用跨供应商审查者。三条真实问题中的两条出现在自测通过之后，其中一条为阻断。

**合入前的最终交付判定。** 上文的判定作出后又产生两次提交——`a6a93f5` 为仓库约定增加 `uv` 必须带 `--no-config` 的规则，`27caa46` 在 `path_for()` 内校验标识符——两者均未经独立审查，彼时完整 `tao verify` 因必需审查过期而返回 failed 与 blocked，其余各项全部通过。经用户决定为复核批次追加预算至 14400 秒后，第 2 轮覆盖了这两次提交。导入该轮 attestation 后、其报告落盘前重新执行：

```
tao verify CHG_20260920_Y0WCT88THT8JXXS2
  status passed | coverage complete | readiness checks-satisfied
  open_tasks []   evidence reusable   diagnostics 0
  python-tests passed 977.06 秒，528 passed、5 skipped
  python-lint  passed   0.25 秒，0 条诊断
  independent-implementation-review -> satisfied
```

该次 `python-tests` 重新执行不是因输入变化：上一次执行距此已超过 `reuse_seconds`，逐行时效判定使其过期。这是本次所实现机制在真实策略上的第三次生效观察，也正是规格本次修订所要求的行为——若时效仍按整份回执的记录时刻判定，期间数次调用会不断把它刷新为新鲜。

回归总数由事项开始时的 508 项增至 528 项。该判定的观察时点在本轮报告与批次导航落盘之前；落盘后必需审查再次因导航改动显示为过期，理由同上文三时点观察。

<!-- /tao:results -->

<!-- tao:section questions -->
## 待确认事项

无。配置键名、回执版本升级方式与子集约束的判定位置均已在设计章节定稿。
