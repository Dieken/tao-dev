# 文档组织

## 唯一权威位置

| 内容 | 默认位置 |
|---|---|
| 用户可命名的能力、REQ/UC | docs/product/<capability>.md |
| 系统或模块边界、接口、失败和取舍 | docs/engineering/<module>.md |
| 跨变更的长期 ADR | docs/engineering/decisions/<slug>.md |
| 一次变更的计划与任务、当前验证摘要 | docs/plans/<yyyy-mm>/<yyyymmdd>-<slug>.md |
| 用户操作、运维、术语 | docs/user/、docs/operations/、docs/glossary.md |
| 明确需要独立长期引用的 evidence | 计划附件或项目既有长期证据目录 |
| 普通审查详情、执行日志、用户请求的临时摘要 | temporary，不进 book |

目录可按项目映射。规格描述承诺，设计说明实现依据，计划引用它们并表达本次差异与任务；不复制正文，也不要求每次修改新建三类文档。完成计划保留为变更记录，长期当前事实回写规格、设计和操作说明。`.tao/` 仅保存项目配置等必要本地工具数据，不维护开发阶段状态。长期文档使用已有 profile 与稳定 ID，进度维护见 [持久计划](planning.md)。

## 拆分与命名

任务默认内联 plan；规模或并行编辑确有需要时，用 tasks_doc 唯一关联一份任务附件。内联与附件二选一，不建父子两份完成状态。附件与计划共享 change，任务关系只写正向字段。共享设计不绑定某次变更；重要决定跨事项复用时才抽 ADR。

日期与 slug 服务浏览，不是对象身份；移动、改名、翻译保留 ID。新增文档挂入现有 toctree，物理目录不另造导航真相。已无长期价值的执行记录不因发生过就保留为知识；有价值的结果合并到原权威文档，参见 [证据保存](evidence-retention.md)。
