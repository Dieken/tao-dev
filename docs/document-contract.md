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

本文是 tao-dev 的内部文档格式设计，供维护者实现解析器、schema、诊断和模板时使用；不属于分发给第三方项目的 skill 文档。现有六篇长期开发文档仍使用待迁移的内部 profile；新建交付文档采用随包 profile 自举。面向使用方的统一格式、机器可读注册表与模板已经随 skill 提供，完整 AST 校验器仍待实现。目标是兼顾 Markdown 的可读性与结构、标识符、关系的可检查性。

<!-- tao:section scope -->
## 一、适用范围与检查层次

本契约记录下表中尚待迁移的内部开发文档 profile，不用于新建文档；术语含义见 [术语与缩写](glossary.md)，文件职责与拆分规则见 [文档组织与产物保存](document-layout.md)。使用方采用随包 [文档规程](../plugins/tao-dev/skills/tao-dev/references/documents.md) 与 [格式注册表](../plugins/tao-dev/skills/tao-dev/assets/document-profiles.json) 中的 `tao.project.*` profile。格式由 tao-dev 定义，项目只映射目录、选择语言及配置允许的阈值；不得要求使用方复制本项目的章节结构、研发任务或设计记录。运行组件的 manifest、SKILL.md、agent、command 和 hook 使用各自公共标准或平台格式，不套用内部 profile。

格式设计优先复用公共语法与成熟惯例，具体映射维护在随包 [公共依据与写法](../plugins/tao-dev/skills/tao-dev/references/document-standards.md)。EARS 约束 REQ 正文，验收方法留在 acceptance；保留现有模板变量与稳定结构键，不另建同义字段。格式解析与自然语言质量判断分别验收，不宣称符合完整 EARS、Gherkin 或 arc42 工具链。

检查分层、结论边界和修正规则统一见随包 [文档诊断规程](../plugins/tao-dev/skills/tao-dev/references/document-diagnostics.md)，本篇只维护实现设计。

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

正式引用语法由随包文档规程定义。DOC、条目与章节的锚点、固定入口、移动和退役规则、实际 HTML 验收统一见随包 [出版规程](../plugins/tao-dev/skills/tao-dev/references/publication.md)。本项目的 Sphinx 适配实现须满足该契约，不能从源文件含有 ID 推导发布链接已经可用。

本项目开发文档的文件链接使用项目内相对路径，解析后须位于 tao-dev 项目范围内；不使用本机绝对路径、`file://` 地址或指向项目外文件的相对路径。外部资料使用公开上游链接；非公开材料不记录其标题、路径或条款编号，采用的原则应独立表述。文档应能随项目独立迁移，无须读者具备作者的研究目录。

构建顺序为：解析全部纳入文档 → 注册定义 → 解析引用 → 检查类型与关系 → 输出诊断和索引。AST 必须区分顶层正式条目与代码示例；正文里提到一个 ID 不是新的定义。

现有内部 profile 的索引包括同目录的 `protocol.md`、`document-contract.md`、`plugin-design.md`、`glossary.md`、`document-layout.md`、`cli-design.md`。外部参考资料不纳入正式条目索引。新增的 docs/changes/ 文档采用随包 profile，并与上述范围共同检查 ID 唯一性和引用；共享格式与内部格式的检查结果分开报告。以后由项目配置明确 include／exclude 范围，外部项目引用使用显式导入的标识符索引，离线无索引时报告 unresolved，不能视为存在。

退役数据由独立 JSONL 读取层按随包 retirement_records 契约提取，再与 Markdown 定义合并检查；docs/retired/ 的全部日期文件都参与索引，不以 Sphinx 导航或当前修改日期决定范围。该目录只在产生实际退役记录时建立，不预写示例作为正式数据；注册表定义格式不等于读取器已经实现。

一条关系只维护其发出方：反向引用、需求覆盖表和汇总由索引生成，生成文件不得成为另一份人工维护的真相。检查目标存在、关系类型、任务依赖无环和替代关系无环。标为 superseded 的对象必须能找到至少一个替代者；引用 retired／superseded 对象给出复查提示，合法的历史解释不必全部阻断。

Sphinx-Needs 是候选索引与渲染工具，需配置自定义类型和关系字段；本协议额外的 frontmatter、章节和任务校验由独立检查层负责。书籍构建、PDF 和第三方编辑器表现仍需实际验证。

出版适配拟将源文的章节键与条目定义转换为 MyST 显式目标或等价 AST 节点；已有显式标签须校验一致，避免重复注入。仅设置 html_permalinks 不足以保证复制稳定链接，需要实际检查主题行为。实现依据见 [MyST 显式目标](https://myst-parser.readthedocs.io/en/latest/syntax/cross-referencing.html#creating-explicit-targets) 与 [Sphinx 永久链接](https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-html_permalinks)。这些实现选择供 tao-dev 开发维护使用；使用方只需读取随包的链接与出版结果规程。

<!-- tao:section tasks -->
## 六、任务列表与完成语义

内部正式任务采用随包文档规程的扁平 checkbox、完整 TASK ID、relates、depends_on、verify 和完成时必需的 evidence。唯一差异是 protocol 将任务放在 bootstrap 章节；任务顺序服务阅读，执行顺序由依赖关系决定。

证据可链接实际报告或使用方 evidence profile 的摘要，不因链接存在而推导验收满足。内部规划任务保留未完成状态，直至其真实结果可复核；日期、任务勾选和模型总结都不能代替实际检查。

<!-- tao:section diagnostics -->
## 七、诊断、质量提示与修正

诊断 JSON 字段、规则号、严重级别、退出码和修正边界统一见随包 [文档诊断规程](../plugins/tao-dev/skills/tao-dev/references/document-diagnostics.md)。CLI 的公共结果封装见 [命令设计](cli-design.md)。实现按规则号与参数消费结果，界面文字可本地化；当前完整校验器尚未实现。

<!-- tao:section evolution -->
## 八、实现与演进约束

### 本地化与使用方语言

项目自身的语言取舍见 {need}`ADR_20260914_WX7BFBRXENPN4CT7`。使用方的语言选择、稳定键、显示资源、诊断回退和翻译源一致性统一见随包 [本地化规程](../plugins/tao-dev/skills/tao-dev/references/localization.md)。实现需使用同一套结构和按 locale 选择的资源，不能要求使用方复制本项目的中文正文。

翻译资源的出版适配优先验证 Sphinx gettext 目录或等价机制；源版本、审校状态与过期检测是需验证的实现能力。该技术选型留在本项目设计中，不作为使用方 agent 的操作指令。

### 校验与升级

实现时先用现有 Markdown 解析器获取 AST 与源码位置，再提取元数据、章节、条目与任务，输出归一化数据。JSON Schema 校验字段类型和枚举，结构规则检查 Markdown 布局，关系检查负责跨文件语义。不用一组全文正则冒充 Markdown 解析器。

正式校验器必须使用包含损坏样例的独立测试集，覆盖围栏嵌套、示例 ID、中文、移动条目和未知版本等边界；普通 Markdown 链接列表不得误判为任务。i18n 反例包括：翻译标签不改变提取结果、结构键丢失在两种语言下报同一规则、翻译占位符丢失、源文变更后译文过期，以及非 ASCII 路径与字符定位。解析本项目文档只是验收的一部分。

契约版本变更需要说明哪些源文档受影响；迁移先产生差异，保留 ID、人工决定与原文件恢复路径。检查器应明确支持的版本，不静默将旧文档按新规则解释。校验器与规则同时修改时，旧版本行为和反例预期须独立审查。

本契约的需求依据为 {need}`REQ_20260914_42AXMZ2KH2RAZ8M3`、{need}`REQ_20260914_5Y6CWDE3MFMKJXSB`；设计取舍见 {need}`ADR_20260914_HHVX7YB5AG7J3TMT`。实现的 schema 与模板通过追踪关系和测试保持一致，运行时不依赖本文。
