---
schema: tao.project.design/v0.1
id: DOC_20260914_Y5RR8BVF6065JTYP
title: 文档组织与产物保存
locale: zh-Hans
status: draft
spec_docs: ["DOC_20260914_4C7N0XHQSP7CY69P"]
---

# 文档组织与产物保存

<!-- tao:section overview -->
## 目标

长期知识各有唯一位置，目录按阅读主题组织，不按执行阶段复制正文。落实 {need}`REQ_20260914_NN0AEQ2E1GTVSMTV`、{need}`REQ_20260914_3JQXRKWXKAZSNJ5R` 和 {need}`REQ_20260914_0J68SDKV86ENKER2`。运行写法见 [文档归属](../../../skills/tao-dev/references/documents.md#文档归属)。

<!-- tao:section architecture -->
## 归属与导航

规格维护能力及 REQ/UC，设计维护边界和实现依据，跨事项取舍抽 ADR，计划维护一次目标的可验证成果任务与当前验证摘要。跨会话、协作或需跟踪工作使用持久计划，局部小改动复用适用文档，不强制生成三件套。任务默认内联，必要时由 tasks_doc 唯一关联附件；客户端临时步骤不另成项目进度源，不引入审批或流程状态文件。

book 以 navigation profile 和 MyST toctree 表达主位置与顺序，不另设 parent/order 或 SUMMARY。每页只有一处主位置，普通链接可跨主题引用；导航须可达、无环、无重复目标。新增文档与导航同批更新。生成编号不写进标题、文件名或稳定 href；正文、侧栏和页内目录共用编号。

长期计划默认 docs/plans/<yyyy-mm>/<yyyymmdd>-<slug>.md；附件同月同 stem。日期与 slug 仅服务浏览，移动与改名保留 ID。创建不覆盖同名文件，路径和符号链接解析后不能越出项目。

## 保留与临时材料

review/evidence 详细输出留 temporary（默认 tmp/tao）或 CI，计划合并当前简短结论；它们不属于长期受管理文档，不分配正式对象 ID、不进入导航。临时摘要不是继续工作的前置条件。agent 根据真实成果写回持久计划；完成的计划保留为变更记录，当前知识回到规格、设计、ADR 与指南。

需要长期保存的是已核实的结论、约束与理由，而不是原样归档一次报告。将这些内容合并到相应知识文档，保留必要来源、输入范围及限制，不改写旧失败为成功。原始材料的专项留存由项目或外部系统管理，tao 不为此提供 review/evidence schema。退役记录仍按 JSONL 保存到 docs/retired。

<!-- tao:section verification -->
## 出版检查

修改出版器时以真实 HTML 核对引用标题转义、唯一 DOM 锚点、复制链接、前后关系、章节编号和中文搜索；中文相邻字符对索引不保证单字搜索。改标题、移动文件及重排导航后访问旧固定入口。章节重定向仍可指向保留的文档，禁用 JavaScript 时保留普通链接；失败不替换旧书籍。日常构建只报告实际检查范围，不推导 PDF、编辑器或跨版本站点已验证。
