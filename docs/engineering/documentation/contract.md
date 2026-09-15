---
schema: tao.project.design/v0.1
id: DOC_20260914_P1G9T0KSCC0FTBM1
title: Markdown 文档契约
locale: zh-Hans
status: draft
created: '2026-09-14'
updated: "2026-09-15"
spec_docs: ["DOC_20260914_4C7N0XHQSP7CY69P"]
---

# Markdown 文档契约

本文是 tao-dev 的内部文档格式设计，供维护者实现解析器、schema、诊断和模板时使用；不属于分发给第三方项目的 skill 文档。面向使用方的统一格式、机器可读注册表与模板已经随 skill 提供，源文件 AST 校验器、回归测试、核心工作流 CLI 与本地 HTML 出版集成已提供；实际支持范围见 [工具规程](../../../plugins/tao-dev/skills/tao-dev/references/tools.md)。目标是兼顾 Markdown 的可读性与结构、标识符、关系的可检查性。

<!-- tao:section overview -->
## 适用范围

本文定义共享 profile 在本仓库的应用与解析器实现边界；术语含义见 [术语与缩写](../../glossary.md)，文件职责与拆分规则见 [文档组织与产物保存](layout.md)。本项目的交付文档与第三方使用方均采用 [文档规程](../../../plugins/tao-dev/skills/tao-dev/references/documents.md) 与 [格式注册表](../../../plugins/tao-dev/skills/tao-dev/assets/document-profiles.json) 中的 `tao.project.*` profile。格式由 tao-dev 定义，项目可映射目录、选择语言，并通过项目开发约定覆盖文档拆分阈值；不得要求使用方复制本项目的章节结构、研发任务或设计记录。运行组件的 manifest、SKILL.md、agent、command 和 hook 使用各自公共标准或平台格式，不套用正文 profile。

格式设计优先复用公共语法与成熟惯例，具体映射维护在 [公共依据与写法](../../../plugins/tao-dev/skills/tao-dev/references/document-standards.md)。EARS 约束 REQ 正文，验收方法留在 acceptance；保留现有模板变量与稳定结构键，不另建同义字段。格式解析与自然语言质量判断分别验收，不宣称符合完整 EARS、Gherkin 或 arc42 工具链。

检查分层、结论边界和修正规则统一见 [文档诊断规程](../../../plugins/tao-dev/skills/tao-dev/references/document-diagnostics.md)，本篇只维护实现设计。

<!-- tao:section architecture -->
## 解析与索引

正式引用语法由文档规程定义。DOC、条目与章节的锚点、固定入口、移动和退役规则、实际 HTML 验收统一见 [出版规程](../../../plugins/tao-dev/skills/tao-dev/references/publication.md)。本项目的 Sphinx 适配实现须满足该契约，不能从源文件含有 ID 推导发布链接已经可用。

本项目开发文档的文件链接使用项目内相对路径，解析后须位于 tao-dev 项目范围内；不使用本机绝对路径、`file://` 地址或指向项目外文件的相对路径。外部资料使用公开上游链接；非公开材料不记录其标题、路径或条款编号，采用的原则应独立表述。文档应能随项目独立迁移，无须读者具备作者的研究目录。

构建顺序为：解析全部纳入文档 → 注册定义 → 解析引用 → 检查类型与关系 → 输出诊断和索引。AST 必须区分顶层正式条目与代码示例；正文里提到一个 ID 不是新的定义。

本仓库 docs/ 下的 Markdown 使用同一份共享格式注册表并纳入全局检查。运行参考、模板、README 与客户端配置使用各自格式，不纳入正文 profile。外部资料不成为本项目正式定义；没有显式导入索引的外部条目引用报告 unresolved。

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

此自定义格式不是标准 ULID；三字母类型前缀的完整 ID 长 29 字符，TASK 长 30 字符。格式借鉴 [ULID 规范](https://github.com/ulid/spec#specification) 的 Crockford Base32 字符集与随机长度，采用可直接阅读的本地日期，属于本项目格式。它无需跨仓库编号服务；同日期同类型的百万次独立均匀随机分配，碰撞概率约为 `4.1 × 10^-13`，仍须查重并发现复制错误。日期是分配日线索，不表示修改时刻或内容版本。

<!-- tao:section errors -->
## 诊断与修正

诊断 JSON 字段、规则号、严重级别、退出码和修正边界统一见 [文档诊断规程](../../../plugins/tao-dev/skills/tao-dev/references/document-diagnostics.md)。CLI 的公共结果封装见 [命令设计](../cli-design.md)。实现按规则号与参数消费结果，界面文字可本地化；源文件校验器和 CLI 共享诊断实现。字符列按 Unicode 码点计数，编辑器采用 UTF-16 等定位方式时由适配层转换。

<!-- tao:section verification -->
## 验证与演进

### 本地化与使用方语言

项目自身的语言取舍见 {need}`ADR_20260914_WX7BFBRXENPN4CT7`。使用方的语言选择、稳定键、显示资源、诊断回退和翻译源一致性统一见 [本地化规程](../../../plugins/tao-dev/skills/tao-dev/references/localization.md)。实现需使用同一套结构和按 locale 选择的资源，不能要求使用方复制本项目的中文正文。

启动层与核心读取同一份诊断翻译资源，无需为本地化安装依赖。英文完整消息模板保留在调用处，动态值单独传入；翻译占位参数必须与原消息一致。hook 缓存绑定翻译资源，避免翻译更新后继续返回旧消息。

翻译资源的出版适配优先验证 Sphinx gettext 目录或等价机制；源版本、审校状态与过期检测是需验证的实现能力。该技术选型留在本项目设计中，不作为使用方 agent 的操作指令。

### 校验与升级

新增 profile 或结构字段时，同时修改注册表、运行规程、模板和独立验证夹具。运行调用方读取同包契约，不从开发文档动态推断格式。

实现时先用现有 Markdown 解析器获取 AST 与源码位置，再提取元数据、章节、条目与任务，输出归一化数据。格式注册表提供字段类型和枚举，结构规则检查 Markdown 布局，关系检查负责跨文件一致性。不用一组全文正则冒充 Markdown 解析器。

正式校验器必须使用包含损坏样例的独立测试集，覆盖围栏嵌套、示例 ID、中文、移动条目和未知版本等边界；普通 Markdown 链接列表不得误判为任务。i18n 反例包括：翻译标签不改变提取结果、结构键丢失在两种语言下报同一规则、翻译占位符丢失、源文变更后译文过期，以及非 ASCII 路径与字符定位。解析本项目文档只是验收的一部分。

契约版本变更需要说明哪些源文档受影响；迁移先产生差异，保留 ID、人工决定与原文件恢复路径。检查器应明确支持的版本，不静默将旧文档按新规则解释。校验器与规则同时修改时，旧版本行为和反例预期须独立审查。

本契约的需求依据为 {need}`REQ_20260914_42AXMZ2KH2RAZ8M3`、{need}`REQ_20260914_5Y6CWDE3MFMKJXSB`；设计取舍见 {need}`ADR_20260914_HHVX7YB5AG7J3TMT`。实现的 schema 与模板通过追踪关系和测试保持一致，运行时不依赖本文。
