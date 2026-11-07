---
schema: tao.project.plan/v0.1
id: "DOC_20261108_K957142Z1BMPC8N3"
title: "文档管理与持久化计划职责收敛"
locale: "zh-Hans"
status: draft
created: "2026-11-08"
change: "CHG_20261108_J9F9HD68H04ZHSBH"
spec_docs: ["DOC_20261108_ZT37NM8REHBYC520", "DOC_20260914_4C7N0XHQSP7CY69P"]
design_docs: ["DOC_20261108_5AH1TA6VTGQQHAA8"]
---

# 文档管理与持久化计划职责收敛

<!-- tao:section scope -->
## 目标与边界

tao 管理跨 Agent、跨会话的项目文档与知识契约，包括持久化计划和真实进度；Agent 与客户端负责开发执行、权限、调度和会话恢复。文档能力覆盖创建、更新、语义审查、结构校验、组织出版与退役，不仅管理格式。不强制每次变更产生 spec/design/plan 全套材料。

plan/tasks 保留项目级权威进度，跨会话、协作或需要追踪的工作应维护持久计划，小改动复用已有文档。会话任务只表达临时执行步骤；把实际结果、剩余工作、阻塞和验证摘要回写计划，不逐操作同步。完成的计划是变更记录，当前长期事实归 spec/design/ADR。

<!-- tao:section references -->
## 依据

复用并原位更新 [产品规格](../../product/project-skill.md)、[项目协议](../../product/protocol.md) 与 [架构设计](../../engineering/project-skill.md)，保留已有 ID 和引用。用户已确认产品边界及持久化计划职责。

<!-- tao:section design -->
## 实现边界

skill 从文档需求选择材料，不再提供通用 implement、review code、continue、handoff 或强制阶段主线。CLI 移除 handoff 与 new/status 的 next_actions 编排字段；保留 new 计划骨架、只读 status、ID/索引、退役、出版及显式配置的检查助手。status 继续区分任务进度、验证摘要与未知审查，不把全部勾选等同交付。

分发只保留被文档管理消费者读取或运行的资源；开发 tao 自身所需的工程依据留在顶层 docs。检查助手不变成执行调度器。客户端安装路径及项目隔离边界不变，不修改全局配置，不启动真实模型会话。

<!-- tao:section tasks -->
## 任务

- [x] `TASK_20261108_VPDMYET6BNTGT9T5` 产品规格、设计与用户文档一致表达文档管理和持久化进度边界。
  - relates: ["REQ_20261108_6FN7VP6CB598Y1DV", "REQ_20261108_EQQAQ6NE9CBMT5SP"]
  - verify: 语义核对现有要求、设计、使用示例与文档职责；保留现有对象 ID。
- [x] `TASK_20261108_Q5J4XHMKG7ER4EPW` skill 按文档需要读取规则，移除开发流程编排与无消费者资源。
  - relates: ["REQ_20261108_2KN2TMG33K5M47TV"]
  - verify: 检查分发引用闭包和当前入口，确认计划读写契约完整且无强制开发阶段。
- [x] `TASK_20261108_VV2K40CJH0AJ3HX8` CLI 移除 handoff 和 next_actions，保留可跨进程读取的真实项目进度。
  - relates: ["REQ_20261108_EQQAQ6NE9CBMT5SP"]
  - verify: 隔离项目运行 new、status、show、verify，重新启动进程读取内联和附件任务；被移除命令拒绝且无文件副作用。
- [x] `TASK_20261108_RRT2SEKYXQ0AVYXC` 文档结构、相关回归与实际发布界面通过集成验证。
  - relates: ["REQ_20261108_C06F8GD5AWHTY6AD"]
  - verify: 运行 Python 回归、源文档校验、book 构建与浏览器检查，记录实际覆盖范围和未验证项。

<!-- tao:section verification -->
## 验证

隔离项目真实进程 smoke 已通过：new 生成计划并填入真实内容后通过源校验；show 定位任务；分别用 CHG、DOC 和计划路径读取 pending；回写文件后新进程读取 tasks_complete；迁移唯一任务集到附件后读取 in_progress 和准确的未完成任务。查询未写入文件；删除临时会话摘要不影响进度；handoff 被拒绝且没有写入；全部勾选仍为 review=unknown；隔离 HOME 未改变。

- 回归：`.venv/bin/python -m pytest -q`，335 项通过，1 项真实原生发现按默认策略跳过；上游 mini-racer 在 Python 3.14 下产生两条弃用警告。
- 静态与依赖：Ruff 的 E9/F63/F7/F82 检查及 `scripts/export_dependencies.py --check` 通过。
- 文档：`tao verify --only docs --simplified --format json` 通过，覆盖 36 份受管理文档、97 个定义和 97 个引用；未提供历史基线，deletion_checked=false，只证明当前集合一致。
- 出版：`tao docs build --format json` 通过，97 个稳定入口校验通过；浏览器实际打开文档协作指南、点击持久进度章节并确认可读正文与导航。
- 分发：实际打包产物从 SKILL.md 遍历本地 Markdown 链接，15 份 references 全部可达，检查 23 份 Markdown 资源，无越出包的依赖；副本无第三方依赖的 help 正常且无 handoff。全量回归另覆盖四个客户端路径的文件复制和保护边界，不代表实际发现。
- 生成计划：模板正文指导曾被 status 原样带入验证摘要，已移回持久计划规程；最终模板用真实 new → 填写 → status → verify smoke 确认摘要只含实际内容且文档有效。
- 审查：集成者核对 skill、规格、设计、用户指南、CLI 及相关测试的职责一致性；复用现有 spec/design，保留对象 ID、历史计划结果及唯一进度源。代码自查确认没有残留 handoff 调用、next_actions 或旧完成状态消费者。未另行执行独立代码审查。

限制：未运行真实客户端发现、模型会话、Windows 或其他 Python 版本；语义指导的跨客户端实际行为仍未验证。个人配置与其他项目未改动；临时 smoke 脚本、隔离项目和打包副本已清理，浏览器页与预览服务已关闭。
