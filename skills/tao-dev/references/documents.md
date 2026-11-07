# 文档管理入口

先定位项目根、需要的知识及其现有权威来源，再选择查找、创建、更新、语义审查、校验、出版或退役。按需读取 [正文写法](document-content.md)、[出版](publication.md)、[本地化](localization.md) 与 [退役](retirement.md)；进度管理见 [持久计划](planning.md)。精确结构以同包 [注册表](../assets/document-profiles.json) 和模板为准，不另设一套结构规范。

## 选择与范围

受管理文档采用规格（`spec`）、设计（`design`）、计划（`plan`）、任务（`tasks`）、决策（`decision`）、用户指南（`user-guide`）、运维手册（`runbook`）、术语表（`glossary`）、导航（`navigation`）九类。按信息职责选择，不要求按规格、设计、计划的顺序编写；小改动更新现有权威位置。README、技能指令和临时 Markdown 不自动变成受管理文档；审查与证据详情不设长期结构规范，不注册正式对象，也不纳入文档书籍。

读取单一文档格式：`python <skill>/scripts/read_profile.py plan --locale zh-Hans`。只读本次涉及的类型和语言。创建后替换全部模板变量，不用模板提示冒充项目结论。

先检索已有定义、引用和相关材料；已知 ID 可用 `tao show <ID>` 定位。修改同一对象保留 ID，更新受影响的契约、任务、链接和导航；需求、决定和验收的修改须有真实依据。

## 文档归属

| 内容 | 默认位置 |
|---|---|
| 用户可命名的能力、REQ/UC | `docs/product/<capability>.md` |
| 系统或模块边界、接口、失败和取舍 | `docs/engineering/<module>.md` |
| 跨变更的长期 ADR | `docs/engineering/decisions/<slug>.md` |
| 一次变更的计划与任务、当前验证摘要 | `docs/plans/<yyyy-mm>/<yyyymmdd>-<slug>.md` |
| 用户操作、运维、术语 | `docs/user/`、`docs/operations/`、`docs/glossary.md` |
| 审查详情、执行日志、临时摘要 | `temporary`（默认 `tmp/tao`）或 CI 产物，不纳入文档书籍 |

目录可按项目映射。规格描述承诺，设计说明实现依据，计划引用它们并表达本次差异，不复制长期正文；重要决定跨事项复用时才抽 ADR。`.tao/` 仅保存项目配置等必要本地工具数据，不维护开发阶段状态。

日期与文件名中的短名称（slug）方便浏览，不是对象标识。新增文档加入现有 `toctree`，不根据物理目录另建一套导航。长期正文保留当前行为、理由、限制与有价值的依据；完成计划的知识归属见 [持久计划](planning.md#完成后的知识归属)，临时材料及结论见 [结果保存](planning.md#结果保存)。

## 元数据与结构

文档保留 YAML 前置元数据、受支持的 `schema`、唯一 DOC、标题、`locale` 及对应文档格式的基础字段。正文使用自然语言和已有 `<!-- tao:section key -->`、`<!-- tao:field key -->` 稳定键。章节按实际内容组织，不强制固定顺序、数量或无关章节；重复键非法。保留各类型的必要语义章节：`spec` 的 `scope`／`requirements`、`design` 的 `overview`／`architecture`、`plan` 的 `scope`（内联任务所在章节使用 `tasks` 键）、`tasks` 的 `tasks`、`decision` 的 `decisions`、指南与运维手册的 `steps`、术语表的 `terms`、导航的 `contents`。

基础必填字段为 `schema`、`id`、`title`、`locale`、`status`。不维护 `created`／`updated`：编辑时间不能说明知识仍有效或任务已有进展；确有业务意义的生效日期、观察时间写入相应正文。退役记录使用 `retired_on` 标识具体事件。检查的输入、执行时间与限制按 [结果保存](planning.md#结果保存) 记录，不另设正式证据元数据。

条目使用 MyST `req`／`uc`／`adr` 块；任务使用扁平复选框与 TASK ID、`verify`，可选 `relates`、`depends_on`、`evidence`；任务语义见 [持久计划](planning.md)。`accepted` 等元数据只能反映真实决定，不能由格式校验自动设置。

## 标识与关系

ID 为 `TYPE_YYYYMMDD_16位随机串`，采用现有安全随机分配器；类型为 DOC、REQ、UC、ADR、TASK、CHG。`tao id new REQ --count 3` 批量返回，不写编号台账。移动、标题变化和翻译保留 ID；复制新对象分配新 ID。

计划的 `change` 定义 CHG；任务文档的 `change` 引用计划 CHG。设计以 `spec_docs` 引用规格，计划以 `spec_docs`／`design_docs` 引用依据，`tasks_doc` 可选且唯一。设计不声明 `change`，长期方案不归属于一次实施；多个计划可以引用同一设计。正文引用使用 `{need}` 和项目内相对链接；关系仅维护正向字段，反向索引由工具生成。计划前的规格与设计不需注册 CHG。

## 检查与保存

源文档结构与关系校验见 [文档校验](tools.md#文档校验)，内容判断见 [文档语义审查](review.md)。结构有效不代表语义正确、实现完成或交付获认可。

正式文档退役先更新引用和导航，保留必要追溯，不能删除无关知识。
