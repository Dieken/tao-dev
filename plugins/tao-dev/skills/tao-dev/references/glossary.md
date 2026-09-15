# 术语、ID 前缀与缩写

理解文档类型、标识符或审查术语时查阅本文。这里定义 tao-dev 的通用词汇；使用方的领域术语由项目术语表维护，精确语法见 [文档规程](documents.md)。

## 概念

| 用语 | 英文 | 在 tao-dev 中的含义 |
|---|---|---|
| 标识符、ID | Identifier | 指向某个对象的固定值。正文可简称“标识”；不用“身份”或“标志”指代 ID，标志通常用于 flag 等状态表示 |
| 对象同一性 | Identity | 编辑前后是否仍是同一个对象。ID 表达这种连续性；认证中的“身份”是另一概念 |
| 条目 | Entity | 可独立引用的需求、用例、决策、任务等对象；普通段落不自动成为条目 |
| 规格 | Specification / spec | 系统承诺的行为、约束与验收条件；回答“做什么、如何判断满足” |
| 设计 | Design | 为满足规格选择的结构、契约、状态与机制，以及选择理由 |
| 变更计划 | Change plan / plan | 一次开发事项的规格与设计引用、执行安排和验证入口；不复制长期规格 |
| 篇、章 | Part / chapter | 篇按读者与职责分组，章按能力、子系统或操作主题分组；章可以是一页，也可以由目录页组织多页，不另设条目类型 |
| 目录页 | Navigation page | 维护一组内容的导读与显式阅读顺序，使用 DOC ID；页内章节仍按各文档 profile 组织 |
| 任务 | Task | 一个可独立验证结果的工作单元；任务列表是计划的一部分，不默认另建文档 |
| 验证、验收 | Verification / acceptance | 前者检查约束和行为；后者按约定判定交付是否满足需求。可包含工具检查和人工判断，不代表把测试交给用户 |
| 产物、证据 | Artifact / evidence | 产物包括编写的文档、代码及执行或构建生成的文件；只有绑定输入、条件和结果并可复核的记录才构成证据 |
| 文档契约、文档类型 | Schema / profile | schema 约束结构与关系；profile 为某类文档选择必需字段、章节和条目 |
| 文件头元数据 | Frontmatter | Markdown 开头的结构化元数据；tao-dev 使用 YAML，不把所有正文都转成 YAML |
| 锚点、永久链接 | Anchor / permalink | 锚点定位页面内对象；永久链接还需保持或解析页面地址，只有稳定锚点不足以抵抗文件移动 |
| Crockford Base32 | Crockford Base32 encoding | 使用 32 字符的编码；tao-dev 将 80 位安全随机数据编码为 16 个大写字符，具体字符集见文档规程 |
| 本地化 | Localization | 按语言与地区约定呈现文字、日期等；机器协议不随显示语言改变 |
| 斜杠命令 | Slash command | agent 客户端中以 `/` 进入的交互操作，不是终端中的 `tao` 命令；包装层表示实现职责，不是命令类型 |
| 钩子 | Hook | 客户端事件触发的处理器；用于短小的确定性动作，不替代完整流程或授权 |
| 退役记录 | Tombstone | 对已移除的正式条目保留最小标识、原因及替代关系，避免复用或悬空引用；不保留无用正文 |
| 弃用 | Deprecation | 不建议继续使用并可能安排迁移，仍可能保持原有行为；不等同于已移除正文或退出有效集合的退役 |
| 独立审查 | Independent review | 使用独立判断过程检查原始材料；新会话可以隔离上下文，但不保证模型或错误来源独立 |
| 对抗式审查 | Adversarial review | 主动尝试用具体反例否定假设和设计，检查能否减去不必要机制；不是必须反对、挑错或进行安全攻击 |
| 跨模型／跨供应商审查 | Cross-model / cross-provider review | 前者使用不同模型，后者进一步选择不同模型供应商；CLI 名称或角色名称不能证明实际差异 |
| 迎合性 | Sycophancy | 因用户或作者的偏好压力改变判断、弱化证据，而非依据事实和约束调整结论 |

## ID 类型前缀

完整 ID 采用 tao-dev 的 `类型_YYYYMMDD_16位随机串` 格式；类型前缀表示用途，日期表示首次分配日，随机串使用 Crockford Base32 字符集。完整格式与生命周期见 [文档规程](documents.md)。一个文件和文件中的条目是不同对象，例如文档有 DOC ID，其中的决策另有 ADR ID。

| 前缀 | 对应英文 | 表达什么、用在哪里 |
|---|---|---|
| DOC | Document | 文档本身，用于元数据、文档引用和稳定章节定位 |
| REQ | Requirement | 一个可验收的需求，用例和任务可关联它 |
| UC | Use Case | 一个使用或验收场景；本协议用 Given／When／Then 表述并以 `verifies` 关联需求 |
| ADR | Architecture Decision Record | 有长期价值的架构或技术决策，记录背景、备选、决定和后果 |
| TASK | Task | 可验证的工作单元，表达依赖和完成证据；不表示已发布 |
| CHG | Change | 一次变更的逻辑对象，聚合意图、相关条目及任务；不同于承载它的 DOC |
| EVD | Evidence | 一份验证证据记录，关联受检输入、检查条件和结果；不等于报告文件名 |

所有前缀已有格式定义与相应模板；模板存在不代表已有可运行的生成器。

## 缩写

| 缩写 | 全称 | 用途或边界 |
|---|---|---|
| UUID | Universally Unique Identifier | 通用唯一标识符；设计比较中的备选，tao-dev 使用可读日期加随机串 |
| ULID | Universally Unique Lexicographically Sortable Identifier | 含编码时间与随机部分的标识符；tao-dev 借鉴其字符集与随机长度，不采用其完整格式 |
| SDD | Spec-Driven Development | 此处指“规格驱动开发”；不是另一些资料中的 Source-Driven Development（按来源核实技术用法） |
| VCS | Version Control System | 版本控制系统；当前完整开发流程依赖 Git，文档校验等独立能力不要求 Git |
| CLI | Command-Line Interface | 命令行接口；区分 tao 工具与 Claude Code／Codex 客户端 |
| CI | Continuous Integration | 持续集成；执行必要检查，不以流水线全绿代替需求验收 |
| AST | Abstract Syntax Tree | 抽象语法树；识别正式条目与围栏示例，避免全文搜索误判 |
| i18n / l10n | Internationalization / Localization | 国际化是让系统支持多语言的设计，本地化是某种语言及地区的具体呈现 |
| EARS | Easy Approach to Requirements Syntax | 用条件、事件、系统主体与可观察结果约束需求表达；可按项目语言书写，不把关键词检查当作语义验收 |
| RFC | Request for Comments | 标准与技术文档系列；精确时间戳格式参考 RFC 3339 |
| BCP | Best Current Practice | 最佳当前实践文档系列；BCP 47 用于语言标签 |
| GFM | GitHub Flavored Markdown | Markdown 方言；此处借用任务列表语法，不要求使用 GitHub 或 Git |
| MCP | Model Context Protocol | 工具和资源接入协议；初版没有引入 MCP 服务的必要 |

## 使用规则

关键术语首次出现时给出中文和英文；后续使用统一简称。新增影响需求或接口理解的术语先补充定义，普通英文单词不必收录。机器字段如 `id`、`locale` 保持原名，显示文字使用本地化标签。

术语表定义含义，精确语法以文档规程为准；避免在多个文件重复维护正则、枚举和完整字段表。
