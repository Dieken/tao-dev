---
schema: tao.project.plan/v0.1
id: "DOC_20261108_K957142Z1BMPC8N3"
title: "文档管理与持久化计划职责收敛"
locale: "zh-Hans"
status: draft
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

skill 从文档需求选择材料，不再提供通用 implement、review code、continue、handoff 或强制阶段主线。CLI 保留 new 计划骨架、只读 status、ID/索引、退役、出版及文档校验，不返回下一执行动作。status 只报进度、待办与定位，不复制验证正文或推断审查、交付；长期依据和实际验证结论留在文档原文。

分发只保留被文档管理消费者读取或运行的资源；开发 tao 自身所需的工程依据留在顶层 docs。项目测试、lint 等由项目原生命令入口管理，不在 .tao/config.toml 保存或执行。客户端安装路径及项目隔离边界不变，不修改全局配置，不启动真实模型会话。

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
- [x] `TASK_20261108_B3JHV9VNEFE03DGX` 全部文档 profile 与条目字段完成精简评估，必要变更同步模板、消费者和既有材料。
  - relates: ["REQ_20260914_42AXMZ2KH2RAZ8M3"]
  - verify: 对照注册表的全部 profile、条目、任务与退役格式说明保留或精简依据；实际生成文档并执行校验，保留 ID、关系及历史记录语义。
- [x] `TASK_20261108_3E6F6A8FMGADVZXV` 项目检查交回原生命令入口，tao 仅管理文档校验与结果知识。
  - relates: ["REQ_20260914_0J68SDKV86ENKER2"]
  - verify: just check 实际执行原测试、lint 和依赖核对；CLI smoke 确认 verify 仅校验文档、旧配置及选项拒绝且不执行命令，计划验证摘要仍可查询。
- [x] `TASK_20261108_JF1STEYRTENB7XDF` 删除没有独立知识或进度价值的可选元数据，并迁移全部受管理文档。
  - relates: ["REQ_20260914_42AXMZ2KH2RAZ8M3"]
  - verify: created/updated、design.change 从 schema 与已有材料移除；旧字段拒绝，退役日期、真实关系、跨计划共享设计和全部保留的 profile 保持有效。
- [x] `TASK_20261108_DTFVVJ6B6WP4GTNH` CLI 采用单一简洁输出，结果知识仍从文档读取。
  - relates: ["REQ_20261108_EQQAQ6NE9CBMT5SP"]
  - verify: 检索 summary/simplified 消费者并实际运行 verify/status/show 与底层索引；检查待办和计数、内联/附件进度变化、无验证正文复制及旧选项拒绝，查询不写文件。
- [x] `TASK_20261108_EXNW9RYJ31J1CN84` review/evidence 不再作为长期受管理文档，结论回到计划与知识文档。
  - relates: ["REQ_20261108_M77FHDMQ112NKMDP"]
  - verify: evidence profile、EVD、模板及专属校验/出版/退役消费者移除；旧 schema 和 ID 拒绝，九类 profile、临时报告排除及 TASK 普通来源链接通过实际校验。

<!-- tao:section verification -->
## 验证

本次完成 schema 字段、输出模式与长期文档范围精简；长期取舍见 [文档契约](../../engineering/documentation/contract.md)，项目检查归属见 [架构决定](../../engineering/decisions/per-check-reuse.md)。保留既有 DOC/CHG/TASK ID、有效关系与计划结果知识。

- 字段：删除 created、updated、design.change，并迁移全部 36 份受管理文档；保留有知识或进度价值的关系、任务依赖、来源链接及退役日期。evidence profile、EVD、模板、专属时间/结果/范围元数据与校验、出版、退役消费者完整移除；review 本就无独立 profile，两者不再作为长期文档管理。
- 结果归属：review/evidence 详情放临时目录或 CI，结论合并到计划、规格、设计或 ADR。TASK.evidence 仅为普通 Markdown 来源链接。仓库没有需迁移的独立正式 evidence 文档或 EVD 退役记录。
- 命令：.tao/config.toml 仅保留版本、语言与文档配置；测试、lint、报告和依赖核对由 justfile 管理。verify/status 固定紧凑输出，删除 simplified 与只读 verify 的 dry-run；status 不复制已完成任务及验证正文，不输出固定审查占位。完整结构索引仍通过底层校验入口读取。
- summary 检索：运行时代码不再有摘要复制或单独 summary 功能；剩余命中为旧参数拒绝测试、临时文件样例、契约说明或历史检查命令。普通临时总结与导航说明不需要 CLI 模式；历史真实命令不改写成现行接口。
- 实际 CLI smoke：en/zh-Hans 分别生成并校验全部九类模板，每组 9 份文档、15 个定义、2 个引用；旧基础日期、design.change、review/evidence schema 和 EVD 分配均拒绝。verify/status 查询前后逐文件内容一致。
- 实际进度 smoke：new 后填写两项任务，新进程依次观察 pending、in_progress、tasks_complete；迁移到唯一 tasks 附件后继续正确读取状态。show 定位附件任务，底层 JSON 索引包含正式定义；旧输出参数拒绝，验证正文保留在计划源文件。
- 项目检查：`just check` 通过，325 项测试通过、1 项原生客户端发现按默认策略跳过；覆盖九类 profile/locale、字段拒绝、共享设计、临时材料排除、普通来源链接、状态、退役与出版。Ruff 的 E9/F63/F7/F82 与依赖导出核对通过；合并覆盖率 87%。首轮有一项模板行布局断言失败，删除该偶然断言后通过，未重设行号常量。
- 文档：`just docs` 通过，36 份文档、102 个定义、102 个引用，HTML 构建与 102 个稳定入口校验通过。未提供历史基线，deletion_checked=false。浏览器实际点击字段最小集并核对九类 profile 的表格，再沿导航打开产物保存页面，确认无长期 evidence 类型且普通任务来源链接仍保留。
- 审查与限制：集成者核对字段价值、CLI 和指引一致性；没有独立代码审查或真实模型行为验收。只在本机 Python 3.14 运行，未实测 Windows、其他 Python 或真实客户端发现。上游 mini-racer 仍有 36 条弃用警告，coverage 父进程提示无数据，子进程合并及报告成功，未压制警告。隔离 smoke 项目已清理，原始日志与 HTML 留忽略目录，个人客户端配置未改动。
