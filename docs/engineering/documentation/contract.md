---
schema: tao.project.design/v0.1
id: DOC_20260914_P1G9T0KSCC0FTBM1
title: Markdown 文档契约
locale: zh-Hans
status: draft
spec_docs: ["DOC_20260914_4C7N0XHQSP7CY69P"]
---

# Markdown 文档契约

<!-- tao:section overview -->
## 适用范围

开发与使用方采用同包 [格式注册表](../../../skills/tao-dev/assets/document-profiles.json)、[文档规程](../../../skills/tao-dev/references/documents.md) 与模板。受管理文档为 spec、design、plan、tasks、decision、user-guide、runbook、glossary、navigation 九类。README、skill 指令和临时输出不自动进入受管理集合；review/evidence 不设长期 schema、正式对象或出版入口。

公开写法沿用 [EARS](https://alistairmavin.com/ears/) 的条件化需求、[Gherkin](https://cucumber.io/docs/gherkin/reference/) 的给定/当/则、[ADR](https://www.cognitect.com/blog/2011/11/15/documenting-architecture-decisions) 的背景/决定/后果，并参考 [arc42](https://arc42.org/overview/) 和 [Diátaxis](https://diataxis.fr/) 按内容组织。它们不是本产品获得的认证；tao 的稳定键、ID 和关系是自己的契约。

<!-- tao:section architecture -->
## 解析与索引

解析纳入范围的 Markdown AST 与 YAML → 注册正式定义 → 解析正向关系 → 检查类型、唯一性、引用及无环导航 → 输出诊断与索引。代码示例不注册定义，裸 ID 不自动建立关系；不以全文正则替代 AST。未接入资料不计入检查覆盖。

正文引用采用 {need} 角色与项目内相对链接，禁止本机绝对地址及越界链接；外部资料用公开上游 URL。反向引用、索引和章节编号派生生成，不维护第二套人工关系表。出版层使用同一索引生成稳定锚点、refs 页面及前后页导航。

## 结构边界

保留 YAML 元数据、profile、DOC 和条目语法；必要语义章节仍要求存在，章节顺序、数量及不相关模板章节不再强制。自定义章节允许，稳定 section/field 键若出现不得重复。正文语言与显示标签不决定结构，locale 不改变 ID、规则号或结果。

文档契约同时约束含义：规格说明可观察行为与验收，设计解释结构、接口、不变量及失败，ADR 保留背景、决定与后果，计划定义范围、成果任务与验证方法。语义审查核对一致性、可验证性和当前事实，不能由必填字段存在推断完成。按实际知识缺口选用类型，不强制每次改动形成文档三件套。

REQ/UC/ADR 仍采用 MyST 指令与现有关系选项。TASK 是 tasks 章节的扁平 checkbox，必须有唯一 TASK ID 和非空 verify；relates、depends_on、evidence 可选。提供的关系必须合法，任务依赖无环。任务描述可验证成果，不照抄客户端临时步骤；完成勾选不要求证据附件，也不推断验证、审查或交付完成。

plan.change 定义 CHG；tasks.change 引用同一计划。plan 内联任务或通过 tasks_doc 指向一份附件，不同时维护两份任务。spec_docs/design_docs 如提供，应引用对应类型文档。草稿可缺尚未形成的依据，审查根据实际内容判断其完整性。

## 字段最小集

基础字段仅 schema、id、title、locale、status，均必填。字段应保存独立知识或支持必要的进度判断，而不是因为已有解析代码就永久保留。created/updated 不表达知识的有效期、决定理由或实际成果，因此不进入 schema；业务有效日期或观察时间按语义写正文。DOC 是文档身份，CHG 是事项身份；标题供展示、locale 支持独立流转、status 表达生命周期，都不能由文件名或任务勾选替代。

| 类型或结构 | 必需信息 | 按需信息与精简边界 |
|---|---|---|
| spec | scope、requirements，至少一个 REQ | terms、cases、questions 按需，不要求凑齐 |
| design | overview、architecture | 保留 spec_docs 说明方案服务的规格；不声明 change，方案不归属于一次实施 |
| plan | change、scope、唯一任务集 | tasks_doc、spec_docs、design_docs 可选；verification 保存真实结果，不保存可执行命令配置 |
| tasks | change、tasks、至少一个 TASK | 保留所属事项校验，不复制计划的任务集 |
| decision | decisions、恰好一个 ADR | 文档与 ADR 是不同对象，不合并其状态 |
| user-guide | steps | 范围、前提、排错章节按需 |
| runbook | steps | 检查与恢复章节按实际操作风险保留 |
| glossary | terms | term 的名称与定义必需；english/code 保存语言和代码映射，avoid/scope 表达禁用歧义与适用边界 |
| navigation | contents、单个非空 toctree | 保留阅读路径及图约束；固定显示选项保持统一出版，不增加每页可调状态 |
| REQ | id、status、行为、acceptance、source | links、supersedes 可选；来源与验收不是重复行为正文，仍保留 |
| UC | id、status、verifies、given/when/then | links、supersedes 可选；verifies 提供有类型的需求追溯 |
| ADR | id、status、context/decision/consequences | links、supersedes 可选；取舍和后果不能由决定一句话代替 |
| TASK | checkbox、ID、标题、verify | relates、depends_on、evidence 可选；模板省略空依赖和重复的所属 CHG，保留真实依赖及需求关系 |
| 退役记录 | id、retired_on、reason、replaced_by | 日期与替代信息使单行记录可独立解释；空 replaced_by 表示无替代，不改协议 |

保留可选关系并非因为存在消费者：spec_docs/design_docs 记录“为何实现、依据什么”，长期可追溯；tasks_doc 确定唯一进度来源；TASK.relates 说明任务服务的需求，depends_on 表达短期真实阻塞，evidence 作为普通 Markdown 链接指向实际依据；links/supersedes 保存跨知识关联与替代原因。这些信息无法从标题、排序或完成计数可靠恢复，仍按需记录，不填空数组凑结构。TASK.evidence 不意味着存在独立 evidence 文档或 EVD 对象。

迁移时直接移除已有文档的 created、updated 和 design.change；旧字段作为未知元数据报错，不保留兼容别名。review/evidence schema、EVD 及其专属字段不再支持；已有报告的有价值结论回到适用知识文档或计划，原始输出移出受管理范围。retired_on、现存正式 ID 和有效关系不变；确有独立语义的时间或版本事实保留在正文。plan.verification 继续保存结果知识，由 agent 读取，CLI 不抽取整段正文充当 summary。

## 知识与记录

规格、设计和 ADR 保留长期当前知识；持久 plan/tasks 是跨会话、协作或跟踪工作的权威项目进度，agent 核对事实后写回成果与阻碍，在 plan verification 合并当前摘要。完成计划作为变更记录保留，不替代长期知识。客户端临时任务和摘要不构成另一份进度源。review/evidence 详情留临时材料或 CI，不创建长期审查记录、批次或证据 schema。历史检查结果、原始材料可用性和当前可复用性分别说明，不因日志消失回写任务状态。

<!-- tao:section invariants -->
## 标识与出版

ID 是 TYPE_YYYYMMDD_16位 Crockford Base32 随机串，随机部分 80 位，由安全随机源离线生成并与现有定义/退役记录查重；不是标准 ULID。百万次同日同类型独立分配的碰撞概率约 4.1 × 10^-13，仍必须发现复制错误。日期是分配日，不是版本；移动、翻译和改名不换 ID。

退役 JSONL 沿用 id、retired_on、reason、replaced_by 契约，全部日期文件参与一致性检查。替代目标同类型、非自身且无环。书籍以 toctree 为唯一主导航，所有出版文档可达、无环、无重复主位置；详细稳定链接与重定向见 [出版规程](../../../skills/tao-dev/references/publication.md)。

<!-- tao:section errors -->
## 诊断

诊断保留规则号、严重度、路径、行列、消息与修正建议；重复定义报告相关位置，语法根错误不放大成级联噪声。基础元数据、重复键、重复 ID、悬空引用、错误关系、非法任务和导航环是错误。固定顺序、无关章节、缺 evidence 或缺审批不是错误。格式通过不证明语义正确、代码通过或交付就绪。

<!-- tao:section verification -->
## 回归与演进

用独立正反例覆盖代码围栏、示例 ID、中文、未知 schema、重复 ID、移动对象、非 ASCII 定位、章节重排、缺必要语义章节和导航环。出版检查实际 HTML 链接、锚点与旧入口，不从 AST 存在推断浏览器可用。语言切换保留结构与规则号，诊断占位符一致，未知外部消息明确回退。

新增格式字段同时更新注册表、模板、参考和回归；保留现有对象 ID 与人工内容。需求依据为 {need}`REQ_20260914_42AXMZ2KH2RAZ8M3`、{need}`REQ_20260914_5Y6CWDE3MFMKJXSB`，长期决定见 {need}`ADR_20260914_HHVX7YB5AG7J3TMT`。
