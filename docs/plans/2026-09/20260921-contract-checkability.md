---
schema: tao.project.plan/v0.1
id: "DOC_20260921_H676H5G6Z6WBQ55S"
title: "契约失效点可检查"
locale: "zh-Hans"
status: draft
created: "2026-09-21"
spec_docs: ["DOC_20260914_4C7N0XHQSP7CY69P"]
design_docs: ["DOC_20260914_0VF190409FQCN197", "DOC_20260914_P1G9T0KSCC0FTBM1"]
change: "CHG_20260921_Y6MW6AX39S9RJHGZ"
---

# 契约失效点可检查

<!-- tao:section scope -->
## 目标与边界

计划契约与闸门条件里存在若干失效点，工具要么沉默，要么以无关原因失败。已确认五处：需求无任务承接不报；成对契约标记未闭合时无诊断，改由计划批准以「已批准文档发生变化」失败；`status()` 在异常保护之外调用会抛异常的 `path_for()`；一个审查批次自身的必要产出使该批次的 finish 闸门条件失效；`review-end` 登记不合格的报告文档，事后修正即与登记摘要不符。它们的共同形状是失效点存在、而工具不说或说错。

本次范围限于 `taolib` 的校验器、验证与审查模块，格式注册表的延后声明规则，以及三份指导页的规则空白。不改逐项输入范围与回执格式，不改审查调度的轮次与预算规则，不改文档校验对 VCS 的无依赖——需求承接核对因此只进完整 `tao verify <CHG>`。

另含两项与上述缺口同源、但属于指导而非工具的改动：阶段小结与受管理文档只记结论与判断依据，操作经过归提交消息或检查点；需要用户行动的事项置于消息末尾并用问题工具或表格呈现。规则写成后按其清理三处已合入文档中不符合该判据的段落，使规则与其首批适用结果一并接受审查。另界定实现期文档细化可由 agent 自行恢复到 implement 的边界：该类修订本身不改变承诺、需求或任务范围，却按现行规则一律需要用户重新批准，与「在批准范围内自主完成」相抵。

<!-- tao:section references -->
## 规格引用

- {need}`REQ_20260914_42AXMZ2KH2RAZ8M3` 本次修订的验收要求成对契约标记的失效报出定位与规则号、不得转由其他条件以无关原因失败，并要求本次新增或修改的需求有任务承接或显式声明延后。
- {need}`REQ_20260914_0J68SDKV86ENKER2` 本次修订的验收要求一个批次自身的记录不改变该批次的受检输入。
- {need}`REQ_20260914_4CS6P421MGW68PME` 要求分发的 skill 入口给出适用条件、具体动作和判断依据。两项指导规则属于这条的具体动作。

本次范围内的需求与设计决定到任务的覆盖对照（无延后项）：

| 左列条目 | 覆盖任务 |
|---|---|
| {need}`REQ_20260914_42AXMZ2KH2RAZ8M3` | {need}`TASK_20260921_H1Z4N62PYGADM21E`、{need}`TASK_20260921_MTT3XBRE6Y4HKJCR` |
| {need}`REQ_20260914_0J68SDKV86ENKER2` | {need}`TASK_20260921_TZZTYV40TK3Q0TTV`、{need}`TASK_20260921_PJ4W5TTCCGBNJ9T4` |
| {need}`REQ_20260914_4CS6P421MGW68PME` | {need}`TASK_20260921_S0VXHHPNRZ759VGH`、{need}`TASK_20260921_MF6MQQC8N467PWSH`、{need}`TASK_20260921_A5M3G2KKZBN2NH9K` |
| {need}`ADR_20260921_7GKEM95QP289V30G` | {need}`TASK_20260921_TZZTYV40TK3Q0TTV` |

左列的设计决定按全部受管理设计文档相对事项基线 `d8b599d` 的正式条目差异枚举，实测差异只有该条新增 ADR。{need}`TASK_20260921_RJHMMH9870M755WV` 是缺陷修复，不对应需求，按使能任务记入右列而不算孤儿。

<!-- tao:section design -->
## 设计

沿用 {need}`DOC_20260914_0VF190409FQCN197` 本次补入的执行契约与验收条目、{need}`DOC_20260914_P1G9T0KSCC0FTBM1` 新增的 `TAO-DOC-003`，以及 {need}`ADR_20260921_7GKEM95QP289V30G`。此处只记本计划特有的安排。

### 延后声明的形状

声明写在计划 `questions` 章节的结构化行，沿用任务字段已有的写法，由注册表定义键与必需内容：延后的需求 ID、触发条件、后续承接方。声明与理由因此在同一处，不像元数据那样把两者拆开而无检查可比对。缺声明时检查失败，不是静默缩小核对范围——失败方向与被否决的 `design_docs` 划范围做法相反，这是该方案成立的前提。

### 两处判定共用一个定义

必需审查的时效与进入 finish 的条件都要回答「本轮结论是否仍对应当前输入」。本次让两者共用同一个排除定义，不各自解释什么算改动；否则同一份记录在一处算改动、在另一处不算，差异只会在某次交付前才暴露。

### 指导规则的落点与体积

两条规则分别落在 [流程操作](../../../plugins/tao-dev/skills/tao-dev/references/workflow.md)（阶段小结与用户行动事项）与文档规程（受管理文档记什么）。[流程操作](../../../plugins/tao-dev/skills/tao-dev/references/workflow.md) 属必读底座，当前 6580 字节且有不得增大的既有约束，本次经用户同意突破，预算不超过 100 字节，超出则改写既有句子而非追加。

<!-- tao:section tasks -->
## 任务

- [x] `TASK_20260921_H1Z4N62PYGADM21E` 成对契约标记的失效报出定位与规则号
  - relates: ["REQ_20260914_42AXMZ2KH2RAZ8M3", "CHG_20260921_Y6MW6AX39S9RJHGZ"]
  - depends_on: []
  - verify: 校验器对未闭合的开启标记、落单的闭合标记、以及出现在不允许章节的标记各报一条 `TAO-DOC-003`，定位到开启处；回归覆盖这三种情形，并确认未闭合时计划契约的提取不再静默把后续内容归入错误区段。以未闭合的执行记录块构造用例，确认 `workflow advance` 不再以「已批准文档发生变化」失败，而是由文档校验先报出该标记错误。
  - evidence: [验证记录](#DOC_20260921_H676H5G6Z6WBQ55S--verification)
- [x] `TASK_20260921_MTT3XBRE6Y4HKJCR` 完整验证按基线核对需求承接
  - relates: ["REQ_20260914_42AXMZ2KH2RAZ8M3", "CHG_20260921_Y6MW6AX39S9RJHGZ"]
  - depends_on: []
  - verify: 完整 `tao verify <CHG>` 枚举受管理规格文档相对工作流状态所记 fork commit 的正式条目差异，未被本事项任务 `relates` 覆盖且未声明延后的需求列入输出并使判定不通过；已声明延后的不报；声明缺少触发条件时报错。注册表定义 `questions` 中延后声明的键与必需内容，校验器据此检查形状。无 VCS 或无基线时报告未评估而非通过。确认 `--only docs` 与钩子路径不引入 VCS 依赖，其耗时不变。
  - evidence: [验证记录](#DOC_20260921_H676H5G6Z6WBQ55S--verification)
- [x] `TASK_20260921_TZZTYV40TK3Q0TTV` 批次自身的记录不参与该批次的受检输入
  - relates: ["REQ_20260914_0J68SDKV86ENKER2", "CHG_20260921_Y6MW6AX39S9RJHGZ"]
  - depends_on: []
  - verify: 排除范围由本轮预留的新报告输出扩到该批次目录下的文件与计划中记录本次执行的结果块，审查绑定与 finish 闸门共用该定义。回归覆盖：写入裁决、批次导航页与执行记录块后，该批次已登记轮次的输入仍为当前且闸门条件成立；其他批次的报告改动仍使结果过期；源码与未声明新文件改动仍使结果过期。在本仓库实测一轮审查的完整产出落盘后闸门仍可通过；批次导航页及其父级入口须在 review-begin 之前就位，否则事后加入的父级入口不是批次记录，仍使该轮过期，该前置条件须写入审查调度页。
  - evidence: [验证记录](#DOC_20260921_H676H5G6Z6WBQ55S--verification)
- [x] `TASK_20260921_PJ4W5TTCCGBNJ9T4` review-end 登记前校验报告文档
  - relates: ["REQ_20260914_0J68SDKV86ENKER2", "CHG_20260921_Y6MW6AX39S9RJHGZ"]
  - depends_on: []
  - verify: `review-end` 对所提交报告执行受管理文档校验，不合格则拒绝登记并报出该报告的诊断；合格时登记的摘要与文件一致。校验范围以项目实际管理的文档为准，不在管理范围内的报告逐份标明未校验，不因未被校验而读作已校验。回归覆盖含无效引用的报告被拒、合格报告正常登记、以及失败结果允许无报告的既有路径不受影响。同步 [审查调度](../../../plugins/tao-dev/skills/tao-dev/references/review-runs.md) 中「不代替输出的 schema、引用和适用的出版检查」一句，使其不再被读作可以事后再查。
  - evidence: [验证记录](#DOC_20260921_H676H5G6Z6WBQ55S--verification)
- [x] `TASK_20260921_RJHMMH9870M755WV` 审查记录路径的构造与读取一律退化为已定义状态
  - relates: ["CHG_20260921_Y6MW6AX39S9RJHGZ"]
  - depends_on: []
  - verify: `status()` 不再在异常保护之外调用 `path_for()`；标识符不合规时该行记为 invalid 而非抛出异常，`tao status` 与完整 `tao verify` 均不崩溃。回归以不合规标识符直接驱动 `status()`，确认返回行状态且无未处理异常。
  - evidence: [验证记录](#DOC_20260921_H676H5G6Z6WBQ55S--verification)
- [x] `TASK_20260921_S0VXHHPNRZ759VGH` 阶段小结与用户行动事项的写法
  - relates: ["REQ_20260914_4CS6P421MGW68PME", "CHG_20260921_Y6MW6AX39S9RJHGZ"]
  - depends_on: []
  - verify: 核对 [流程操作](../../../plugins/tao-dev/skills/tao-dev/references/workflow.md) 写明阶段小结只写影响后续决定的内容，已修复且不改变产物的操作经过记入提交消息或检查点而不占小结；需要用户行动的事项置于消息末尾并用原生提问工具或表格呈现，说明事由、为何不能自行决定与期望回复。实测必读底座字节数，确认增量不超过 100 字节。运行受管理文档校验与全仓相对链接解析无新增诊断。
  - evidence: [验证记录](#DOC_20260921_H676H5G6Z6WBQ55S--verification)
- [x] `TASK_20260921_MF6MQQC8N467PWSH` 受管理文档只记结论与判断依据
  - relates: ["REQ_20260914_4CS6P421MGW68PME", "CHG_20260921_Y6MW6AX39S9RJHGZ"]
  - depends_on: ["TASK_20260921_S0VXHHPNRZ759VGH"]
  - verify: 核对文档规程写明受管理文档记结论与判断依据，不记执行者的操作经过；判据为未来读者判断产品或某个决定时是否需要该内容，支撑阈值与验收的测量值属依据而须保留。按该规则清理三处已合入内容：删去 20260920 计划中漏传事项标识的操作叙述，压缩 20260919 计划中登记顺序失误与超时测量两段，保留其失效机制与四个测量值。确认压缩后 `timeout_seconds` 取值的依据仍可从正文追溯。
  - evidence: [验证记录](#DOC_20260921_H676H5G6Z6WBQ55S--verification)

- [x] `TASK_20260921_A5M3G2KKZBN2NH9K` 界定实现期文档细化可自行恢复的边界
  - relates: ["REQ_20260914_4CS6P421MGW68PME", "CHG_20260921_Y6MW6AX39S9RJHGZ"]
  - depends_on: ["TASK_20260921_S0VXHHPNRZ759VGH"]
  - verify: 核对 [工作流状态](../../../plugins/tao-dev/skills/tao-dev/references/workflow-state.md) 写明哪些修订属于实现期细化——把已实现的技术选择补进设计、把实测结论写回文档、修补任务 verify 的措辞或登记例外——这类修订 agent 可自行 revise 并重新批准，决定文字须记明是自评、被修订的具体内容及不属于停止条件的理由；哪些必须停下取得用户批准——改变产品承诺或验收实质、增删需求、改变任务范围、判断不准或存在两种合理改法。核对 [流程操作](../../../plugins/tao-dev/skills/tao-dev/references/workflow.md) 的授权条目指向该边界而非另述一遍。实测必读底座字节数，连同前一项合计增量不超过 130 字节。运行文档校验与全仓相对链接解析无新增诊断。
  - evidence: [验证记录](#DOC_20260921_H676H5G6Z6WBQ55S--verification)

<!-- tao:section verification -->
## 验证

按任务的 verify 字段执行。源码改动的回归落在 `tests/test_documents.py`、`tests/test_verification.py`、`tests/test_reviews.py` 与 `tests/test_workflows.py`，按已记录做法在全部编辑完成后运行一次完整回归。事项开始时全仓受管理文档诊断为 0 条，结束后应仍为 0 条。

{need}`TASK_20260921_TZZTYV40TK3Q0TTV` 的闸门可达性须在本仓库真实走一轮审查后观察，不以回归用例顶替：回归构造的是受控状态，证明不了真实批次目录与导航挂接下的结果。

两项指导规则改的是 agent 行为，确定性检查只覆盖其结构与链接，不能证明改动后的 agent 真的照做；其效果须在后续事项中观察，本计划不声称已验证。

<!-- tao:results -->
{need}`TASK_20260921_H1Z4N62PYGADM21E`：校验器新增 `TAO-DOC-003`，覆盖未闭合、落单闭合、重复开启与位于错误章节四种失效；plan profile 声明 `results_section`，标记只在该章节合法。`plan_contract()` 的分支同步修正——它此前把落单标记当章节名赋值，这正是契约归属被静默改变的机制。回归四种失效各一条，另一条确认成对标记既不报错又确实被排除出契约。

{need}`TASK_20260921_MTT3XBRE6Y4HKJCR`：新增 `taolib/coverage.py`，从受管理规格文档相对事项基线的条目差异枚举本次新增或修改的需求，与本事项任务 `relates` 比对；延后声明取自计划 questions 的 `- deferred: <REQ_ID> — <触发条件与后续承接>` 行。完整验证输出 `requirement_coverage`，未承接或声明无效时返回 1。无工作流记录报 not-applicable 且不计退出码——没有声明过的基线可比，属条件不适用；有记录而无基线修订报 not-evaluated 并返回 2。在本事项自身实测：基线 `d8b599d`，识出本次修改的 `REQ_...0J68` 与 `REQ_...42AX`，两条均有任务承接，未承接项为空。

{need}`TASK_20260921_TZZTYV40TK3Q0TTV`：排除范围由本轮预留的新报告输出扩到该批次目录下的文件，计划中记录本次执行的结果块按其契约摘要计入，审查绑定与 finish 闸门共用 `own_records` 的同一定义。批次由本轮 `output_files` 所在目录判定，其他批次照旧参与摘要。

{need}`TASK_20260921_PJ4W5TTCCGBNJ9T4`：`review-end` 登记前对所提交报告执行受管理文档校验，不合格拒绝登记且轮次保持 running，可改好再登记；[审查调度](../../../plugins/tao-dev/skills/tao-dev/references/review-runs.md) 相应改写，不再被读作可事后再查。

{need}`TASK_20260921_RJHMMH9870M755WV`：`status()` 把 `path_for()` 的调用移入同一异常保护，标识符不合规时记为 invalid 行。

{need}`TASK_20260921_S0VXHHPNRZ759VGH`、{need}`TASK_20260921_A5M3G2KKZBN2NH9K`：两条规则分别落在 [流程操作](../../../plugins/tao-dev/skills/tao-dev/references/workflow.md) 与 [工作流状态](../../../plugins/tao-dev/skills/tao-dev/references/workflow-state.md)。必读底座由 6580 增至 6709 字节，增量 129，在计划预算内；两次初稿分别为 +230 与 +168，靠删除既有冗余压回，未删减规则内容。

{need}`TASK_20260921_MF6MQQC8N467PWSH`：判据写入 [文档规程](../../../plugins/tao-dev/skills/tao-dev/references/documents.md)。按其清理三处已合入内容：删去一段操作叙述；压缩两段叙事并保留其失效机制与四个耗时测量值，`timeout_seconds` 取 1200 的依据仍可从正文追溯。

**回归。** 完整回归 543 passed、4 skipped、371 秒，事项开始时为 528 项。首次完整执行报 14 项失败，归因三类：六项为执行者传入相对 wheelhouse 路径所致，绝对路径重跑 20 项全过，代码未改；两项为本次新增的覆盖核对在无工作流记录时一律记未完成，掩盖了任务未完成这一更具体的失败，已按 not-applicable 与 not-evaluated 区分修正；一项为该修正引入的分支取用不存在的键而抛出异常，已加状态判别。其余三项随上述修正消失。

**已知缺口。** 两项指导规则改的是 agent 行为，确定性检查只覆盖其结构与链接，不能证明改动后的 agent 照做；其效果须在后续事项中观察。finish 闸门的可达性须在本仓库真实走一轮审查后观察，本计划的回归构造的是受控状态。
**闸门可达性。** {need}`TASK_20260921_TZZTYV40TK3Q0TTV` 的检查在本事项自身的审查批次上追到底，共暴露四个各自独立的漏口，它们的共同形状是派生字段未随排除规则一并变换：

| # | 漏口 | 发现方式 |
|---|---|---|
| 1 | 只排除本轮预留输出，裁决与批次导航页未排除 | 上一事项实测 |
| 2 | 父级导航入口不属批次记录，事后加入即使该轮过期 | 本事项第 1 轮实测 |
| 3 | `input_bytes` 仍按原字节数累加，而摘要已按计划契约计算 | 第 2 轮后逐键比对请求 |
| 4 | `excluded_files` 逐个枚举批次记录，随本轮自身产出增长 | 新写的回归自己失败 |

第 1 项由本次的批次目录排除处理；第 2 项无代码可改，是前置条件，已写入审查调度页；第 3、4 项是本次修摘要时自己引入的，现已使字节计数与排除声明都跟随同一变换——后者改为声明排除规则所涉目录，而不枚举当下匹配到的文件。

两轮实测确立了第 2 项：两轮的文件集合在各自前后完全相同，第 1 轮移动摘要的是父级导航入口，第 2 轮该入口已在受检版本内，产出落盘后该轮 `inputs` 为 `current`。第 3、4 项因改变了计算方式，已登记轮次无法再匹配，故不以实测而以回归确立：一条用例在一轮内写下报告、裁决、批次导航页与计划执行记录后，断言重算的请求与登记值逐字相同、`inputs` 为 `current` 且闸门条件成立。该不变量此后不再依赖真跑一轮审查去观察。

**回归。** 完整回归 544 passed、4 skipped、375 秒。

<!-- /tao:results -->

<!-- tao:section questions -->
## 待确认事项

无。
