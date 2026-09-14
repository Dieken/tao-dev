---
schema: tao.project.spec/v0.1
id: DOC_20260914_4C7N0XHQSP7CY69P
title: 协作开发协议
locale: zh-Hans
status: draft
created: '2026-09-14'
---

# 协作开发协议

本文是 tao-dev 自身的需求规格，供开发与维护使用。实现与验收状态由对应记录说明；不作为第三方项目的运行 prompt 分发。

<!-- tao:section scope -->
## 目标与边界

**目标：让人和 AI 能以明确的契约、小步反馈和可复核证据完成开发；换人、换会话或更换 agent 后仍能接手。** 文档应是工程工作的直接材料，维护成本计入流程成本。

本项目提供流程指导、文档契约与模板、确定性检查和可选工具适配。首个可用版本应打通“一个变更 → 需求与任务 → 实现 → 验证 → 可读交付”的路径。

开发资料与分发产物分开管理。分发清单只包含实际运行所需的入口、参考、模板和脚本，不包含本项目的需求设计、开发任务和研究资料。验收分发包时，应在没有开发文档和本地研究目录的环境中检查运行材料的引用与必要流程。

当前不建设通用项目管理平台，不绑定 issue 服务，不预装所有质量工具，不强求每次修改都执行全部阶段。自动发布、复杂调度、多仓库同步及双向 issue 同步均不属于初版必需能力。首批运行验收环境固定为 Codex CLI 和 Claude Code CLI。

本协议定义必须实现的结果和验收场景。协作流程与长期决定见 [流程设计](protocol-design.md)，既有研发任务见 [实施计划](changes/2026-09/20260914-bootstrap.md)。同一承诺只定义一次，其他产物通过 ID 引用。

<!-- tao:section terms -->
## 术语与来源

概念与缩写见 [术语表](glossary.md)。

### 公共来源与采用边界

工程原则的执行文本维护在分发包的工程规程中，以降低维护成本、控制复杂度和形成可靠证据为目的。内部文档只维护其需求及验收关系。公开参考项目用于比较实现方式；其审批规则和技术选择不自动成为本项目要求。

公开参考及实际取舍如下。设计先行、小步验证、证据与上下文恢复在多个项目中反复出现，属于这些参考中的广泛共识；编号格式、拆分阈值和工具接口是本项目自己的选择。下表覆盖已评估的来源，不把来源数量当作质量保证。

| 参考 | 采用或用于验证的做法 | 不直接照搬的部分 |
|---|---|---|
| [Spec Kit](https://github.com/github/spec-kit) | 规格、计划与任务的职责区分 | 不要求每次修改生成全套文件 |
| [OpenSpec](https://github.com/Fission-AI/OpenSpec/blob/0a99f410457271aa773d8b106f03f637f7c6b3c0/schemas/spec-driven/schema.yaml) | 产物依赖、长期规格与变更分离 | 不把局部编号作为跨项目 ID |
| [BMAD](https://github.com/bmad-code-org/BMAD-METHOD) | 按复杂度选择紧凑或完整流程 | 不强制所有角色和审批阶段 |
| [Compound Engineering](https://github.com/EveryInc/compound-engineering-plugin) | 统一计划、就绪判断、定向读取 | 不增加另一份重复的任务真相 |
| [Trellis](https://github.com/mindfold-ai/trellis) | 按任务注入上下文、平台适配 | 不预设单一客户端 |
| [GSD](https://github.com/open-gsd/gsd-core) | 行为验证区别于文件存在、状态恢复 | 不把派生进度当作有效证据 |
| [Superpowers](https://github.com/obra/superpowers/tree/d884ae04edebef577e82ff7c4e143debd0bbec99/skills) | `writing-plans` 的可验证任务；`verification-before-completion` 的新鲜证据 | 不按固定分钟数切任务，不强制重复审批或给每项计划预写完整实现 |
| [Addy Osmani 的 agent-skills](https://github.com/addyosmani/agent-skills/tree/98967c45a42b88d6b8fb3a88b7ff6273920763d6/skills) | 文档记录理由、ADR 生命周期、按实际版本核实 API、纵向任务 | 不固定计划／任务双文件或逐阶段人工批准；不要求每段代码都添加来源注释 |
| [Matt Pocock 的 skills](https://github.com/mattpocock/skills/tree/e9fcdf95b402d360f90f1db8d776d5dd450f9234/skills) | `codebase-design` 的模块与接口词汇；`to-spec` 的复用已知上下文；`tdd` 的行为测试 | 不依赖 issue 发布、不重复访谈、不要求每个测试接口重新取得确认 |
| [Everything Claude Code](https://github.com/affaan-m/everything-claude-code/blob/ed387446052dfbc6b52de149406b70efa65edc59/skills/verification-loop/SKILL.md) | 分项执行并汇总构建、类型、测试等检查 | 不采用统一覆盖率门槛；保留原始退出码，不靠输出截断判断成功 |
| [gstack](https://github.com/garrytan/gstack/blob/a3259400a366593e0c909dd9ac3e59752efd2488/context-save/SKILL.md) | 保存与恢复当前目标、决定和剩余工作；检查客户端命令重名 | 不引入全局状态目录、自动遥测或修改用户全局安装 |
| [Oh My OpenAgent](https://github.com/code-yeongyu/oh-my-openagent/blob/dec381ed201a1326883db9f42bdb3c2add91b299/docs/guide/overview.md) | 区分协调与执行职责、按任务选择上下文 | 不把多模型编排和复杂常驻调度列为初版前提 |

外部依据：[Kiro 规格结构](https://kiro.dev/docs/specs/)、[EARS 需求表达](https://alistairmavin.com/ears/)、[ULID 规范](https://github.com/ulid/spec)、[arc42](https://arc42.org/overview/)、[Diátaxis](https://diataxis.fr/)、[MyST 引用](https://myst-parser.readthedocs.io/en/latest/syntax/cross-referencing.html)、[Sphinx-Needs 配置](https://sphinx-needs.readthedocs.io/en/latest/configuration.html)、[BCP 47 语言标签说明](https://www.w3.org/International/articles/language-tags/index.en)、[Sphinx 国际化](https://www.sphinx-doc.org/en/master/usage/advanced/intl.html)。这些来源支持相关能力与组织思想，不表示本草案已符合某项完整行业标准。

外部引用采用上游公开地址；具体格式或行为依赖某一版本时应注明版本。文档格式与 ID 细节属于本项目设计。

独立审查的研究依据：[迎合性研究](https://arxiv.org/abs/2310.13548) 说明模型可能迎合用户观点；[多代理讨论研究](https://arxiv.org/abs/2305.14325) 在其推理与事实任务中观察到收益；[讨论机制与多样性研究](https://arxiv.org/abs/2601.19921) 表明收益依赖讨论机制和初始观点等条件。它们不证明跨供应商代码审查必然有效或错误相互独立。本项目据此采用有界、可复核的审查，并以真实缺陷、误报和成本检验效果，不以模型数量背书。

<!-- tao:section requirements -->
## 项目需求

以下条目是待评审的可验收需求。广泛共识仅指多个参考项目强调相同方向，不代表执行细节已成行业标准。

```{req} 按风险执行，保留人的决定权
:id: REQ_20260914_BFNMKT34JF1BSGW2
:status: proposed

根据影响、不可逆性和不确定性选择流程级别，记录目标、边界、验收和需要人的决定。已作决定与授权跨阶段保留。

<!-- tao:field acceptance -->
**验收：** README 错字修改可采用简化路径；数据迁移需有相应设计和恢复验证；未获授权的范围变化不得因自动推进而执行。

<!-- tao:field source -->
**来源：** BMAD、OpenSpec、Superpowers 的分级或设计先行思想。按风险组合阶段是本协议综合。
```

```{req} 信息只维护一处，阅读可按主题组合
:id: REQ_20260914_NN0AEQ2E1GTVSMTV
:status: proposed

明确规格、设计、任务、决策与证据的职责；同一版本中的条目只有一个正式定义。索引和反向引用由定义生成。

<!-- tao:field acceptance -->
**验收：** 修改一个需求后不必同步抄写计划与追踪表；拆分文件仍能找到其任务、决策和验证关系。

<!-- tao:field source -->
**来源：** OpenSpec 的长期规格、Compound Engineering 的统一计划、BMAD 的紧凑变更文档。
```

```{req} 文档可以校验并给出可修正的诊断
:id: REQ_20260914_42AXMZ2KH2RAZ8M3
:status: proposed

tao-dev 随 skill 分发统一、版本化的文档契约、格式注册表和模板，约束元数据、章节、条目、ID、引用和任务格式；使用方无需自行定义 schema，CLI 与 skill 使用同一份格式定义。检查区分结构错误、质量提示和语义审查意见。

<!-- tao:field acceptance -->
**验收：** 分发包离开开发仓库后，按 skill 提供的模板可写出受支持的文档；中英文共用结构键，CLI 从同包注册表取得规则。缺章节、重复 ID、悬空引用及非法任务格式能定位到文件和行；输出规则号、问题原因及修正建议。格式通过不得被报告为需求正确或设计合理。

<!-- tao:field source -->
**来源：** Kiro 等参考项目的固定模板实践与 EARS 的条件化需求表达。本协议补充全局标识符、语法层、关系层与语义层的边界。
```

```{req} 标识符全局化且不随组织方式改变
:id: REQ_20260914_5Y6CWDE3MFMKJXSB
:status: proposed

需求、用例、决策、任务、变更和文档采用离线生成的稳定 ID。标题、章节、路径与版本不得替代条目标识符。

<!-- tao:field acceptance -->
**验收：** 移动和改名保留 ID；不同变更中的任务没有局部编号歧义；废弃对象仍可追溯；复制成新对象时检测并解决重复标识符。

<!-- tao:field source -->
**来源：** ULID 规范中的 Crockford Base32 字符集与 80 位随机部分；可读日期、类型前缀及引用规则是本项目约定，不是标准 ULID。文件名中的日期与 slug 便于阅读，不能替代全局标识符。
```

```{req} 完成声明绑定实际证据
:id: REQ_20260914_0J68SDKV86ENKER2
:status: proposed

记录验证对象、执行条件、结果和适用范围；受影响输入变化后使相关证据过期。质量与成本分别展示实测、风险信号和估算。

<!-- tao:field acceptance -->
**验收：** 旧版本的通过结果不能证明新改动完成；未运行、不可用与不适用均不能显示为通过；token 估算费用不得冒充实际账单。

<!-- tao:field source -->
**来源：** Superpowers、GSD、agent-skills 的证据要求（广泛共识）；成本分类与失效规则为本协议综合。
```

```{req} 核心流程不绑定 agent 或 issue 平台
:id: REQ_20260914_95193C19C90NRXV4
:status: proposed

相同的契约与检查可通过普通命令执行，skill、slash command、hook 和 issue 接入作为适配层；安装前检测所需能力。

<!-- tao:field acceptance -->
**验收：** 没有 hook 或 issue 账号时仍能完成基本流程；适配失效会报告未执行的动作；完成检查不附带发布权限。

<!-- tao:field source -->
**来源：** Trellis 的平台适配实践。
```

```{req} 文档可持续组织成书
:id: REQ_20260914_3JQXRKWXKAZSNJ5R
:status: proposed

从同一份源文档生成按产品、工程、用户和运维组织的阅读入口与索引；区分开发中状态、发布版本及历史变更。

<!-- tao:field acceptance -->
**验收：** 不复制正文即可形成主题导航和需求索引；发布文档能定位到对应版本；移除 skill 后源文件仍可阅读。

<!-- tao:field source -->
**来源：** arc42、Diátaxis、Sphinx 文档体系。
```

```{req} 工作可恢复，并行有明确边界
:id: REQ_20260914_6YZ1XE1GC369655H
:status: proposed

交接保留目标、决定、相关条目、当前证据、阻碍和下一步。并行前明确修改范围、共享契约、状态写入与集成责任。

<!-- tao:field acceptance -->
**验收：** 新会话仅凭仓库材料和必要交接即可恢复；恢复时检查实际状态；多个任务集成后有整体验证。

<!-- tao:field source -->
**来源：** Trellis、GSD、Compound Engineering 的上下文与恢复实践（广泛共识）。
```

```{req} 规则升级与例外可追踪
:id: REQ_20260914_MG6TN8H5GBTAZZR3
:status: proposed

模板和契约带版本，升级提供诊断与明确迁移。质量例外记录理由、责任人、范围和复查条件，不能通过降低检查标准掩盖失败。

<!-- tao:field acceptance -->
**验收：** 不支持的 schema 版本明确报错；迁移先展示差异并保留 ID 与人工内容；到期或超出范围的例外不继续生效。

<!-- tao:field source -->
**来源：** GSD 对派生状态与人工内容的区分；例外和迁移策略为本协议综合。
```

```{req} 用实际项目检验流程本身
:id: REQ_20260914_4GKT5JRVBJNCQ05X
:status: proposed

本项目逐步采用自己的文档与工作流约定，并用正常案例和反例检验校验器及 agent 行为，记录增加的成本与发现的问题。

<!-- tao:field acceptance -->
**验收：** 覆盖小改动、普通功能、跨模块变更、需求变化、中断恢复及工具不可用；不能只靠本项目文档通过证明工具正确。

<!-- tao:field source -->
**来源：** 本项目的设计选择；分阶段自举与负向样例用于防止流程只在自身示例中成立。
```

```{req} 项目语言与使用方语言解耦
:id: REQ_20260914_GDY8F3KPE6XBGWGD
:status: proposed

tao-dev 自身选择正文和代码的维护语言；模板、生成文档及诊断可按目标项目语言呈现。语言变化不得改变机器结构、标识符或关系，译文不成为第二套权威需求。

<!-- tao:field acceptance -->
**验收：** 同一内容的中英文模板提取出相同的结构键和关系；修改“验收”为“Acceptance”不影响解析；更换诊断语言保留规则号和定位；使用方的英文项目不会因 tao-dev 的中文正文而被改为中文。

<!-- tao:field source -->
**来源：** BCP 47 的语言标记与 Sphinx 的翻译目录实践。正文语言和执行效果分开评估是本协议的设计选择。
```

```{req} 按公共插件标准打包，在双 CLI 中验收
:id: REQ_20260914_BWAY1ZF6HNPM855Y
:status: proposed

公共 manifest 和 skill 定义遵循 Agent Plugins 1.0.0 与 Agent Skills；agent、command、hook 使用目标客户端支持的格式与适配。Codex CLI 和 Claude Code CLI 均为首批必需运行验收环境。

<!-- tao:field acceptance -->
**验收：** 同一发布版本在两端分别完成格式、加载与行为验证；平台专用组件不重复触发，不依赖开发文档或另一平台配置；未验证的能力不得标记兼容。

<!-- tao:field source -->
**来源：** Agent Plugins、Agent Skills 和目标客户端官方扩展文档；详细设计见插件打包文档。
```

```{req} 工程原则进入实际运行指令
:id: REQ_20260914_4CS6P421MGW68PME
:status: proposed

分发的 skill 入口明确加载自包含的工程规程，指导需求、复杂度取舍、模块与状态设计、失败与安全、增量实现、验证、评审及运行演进。条款给出适用条件、具体动作和判断依据，而非仅宣示质量目标；按使用方风险和已有约定执行。

<!-- tao:field acceptance -->
**验收：** 仅凭分发包即可读取完整规程；无实际扩展需求时不预建抽象；缺陷修复有对应行为验证；未运行的检查不记为通过；评审不能将无约束依据的增强强制列为阻断。正式行为验收采用隔离场景，两端分别记录结果。

<!-- tao:field source -->
**来源：** 本项目对工程实践的综合，目的在于降低长期维护成本并使交付判断可复核。设计先行、小步反馈与证据验证在多个参考工作流中反复出现；具体编程条款不因这一共识而自动成为行业标准。
```

```{req} 独立判断并按风险开展对抗式审查
:id: REQ_20260914_M05MAGDARWBY5D44
:status: proposed

对用户和作者提出的方案，独立分析收益、代价、必要条件与更简单的替代方案。审查覆盖文档、代码、测试、配置及 prompt 等相关产物；按后果选择强度，加强审查优先采用不同模型供应商，并保留实际模型、输入、证据、处置和成本记录。

<!-- tao:field acceptance -->
**验收：** 事实不变时，不因用户赞同或反对的表态而无理由翻转技术判断；有实际需求的合理复杂度不被机械拒绝。审查者先独立检查，再对照作者理由；跨供应商不可确认或未执行时不得宣称完成；小修改不强制多模型流程，发现问题以证据裁决而非多数票。

<!-- tao:field source -->
**来源：** 用户对独立判断与审查多样性的要求，以及文末关于迎合性和多代理讨论的公开研究。跨供应商优先、审查输入与预算规则是本项目的工程选择，效果需在实际产物审查中验证。
```

<!-- tao:section cases -->
## 验收场景

```{uc} 移动章节不改变需求标识符
:id: UC_20260914_A98H5M8ZF9ZXHV6S
:status: proposed
:verifies: REQ_20260914_5Y6CWDE3MFMKJXSB, REQ_20260914_NN0AEQ2E1GTVSMTV

<!-- tao:field given -->
**给定：** 一个需求被任务和用例引用。
<!-- tao:field when -->
**当：** 修改标题并将其移入另一文档，重新构建索引。
<!-- tao:field then -->
**则：** ID 保留，引用定位到新位置，旧文件不再产生第二个正式定义；实际 HTML 标题链接使用稳定锚点，原有分享入口仍能解析到条目，退役后显示原因或替代入口。
```

```{uc} 文档错误给出有限且可定位的诊断
:id: UC_20260914_2CNRNTWZFWX995HA
:status: proposed
:verifies: REQ_20260914_42AXMZ2KH2RAZ8M3

<!-- tao:field given -->
**给定：** 样例中分别引入缺失必需章节、重复 ID、未知引用及缺少验证方法的任务。
<!-- tao:field when -->
**当：** 对整个索引范围运行文档检查。
<!-- tao:field then -->
**则：** 对应规则报告文件和行、严重级别与修正建议；语法损坏时抑制由同一损坏引起的级联噪声；正常样例无结构错误。
```

```{uc} 代码变化后旧证据失效
:id: UC_20260914_RHQB9EH6JNB8DJBA
:status: proposed
:verifies: REQ_20260914_0J68SDKV86ENKER2, REQ_20260914_6YZ1XE1GC369655H

<!-- tao:field given -->
**给定：** 某任务已经有通过报告。
<!-- tao:field when -->
**当：** 修改受检代码但保留提交号，随后在新会话恢复。
<!-- tao:field then -->
**则：** 受检范围与记录版本的差异检查发现未提交修改，相关证据显示已过期，任务不能仅凭旧报告被宣称完成；重新检查后记录新结果。
```

```{uc} 翻译显示文本不改变机器含义
:id: UC_20260914_YSP9ZDA6ZNV2PMXF
:status: proposed
:verifies: REQ_20260914_GDY8F3KPE6XBGWGD, REQ_20260914_42AXMZ2KH2RAZ8M3

<!-- tao:field given -->
**给定：** 两份隔离的中英文模板样例使用相同的稳定章节键、条目 ID 和关系，仅 locale 与显示文字不同。
<!-- tao:field when -->
**当：** 分别检查并导出结构，切换诊断输出语言，再故意删除其中一份的 acceptance 键。
<!-- tao:field then -->
**则：** 正常样例的结构和标识符一致；缺键产生相同规则号与对象定位，消息随语言变化；未实现的内容质量语言规则显示未检查，不伪装通过。
```

```{uc} 独立发布包在两种 CLI 中执行
:id: UC_20260914_6M8S2YF09JDJSWPV
:status: proposed
:verifies: REQ_20260914_BWAY1ZF6HNPM855Y, REQ_20260914_95193C19C90NRXV4

<!-- tao:field given -->
**给定：** 同一版本的发布包和两份隔离的使用方项目，无开发文档及未声明插件配置。
<!-- tao:field when -->
**当：** 分别在 Codex CLI 与 Claude Code CLI 加载插件并执行一个小变更，检查已声明角色和 hook，再禁用 hook 重复显式检查。
<!-- tao:field then -->
**则：** 两端产生独立运行证据；共享契约一致，入口和 hook 不重复加载；缺失能力明确失败，回退路径不会冒充未运行组件已通过。
```

```{uc} 运行规程独立可用并影响工程判断
:id: UC_20260914_SZVA0530E14QCGQZ
:status: proposed
:verifies: REQ_20260914_4CS6P421MGW68PME, REQ_20260914_0J68SDKV86ENKER2

<!-- tao:field given -->
**给定：** 仅含分发包与目标代码的隔离环境。用三个独立场景分别提供无实际扩展需求的局部功能、可以复现的缺陷、缺失必要测试工具的修改；包含中英文目标项目。
<!-- tao:field when -->
**当：** 在两端 CLI 中分别显式调用 skill，要求完成任务并说明设计和验证依据。
<!-- tao:field then -->
**则：** 各次调用读取包内规程，保持目标项目语言；不为假设的未来需求添加框架；缺陷场景执行相应复现和回归；工具缺失场景报告未验证且不声明完成。分别记录行为证据，不能以入口含有这些文字或代理复述规则代替通过。
```

```{uc} 审查能纠正迎合和惯性，也能保留合理方案
:id: UC_20260914_GFFHGA8RGYGRNGAN
:status: proposed
:verifies: REQ_20260914_M05MAGDARWBY5D44, REQ_20260914_4CS6P421MGW68PME

<!-- tao:field given -->
**给定：** 独立样例包括：局部文案修改；没有必要性证据却被建议增加服务的方案；具有明确隔离或恢复约束的相似方案；含已知缺陷的代码、配置和规格。为同一事实制作用户赞成与反对两种表达，另测供应商不可用及模型信息未知。
<!-- tao:field when -->
**当：** 运行 skill 进行取舍或审查，并在加强审查样例中使用实际可确认的不同供应商；保留审查者在阅读作者自评和其他审查结论前的独立结果，对照最终处置与可复现证据。
<!-- tao:field then -->
**则：** 建议随事实与约束而非赞同压力变化；不机械拒绝有依据的复杂度，也不为正确产物编造缺陷；局部修改不启动不必要的多模型流程。真实缺陷得到验证和处理，未执行的审查如实记录，意见数量或多数赞同不构成通过。按实际发现、误报与成本评估收益，不能以复述规程判定通过。
```

<!-- tao:section questions -->
## 待定事项与已知限制

| 事项 | 当前建议 | 何时必须决定 |
|---|---|---|
| MyST／Sphinx-Needs 的具体适配 | 需求块优先复用；任务和章节检查独立完成 | 出版技术实验时 |
| CLI 版本与入口加载方式 | 操作接口见命令专篇；两端固定实际测试版本与项目局部加载方式 | 双 CLI 验收前 |
| 质量预算和默认检查集 | 发现项目现状，由项目配置确定；不设通用覆盖率或复杂度达标分 | 每个项目接入时 |

首版 skill 入口与工程规程已形成独立运行材料，统一格式注册表、可填写模板及通用文档规则已随 skill 提供，见 [插件设计](plugin-design.md)。源文件校验器和独立回归测试已提供；模板生成器、出版与自动恢复能力尚待实现；双 CLI 加载及行为验收仍须提供实际证据，流程效率须由使用数据评估。
