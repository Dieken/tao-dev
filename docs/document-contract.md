---
schema: tao.document-contract/v0.2
id: DOC_20260914_P1G9T0KSCC0FTBM1
title: Markdown 文档契约
locale: zh-Hans
status: draft
created: "2026-09-14"
bootstrap: manual
---

# Markdown 文档契约

本文是 tao-dev 的内部文档格式设计，供维护者实现解析器、schema、诊断和模板时使用；不属于分发给第三方项目的 skill 文档。本项目开发文档采用内部 profile 自举；面向使用方的统一格式、机器可读注册表与模板已经随 skill 提供，完整 AST 校验器仍待实现。目标是兼顾 Markdown 的可读性与结构、标识符、关系的可检查性。

<!-- tao:section scope -->
## 一、适用范围与检查层次

本契约定义下表列出的内部开发文档 profile；术语含义见 [术语与缩写](glossary.md)，文件职责与拆分规则见 [文档组织与产物保存](document-layout.md)。使用方采用随包 [文档规程](../plugins/tao-dev/skills/tao-dev/references/documents.md) 与 [格式注册表](../plugins/tao-dev/skills/tao-dev/assets/document-profiles.json) 中的 `tao.project.*` profile。格式由 tao-dev 定义，项目只映射目录、选择语言及配置允许的阈值；不得要求使用方复制本项目的章节结构、研发任务或设计记录。运行组件的 manifest、SKILL.md、agent、command 和 hook 使用各自公共标准或平台格式，不套用内部 profile。

| 层次 | 检查内容 | 结论边界 |
|---|---|---|
| 语法与结构 | 元数据、章节顺序、条目块、任务格式 | 可确定是否符合文档契约 |
| 标识符与关系 | 唯一性、引用目标、类型、依赖环、状态约束 | 可确定索引范围内的一致性 |
| 内容提示 | 空验收、占位符、未决项、模糊词等 | 提示复查；词语命中不等于需求无效 |
| 语义审查 | 是否解决真实问题、是否遗漏场景、设计是否承担合理成本 | 人或 AI 提供理由与证据，保留不确定性 |

普通正文只约束必要结构，不因字数或使用某个词自动判定低质量。章节必需不意味着必须填充无关内容；profile 应删去无用栏目，而非堆积“无／不适用”文字。

<!-- tao:section metadata -->
## 二、文档元数据与章节

通用元数据、日期、章节键、字段键与安全读取要求采用随包文档规程及格式注册表的共同部分。本节只定义开发文档差异，避免内部说明与执行规程各维护一套格式。

内部 v0.2 profile 使用共同必需字段 schema、id、title、locale、status、created 与可选 updated；另允许 `bootstrap: manual`，表示采用手工或临时检查，不豁免格式错误。该字段不出现在使用方 profile 或其模板中。内部 DOC、REQ、UC、ADR 与 TASK 的定义和引用仍参与自举索引。

当前 profile 的必需二级章节按下列顺序出现，不允许未声明的二级章节；扩充时显式修订 profile。补充解释可以放在现有章节的三级标题下。

| profile | 章节键顺序 |
|---|---|
| `tao.protocol/v0.2` | `purpose` → `requirements` → `workflow` → `artifacts` → `design` → `verification` → `bootstrap` → `open-questions` → `sources` |
| `tao.document-contract/v0.2` | `scope` → `metadata` → `identity` → `entities` → `references` → `tasks` → `diagnostics` → `evolution` |
| `tao.plugin-design/v0.2` | `scope` → `package` → `components` → `acceptance` → `sources` |
| `tao.glossary/v0.2` | `terms` → `prefixes` → `abbreviations` → `usage` |
| `tao.document-layout/v0.2` | `ownership` → `splitting` → `naming` → `artifacts` → `bootstrap` |
| `tao.cli-design/v0.2` | `scope` → `commands` → `contract` → `integration` → `acceptance` |

一级标题与第一处二级标题之间允许导语。章节匹配依据 AST 位置和键，不依据中文标题、行号或全文正则搜索。

<!-- tao:section identity -->
## 三、全局 ID 与生命周期

正式 ID 使用 `类型_YYYYMMDD_16位随机串`；完整正则、日历校验、80 位安全随机数据编码、分配与退役规则由随包文档规程及格式注册表权威定义，内部自举采用相同规则。移动、翻译或修改标题不重编 ID。

格式借鉴 [ULID 规范](https://github.com/ulid/spec#specification) 的 Crockford Base32 字符集与随机长度，采用可直接阅读的本地日期，属于本项目格式。它无需跨仓库编号服务；同日期同类型的百万次独立均匀随机分配，碰撞概率约为 `4.1 × 10^-13`，仍须查重并发现复制错误。日期是分配日线索，不表示修改时刻或内容版本。

<!-- tao:section entities -->
## 四、条目块与最小内容

REQ／UC／ADR 的选项、字段键、状态、关系及片段模板采用随包文档规程；正文保持自然语言，结构检查不根据中文或英文显示标签推断语义。REQ 的条件与验收、UC 的场景或性质、ADR 的备选与后果要求同样适用于内部条目。

内部 protocol profile 至少包含一个 REQ、一个 ADR、一个 UC 和一个正式 TASK；其他内部 profile 不继承该数量要求。内部 protocol 的 requirements、design、verification、bootstrap 章节分别承载这些对象；这是开发 profile 的位置映射，不要求第三方项目复制。

使用方的 CHG、EVD 由相应 profile 的 frontmatter 字段定义，DOC 与条目是不同对象。内部 profile 不额外允许 change、evidence 等元数据，不创造 `{chg}` 或 `{evd}` 条目块。

<!-- tao:section references -->
## 五、引用、定义范围与派生索引

持久的正文条目引用使用 MyST need role：

```markdown
参见 {need}`REQ_<YYYYMMDD>_<16位随机串>`。
```

关系字段和任务中的 ID 列表也是正式引用。普通文件导航使用标准 Markdown 链接；可分享的正式条目与章节必须使用由稳定标识生成的锚点，不能依赖标题文字自动生成的 slug。代码注释引用完整条目 ID，由工具解析到正式位置；不要求在每个函数重复标注任务。

出版契约如下：DOC 首页锚点为完整 DOC ID；REQ／UC／ADR／TASK 等条目使用其完整 ID；二级章节使用 `<DOC-ID>--<section-key>`。需要独立分享的下级章节也分配稳定键，键在文档内唯一，不从标题动态推导。条目标题已有条目 ID 时不再分配第二个标识符。普通排版小标题可保留自动锚点，但不能把它作为正式永久链接。

源文中的章节键与条目定义是唯一维护位置；出版层将其转换为 MyST 显式目标或等价 AST 节点。已有显式标签则校验一致，不重复注入。标题旁的链接按钮及“复制链接”操作必须给出稳定目标；仅设置 `html_permalinks` 并不足以保证此要求。标准支持和具体主题行为分别见 [MyST 显式目标](https://myst-parser.readthedocs.io/en/latest/syntax/cross-referencing.html#creating-explicit-targets) 与 [Sphinx 永久链接](https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-html_permalinks)。

稳定锚点不能单独解决文件移动。书籍需生成固定入口 `refs/<ID>.html#<ID>`，章节入口使用同样规则附加稳定章节键，由索引指向当前页面；复制链接优先给出此入口。移动条目只更新解析位置，移动章节跨文档时保留原入口的别名映射。退役对象生成说明页；针对历史版本的链接保留版本路径。发布域名及书籍根路径变化仍需站点迁移重定向，不能承诺仅靠 ID 自动解决。

验收必须实际构建 HTML，检查 DOM 中的唯一锚点与复制链接，再改标题、移动文件并重新访问旧入口；不得以 Markdown 含有 ID 作为通过。上述转换与链接入口仍待出版实现；源文件托管平台的自动标题链接不等同本书籍的永久链接。

本项目开发文档的文件链接使用项目内相对路径，解析后须位于 tao-dev 项目范围内；不使用本机绝对路径、`file://` 地址或指向项目外文件的相对路径。外部资料使用公开上游链接；非公开材料不记录其标题、路径或条款编号，采用的原则应独立表述。文档应能随项目独立迁移，无须读者具备作者的研究目录。

构建顺序为：解析全部纳入文档 → 注册定义 → 解析引用 → 检查类型与关系 → 输出诊断和索引。AST 必须区分顶层正式条目与代码示例；正文里提到一个 ID 不是新的定义。

当前自举索引包括同目录的 `protocol.md`、`document-contract.md`、`plugin-design.md`、`glossary.md`、`document-layout.md`、`cli-design.md`。外部参考资料不纳入正式条目索引。以后由项目配置明确 include／exclude 范围，外部项目引用使用显式导入的标识符索引，离线无索引时报告 unresolved，不能视为存在。

一条关系只维护其发出方：反向引用、需求覆盖表和汇总由索引生成，生成文件不得成为另一份人工维护的真相。检查目标存在、关系类型、任务依赖无环和替代关系无环。标为 superseded 的对象必须能找到至少一个替代者；引用 retired／superseded 对象给出复查提示，合法的历史解释不必全部阻断。

Sphinx-Needs 是候选索引与渲染工具，需配置自定义类型和关系字段；本协议额外的 frontmatter、章节和任务校验由独立检查层负责。书籍构建、PDF 和第三方编辑器表现仍需实际验证。

<!-- tao:section tasks -->
## 六、任务列表与完成语义

内部正式任务采用随包文档规程的扁平 checkbox、完整 TASK ID、relates、depends_on、verify 和完成时必需的 evidence。唯一差异是 protocol 将任务放在 bootstrap 章节；任务顺序服务阅读，执行顺序由依赖关系决定。

证据可链接实际报告或使用方 evidence profile 的摘要，不因链接存在而推导验收满足。内部规划任务保留未完成状态，直至其真实结果可复核；日期、任务勾选和模型总结都不能代替实际检查。

<!-- tao:section diagnostics -->
## 七、诊断、质量提示与修正

诊断结果同时面向终端阅读与机器消费。拟议 JSON 记录至少包含 `rule_id`、`severity`、`path`、`line`、`message`、`suggestion`、`message_locale`，可选 `column`、`entity_id`、`related_locations`、`parameters`。行列从 1 开始，重复定义同时报告两个位置；字符列按 Unicode 码点计数，适配采用 UTF-16 等定位方式的编辑器时显式转换。

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
| TAO-ENTITY-001 | error | 条目字段或必需标记段非法、缺失、空白；列出缺项 |
| TAO-TASK-001 | error | 任务格式、字段或完成证据入口不符合约定 |
| TAO-QUALITY-001 | warning | 可疑占位符、空泛验收或未决项；要求结合语境复查 |
| TAO-REF-003 | warning | 引用已废弃或已替代条目；提示新目标或说明历史用途 |
| TAO-REF-004 | error | 开发文档的文件链接使用本机绝对地址或越出项目范围；改用项目内相对路径或公开上游链接 |

上述规则号稳定，措辞可以改善。输入语法损坏时先报告根错误，抑制由它引起的大量误报。拟议退出码：`0` 无 error（可含 warning），`1` 有文档 error，`2` 工具或配置故障、检查未完成。发布就绪检查另评阻断问题，不能与格式退出码混为一谈。

文档质量审查报告必须区分事实、推断与建议，指出具体条目和遗漏场景；不输出缺少解释的“质量 87 分”。格式工具不能自动决定需求优先级、选择架构或批准风险。

自动修正初期只考虑空白、格式化等不改变语义的动作，并展示差异。重复 ID、缺失验收、破坏性迁移、重新关联需求等需要语义判断，不能无提示自动修复。例外必须显式记录理由、范围、责任人及复查条件，不能靠全局忽略让错误消失。

<!-- tao:section evolution -->
## 八、实现与演进约束

### 本地化与使用方语言

本项目维护语言见主协议中的 {need}`ADR_20260914_WX7BFBRXENPN4CT7`。它不限制采用 tao-dev 的其他项目。正文语言、诊断界面语言和机器协议分别选择：

- **既有文档：** 默认保留其 locale 和语言；收到明确翻译请求时才创建或转换语言版本。
- **新文档：** 优先使用用户对该产物明确指定的语言，其次采用目标项目的文档约定；均不明确时询问一次。不能从 tao-dev 的中文手册推导使用方语言，也不能把聊天语言直接当作产物语言。
- **机器协议：** schema、章节／字段键、条目类型、ID、关系名、状态值、规则号、占位变量和退出码保持稳定英文／ASCII 形式。正文、标题、说明、任务目标和诊断消息可本地化；日期、数值等机器字段使用固定格式，本地化显示由呈现层处理。
- **诊断语言：** 优先使用显式参数，其次使用方的界面配置，再采用文档 locale；未提供该消息翻译时回退到英文并报告实际 `message_locale`。外部工具原始输出保持原样，翻译说明与原始证据区分。机器消费依赖规则号与参数，不匹配消息文字。

示例：下面两种表达使用同一字段键。普通 Markdown 阅读器显示各自语言，检查器只识别结构键与后续段落。

```markdown
<!-- tao:field acceptance -->
**验收：** 移动文件后引用仍能解析。
```

```markdown
<!-- tao:field acceptance -->
**Acceptance:** References still resolve after moving the file.
```

模板采用一套语言无关的结构及按 locale 分开的显示文字资源；初期只要求简体中文和英文用例成立。变量名与占位符集合在各语言资源中一致，整段消息允许按语言重排变量，不能靠拼接碎片实现翻译。标签缺失要报告回退或缺项，不能偷偷生成混杂语言的正式文档。对尚无内容质量规则的语言，结构检查仍可运行，内容质量项明确标记未检查；中文不沿用按英文空格数统计的长度规则。

按单个文档或条目确定一个权威源语言，其他语言是派生视图。当前不维护中英文两份完整正文。未来优先验证 Sphinx gettext 目录或等价翻译资源，保留源版本／摘要与审校状态；源文变化后标记译文待复核，不因结构通过自动认可翻译。

同一语义对象翻译后保留 ID，不新增需求、任务或批准状态。译文不重新注册正式定义，按 locale 构建阅读视图；同一版本同一 locale 出现两个正式定义仍报重复，换一个 locale 不能掩盖源文重复。包含多个权威语言文档的项目仍先对全部源文建立全局索引，不能各按语言独立编号。若译文实际新增了承诺，应作为需求变更处理。

### 校验与升级

实现时先用现有 Markdown 解析器获取 AST 与源码位置，再提取元数据、章节、条目与任务，输出归一化数据。JSON Schema 校验字段类型和枚举，结构规则检查 Markdown 布局，关系检查负责跨文件语义。不用一组全文正则冒充 Markdown 解析器。

正式校验器必须使用包含损坏样例的独立测试集，覆盖围栏嵌套、示例 ID、中文、移动条目和未知版本等边界；普通 Markdown 链接列表不得误判为任务。i18n 反例包括：翻译标签不改变提取结果、结构键丢失在两种语言下报同一规则、翻译占位符丢失、源文变更后译文过期，以及非 ASCII 路径与字符定位。解析本项目文档只是验收的一部分。

契约版本变更需要说明哪些源文档受影响；迁移先产生差异，保留 ID、人工决定与原文件恢复路径。检查器应明确支持的版本，不静默将旧文档按新规则解释。校验器与规则同时修改时，旧版本行为和反例预期须独立审查。

本契约的需求依据为 {need}`REQ_20260914_42AXMZ2KH2RAZ8M3`、{need}`REQ_20260914_5Y6CWDE3MFMKJXSB`；设计取舍见 {need}`ADR_20260914_HHVX7YB5AG7J3TMT`。实现的 schema 与模板通过追踪关系和测试保持一致，运行时不依赖本文。
