---
schema: tao.project.spec/v0.1
id: DOC_20260914_4C7N0XHQSP7CY69P
title: 项目文档与知识协议
locale: zh-Hans
status: draft
---

# 项目文档与知识协议

本文是 tao-dev 自身的需求规格，供开发与维护使用。实现与验收状态由对应记录说明；不作为第三方项目的运行 prompt 分发。

<!-- tao:section scope -->
## 目标与边界

**目标：让项目知识具有明确语义、唯一归属和可复核依据；换人、换会话或更换客户端后，仍能从持久计划与真实产物掌握项目进度。** 文档是工程工作的直接材料，不只是格式化记录；维护成本计入协作成本。

本项目提供文档生命周期指导、语义契约与模板、持久计划、确定性查询、检查和出版。agent 自行管理执行，把实际成果、阻碍与验证结果写回计划，把当前长期事实更新到规格、设计、ADR 和指南；产品不编排通用开发流程。

开发资料与分发产物分开管理。分发清单只包含文档与计划管理实际需要的入口、参考、模板和脚本，不包含本项目的需求设计、开发任务、通用工程规程和研究资料。验收分发包时，应在没有开发文档和本地研究目录的环境中检查资源引用与文档协作能力。

不建设通用项目管理平台，不绑定 issue 服务，不预装所有质量工具，不要求每次修改生成规格、设计、计划。通用实现、代码审查、恢复动作、自动发布、复杂调度、多仓库同步及双向 issue 同步不属于产品职责。Codex CLI 和 Claude Code CLI 保留真实行为验收目标，未经实际执行不声称通过。

本协议定义文档与项目知识管理的结果和验收场景。协作方式见 [知识架构](../engineering/protocol-design.md)，长期技术取舍见 [架构决定](../engineering/decisions/index.md)。同一承诺只定义一次，其他产物通过 ID 引用。

当前产品是项目级纯 skill，资源、模板和确定性工具见 [Skill 打包与运行依赖](../engineering/skill-design.md)。文档语义工作由 agent 完成，工具能力见 [工具规程](../../skills/tao-dev/references/tools.md)，项目边界见 [项目级文档驱动 skill](project-skill.md)。

出版适配采用 [现有 Sphinx 方案](../engineering/decisions/sphinx-publication.md)。客户端版本和加载方式按 [接入指南](../user/clients.md) 选择；测试、lint、构建及缓存由项目的 justfile、Makefile、manifest 或 CI 管理，不纳入 .tao/config.toml。tao 只校验文档并管理结果知识，文档配置见 [项目接入](../../skills/tao-dev/references/project-setup.md)。

<!-- tao:section terms -->
## 术语与来源

概念与缩写见 [术语表](../glossary.md)。

### 公共来源与采用边界

文档语义、计划成果和证据边界随 skill 分发；本仓库自身的通用工程原则留在 [开发指南](../engineering/development.md) 与项目 ADR，不作为使用方执行规程。以下公开参考用于解释设计来源，其开发阶段、审批规则和技术选择不自动成为产品要求。

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
| [Addy Osmani 的 agent-skills](https://github.com/addyosmani/agent-skills/tree/98967c45a42b88d6b8fb3a88b7ff6273920763d6/skills) | 文档记录理由、ADR 生命周期、按实际版本核实 API、端到端增量任务 | 不固定计划／任务双文件；不要求每段代码都添加来源注释 |
| [Matt Pocock 的 skills](https://github.com/mattpocock/skills/tree/e9fcdf95b402d360f90f1db8d776d5dd450f9234/skills) | `codebase-design` 的模块与接口词汇；`to-spec` 的复用已知上下文；`tdd` 的行为测试 | 不依赖 issue 发布、不重复访谈、不要求每个测试接口重新取得确认 |
| [Everything Claude Code](https://github.com/affaan-m/everything-claude-code/blob/ed387446052dfbc6b52de149406b70efa65edc59/skills/verification-loop/SKILL.md) | 分项执行并汇总构建、类型、测试等检查 | 不采用统一覆盖率门槛；保留原始退出码，不靠输出截断判断成功 |
| [gstack](https://github.com/garrytan/gstack/blob/a3259400a366593e0c909dd9ac3e59752efd2488/context-save/SKILL.md) | 保存与恢复当前目标、决定和剩余工作；检查客户端命令重名 | 不引入全局状态目录、自动遥测或修改用户全局安装 |
| [Oh My OpenAgent](https://github.com/code-yeongyu/oh-my-openagent/blob/dec381ed201a1326883db9f42bdb3c2add91b299/docs/guide/overview.md) | 区分协调与执行职责、按任务选择上下文 | 不把多模型协同执行和复杂常驻调度列为使用前提 |

外部依据：[Kiro 规格结构](https://kiro.dev/docs/specs/)、[EARS 需求表达](https://alistairmavin.com/ears/)、[ULID 规范](https://github.com/ulid/spec)、[arc42](https://arc42.org/overview/)、[Diátaxis](https://diataxis.fr/)、[MyST 引用](https://myst-parser.readthedocs.io/en/latest/syntax/cross-referencing.html)、[Sphinx-Needs 配置](https://sphinx-needs.readthedocs.io/en/latest/configuration.html)、[BCP 47 语言标签说明](https://www.w3.org/International/articles/language-tags/index.en)、[Sphinx 国际化](https://www.sphinx-doc.org/en/master/usage/advanced/intl.html)。这些来源支持相关能力与组织思想，不表示本草案已符合某项完整行业标准。

外部引用采用上游公开地址；具体格式或行为依赖某一版本时应注明版本。文档格式与 ID 细节属于本项目设计。

独立审查的研究依据：[迎合性研究](https://arxiv.org/abs/2310.13548) 说明模型可能迎合用户观点；[多代理讨论研究](https://arxiv.org/abs/2305.14325) 在其推理与事实任务中观察到收益；[讨论机制与多样性研究](https://arxiv.org/abs/2601.19921) 表明收益依赖讨论机制和初始观点等条件。它们不证明跨供应商代码审查必然有效或错误相互独立。本项目据此采用有界、可复核的审查，并以真实缺陷、误报和成本检验效果，不以模型数量背书。

<!-- tao:section requirements -->
## 项目需求

以下条目是文档与知识管理的可验收需求。广泛共识仅指多个参考项目强调相同方向，不代表执行细节已成行业标准；参考中的通用工程方法仅为设计背景。

```{req} 按知识需要组织文档，保留人的决定权
:id: REQ_20260914_BFNMKT34JF1BSGW2
:status: proposed

根据影响、不可逆性和不确定性确定需要记录的目标、边界、验收和决定。复用现有权威材料，仅在有独立知识归属时新建规格、设计或 ADR；跨会话、协作或跟踪工作使用持久计划，不强制文档序列。执行由 agent 自行管理，文档记录不能冒充授权。

<!-- tao:field acceptance -->
**验收：** README 错字修改无需新建三件套；新目标可以复用已有规格与设计，成果任务可跨会话跟踪；未确认建议不写成已决定要求，工具输出不授予写入、发布或执行权限。

<!-- tao:field source -->
**来源：** BMAD、OpenSpec 的按需材料与用户的文档优先要求。产品采用知识职责区分，不采用阶段编排。
```

```{req} 信息只维护一处，阅读可按主题组合
:id: REQ_20260914_NN0AEQ2E1GTVSMTV
:status: proposed

规格、设计、ADR 与计划各有语义职责而非固定生成顺序，可复用适用的共享文档。任务默认内嵌计划，必要时唯一关联附件；同一版本中的条目只有一个正式定义。完成计划保留变更历史，当前事实更新长期知识。索引和反向引用由定义生成，不维护重复进度表。

<!-- tao:field acceptance -->
**验收：** 修改一个需求后不必同步抄写计划与追踪表；拆分文件仍能找到其任务、决策和验证关系。

<!-- tao:field source -->
**来源：** OpenSpec 的长期规格、Compound Engineering 的统一计划、BMAD 的紧凑变更文档。
```

```{req} 文档可以校验并给出可修正的诊断
:id: REQ_20260914_42AXMZ2KH2RAZ8M3
:status: proposed

tao-dev 随 skill 分发统一、版本化的文档契约、格式注册表和模板，校验元数据、必要语义章节、条目、ID、引用和任务基本格式；使用方无需自行定义 schema。章节顺序、数量与无关内容不形成形式门禁。检查区分结构错误、质量提示和语义审查意见，格式通过不能推断内容正确。

<!-- tao:field acceptance -->
**验收：** 独立分发包可读取中英文模板；重排可选章节不失败，重复 ID、悬空引用、导航环及无 verify 的任务能定位诊断。正向关系保持目标类型，语义需求覆盖由实际文档审查核对，而非审批或差异覆盖门禁。

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

记录验证对象、执行条件、结果和适用范围；受影响输入变化后不能把旧证据当作当前通过。区分任务成果、格式检查、行为检查、语义审查和交付；产品不自动认证完成，成本记录区分实测与估算。

<!-- tao:field acceptance -->
**验收：** 旧版本通过不能证明新改动完成；未运行、不可用与不适用均不能显示为通过。项目工具若复用检查，记录其实际执行时刻与输入范围，不因刷新摘要而变新；tao 不另建命令执行或缓存系统。任务全勾选不推断审查通过，审查未知保持未知；计划保存当前结果摘要，普通 review/evidence 详情默认临时，不自动注册、建档或提交。token 估算不能冒充账单。

<!-- tao:field source -->
**来源：** Superpowers、GSD、agent-skills 的证据要求（广泛共识）；成本分类与失效规则为本协议综合。
```

```{req} 项目知识与进度不绑定 agent 或 issue 平台
:id: REQ_20260914_95193C19C90NRXV4
:status: proposed

相同的文档契约、持久计划与确定性检查可通过项目内普通命令使用，不依赖客户端临时任务状态、issue 平台或专用扩展。安装只部署完整 skill。

<!-- tao:field acceptance -->
**验收：** 仅用项目内 skill 与可用工具即可管理文档并查询进度，无需 issue 账号；换客户端保留同一任务集，缺失检查能力明确报告，检查结果不附带发布权限。

<!-- tao:field source -->
**来源：** Trellis 的平台适配实践。
```

```{req} 文档可持续组织成书
:id: REQ_20260914_3JQXRKWXKAZSNJ5R
:status: proposed

从同一份源文档生成按产品、工程、用户和运维组织的阅读入口与索引；区分开发中状态、发布版本及历史变更。

<!-- tao:field acceptance -->
**验收：** 关联链接显示类型和目标标题，文档页提供自动生成的前向与反向关系；任务的需求及依赖链接可点击，ID 保持稳定。无需手工维护关联表即可形成主题导航和需求索引；发布文档能定位到对应版本；移除 skill 后源文件仍可阅读。

<!-- tao:field source -->
**来源：** arc42、Diátaxis、Sphinx 文档体系。
```

```{req} 持久计划支持恢复与协作
:id: REQ_20260914_6YZ1XE1GC369655H
:status: proposed

plan/tasks 是权威项目进度，任务描述可验证成果、依赖和验收方法；客户端任务只是临时步骤。agent 从计划与真实产物核对状态，按实际成果、阻碍及范围变化回写同一任务集和当前验证摘要。多人协作明确修改范围、共享契约与集成责任，不维护重复流程状态。

<!-- tao:field acceptance -->
**验收：** 临时摘要或客户端任务丢失后仍能定位未完成成果；status 只读明确项目，恢复时核对实际状态；多人协作的局部成果不冒充整体通过，任务全勾选不推断已验证、已审查或已交付。

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

```{req} 用实际项目检验文档协作
:id: REQ_20260914_4GKT5JRVBJNCQ05X
:status: proposed

本项目采用自己的文档语义与持久计划约定，用正常案例和反例检验校验器及 agent 文档行为，记录维护成本与发现的问题。

<!-- tao:field acceptance -->
**验收：** 覆盖小改动、普通功能、跨模块变更、需求变化、中断恢复及工具不可用；不能只靠本项目文档通过证明工具正确。

<!-- tao:field source -->
**来源：** 本项目的设计选择；自举与负向样例用于防止契约只在自身示例中成立。
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

```{req} 按共享 skill 结构打包并分层验收客户端
:id: REQ_20260914_BWAY1ZF6HNPM855Y
:status: proposed

发布物遵循 Agent Skills 的入口与资源组织，完整包由使用者复制到客户端项目发现目录，或由可选通用工具管理；tao 不提供安装适配。Codex 与 Claude Code 保留真实行为验收目标，Cursor 与 Kiro 同样记录项目发现路径；各层能力分别报告。

<!-- tao:field acceptance -->
**验收：** 同一包在隔离项目执行文件部署与移除，保护用户文件并验证项目外不受影响；实际客户端加载与行为另外验收，未运行不得标记兼容，不依赖开发文档或其他客户端配置。

<!-- tao:field source -->
**来源：** Agent Skills 与客户端官方项目技能文档；当前设计见 Skill 打包与运行依赖。
```

```{req} 文档语义指导独立于开发仓库可用
:id: REQ_20260914_4CS6P421MGW68PME
:status: proposed

分发的 skill 提供自包含的文档语义指导：需求说明条件、行为与可观察验收；设计解释边界、接口、不变量、失败与取舍；计划任务表达可验证成果；证据明确范围和限制。以使用方事实及现有约定为依据，不携带通用工程执行规程或代码审查动作。

<!-- tao:field acceptance -->
**验收：** 仅凭分发包即可维护和审查这些文档；结构完整但行为含糊、设计矛盾、任务不可验证的样例仍能得到具体语义发现。缺检查工具报告未运行，未实施方案不能记成当前事实。真实行为验收分别记录实际客户端结果，不以入口文字作为通过证明。

<!-- tao:field source -->
**来源：** 用户的文档优先要求与 EARS、arc42、ADR 的内容职责。复杂度控制、小步反馈和代码工程取舍保留为本仓库开发依据，不扩张为分发产品职责。
```

```{req} 语义审查独立判断并保留依据
:id: REQ_20260914_M05MAGDARWBY5D44
:status: proposed

对文档中的重要提议独立分析收益、代价、必要条件与可行替代，区分候选、确认决定与授权。语义审查核对需求、设计、任务和现行事实，明确矛盾、遗漏、过时知识及验证限制；发现以事实和契约为依据，不把建议增强自动列为阻断。本仓库可按风险选择独立审查，其模型与成本记录不成为产品通用编排要求。

<!-- tao:field acceptance -->
**验收：** 事实不变时，不因用户赞同或反对而无理由翻转判断；合理方案不被强制反对，不为正确文档编造缺陷。候选不冒充决定，格式通过不冒充语义通过；发现给出具体位置、依据、影响和必要修正。实际未执行或模型身份不可确认的审查保持未知，不以模型数量或多数票背书。

<!-- tao:field source -->
**来源：** 用户的独立判断要求及迎合性研究。多代理讨论研究保留为本仓库评估审查方式的背景，不构成分发包的多模型执行承诺。
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
**则：** agent 核对受检范围与实际文件后发现变化，记录旧结果不适用于当前输入，不能仅凭旧报告宣称任务完成；调用项目原生命令重新检查后记录新结果。tao 不自动对代码证据计算失效或认证完成。
```

```{uc} 翻译显示文本不改变机器含义
:id: UC_20260914_YSP9ZDA6ZNV2PMXF
:status: proposed
:verifies: REQ_20260914_GDY8F3KPE6XBGWGD, REQ_20260914_42AXMZ2KH2RAZ8M3

<!-- tao:field given -->
**给定：** 两份隔离的中英文模板样例使用相同的稳定章节键、条目 ID 和关系，仅 locale 与显示文字不同。
<!-- tao:field when -->
**当：** 分别检查并导出结构，切换诊断输出语言，再故意重复一个稳定章节键。
<!-- tao:field then -->
**则：** 正常样例的结构和标识符一致；重复键产生相同规则号与定位，消息随语言变化；未执行的语义检查显示未知，不伪装通过。
```

```{uc} 独立发布包在两种 CLI 中执行
:id: UC_20260914_6M8S2YF09JDJSWPV
:status: proposed
:verifies: REQ_20260914_BWAY1ZF6HNPM855Y, REQ_20260914_95193C19C90NRXV4

<!-- tao:field given -->
**给定：** 同一版本的纯 skill 包和两份隔离项目，无开发文档或客户端全局改动。
<!-- tao:field when -->
**当：** 分别在 Codex CLI 与 Claude Code CLI 从原生项目目录加载 skill，更新已有文档并查询或维护同一类持久成果计划。
<!-- tao:field then -->
**则：** 两端分别记录真实运行依据，共享契约一致且项目外不发现安装；缺失能力明确报告，不能用文件部署成功代替模型行为通过。
```

```{uc} 分发文档规程独立可用并识别语义问题
:id: UC_20260914_SZVA0530E14QCGQZ
:status: proposed
:verifies: REQ_20260914_4CS6P421MGW68PME, REQ_20260914_0J68SDKV86ENKER2

<!-- tao:field given -->
**给定：** 仅含分发包与项目文档的隔离环境。独立场景包含无需新文件的小修改、格式合法但行为和设计矛盾的材料、缺少检查工具的计划；包含中英文目标项目。
<!-- tao:field when -->
**当：** 在两端 CLI 中分别显式调用 skill，要求维护文档、核对语义与成果任务，并说明验证依据。
<!-- tao:field then -->
**则：** 保持项目语言与对象 ID；小修改复用权威材料，不生成无用三件套；语义问题有具体位置和依据，任务对应可验证成果；缺检查工具明确未验证且不推断交付。分别记录真实行为，不能以入口含有这些文字或代理复述规则代替通过。
```

```{uc} 审查能纠正迎合和惯性，也能保留合理方案
:id: UC_20260914_GFFHGA8RGYGRNGAN
:status: proposed
:verifies: REQ_20260914_M05MAGDARWBY5D44, REQ_20260914_4CS6P421MGW68PME

<!-- tao:field given -->
**给定：** 文档样例包括局部文案修改、没有必要性依据却增加组件的方案、有明确隔离约束的类似方案，以及含已知矛盾的规格、设计和任务。对同一事实分别给出用户赞成与反对的表达，并区分候选、决定与授权；另含未执行或身份未知的审查记录。
<!-- tao:field when -->
**当：** 运行文档语义审查，保留独立发现、位置、依据与最终处置，对照实际材料中的缺陷和约束。
<!-- tao:field then -->
**则：** 建议随事实与约束而非赞同压力变化；有依据的复杂度可保留，候选不冒充决定或授权，正确文档不被编造缺陷。真实矛盾得到定位与处理，未知审查不变为通过，格式成功和多数赞同均不构成语义正确证明；按发现、误报与成本评估效果。
```

<!-- tao:section questions -->
## 待确认事项

无。
