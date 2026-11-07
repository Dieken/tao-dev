---
schema: tao.project.design/v0.1
id: DOC_20260914_Y5RR8BVF6065JTYP
title: 文档组织与产物保存
locale: zh-Hans
status: draft
created: '2026-09-14'
updated: "2026-09-18"
spec_docs: ["DOC_20260914_4C7N0XHQSP7CY69P"]
---

# 文档组织与产物保存

<!-- tao:section overview -->
## 目标

长期知识各有唯一位置，目录按阅读主题组织，不按执行阶段复制正文。落实 {need}`REQ_20260914_NN0AEQ2E1GTVSMTV`、{need}`REQ_20260914_3JQXRKWXKAZSNJ5R` 和 {need}`REQ_20260914_0J68SDKV86ENKER2`。运行写法见 [文档组织](../../../skills/tao-dev/references/document-layout.md)。

<!-- tao:section architecture -->
## 归属与导航

规格维护能力及 REQ/UC，设计维护边界和实现依据，跨事项取舍抽 ADR，计划维护一次目标的任务与当前验证摘要。任务默认内联，必要时由 tasks_doc 唯一关联附件；不引入审批、生命周期或流程文件。

book 以 navigation profile 和 MyST toctree 表达主位置与顺序，不另设 parent/order 或 SUMMARY。每页只有一处主位置，普通链接可跨主题引用；导航须可达、无环、无重复目标。新增文档与导航同批更新。生成编号不写进标题、文件名或稳定 href；正文、侧栏和页内目录共用编号。

长期计划默认 docs/plans/<yyyy-mm>/<yyyymmdd>-<slug>.md；附件同月同 stem。日期与 slug 仅服务浏览，移动与改名保留 ID。创建不覆盖同名文件，路径和符号链接解析后不能越出项目。

## 保留与临时材料

普通 review/evidence 详细输出留 temporary（默认 tmp/tao）或 CI，计划合并当前简短结论。显式 handoff 只替换 temporary/handoffs/<CHG-or-DOC>.md，不建 DOC/EVD，不加入导航，不是继续工作的前置条件。

确有独立引用、审计或长期复查价值时才用 evidence profile；不能仅因执行过某轮检查就建报告。保留有价值的历史结果、输入范围及限制，不改写旧失败为成功。退役记录按现有 JSONL 格式保存到 docs/retired，区分已删除对象与仍可使用但不推荐的功能。

<!-- tao:section verification -->
## 出版检查

修改出版器时以真实 HTML 核对引用标题转义、唯一 DOM 锚点、复制链接、前后关系、章节编号和中文搜索；中文相邻字符对索引不保证单字搜索。改标题、移动文件及重排导航后访问旧固定入口。章节重定向仍可指向保留的文档，禁用 JavaScript 时保留普通链接；失败不替换旧书籍。日常构建只报告实际检查范围，不推导 PDF、编辑器或跨版本站点已验证。
