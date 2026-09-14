---
schema: tao.cli-design/v0.2
id: DOC_EA15378E13FE4EC081163CEE651E17B1
title: tao 命令与流程接入
locale: zh-Hans
status: draft
created: "2026-09-14"
bootstrap: manual
---

# tao 命令与流程接入

本文定义拟实现的工具接口，落实 {need}`REQ_8D96CE7C86D6463194942315CB61B62B`、{need}`REQ_879A3065136F4F1993721F8840A0121D`、{need}`REQ_B5412B888E844FD8AA6F76B9B59C4806` 和 {need}`REQ_AD6954B59E45455287DB1A499FB7232F`。**当前尚无 tao 可执行程序，下述命令均为接口设计，不是可直接运行的使用说明。** 随包的 [流程操作规程](../plugins/tao-dev/skills/tao-dev/references/workflow.md) 规定 agent 的调用时机与当前回退行为。

<!-- tao:section scope -->
## 一、用户操作与命名依据

用户通常只需表达“整理需求、制定计划、实现、审查、验证”的意图，由 skill 推进。流程名称统一为 `specify → plan → implement → review → verify`：specify 包含必要澄清，plan 包含必要设计与任务拆分；调试、恢复和交接按需进入。它们不是每次都需用户手动调用的五个命令，也不要求每个节点生成一份文件。

**tao CLI 只承接确定性操作。** 解析、生成、验证、查询和保存记录可以在普通终端或 CI 执行；需求判断、设计、对抗式审查仍由 skill、可用客户端或人工完成。初版不提供会隐式调用多个模型的 `tao review`，不从报告数量或客户端名称推导审查通过。

斜杠命令是客户端对这些意图的入口，CLI 是执行工具，二者不要求逐个同名。优先使用自然语言加 skill；只在实际需要时增加原生斜杠命令包装，不要求用户记住工具内部分类。

| 参考的命名与语义 | tao-dev 的取舍 |
|---|---|
| [Spec Kit](https://github.com/github/spec-kit) 的 specify、plan、tasks、implement | 流程使用 specify、plan、implement；任务列表属于 plan，不新增强制 tasks 步骤 |
| [OpenSpec CLI](https://github.com/Fission-AI/OpenSpec/blob/main/docs/cli.md) 的 new change、show、status、validate | 创建、展示与状态查询采用这些直观名称；验证还执行代码检查，统一命名 verify，不只表示规格格式合法 |
| [OpenSpec 工作流](https://github.com/Fission-AI/OpenSpec/blob/main/docs/opsx.md) 的 verify、archive | 保留验证意图；archive 有归档／规格同步语义，本项目目前不需要相同的独立动作 |
| [Superpowers 分支收尾](https://github.com/obra/superpowers/blob/d884ae04edebef577e82ff7c4e143debd0bbec99/skills/finishing-a-development-branch/SKILL.md) | 收尾包含测试、集成选择和清理；本项目保留必要检查，不引入固定菜单或默认合并行为 |
| [gstack context-save](https://github.com/garrytan/gstack/blob/a3259400a366593e0c909dd9ac3e59752efd2488/context-save/SKILL.md) | 使用 context save 表达交接保存，避免 checkpoint 被理解为 VCS 提交或客户端回退点 |

这些项目没有统一的命令标准。命名依据真实动作，不照搬命令数量；未发布的旧草案名称不保留兼容别名。原 check 与 verify 的区别仍作为内部检查分类存在，入口合并；原 finish 的只读收尾判断也进入 verify。原 start 改为 new change，resolve 改为 show，checkpoint 改为 context save。

<!-- tao:section commands -->
## 二、命令、输入与副作用

表中的 `tao` 代表受信任的项目局部入口。发布实现拟随 skill 提供 `scripts/tao.py`，由已确认的 Python 环境通过文件路径调用；可由项目任务运行器提供 `tao` 别名，不要求全局安装。不能因为 PATH 中存在同名程序就认定它属于 tao-dev。

| 拟议接口 | 输入与结果 | 副作用及实施顺序 |
|---|---|---|
| `tao new change <slug>` | 创建一个变更计划，生成 DOC／CHG 标识符；语言与日期规则从项目约定取得，必要时用 `--locale` 覆盖 | 模板阶段；更新项目内日期序号登记，排他创建，不覆盖已有内容 |
| `tao verify [CHG-ID]` | 自动选择必要检查，执行后汇总文档、项目行为、证据及收尾条件 | 首批先实现文档子集，随后补足行为与证据；执行已授权子进程并写报告，不修改受检源文件或批准交付 |
| `tao status [CHG-ID]` | 查询任务、依赖、未决项和证据时效；不运行检查，不刷新旧证据 | 证据阶段；只读，无目标时可展示项目摘要，不能因查询而勾选任务 |
| `tao show <ID>` | 展示正式条目、定义位置、退役信息及可用的发布入口 | 首批；只读，类型从 ID 得到，不要求用户另选；未构建站点时 URL 可为空 |
| `tao context save [CHG-ID] --from <file>` | 保存 agent 提供的目标、决定、阻碍和下一步，并附实际状态与证据索引 | 恢复阶段；原子更新变更附件中的 `handoff.md`，不自动提交或推送 |
| `tao doctor` | 检测项目根、配置、工具、schema 与命令能力 | 首批；只读，不安装依赖、不修复配置、不主动试跑构建 |
| `tao id new <TYPE>` | 为已支持的条目类型生成 UUIDv4，检查当前索引与退役记录是否重复 | 首批辅助命令；只输出 ID；正常生成文档由生成器自动分配，用户不逐项选号 |
| `tao retire <ID> --reason <text>` | 展示条目及引用影响，移除正文并登记退役 | 模板阶段；默认预览，显式 `--apply` 才写入；不把退役叫作 archive，以免混淆删除承诺与归档已完成工作 |
| `tao docs build` | 生成书籍、条目索引与永久链接入口 | 出版阶段；只写配置的生成目录，默认 `artifacts/book/`，不部署网站 |

常规交互集中在创建、验证、查看进度；doctor、编号、保存等由 agent 按时机调用或供排障使用。没有单独 finish 命令：交付前必须核对的条件在完整 verify 中自动汇总，验收后的提交、合入、归档或发布仍按实际授权与项目流程处理，不因验证成功附带执行。

第一批发布 doctor、id new、show 与 verify 的文档子集。能力列表区分 `verify.docs`、`verify.code`、`verify.evidence`；只实现文档子集时不能声称支持完整交付验证。没有实现的命令或子能力不列为可用，也不用返回成功的空实现占位。

<!-- tao:section contract -->
## 三、自动选择与公共执行契约

### 默认选择，特殊情况才覆盖

`tao verify` 默认检查当前目标的全部必需条件，而非只检查语法。目标优先来自显式 CHG ID，其次是当前变更目录或当前任务已有绑定；只有一个活动变更时可以自动选中。存在多个候选且上下文不能区分时才要求指定，不以“最近修改”猜测。项目级调用按明确的项目验证配置执行，不凭文件扩展名推断项目只有文档。

项目接入时确定一次检查策略：检查标识、适用输入、依赖、执行命令、必需条件、输入指纹规则及预算。每次调用按变更、契约关系和策略选择检查，并输出选择原因。有可靠基线和依赖信息时选择受影响范围；没有基线、依赖不完整或遇到共享配置变更时扩大到全部相关范围，不能把“不知道影响什么”当作没有影响。全局 ID 唯一性、必要跨文件引用及项目硬性门槛不因局部修改而被省略。

接入由 agent 优先发现并复用现有构建、测试、CI 和项目约定，不把工具清单交给用户逐项勾选。只有目标、预算或权限等无法从已有信息确定的关键选择才询问；策略确定后日常调用自动复用，不静默降低既有门槛。

普通用户不选择类型、范围或级别。以下选项供 skill、hook、CI 或排障按需使用：

| 选项 | 意义与限制 |
|---|---|
| `--only docs`、`--only code`、`--only evidence` | 仅运行指定分类，也可逗号组合。docs 包含格式与关系；code 包含配置的构建、类型、测试等行为检查；evidence 检查必要任务、审查记录与证据时效。属于局部验证，报告必须标记 partial，不构成整体完成依据 |
| `--scope changed` 或 `--scope all` | 覆盖范围选择；changed 仍包含必要依赖与全局规则，无可靠基线时回退 all 并说明。all 扩大相关范围，不意味着执行项目未声明、未授权的操作 |
| `--dry-run` | 展示目标、检查集合、选择原因、预计副作用和缺失能力，不执行检查子进程；不生成通过证据 |
| `--format text` 或 `--format json` | 选择输出格式，不改变检查内容和通过条件 |

不增加 fast／strict 等通用等级开关，也不要求每次选 `--profile`。快速反馈通过局部分类及有效证据复用获得；高风险需要的额外检查由既定策略和明确的风险判断决定。预算不足或能力缺失时记录 not_run，不偷偷降级。后续修订策略应有明确理由与版本，不能为本次通过临时降低要求。

有效的旧检查结果可以复用，但需匹配本次完整输入、工具／配置版本和保存期限；报告指出 reused 与证据位置。仅因文件时间戳或 VCS 修订未变不能推导有效。新验证执行前后比较受检输入，执行中发生变化则标记 stale。原始报告和摘要按 [产物保存约定](document-layout.md) 归档。

### 结果与完成语义

所有命令支持 `--format text|json`。JSON 公共结果包含 `tool: "tao-dev"`、`protocol_version`、`tool_version`、`command`、`status`、`diagnostics` 和 `outputs`；doctor 额外返回支持的 schema 和 `capabilities`。verify 额外记录目标、检查清单及选择原因、未覆盖条件、`coverage`（complete／partial／unknown）和 `readiness`（checks-satisfied／blocked／not-evaluated）。子工具原始输出进入报告，进度写 stderr，不混入 JSON。

完整 verify 汇总格式、项目必需检查、任务与依赖、已要求的审查记录及当前证据；缺失完成条件时 readiness 为 blocked。该结果只证明记录和确定性条件，不能代替语义评审、真实性判断或人工授权。调用 status 只读取已有结果，不能获得更高保障。

退出码 `0` 表示本次所选检查通过，`1` 表示发现不满足条件的结果，`2` 表示配置／工具故障、能力缺失或检查未完成。带 `--only` 的通过可以返回 0，但 coverage 固定为 partial、readiness 为 not-evaluated。完整调用只有必需检查及收尾条件满足才返回 0，并报告 complete／checks-satisfied；开放任务或未解决阻断返回 1，必需工具不可用返回 2。CI 的交付门槛必须核实完整报告，不能把局部调用的 0 当作整体通过。dry-run 的 0 仅表示选择计划有效，coverage 为 unknown、readiness 为 not-evaluated，不是执行证据。

逐项结果区分 passed、failed、not_run、not_applicable、stale；不适用必须有条件依据。文档子集或尚无 CHG／EVD 支持的版本，不能把缺失的完整验证能力自动标为不适用。人工观察可登记为证据，但不伪造工具退出码，也不从两份模型报告的存在推导独立审查完成。

### 环境与写入边界

项目根由显式 `--project <path>` 或当前目录向上最近的 `.tao/config.toml` 确定。无配置时 doctor、id new、show 和 `verify --only docs` 可以在显式给定的项目根工作；完整验证缺少策略或目标时说明需补齐的信息，不擅自创建全局配置。

Python 枚举、Markdown AST 与 UUID 库是正确性路径；`rg` 只作可选加速，不以全文命中决定正式定义或 ID 分配。VCS 是可选基线来源，Sphinx 是可选出版依赖，没有它们仍可执行文档子集。枚举当前文件包含未跟踪内容，不用 VCS 跟踪列表代替受检范围。

写入限制在项目内明确目录，路径和符号链接解析后不得越界，不修改插件缓存或全局配置。生成器、退役和交接使用锁与原子操作，验证不自动修复语义问题。配置中新增执行命令仍需符合已有授权，不能因来自仓库就扩大权限。

<!-- tao:section integration -->
## 四、skill、hook 与自动收尾

skill 对照随包 [流程操作规程](../plugins/tao-dev/skills/tao-dev/references/workflow.md) 自动选择调用：编辑文档后用文档子集反馈；实施中按当前工作运行相关项目检查；对用户作完成声明前执行完整 verify 并读取报告。用户不用分别记住检查类型，也不用再执行收尾命令。没有自动事件适配时由 skill 显式调用，不能宣称 hook 已触发。

doctor 在进入项目、工具或配置变化时检测能力；入口必须来自受信任的包或项目配置，不能随意执行 PATH 中同名程序，缺失时不自动安装。当前没有 CLI 时继续使用项目已有检查和简明交接，但明确未自动完成的条件，不把人工查看报告成 tao verify 通过。

hook 仅在已验证的平台事件上触发预算内的短检查，例如 `verify --only docs --scope changed`；它不启动完整跨模型评审、全量长测试或生成／退役操作。相同输入的重复事件合并，避免验证报告写入后再次触发自身。完整交付验证由 skill 在收尾时发起，CI 按项目配置复核；未来自动化不能绕过既有授权或未解决阻断。

两端试验只在隔离项目或单次调用内生效，直接使用已配置的 `codex`、`claude`。当前只有未发布的接口设计；斜杠命令包装、安装配置和可执行程序按实际需求与验证结果逐步提供。

<!-- tao:section acceptance -->
## 五、验证与实现顺序

每个命令以真实结果和独立反例验收，不能只检查帮助文字。首批文档能力到完整验证逐步实施，至少覆盖：

- 文档错误、重复 ID、错误日期、悬空引用与任务依赖环可定位；围栏示例不注册定义，移动文件不破坏引用。
- 常规用户只表达意图，agent 在编辑时选文档子集、交付时选完整验证；局部通过和 dry-run 均不能产生整体完成结论。
- 改动范围或依赖未知时扩大选择；未跟踪输入不遗漏；不能因为全部文件是 Markdown 就跳过 prompt 行为验收。
- 无 VCS、Sphinx、rg 时文档子集仍工作；多个候选变更仅在无法确定目标时要求指定，不反复询问已绑定目标。
- 开放任务、证据过期、工具缺失、预算不足或执行中输入变化均不能完整通过；复用有效证据须有可核实指纹。
- 生成、退役、归档、合入和发布不会由验证成功附带发生；短 hook 不执行完整长流程或循环触发。
- 日期序号删除、并发和耗尽遵循分配契约；模型审查、出版永久链接和隔离加载分别以其真实行为验收。

先实现核心文档能力，再接 CHG／EVD 模板、项目行为检查和完整收尾判定，最后接入 hook 与出版。功能状态随证据更新，不能将本文的接口表当作已实现能力。
