# 文档管理入口

先定位项目根、用户需要的知识及其现有权威来源，再选择查找、创建、更新、语义审查、校验、出版或退役。按需读取 [正文写法](document-content.md)、[组织](document-layout.md)、[出版](publication.md)、[本地化](localization.md) 与 [退役](retirement.md)；跟踪跨会话或协作工作读取 [持久计划](planning.md)。精确结构以同包 [注册表](../assets/document-profiles.json) 和模板为准，不创造平行 schema。

## 选择与范围

受管理文档采用 spec、design、plan、tasks、decision、user-guide、runbook、glossary、navigation 九类。按信息职责选择文档，不要求 spec → design → plan 顺序；小改动更新现有权威位置，跨会话、协作或明确跟踪的结果使用持久计划。README、skill 指令和临时 Markdown 不自动变成受管理文档；review/evidence 详情不设长期 schema，不注册正式对象或进入 book。

读取单 profile：`python <skill>/scripts/read_profile.py plan --locale zh-Hans`。只读本次涉及的类型和语言。创建后替换全部模板变量，不用模板提示冒充项目结论。审查和检查产生的有效结论更新计划、规格、设计或 ADR，原始报告留临时材料。

先检索已有定义、引用和相关材料；已知 ID 可用 `tao show <ID>` 定位。修改同一对象保留 ID，更新受影响的契约、任务、链接和导航；改变需求、决定或验收须有真实依据，不能通过文案修改掩盖未实现承诺。只在授权项目内写入，已知事实自行查找，确有目标冲突或范围外决定时再请求必要裁决。

## 元数据与结构

文档保留 YAML frontmatter、受支持的 schema、唯一 DOC、标题、locale 及对应 profile 的基础字段。正文使用自然语言和已有 `<!-- tao:section key -->`、`<!-- tao:field key -->` 稳定键。章节按实际内容组织，不强制固定顺序、数量或无关章节；重复键非法。保留各类型的必要语义章节：spec 的 scope/requirements、design 的 overview/architecture、plan 的 scope（内联任务所在章节使用 tasks 键）、tasks 的 tasks、decision 的 decisions、指南与 runbook 的 steps、glossary 的 terms、navigation 的 contents。

基础必填为 schema、id、title、locale、status。不维护 created/updated：编辑时间不能说明知识仍有效或任务已有进展；确有业务意义的生效日期、观察时间写入相应正文。退役记录使用 retired_on 标识具体事件。检查的输入、执行时间与限制按 [结果保存](evidence-retention.md) 记录，不另设正式证据元数据。

条目使用 MyST req/uc/adr 块；任务使用扁平 checkbox 与 TASK ID、verify，可选 relates、depends_on、evidence。任务全勾选不是验证、审查或交付通过。accepted 等元数据只能反映真实决定，不能由格式校验自动设置。

## 标识与关系

ID 为 `TYPE_YYYYMMDD_16位随机串`，采用现有安全随机分配器；类型为 DOC、REQ、UC、ADR、TASK、CHG。`tao id new REQ --count 3` 批量返回，不写编号台账。移动、标题变化和翻译保留 ID；复制新对象分配新 ID。

plan 的 change 定义 CHG；tasks 的 change 引用计划 CHG。design 以 spec_docs 引用规格，plan 以 spec_docs/design_docs 引用依据，tasks_doc 可选且唯一。设计不声明 change，长期方案不归属于一次实施；多个计划可以引用同一设计。正文引用使用 `{need}` 和项目内相对链接；关系仅维护正向字段，反向索引由工具生成。计划前的 spec/design 不需注册 CHG。

## 检查与保存

`tao verify` 校验基本元数据、必要语义结构、唯一 ID、关系及无环可达导航。它不执行项目测试，也不证明需求正确、设计合理、来源真实、实现完成或审查通过；内容判断使用 [文档语义审查](review.md)，显式检查及结果解释见 [确定性检查](verification.md)。重复 ID、悬空引用和导航环必须修正；不通过删需求、降低约束或全局忽略隐藏问题。

长期正文保留当前行为、理由、限制与独立有价值的依据；计划 verification 合并当前结果，完成的计划保留为变更记录而非长期当前事实入口。详细执行和普通审查输出按 [证据保存](evidence-retention.md) 留临时，不自动归档或提交。正式文档退役先更新引用和导航，保留必要追溯，不能删除无关知识。
