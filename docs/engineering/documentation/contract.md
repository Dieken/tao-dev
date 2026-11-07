---
schema: tao.project.design/v0.1
id: DOC_20260914_P1G9T0KSCC0FTBM1
title: Markdown 文档契约
locale: zh-Hans
status: draft
created: '2026-09-14'
updated: "2026-09-21"
spec_docs: ["DOC_20260914_4C7N0XHQSP7CY69P"]
---

# Markdown 文档契约

<!-- tao:section overview -->
## 适用范围

开发与使用方采用同包 [格式注册表](../../../skills/tao-dev/assets/document-profiles.json)、[文档规程](../../../skills/tao-dev/references/documents.md) 与模板。README、skill 指令、临时输出不自动进入受管理集合；长期 spec/design/plan/tasks/ADR、指南、术语与导航使用现有 v0.1 profile。需要独立长期引用的 evidence 可选；不额外引入交接或流程状态文档。

公开写法沿用 [EARS](https://alistairmavin.com/ears/) 的条件化需求、[Gherkin](https://cucumber.io/docs/gherkin/reference/) 的给定/当/则、[ADR](https://www.cognitect.com/blog/2011/11/15/documenting-architecture-decisions) 的背景/决定/后果，并参考 [arc42](https://arc42.org/overview/) 和 [Diátaxis](https://diataxis.fr/) 按内容组织。它们不是本产品获得的认证；tao 的稳定键、ID 和关系是自己的契约。

<!-- tao:section architecture -->
## 解析与索引

解析纳入范围的 Markdown AST 与 YAML → 注册正式定义 → 解析正向关系 → 检查类型、唯一性、引用及无环导航 → 输出诊断与索引。代码示例不注册定义，裸 ID 不自动建立关系；不以全文正则替代 AST。未接入资料不计入检查覆盖。

正文引用采用 {need} 角色与项目内相对链接，禁止本机绝对地址及越界链接；外部资料用公开上游 URL。反向引用、索引和章节编号派生生成，不维护第二套人工关系表。出版层使用同一索引生成稳定锚点、refs 页面及前后页导航。

## 结构边界

保留 YAML 元数据、profile、DOC 和条目语法；必要语义章节仍要求存在，章节顺序、数量及不相关模板章节不再强制。自定义章节允许，稳定 section/field 键若出现不得重复。正文语言与显示标签不决定结构，locale 不改变 ID、规则号或结果。

文档契约同时约束含义：规格说明可观察行为与验收，设计解释结构、接口、不变量及失败，ADR 保留背景、决定与后果，计划定义范围、成果任务与验证方法。语义审查核对一致性、可验证性和当前事实，不能由必填字段存在推断完成。按实际知识缺口选用类型，不强制每次改动形成文档三件套。

REQ/UC/ADR 仍采用 MyST 指令与现有关系选项。TASK 是 tasks 章节的扁平 checkbox，必须有唯一 TASK ID 和非空 verify；relates、depends_on、evidence 可选。提供的关系必须合法，任务依赖无环。任务描述可验证成果，不照抄客户端临时步骤；完成勾选不要求证据附件，也不推断验证、审查或交付完成。

plan.change 定义 CHG；tasks.change 引用同一计划；evidence.evidence 定义 EVD。plan 内联任务或通过 tasks_doc 指向一份附件，不同时维护两份任务。spec_docs/design_docs 如提供，应引用对应类型文档。草稿可缺尚未形成的依据，审查根据实际内容判断其完整性。

## 知识与记录

规格、设计和 ADR 保留长期当前知识；持久 plan/tasks 是跨会话、协作或跟踪工作的权威项目进度，agent 核对事实后写回成果与阻碍，在 plan verification 合并当前摘要。完成计划作为变更记录保留，不替代长期知识。客户端临时任务和摘要不构成另一份进度源。详细 review/evidence 默认临时；显式长期记录沿用 evidence，不新增批次或审查 schema。历史检查结果、原始材料可用性和当前可复用性分别说明，不因日志消失回写任务状态。

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
