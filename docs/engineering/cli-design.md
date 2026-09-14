---
schema: tao.project.design/v0.1
id: DOC_20260914_0VF190409FQCN197
title: tao 命令与流程接入
locale: zh-Hans
status: draft
created: '2026-09-14'
---

# tao 命令与流程接入

本文定义拟实现的工具接口，落实 {need}`REQ_20260914_95193C19C90NRXV4`、{need}`REQ_20260914_42AXMZ2KH2RAZ8M3`、{need}`REQ_20260914_0J68SDKV86ENKER2` 和 {need}`REQ_20260914_6YZ1XE1GC369655H`。**当前尚无 tao 可执行程序，下述命令均为接口设计，不是可直接运行的使用说明。** [流程操作规程](../../plugins/tao-dev/skills/tao-dev/references/workflow.md) 规定 agent 的调用时机与当前回退行为。

使用方格式由 [文档规程](../../plugins/tao-dev/skills/tao-dev/references/documents.md) 和 [格式注册表](../../plugins/tao-dev/skills/tao-dev/assets/document-profiles.json) 定义。CLI 读取同包注册表，按 schema 选择结构规则；生成器使用其模板，不根据使用方目录名或模型判断另造格式。本项目交付文档也使用这些 profile；开发文档的校验范围见 [文档契约](document-contract.md)。

<!-- tao:section overview -->
## 用户操作与命名依据

用户通常只需表达“整理需求、制定计划、实现、审查、验证”的意图，由 skill 推进。流程名称统一为 `specify → plan → implement → review → verify`：specify 包含必要澄清，plan 包含必要设计与任务拆分；调试、恢复和交接按需进入。它们不是每次都需用户手动调用的五个命令，也不要求每个节点生成一份文件。

**tao CLI 只承接确定性操作。** 解析、生成、验证、查询和保存记录可以在普通终端或 CI 执行；需求判断、设计、对抗式审查仍由 skill、可用客户端或人工完成。初版不提供会隐式调用多个模型的 `tao review`，不从报告数量或客户端名称推导审查通过。

### 参考项目的实际入口

以下为所审阅版本中的代表性入口，不是完整目录或流行度排名；链接固定到该版本。名称省略重复的斜杠命名空间时保留操作部分，并区分 CLI、command 与 skill。共同倾向是核心动作简短、必要时加对象或用途；不存在统一的行业命令标准。

| 项目 | 代表名称 | 对 tao-dev 的启示 |
|---|---|---|
| [Spec Kit](https://github.com/github/spec-kit/tree/ad601e5d52251f9131220c621d1cbbb7d61bebee/templates/commands) | specify、plan、tasks、implement、clarify | 按流程动作命名；保留 specify／plan 等语义，不强制每步一个入口 |
| [OpenSpec](https://github.com/Fission-AI/OpenSpec/tree/0a99f410457271aa773d8b106f03f637f7c6b3c0/src/core/templates/workflows) | CLI new change；斜杠 new、propose、apply、verify、archive；skill openspec-new-change | 同一动作可以有短入口和描述性 skill 名；new 适合创建，propose 还包含内容生成 |
| [Trellis](https://github.com/mindfold-ai/trellis/tree/e7c5ead4d0dfd717d11a40b6bc0c80d8af94c49a/packages/cli/src/templates/codex/skills) | start、brainstorm、check、finish-work、record-session | start 表示建立或恢复会话上下文，record-session 偏进度日志，均不等于创建变更 |
| [GSD](https://github.com/open-gsd/gsd-core/tree/a68f1be10e8338128065691d5ea777a14eaca51a/commands/gsd) | new-project、plan-phase、execute-phase、pause-work、resume-work、verify-work | 对象或阶段确有区分需要时才加后缀；保存交接不应暗示已暂停执行 |
| [Compound Engineering](https://github.com/EveryInc/compound-engineering-plugin/tree/0a2957852e2034d04eb01120fd7da6ed5307dc56/skills) | ce-brainstorm、ce-plan、ce-work、ce-handoff | handoff 用于生成或读取交接摘要；前缀用于命名空间 |
| [Matt Pocock Skills](https://github.com/mattpocock/skills/tree/e9fcdf95b402d360f90f1db8d776d5dd450f9234/skills) | handoff；工程 skill 另有 to-spec、implement、tdd | handoff 明确产出给后续 agent 阅读的摘要；不照搬其保存位置或 issue 依赖 |
| [Oh My OpenAgent](https://github.com/code-yeongyu/oh-my-openagent/blob/dec381ed201a1326883db9f42bdb3c2add91b299/packages/omo-opencode/src/features/builtin-commands/commands.ts) | start-work、handoff、refactor | start-work 进入计划执行；handoff 生成会话摘要，含义与本项目交接吻合 |
| [gstack](https://github.com/garrytan/gstack/tree/a3259400a366593e0c909dd9ac3e59752efd2488) | spec、review、ship、context-save、context-restore | 短核心动词与必要复合词并存；保存摘要不等于 ship 或恢复客户端内部上下文 |
| [Everything Claude Code](https://github.com/affaan-m/everything-claude-code/tree/ed387446052dfbc6b52de149406b70efa65edc59/commands) | plan、code-review、save-session、resume-session、checkpoint | save-session 表意明确；checkpoint 还创建 stash／commit，不适合仅保存摘要 |
| [Superpowers](https://github.com/obra/superpowers/tree/d884ae04edebef577e82ff7c4e143debd0bbec99/skills) | brainstorming、writing-plans、executing-plans、verification-before-completion | 长名称用于能力发现与自动触发，不作为要求用户记住长命令的依据 |
| [Addy Osmani Agent Skills](https://github.com/addyosmani/agent-skills/tree/98967c45a42b88d6b8fb3a88b7ff6273920763d6/skills) | idea-refine、interview-me、planning-and-task-breakdown、context-engineering | 描述性 skill 名说明能力范围，不必映射成同长的 CLI 或斜杠命令 |
| [BMAD](https://github.com/bmad-code-org/BMAD-METHOD/tree/1cd4a7f5c06421727d779cbb3f3b5953b4c7282d/src/core-skills) | bmad-spec、bmad-brainstorming、bmad-review-adversarial-general | 命名空间与审查类型各有作用；不为简短而丢失必要区分 |

### 本项目的命名规则

常用入口优先使用一个完整、常见的词：`new`、`verify`、`status`、`handoff`。`new` 唯一表示创建变更计划，因此无需再输入 change；不表示初始化项目、启动实现或恢复会话。`handoff` 表示保存供后续工作读取的交接摘要，不创建可回滚快照、不停止会话、不转交执行权，也不把机器保存过程称为内容分析。摘要由 agent 整理，CLI 负责校验、附加状态索引与落盘。

使用完整词而非 n／v／ctx 等缩写，不增加同义别名或让用户在 start／new／propose 之间选择。`start` 在参考项目中并不少见，但涵盖会话初始化或计划执行，不能准确描述这里只创建计划的操作。`save` 缺少保存对象，`pause` 暗示暂停执行，均不如 handoff 明确。低频且需要对象限定的 `id new`、`docs build` 保留分组；直接叫 build 容易与使用方项目的代码构建混淆。

斜杠命令采用同一操作词，并由客户端提供必要命名空间；例如 `new`、`handoff` 可呈现为 `/tao:new`、`/tao:handoff`，不再展开为 new-change 或 context-save。**这是操作名示意，不是已经可用或保证两端相同的调用语法。** 实际前缀与 skill 调用方式随客户端适配验收，遵循 [插件设计](plugin-design.md)，不另造跨客户端通用语法。

CLI 和 agent 入口共享操作意图，但输入和完成条件不同。开发者日常使用客户端中的 skill／斜杠入口或自然语言请求；终端 CLI 面向 agent、自动化和需要直接操作文件的开发者，不要求日常用户手动调用。handoff 同样由 agent 整理摘要，再调用 `tao handoff --from <file>`；用户无需准备中间文件。

### new 的两层契约

| 层次 | 输入示意 | 职责与完成条件 |
|---|---|---|
| 开发者使用的 agent 入口 | `new 为导出功能增加取消操作`，或“用 tao-dev 为导出取消功能制定计划” | 接受自然语言及已有会话上下文，调查与必要澄清，提炼 slug，组织并写入可阅读的计划草稿；真实斜杠语法由客户端适配决定 |
| agent 使用的终端 CLI | `tao new --slug cancel-export` | 校验显式 slug、目标路径和冲突，按模板创建草稿骨架、分配 DOC／CHG 等生成内容所需 ID，返回实际路径与 ID；不调用模型或理解需求 |

`<slug>` 在 CLI 接口表中表示必需值；改为显式 `--slug` 选项是为了与自然语言描述区分。裸 `tao new` 或缺少该选项时返回参数诊断，不猜测描述、不调用模型、不落盘。CLI 的成功只表示骨架已创建，不表示计划已写好、验证通过或可开始实现。直接使用 CLI 的开发者承担后续填写工作。

agent 入口的描述不是 slug 参数，也不按 shell 参数拆分。只输入 new 时先复用会话中已明确的目标；没有可识别目标才询问。知道目标后由 agent 提炼简短 slug，冲突时判断继续已有变更或细化名称，不把命名选择转交用户。命令包装只传递操作、完整描述及必要上下文，不能直接把用户描述拼成底层 shell 命令。

执行顺序为“理解目标与读取相关材料 → 判断是否需要新计划 → CLI 创建模板骨架 → agent 填写并检查草稿”。骨架包含结构和元数据，不是空文件；尚待填写的模板变量不满足正式文档契约。agent 应在本次工作中继续补齐已有信息，缺少实质信息时明确未决项；中断遗留骨架须报告未完成，恢复时继续同一文件和 ID。不能以生成器返回 0 或文件存在作为 new 的交付结果。

new 的 agent 入口交付目标、范围、已有依据、可确定的验收及下一步规划入口；不足以决定的设计与任务如实标为未决，不虚构方案。草稿不等于评审通过或完整 plan 阶段完成，new 本身不隐含开始编码；同一请求已明确授权继续设计或实现时，按原请求推进，不额外要求用户输入下一条命令。

优先复用已有 skill；按需增加入口包装，不为每个辅助 CLI 子命令创建一个 skill。核心 CLI 与变更骨架生成已实现，客户端入口待验收；操作能力和配置以 [工具规程](../../plugins/tao-dev/skills/tao-dev/references/tools.md) 及 doctor 输出为准。

验证统一使用 verify；文档检查、行为验证及只读收尾判断是其内部分类。验收后的归档、集成和发布按实际授权处理，不从命名自动派生额外步骤。未发布的草案名称不保留兼容别名。

<!-- tao:section architecture -->
## 流程接入

skill 对照 [流程操作规程](../../plugins/tao-dev/skills/tao-dev/references/workflow.md) 自动选择调用：编辑文档后用文档子集反馈；实施中按当前工作运行相关项目检查；对用户作完成声明前执行完整 verify 并读取报告。用户不用分别记住检查类型，也不用再执行收尾命令。没有自动事件适配时由 skill 显式调用，不能宣称 hook 已触发。

doctor 在进入项目、工具或配置变化时检测能力；入口必须来自受信任的包或项目配置，不能随意执行 PATH 中同名程序，缺失时不自动安装。某项 CLI 能力缺失时继续使用项目已有检查和简明交接，但明确未自动完成的条件，不把人工查看报告成 tao verify 通过。

hook 仅在已验证的平台事件上触发预算内的短检查，例如 `verify --only docs --scope changed`；它不启动完整跨模型评审、全量长测试或生成／退役操作。相同输入的重复事件合并，避免验证报告写入后再次触发自身。完整交付验证由 skill 在收尾时发起，CI 按项目配置复核；未来自动化不能绕过既有授权或未解决阻断。

两端试验只在隔离项目或单次调用内生效，直接使用已配置的 `codex`、`claude`。核心命令已提供，斜杠命令和 hook 的平台适配另行以真实行为验收。

<!-- tao:section contracts -->
## 命令与执行契约

### 命令、输入与副作用

表中的 `tao` 代表受信任的项目局部入口。实现随 skill 提供 `scripts/tao.py`，由已确认的 Python 环境通过文件路径调用；可由项目任务运行器提供 `tao` 别名，不要求全局安装。不能因为 PATH 中存在同名程序就认定它属于 tao-dev。

| 拟议接口 | 输入与结果 | 副作用及实施顺序 |
|---|---|---|
| `tao new --slug <slug>` | 在 `docs/changes/<yyyy-mm>/` 创建 `<yyyymmdd>-<slug>.md` 变更计划的模板骨架，不生成需求或启动实现；返回实际路径与分配的标识符；语言从项目约定取得，必要时用 `--locale` 覆盖；日期取执行环境的本地日期，无需选择时区 | 模板生成器阶段；检查计划与附件路径，排他创建；重名返回错误，不覆盖或自动加计数后缀 |
| `tao verify [CHG-ID]` | 自动选择必要检查，执行后汇总文档、项目行为、证据及收尾条件 | 首批先实现文档子集，随后补足行为与证据；执行已授权子进程并写报告，不修改受检源文件或批准交付 |
| `tao status [CHG-ID]` | 查询任务、依赖、未决项和证据时效；不运行检查，不刷新旧证据 | 证据阶段；只读，无目标时可展示项目摘要，不能因查询而勾选任务 |
| `tao show <ID>` | 展示正式条目、定义位置、退役信息及可用的发布入口 | 首批；只读，类型从 ID 得到，不要求用户另选；未构建站点时 URL 可为空 |
| `tao handoff [CHG-ID] --from <file>` | 保存 agent 提供的目标、决定、阻碍和下一步，并附实际状态与证据索引；不总结整段原始会话 | 恢复阶段；原子更新变更附件中的 `handoff.md`，不停止会话、创建快照或自动移交执行，不提交或推送 |
| `tao doctor` | 检测项目根、配置、工具、schema 与命令能力 | 首批；只读，不安装依赖、不修复配置、不主动试跑构建 |
| `tao id new <TYPE>` | 为已支持的条目类型生成本地日期＋80 位安全随机部分的 ID，检查当前索引与退役记录是否重复 | 首批辅助命令；只输出 ID；正常生成文档由生成器自动分配，用户不逐项选号 |
| `tao retire <ID> --reason <text>` | 展示条目及引用影响，移除正文并登记到 `docs/retired/<yyyymmdd>.jsonl`，日期取退役的本地日期 | 模板生成器阶段；默认预览，显式 `--apply` 才写入；不把退役叫作 deprecate 或 archive，以免混淆弃用通知、删除承诺与归档已完成工作 |
| `tao docs build` | 生成书籍、条目索引与永久链接入口 | 出版阶段；只写配置的生成目录，默认 `tmp/tao/book/`，不部署网站 |

常规交互集中在创建、验证、查看进度；doctor、编号、保存等由 agent 按时机调用或供排障使用。没有单独 finish 命令：交付前必须核对的条件在完整 verify 中自动汇总，验收后的提交、合入、归档或发布仍按实际授权与项目流程处理，不因验证成功附带执行。

第一批发布 doctor、id new、show 与 verify 的文档子集。能力列表区分 `verify.docs`、`verify.code`、`verify.evidence`；只实现文档子集时不能声称支持完整交付验证。没有实现的命令或子能力不列为可用，也不用返回成功的空实现占位。

### 自动选择与公共执行契约

#### 默认选择，特殊情况才覆盖

`tao verify` 默认检查当前目标的全部必需条件，而非只检查语法。目标优先来自显式 CHG ID，其次是当前变更目录或当前任务已有绑定；只有一个活动变更时可以自动选中。存在多个候选且上下文不能区分时才要求指定，不以“最近修改”猜测。项目级调用按明确的项目验证配置执行，不凭文件扩展名推断项目只有文档。

项目接入时确定一次检查策略：检查标识、适用输入、依赖、执行命令、必需条件、输入识别规则及预算。每次调用按变更、契约关系和策略选择检查，并输出选择原因。有可靠基线和依赖信息时选择受影响范围；没有基线、依赖不完整或遇到共享配置变更时扩大到全部相关范围，不能把“不知道影响什么”当作没有影响。全局 ID 唯一性、必要跨文件引用及项目硬性门槛不因局部修改而被省略。

接入由 agent 优先发现并复用现有构建、测试、CI 和项目约定，不把工具清单交给用户逐项勾选。只有目标、预算或权限等无法从已有信息确定的关键选择才询问；策略确定后日常调用自动复用，不静默降低既有门槛。

普通用户不选择类型、范围或级别。以下选项供 skill、hook、CI 或排障按需使用：

| 选项 | 意义与限制 |
|---|---|
| `--only docs`、`--only code`、`--only evidence` | 仅运行指定分类，也可逗号组合。docs 包含格式与关系；code 包含配置的构建、类型、测试等行为检查；evidence 检查必要任务、审查记录与证据时效。属于局部验证，报告必须标记 partial，不构成整体完成依据 |
| `--scope changed` 或 `--scope all` | 覆盖范围选择；changed 仍包含必要依赖与全局规则，无可靠基线时回退 all 并说明。all 扩大相关范围，不意味着执行项目未声明、未授权的操作 |
| `--dry-run` | 展示目标、检查集合、选择原因、预计副作用和缺失能力，不执行检查子进程；不生成通过证据 |
| `--format text` 或 `--format json` | 选择输出格式，不改变检查内容和通过条件 |

不增加 fast／strict 等通用等级开关，也不要求每次选 `--profile`。快速反馈通过局部分类及有效证据复用获得；高风险需要的额外检查由既定策略和明确的风险判断决定。预算不足或能力缺失时记录 not_run，不偷偷降级。后续修订策略应有明确理由与版本，不能为本次通过临时降低要求。

输入识别采用 skill 中的保存规则：默认在证据内记录固定 VCS 版本、受检范围及版本一致性结论，必要时引用持久差异或快照，不默认生成逐文件哈希清单。有效的旧检查结果可以复用，但需匹配本次完整输入、工具／配置版本和保存期限；报告指出 reused 与证据位置。仅因文件时间戳或 VCS 修订未变不能推导有效。新验证执行前后比较受检输入，执行中发生变化则标记 stale。摘要默认写入计划 verification；原始输出只在生成目录或 CI 保存，确有持久需求才按 [产物保存约定](document-layout.md) 归档。日志不可用与输入不匹配分别报告，不因前者改写历史 passed 或任务状态。

#### 结果与完成语义

所有命令支持 `--format text|json`。JSON 公共结果包含 `tool: "tao-dev"`、`protocol_version`、`tool_version`、`command`、`status`、`diagnostics` 和 `outputs`；doctor 额外返回支持的 schema 和 `capabilities`。verify 额外记录目标、检查清单及选择原因、未覆盖条件、`coverage`（complete／partial／unknown）和 `readiness`（checks-satisfied／blocked／not-evaluated）。子工具原始输出进入报告，进度写 stderr，不混入 JSON。

完整 verify 汇总格式、项目必需检查、任务与依赖、已要求的审查记录及当前证据；缺失完成条件时 readiness 为 blocked。该结果只证明记录和确定性条件，不能代替语义评审、真实性判断或人工授权。调用 status 只读取已有结果，不能获得更高保障。

退出码 `0` 表示本次所选检查通过，`1` 表示发现不满足条件的结果，`2` 表示配置／工具故障、能力缺失或检查未完成。带 `--only` 的通过可以返回 0，但 coverage 固定为 partial、readiness 为 not-evaluated。完整调用只有必需检查及收尾条件满足才返回 0，并报告 complete／checks-satisfied；开放任务或未解决阻断返回 1，必需工具不可用返回 2。CI 的交付门槛必须核实完整报告，不能把局部调用的 0 当作整体通过。dry-run 的 0 仅表示选择计划有效，coverage 为 unknown、readiness 为 not-evaluated，不是执行证据。

逐项结果区分 passed、failed、not_run、not_applicable、stale；不适用必须有条件依据。文档子集或尚无 CHG／EVD 支持的版本，不能把缺失的完整验证能力自动标为不适用。人工观察可登记为证据，但不伪造工具退出码，也不从两份模型报告的存在推导独立审查完成。

#### 环境与写入边界

项目根由显式 `--project <path>` 或当前目录向上最近的 `.tao/config.toml` 确定。无配置时 doctor、id new、show 和 `verify --only docs` 可以在显式给定的项目根工作；完整验证缺少策略或目标时说明需补齐的信息，不擅自创建全局配置。

Python 枚举、Markdown AST、日历解析与 `secrets` 安全随机源是正确性路径；`rg` 只作可选加速，不以全文命中决定正式定义或 ID 分配。VCS 是可选基线来源，Sphinx 是可选出版依赖，没有它们仍可执行文档子集。枚举当前文件包含未跟踪内容，不用 VCS 跟踪列表代替受检范围。

写入限制在项目内明确目录，路径和符号链接解析后不得越界，不修改插件缓存或全局配置。生成器、退役和交接使用锁与原子操作，验证不自动修复语义问题。配置中新增执行命令仍需符合已有授权，不能因来自仓库就扩大权限。

.tao/ 仅保存控制 CLI 和 skill 行为的配置；项目资产在 docs/ 或其显式映射位置，派生索引、缓存与短期锁默认在 tmp/tao/cache/。退役读取器遍历全部日期 JSONL 并与正文统一查重；写入时保护当日文件，正文移除与记录落盘作为一致修改处理，失败不能遗失唯一的追溯记录。具体字段与合并约束使用 skill 的文档契约，不在工具实现中另造规则。

<!-- tao:section invariants -->
## 检查结果与写入约束

局部检查不构成整体完成；能力缺失不自动成为不适用。验证不得修改受检源文档或扩大授权，生成与退役操作保护已有内容及稳定 ID。完整契约由上一节定义。

<!-- tao:section errors -->
## 故障与恢复

参数、配置、工具不可用与条件不满足按公共退出码区分。写入失败不得遗失源内容或追溯记录；中断后恢复同一变更，不能通过重建 ID 掩盖部分完成。

<!-- tao:section verification -->
## 验收与实施顺序

每个命令以真实结果和独立反例验收，不能只检查帮助文字。首批文档能力到完整验证逐步实施，至少覆盖：

- 同包模板填充后按注册表解析；新增 profile 同步更新规则、模板与独立夹具；未知 schema、缺章节、残留模板变量和非法字段不能静默通过。
- 文档错误、重复 ID、错误日期、悬空引用与任务依赖环可定位；ID 验收覆盖非法字符、随机串长度、前导零、完整字符集首位及连续碰撞后报错；围栏示例不注册定义，移动文件不破坏引用。
- new 只创建计划；handoff 只保存交接，不能创建 VCS 快照、停止会话或移交执行。agent 入口准备 slug／摘要输入，用户无需选择对象类型或编写中间文件。
- 常规用户只表达意图，agent 在编辑时选文档子集、交付时选完整验证；局部通过和 dry-run 均不能产生整体完成结论。
- 改动范围或依赖未知时扩大选择；未跟踪输入不遗漏；不能因为全部文件是 Markdown 就跳过 prompt 行为验收。
- 无 VCS、Sphinx、rg 时文档子集仍工作；多个候选变更仅在无法确定目标时要求指定，不反复询问已绑定目标。
- new 的 agent 入口接受完整自然语言描述并自动提炼 slug；无描述时复用明确上下文，无目标时询问。CLI 缺少 --slug 不落盘，骨架创建成功不等于 agent 完成草稿；中断后保留原路径和 ID 继续填写，不创建重复计划。
- 开放任务、证据过期、工具缺失、预算不足或执行中输入变化均不能完整通过；日志过期不自动否定历史结果，只有缺少本次判断必需的材料才阻断复用；复用有效证据须有可核实的输入引用，固定版本加未提交修改不得误判为一致；仅保存报告不改变受检源内容时不触发无意义重验。
- 生成、退役、归档、合入和发布不会由验证成功附带发生；短 hook 不执行完整长流程或循环触发。
- 同日不同 slug 可共存；已有计划或附件路径及并发创建冲突均不覆盖；跨分支不同 CHG 的同名计划在集成时分别保留。模型审查、出版永久链接和隔离加载分别以其真实行为验收。
- 退役文件名与 retired_on 相符；跨日期重复 ID、仍在正文定义的 ID、无效替代及关系环均能发现；同日并发与失败恢复不会丢记录。没有 .tao/、清空非活跃缓存或移除工具后，项目文档和退役数据仍可保留并重建索引。

先实现核心文档能力，再接 CHG／EVD 模板、项目行为检查和完整收尾判定，最后接入 hook 与出版。功能状态随证据更新，不能将本文的接口表当作已实现能力。
