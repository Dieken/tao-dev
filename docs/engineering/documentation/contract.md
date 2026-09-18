---
schema: tao.project.design/v0.1
id: DOC_20260914_P1G9T0KSCC0FTBM1
title: Markdown 文档契约
locale: zh-Hans
status: draft
created: '2026-09-14'
updated: "2026-09-18"
spec_docs: ["DOC_20260914_4C7N0XHQSP7CY69P"]
---

# Markdown 文档契约

本文是 tao-dev 的内部文档格式设计，供维护者实现解析器、schema、诊断和模板时使用；不属于分发给第三方项目的 skill 文档。面向使用方的统一格式、机器可读注册表与模板已经随 skill 提供，源文件 AST 校验器、回归测试、核心工作流 CLI 与本地 HTML 出版集成已提供；实际支持范围见 [工具规程](../../../plugins/tao-dev/skills/tao-dev/references/tools.md)。目标是兼顾 Markdown 的可读性与结构、标识符、关系的可检查性。

<!-- tao:section overview -->
## 适用范围

本文定义共享 profile 在本仓库的应用与解析器实现边界；术语含义见 [术语与缩写](../../glossary.md)，文件职责与拆分规则见 [文档组织与产物保存](layout.md)。本项目的交付文档与第三方使用方均采用 [文档规程](../../../plugins/tao-dev/skills/tao-dev/references/documents.md) 与 [格式注册表](../../../plugins/tao-dev/skills/tao-dev/assets/document-profiles.json) 中的 `tao.project.*` profile。格式由 tao-dev 定义，项目可映射目录、选择语言，并通过项目开发约定覆盖文档拆分阈值；不得要求使用方复制本项目的章节结构、研发任务或设计记录。运行组件的 manifest、SKILL.md、agent、command 和 hook 使用各自公共标准或平台格式，不套用正文 profile。

### 公共依据与采用范围

| 内容 | 采用的依据 | 在 tao-dev 中如何使用 |
|---|---|---|
| 行为需求 | [EARS 作者说明](https://alistairmavin.com/ears/) | REQ 正文默认使用下述条件化句式；不把 EARS 扩大为文件组织标准 |
| 验收场景 | [Gherkin 的 Given／When／Then](https://cucumber.io/docs/gherkin/reference/) | UC 按前置条件、动作、可观察结果编写；MyST 中的 UC 不是可直接执行的 .feature 文件 |
| 架构决策 | [Nygard ADR](https://www.cognitect.com/blog/2011/11/15/documenting-architecture-decisions) | 沿用标题、状态、context、decision、consequences；使用全局 ID，保留替代关系 |
| 系统设计 | [arc42](https://arc42.org/overview/) | 按需覆盖边界、约束、结构、运行与部署、质量和风险；用既有 profile 的章节或子节承载，不强制复制整套目录 |
| 面向使用者的文档 | [Diátaxis](https://diataxis.fr/) | 区分教程、操作指南、参考、解释的阅读目的；按目的组织页面，避免同页混写学习教程与故障操作步骤 |

EARS 是受约束的自然语言写法，ADR、arc42、Diátaxis 是文档实践或框架；不能统一声称它们是正式认证标准。tao 的 profile、章节标记、全局 ID、关系字段和 JSONL 退役记录是本项目补充。MyST 承载正文，YAML 承载元数据，GFM 提供 checkbox 写法；这些公开语法并不自动认可 tao 的附加字段或渲染指令。


面向消费项目的写法见 [正文写法](../../../plugins/tao-dev/skills/tao-dev/references/document-content.md)。

<!-- tao:section architecture -->
## 解析与索引

正式引用语法由文档规程定义。DOC、条目与章节的锚点、固定入口、移动和退役规则、实际 HTML 验收统一见 [出版规程](../../../plugins/tao-dev/skills/tao-dev/references/publication.md)。本项目的 Sphinx 适配实现须满足该契约，不能从源文件含有 ID 推导发布链接已经可用。

本项目开发文档的文件链接使用项目内相对路径，解析后须位于 tao-dev 项目范围内；不使用本机绝对路径、`file://` 地址或指向项目外文件的相对路径。外部资料使用公开上游链接；非公开材料不记录其标题、路径或条款编号，采用的原则应独立表述。文档应能随项目独立迁移，无须读者具备作者的研究目录。

构建顺序为：解析全部纳入文档 → 注册定义 → 解析引用 → 检查类型与关系 → 输出诊断和索引。AST 必须区分顶层正式条目与代码示例；正文里提到一个 ID 不是新的定义。

本仓库 docs/ 下的 Markdown 使用同一份共享格式注册表并纳入全局检查。运行参考、模板、README 与客户端配置使用各自格式，不纳入正文 profile。外部资料不成为本项目正式定义；没有显式导入索引的外部条目引用报告 unresolved。

### Markdown 管理边界

按内容职责接入，不能通过另建 reviews/、reports/ 或移动目录使正式结论逃离校验。正式审查报告和裁决复用 evidence profile；[独立报告模板](../../../plugins/tao-dev/skills/tao-dev/assets/templates/review.md) 由审查者或整理者读取，[主审裁决模板](../../../plugins/tao-dev/skills/tao-dev/assets/templates/review-adjudication.md) 由裁决作者读取。两者注册为同一 profile 的写作变体，沿用解析器与出版器，无新增审查实体。审查者来源、发现及处置由写作规程要求，schema 检查既有 evidence 字段和章节，不验证来源真实性或语义完整性。JSON 审查回执、调度状态与 Markdown 报告职责不同，登记成功不代表报告格式有效。

evidence.result 接受 unknown，表达原材料未记载或无法确定的总体结论；保留所有旧值及五个固定二级章节。结果、覆盖与记录时间语义统一见 [正文写法](../../../plugins/tao-dev/skills/tao-dev/references/document-content.md)，不改写历史结果以适配模板。该扩充由注册表驱动，未改变 JSON 审查回执的契约与门槛；未知结论的报告不满足必需审查。旧版本校验器可能拒绝新枚举，消费项目使用 unknown 前须更新对应包。

审查批次目录、slug 与 00／NN 文件名由 [文档组织](../../../plugins/tao-dev/skills/tao-dev/references/document-layout.md) 约束；编号不替代导航顺序，当前源校验器不校验该命名模式。[报告组织规程](../../../plugins/tao-dev/skills/tao-dev/references/review.md) 说明两种模板的填写方式与内容职责；schema、引用检查及 HTML 回归分别验证结构和发布能力，不验证判断依据是否完整。skill 指导按规范生成文档，不提供外部报告迁移流程。

| Markdown 内容 | 管理方式 |
|---|---|
| 产品、设计、决定、计划、任务、交接、术语、操作说明、导航 | docs/ 内使用对应共享 profile |
| 正式测试摘要、审查报告、裁决、需要保留的调查结论 | 按职责放入计划 verification 或独立 evidence；不能用普通 Markdown 绕过 schema |
| skill 入口、运行参考、agent 与 command | 供客户端或 LLM 读取，遵循各自格式；检查分发和链接，不注册为项目交付文档 |
| 模板与条目片段 | 填写前含变量，作为输入资源；生成文档后按 profile 校验 |
| README 与客户端开发指令 | 入口及开发约定，检查链接，不套交付 profile；不在其中持续存放正式审查结论 |
| 临时原始输出、测试夹具、外部历史资料 | 明确范围外；不得计入正式文档覆盖或直接冒充交付结论 |

源校验器在 AST 正文中提示未链接的完整 ID 和独立代码片段中的 Markdown 路径，使用 TAO-REF-005／TAO-LINK-002 warning。已解析的 TASK 定义和关系字段、链接显示文字及围栏代码不重复提示；不从裸文字自动建立关系。该检查是引用意图的提示，不能可靠识别缩写、普通文本中的任意路径或所有语义引用；内容审查及实际 HTML 链接核验仍必需。

退役数据由独立 JSONL 读取层按格式注册表中的 retirement_records 契约提取，再与 Markdown 定义合并检查；docs/retired/ 的全部日期文件都参与索引，不以 Sphinx 导航或当前修改日期决定范围。该目录只在产生实际退役记录时建立，不预写示例作为正式数据；读取器与跨文件一致性由回归测试验收。

一条关系只维护其发出方：反向引用、需求覆盖表和汇总由索引生成，生成文件不得成为另一份人工维护的真相。检查目标存在、关系类型、任务依赖无环和替代关系无环。标为 superseded 的对象必须能找到至少一个替代者；引用 retired／superseded 对象给出复查提示，合法的历史解释不必全部阻断。

出版层复用 taolib 的源文档索引，以同一份定义和关系生成条目引用、稳定锚点及 refs/ 解析页。PDF 和第三方编辑器表现不由 HTML 构建结果推导。

出版适配将源文的章节键与条目定义转换为 MyST 显式目标或等价 AST 节点；已有显式标签须校验一致，避免重复注入。仅设置 html_permalinks 不足以保证复制稳定链接，需要实际检查主题行为。实现依据见 [MyST 显式目标](https://myst-parser.readthedocs.io/en/latest/syntax/cross-referencing.html#creating-explicit-targets) 与 [Sphinx 永久链接](https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-html_permalinks)。这些实现选择供 tao-dev 开发维护使用；使用方只需读取 skill 中的链接与出版结果规程。

### 类型化文档关系

规格是行为依据，设计通过 spec_docs 关联规格，计划通过 spec_docs/design_docs 关联本次依据，任务内嵌或由 tasks_doc 唯一指定。字段、目标类型及数组约束以分发注册表为准；正文的一般链接不自动推断成依据。每条关系只维护正向定义，出版层据此生成类型与标题链接及反向入口，不把目录树当作业务依赖图。

源校验允许关系尚未补齐的草稿；阶段批准要求相应字段存在并覆盖工作流已确认的上游文档。计划批准摘要还包含独立任务附件的契约，任务说明或依赖变化会使批准过期，完成勾选和执行证据本身不改变契约。

项目受控词汇沿用 glossary profile，以有定义的 term 条目约束首选名称、可选代码名称、范围及不建议用词；不新增条目 ID 或全仓词语禁令。只收录有歧义或反复误用的跨文档概念。

<!-- tao:section contracts -->
## 结构与条目

### 元数据与章节

所有开发正文采用同包注册表中的 tao.project.* profile。元数据、稳定章节键和字段语法不另设仓库例外。需求与用例放入规格，设计决定放入设计文档，研发任务放入实施计划；一级标题前的元数据与正文匹配，补充层级从三级标题开始。

### 正式条目

REQ／UC／ADR 的选项、字段键、状态、关系及片段模板采用文档规程；正文保持自然语言，结构检查不根据中文或英文显示标签推断语义。REQ 的条件与验收、UC 的场景或性质、ADR 的备选与后果要求同样适用于内部条目。

CHG、EVD 由相应 profile 的 frontmatter 字段定义；DOC 与正文条目是不同对象。

### 任务与证据

正式任务采用文档规程的扁平 checkbox、完整 TASK ID、relates、depends_on、verify 和完成时必需的 evidence。任务位于 change 或 tasks profile 的 tasks 章节；显示顺序服务阅读，执行顺序由依赖关系决定。

任务证据默认链接计划 verification 章节的简短记录，需要独立保存时再用 evidence profile 或实际报告，不因链接存在而推导验收满足。检查器分别处理历史结果、原始材料可用性及当前复用资格，不因日志过期回写历史任务状态；日期、任务勾选和模型总结都不能代替实际检查。

<!-- tao:section invariants -->
## 全局标识符

正式 ID 使用 `类型_YYYYMMDD_16位随机串`；完整正则、日历校验、80 位安全随机数据编码、分配与退役规则由文档规程及格式注册表权威定义，内部自举采用相同规则。移动、翻译或修改标题不重编 ID。

此自定义格式不是标准 ULID；三字母类型前缀的完整 ID 长 29 字符，TASK 长 30 字符。格式借鉴 [ULID 规范](https://github.com/ulid/spec#specification) 的 Crockford Base32 字符集与随机长度，采用可直接阅读的本地日期，属于本项目格式。分配器从安全随机源取 10 字节，按大端编码并保留前导零；每位使用完整字符集，不套用 ULID 首位限制。结合当前定义和退役索引检查完整 ID 碰撞，最多生成三个候选，仍冲突则失败。它无需跨仓库编号服务；同日期同类型的百万次独立均匀随机分配，碰撞概率约为 `4.1 × 10^-13`，仍须查重并发现复制错误。日期是分配日线索，不表示修改时刻或内容版本。

<!-- tao:section errors -->
## 诊断与修正

诊断结果同时面向终端阅读与机器消费。JSON 记录至少包含 `rule_id`、`severity`、`path`、`line`、`message`、`suggestion`、`message_locale`，可选 `column`、`entity_id`、`related_locations`、`parameters`。行列从 1 开始，重复定义同时报告两个位置；字符列按 Unicode 码点计数。

| 规则号 | 默认级别 | 诊断与建议 |
|---|---|---|
| TAO-DOC-001 | error | 元数据非法／缺失／版本不支持；说明字段或所需版本 |
| TAO-DOC-002 | error | 必需章节缺失、顺序错误或键重复；给出期望结构 |
| TAO-ID-001 | error | ID 格式或对象类型错误；定位创建处，不擅自重写所有引用 |
| TAO-ID-002 | error | 重复定义；要求判断是误复制还是新对象 |
| TAO-ID-003 | error | 与基线相比正式条目被删除但无退役记录；恢复定义或登记退役 |
| TAO-LINK-001 | error | 构建后稳定锚点、复制链接或旧入口不可解析；修复出版映射 |
| TAO-REF-001 | error | 引用目标无法解析；提示检查拼写、索引范围或导入 |
| TAO-REF-002 | error | 关系目标类型不符或依赖／替代成环；输出路径 |
| TAO-ENTITY-001 | error | 条目字段或必需标记段非法、缺失、空白；ADR 缺少加粗标签、冒号或非空说明时定位对应字段 |
| TAO-TASK-001 | error | 任务格式、字段或完成证据入口不符合约定 |
| TAO-QUALITY-001 | warning | 可疑占位符、空泛验收或未决项；要求结合语境复查 |
| TAO-REF-003 | warning | 引用已废弃或已替代条目；提示新目标或说明历史用途 |
| TAO-REF-004 | error | 纳入管理的文档文件链接使用本机绝对地址或越出项目范围；改用项目内相对路径或公开上游链接 |

上述规则号稳定，措辞可以改善。输入语法损坏时先报告根错误，抑制由它引起的大量误报。退出码：`0` 无 error（可含 warning），`1` 有文档 error，`2` 工具或配置故障、检查未完成。发布就绪检查另评阻断问题，不能与格式退出码混为一谈。


错误传播先保留根诊断，抑制派生误报；消费项目的修正方法见 [文档规程](../../../plugins/tao-dev/skills/tao-dev/references/documents.md)。

<!-- tao:section verification -->
## 验证与演进

### 本地化与使用方语言

项目自身的语言取舍见 {need}`ADR_20260914_WX7BFBRXENPN4CT7`。使用方的语言选择、稳定键、显示资源、诊断回退和翻译源一致性统一见 [本地化](../../../plugins/tao-dev/skills/tao-dev/references/localization.md)。实现需使用同一套结构和按 locale 选择的资源，不能要求使用方复制本项目的中文正文。

启动层与核心读取同一份诊断翻译资源，无需为本地化安装依赖。英文完整消息模板保留在调用处，动态值单独传入；翻译占位参数必须与原消息一致。hook 缓存绑定翻译资源，避免翻译更新后继续返回旧消息。

翻译资源的出版适配优先验证 Sphinx gettext 目录或等价机制；源版本、审校状态与过期检测是需验证的实现能力。该技术选型留在本项目设计中，不作为使用方 agent 的操作指令。

诊断回退的 JSON 协议保留 requested_locale、实际 message_locale、locale_fallback、suggestion_locale 与未翻译 parameters；位置、规则号、退出码和结果不因语言改变。无有效源或无配置的启动错误使用英文，未知外部解析消息保留原文并标记回退。中文质量检查不能套用英文空格计词规则。

### 校验与升级

新增 profile 或结构字段时，同时修改注册表、运行规程、模板和独立验证夹具。运行调用方读取同包契约，不从开发文档动态推断格式。

实现时先用现有 Markdown 解析器获取 AST 与源码位置，再提取元数据、章节、条目与任务，输出归一化数据。格式注册表提供字段类型和枚举，结构规则检查 Markdown 布局，关系检查负责跨文件一致性。不用一组全文正则冒充 Markdown 解析器。

正式校验器必须使用包含损坏样例的独立测试集，覆盖围栏嵌套、示例 ID、中文、移动条目和未知版本等边界；普通 Markdown 链接列表不得误判为任务。i18n 反例包括：翻译标签不改变提取结果、结构键丢失在两种语言下报同一规则、翻译占位符丢失、源文变更后译文过期，以及非 ASCII 路径与字符定位。解析本项目文档只是验收的一部分。

契约版本变更需要说明哪些源文档受影响；迁移先产生差异，保留 ID、人工决定与原文件恢复路径。检查器应明确支持的版本，不静默将旧文档按新规则解释。校验器与规则同时修改时，旧版本行为和反例预期须独立审查。

本契约的需求依据为 {need}`REQ_20260914_42AXMZ2KH2RAZ8M3`、{need}`REQ_20260914_5Y6CWDE3MFMKJXSB`；设计取舍见 {need}`ADR_20260914_HHVX7YB5AG7J3TMT`。实现的 schema 与模板通过追踪关系和测试保持一致，运行时不依赖本文。
