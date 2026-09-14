---
schema: tao.glossary/v0.2
id: DOC_CF3029642DDF4DEB9FC229C49E216F86
title: 术语与缩写
locale: zh-Hans
status: draft
created: "2026-09-14"
bootstrap: manual
---

# 术语与缩写

本文统一 tao-dev 开发文档的用语。它不是运行时依赖；使用方的领域术语由其项目自己维护。

<!-- tao:section terms -->
## 一、概念与中文用语

| 用语 | 英文 | 本项目中的含义 |
|---|---|---|
| 标识符、ID | Identifier | 指向某个对象的固定值。正文可简称“标识”；不用“标志”指代 ID，标志通常用于 flag 等状态表示 |
| 对象同一性 | Identity | 编辑前后是否仍是同一个对象。ID 表达这种连续性；认证中的“身份”是另一概念 |
| 条目 | Entity | 可独立引用的需求、用例、决策、任务等对象；普通段落不自动成为条目 |
| 规格 | Specification / spec | 系统承诺的行为、约束与验收条件；回答“做什么、如何判断满足” |
| 设计 | Design | 为满足规格选择的结构、契约、状态与机制，以及选择理由 |
| 变更计划 | Change plan / plan | 一次变更的目标引用、必要设计、执行安排与验证入口；不复制长期规格 |
| 任务 | Task | 一个可独立验证结果的工作单元；任务列表是计划的一部分，不默认另建文档 |
| 验证、验收 | Verification / acceptance | 前者检查约束和行为；后者按约定判定交付是否满足需求。可包含工具检查和人工判断，不代表把测试交给用户 |
| 产物、证据 | Artifact / evidence | 产物是执行或构建生成的文件；只有绑定输入、条件和结果并可复核的记录才构成证据 |
| 文档契约、文档类型 | Schema / profile | schema 约束结构与关系；profile 为某类文档选择必需字段、章节和条目 |
| 文件头元数据 | Frontmatter | Markdown 开头的结构化元数据；本项目使用 YAML，不把所有正文都转成 YAML |
| 锚点、永久链接 | Anchor / permalink | 锚点定位页面内对象；永久链接还需保持或解析页面地址，只有稳定锚点不足以抵抗文件移动 |
| 本地化 | Localization | 按语言与地区约定呈现文字、日期等；机器协议不随显示语言改变 |
| 斜杠命令 | Slash command | agent 客户端中以 `/` 进入的交互操作，不是终端中的 `tao` 命令；包装层表示实现职责，不是命令类型 |
| 钩子 | Hook | 客户端事件触发的处理器；用于短小的确定性动作，不替代完整流程或授权 |
| 退役记录 | Tombstone | 对已移除的正式条目保留最小标识、原因及替代关系，避免复用或悬空引用；不保留无用正文 |
| 独立审查 | Independent review | 使用独立判断过程检查原始材料；新会话可以隔离上下文，但不保证模型或错误来源独立 |
| 对抗式审查 | Adversarial review | 主动尝试用具体反例否定假设和设计，检查能否减去不必要机制；不是必须反对、挑错或进行安全攻击 |
| 跨模型／跨供应商审查 | Cross-model / cross-provider review | 前者使用不同模型，后者进一步选择不同模型供应商；CLI 名称或角色名称不能证明实际差异 |
| 迎合性 | Sycophancy | 因用户或作者的偏好压力改变判断、弱化证据，而非依据事实和约束调整结论 |

<!-- tao:section prefixes -->
## 二、ID 类型前缀

前缀是 tao-dev 的类型约定，不是 UUID 标准的一部分。完整格式与生命周期见 [文档契约](document-contract.md)。一个文件和文件中的条目是不同对象，例如文档有 DOC ID，其中的决策另有 ADR ID。

| 前缀 | 对应英文 | 表达什么、用在哪里 |
|---|---|---|
| DOC | Document | 文档本身，用于元数据、文档引用和稳定章节定位 |
| REQ | Requirement | 一个可验收的需求，用例和任务可关联它 |
| UC | Use Case | 一个使用或验收场景；本协议用 Given／When／Then 表述并以 `verifies` 关联需求 |
| ADR | Architecture Decision Record | 有长期价值的架构或技术决策，记录背景、备选、决定和后果 |
| TASK | Task | 可验证的工作单元，表达依赖和完成证据；不表示已发布 |
| CHG | Change | 一次变更的逻辑对象，聚合意图、相关条目及任务；不同于承载它的 DOC |
| EVD | Evidence | 一份验证证据记录，关联受检输入、检查条件和结果；不等于报告文件名 |

DOC、REQ、UC、ADR、TASK 已有自举语法；CHG、EVD 的产品模板仍待实现。预留前缀不代表已有可运行的生成器。

<!-- tao:section abbreviations -->
## 三、其他缩写

| 缩写 | 全称 | 用途或边界 |
|---|---|---|
| UUID | Universally Unique Identifier | 通用唯一标识符；本项目采用 v4，随机生成且不编码创建日期 |
| SDD | Spec-Driven Development | 本项目指“规格驱动开发”；不是另一些资料中的 Source-Driven Development（按来源核实技术用法） |
| VCS | Version Control System | 版本控制系统；通用流程不假定 Git。本项目自身选用 Git，因此开发提交约定仍使用 Git 专有术语 |
| CLI | Command-Line Interface | 命令行接口；区分 tao 工具与 Claude Code／Codex 客户端 |
| CI | Continuous Integration | 持续集成；执行必要检查，不以流水线全绿代替需求验收 |
| AST | Abstract Syntax Tree | 抽象语法树；识别正式条目与围栏示例，避免全文搜索误判 |
| i18n / l10n | Internationalization / Localization | 国际化是让系统支持多语言的设计，本地化是某种语言及地区的具体呈现 |
| RFC | Request for Comments | 标准与技术文档系列；UUID 依据 RFC 9562，日期格式参考 RFC 3339 |
| BCP | Best Current Practice | 最佳当前实践文档系列；BCP 47 用于语言标签 |
| GFM | GitHub Flavored Markdown | Markdown 方言；此处借用任务列表语法，不要求使用 GitHub 或 Git |
| MCP | Model Context Protocol | 工具和资源接入协议；初版没有引入 MCP 服务的必要 |

<!-- tao:section usage -->
## 四、使用规则

关键术语首次出现时给出中文和英文；后续使用统一简称。新增影响需求或接口理解的术语先补充定义，普通英文单词不必收录。机器字段如 `id`、`locale` 保持原名，显示文字使用本地化标签。

术语表定义含义，精确语法以文档契约为准；避免在多个文件重复维护正则、枚举和完整字段表。
