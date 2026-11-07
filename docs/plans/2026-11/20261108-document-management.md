---
schema: tao.project.plan/v0.1
id: "DOC_20261108_K957142Z1BMPC8N3"
title: "文档管理与持久化计划"
locale: "zh-Hans"
status: draft
change: "CHG_20261108_J9F9HD68H04ZHSBH"
spec_docs: ["DOC_20261108_ZT37NM8REHBYC520", "DOC_20260914_4C7N0XHQSP7CY69P"]
design_docs: ["DOC_20261108_5AH1TA6VTGQQHAA8"]
---

# 文档管理与持久化计划

<!-- tao:section scope -->
## 目标与边界

tao 管理跨 Agent、跨会话的项目文档与知识契约，包括持久化计划和真实进度；Agent 与客户端负责开发执行、权限、调度和会话恢复。文档能力覆盖创建、更新、语义审查、结构校验、组织出版与退役，不仅管理格式。不强制每次变更产生 spec/design/plan 全套材料。

plan/tasks 保留项目级权威进度，跨会话、协作或需要追踪的工作应维护持久计划，小改动复用已有文档。会话任务只表达临时执行步骤；把实际结果、剩余工作、阻塞和验证摘要回写计划，不逐操作同步。完成的计划是变更记录，当前长期事实归 spec/design/ADR。

<!-- tao:section references -->
## 依据

复用并原位更新 [产品规格](../../product/project-skill.md)、[项目协议](../../product/protocol.md) 与 [架构设计](../../engineering/project-skill.md)，保留已有 ID 和引用。用户已确认产品边界及持久化计划职责。

<!-- tao:section design -->
## 实现边界

skill 从文档需求选择材料，不编排通用开发流程。CLI 提供 new 计划骨架、只读 status、ID/索引、退役、出版及文档校验，不返回下一执行动作。status 只报进度、待办与定位，不复制验证正文或推断审查、交付；长期依据和实际验证结论留在文档原文。

分发只包含被文档管理消费者读取或运行的资源；开发 tao 自身所需的工程依据留在顶层 docs。项目测试、lint 等由项目原生命令入口管理，不在 .tao/config.toml 保存或执行。客户端接入限于项目作用域，不修改全局配置，不启动真实模型会话。

<!-- tao:section tasks -->
## 任务

- [x] `TASK_20261108_VPDMYET6BNTGT9T5` 产品规格、设计与用户文档一致表达文档管理和持久化进度边界。
  - relates: ["REQ_20261108_6FN7VP6CB598Y1DV", "REQ_20261108_EQQAQ6NE9CBMT5SP"]
  - verify: 语义核对现有要求、设计、使用示例与文档职责；保留现有对象 ID。
- [x] `TASK_20261108_Q5J4XHMKG7ER4EPW` skill 按文档需要读取规则，分发资源均有指令读者或运行时消费者。
  - relates: ["REQ_20261108_2KN2TMG33K5M47TV"]
  - verify: 检查分发引用闭包和当前入口，确认计划读写契约完整且无强制开发阶段。
- [x] `TASK_20261108_VV2K40CJH0AJ3HX8` CLI 提供可跨进程读取的真实项目进度，不编排执行。
  - relates: ["REQ_20261108_EQQAQ6NE9CBMT5SP"]
  - verify: 隔离项目运行 new、status、show、verify，重新启动进程读取内联和附件任务；查询无文件副作用。
- [x] `TASK_20261108_RRT2SEKYXQ0AVYXC` 文档结构、相关回归与实际发布界面通过集成验证。
  - relates: ["REQ_20261108_C06F8GD5AWHTY6AD"]
  - verify: 运行 Python 回归、源文档校验、book 构建与浏览器检查，记录实际覆盖范围和未验证项。
- [x] `TASK_20261108_B3JHV9VNEFE03DGX` 文档 profile 与条目字段均有独立语义，模板、消费者和文档一致。
  - relates: ["REQ_20260914_42AXMZ2KH2RAZ8M3"]
  - verify: 对照注册表的全部 profile、条目、任务与退役格式核对字段用途；实际生成文档并校验 ID、关系及退役记录。
- [x] `TASK_20261108_3E6F6A8FMGADVZXV` 原生命令入口管理项目检查，tao 仅管理文档校验与结果知识。
  - relates: ["REQ_20260914_0J68SDKV86ENKER2"]
  - verify: just check 执行测试、lint 和依赖核对；CLI smoke 确认 verify 仅校验文档、不执行项目命令，未知配置及选项明确拒绝，验证摘要可从计划读取。
- [x] `TASK_20261108_JF1STEYRTENB7XDF` 元数据仅包含独立知识或必要进度信息，全部受管理文档符合契约。
  - relates: ["REQ_20260914_42AXMZ2KH2RAZ8M3"]
  - verify: 校验器拒绝未知字段；退役日期、真实关系、跨计划共享设计和九类 profile 均有效。
- [x] `TASK_20261108_DTFVVJ6B6WP4GTNH` CLI 采用单一简洁输出，结果知识从文档读取。
  - relates: ["REQ_20261108_EQQAQ6NE9CBMT5SP"]
  - verify: 实际运行 verify/status/show 与底层索引；检查待办和计数、内联/附件进度变化、无验证正文复制及未知选项拒绝，查询不写文件。
- [x] `TASK_20261108_EXNW9RYJ31J1CN84` review/evidence 详情存于临时材料，结论归计划与知识文档。
  - relates: ["REQ_20261108_M77FHDMQ112NKMDP"]
  - verify: 校验器拒绝未知 schema 和 ID 类型；九类 profile、临时报告排除及 TASK 普通来源链接通过实际校验。
- [x] `TASK_20261108_RK0JE4EWNCZ1W98X` 文档与代码说明只描述当前功能、状态及有效约束。
  - relates: ["REQ_20261108_M77FHDMQ112NKMDP"]
  - verify: 审阅维护文档、skill 指引、代码注释与测试说明；执行项目检查、源校验和出版检查，确认 ID、引用及当前契约有效。

<!-- tao:section verification -->
## 验证

当前契约见 [文档契约](../../engineering/documentation/contract.md)，项目检查归属见 [架构决定](../../engineering/decisions/per-check-reuse.md)。DOC/CHG/TASK ID、有效关系与成果任务保持稳定。

文档、skill 指引与测试名称以当前功能、状态和有效约束为准；运行时逻辑与测试断言未变。退役、重定向、删除基线和验证时效属于当前功能，保留相应说明。结果集中在本节，其他计划通过链接读取，不复制检查计数。

- 项目检查：`just check` 通过，325 项测试通过、1 项原生客户端发现按默认策略跳过；Ruff E9/F63/F7/F82 与依赖导出核对通过，合并覆盖率 87%。
- 文档检查：`just docs` 通过，按各文档声明的 schema 校验 36 份受管理文档、103 个定义和 103 个引用；HTML 构建与 103 个稳定入口校验通过。没有提供删除基线，`deletion_checked=false`，不证明历史删除追溯完整。
- 实际界面：浏览器核对客户端更新与移除说明、当前元数据契约，并从 skill 计划点击验证摘要链接到文档管理计划的稳定章节。CLI `status` 正确读取本计划的任务计数与待办。
- 审查与限制：按文件范围检查维护文档、skill 指引和代码说明，保留正式 ID、当前行为与有效设计理由；未执行独立代码审查、真实客户端发现、模型会话或跨平台验收。本机 Python 3.14 下有 36 条上游 mini-racer 弃用警告及 coverage 父进程无数据提示，子进程覆盖率合并成功；原始输出与 HTML 留在忽略目录。
