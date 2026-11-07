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
- [x] `TASK_20261108_CV1SBCKZTXESGGGE` 测试去除措辞锁定与重复路径，配置和退役记录错误各有有效断言。
  - verify: 运行项目检查；真实 CLI 使用非默认计划目录并分别拒绝重复 JSON 键和空行；注入对应故障确认断言可捕获，保留无外部 Node 的真实重定向验证。
- [x] `TASK_20261108_ERZHNWMYD35YEQJY` skill 参考集中维护文档契约，去除重复规则、通用工程训诫和审查执行编排。
  - relates: ["REQ_20261108_2KN2TMG33K5M47TV"]
  - verify: 核对合并后的指引与原契约，检查分发及仓库引用闭包；实际读取 profile、运行源文档校验，区分 skill 普通 Markdown 与受管理文档的检查范围。

<!-- tao:section verification -->
## 验证

当前契约见 [文档契约](../../engineering/documentation/contract.md)，项目检查归属见 [架构决定](../../engineering/decisions/per-check-reuse.md)。DOC/CHG/TASK ID、有效关系与成果任务保持稳定。

本次仅精简 skill 指引及其引用：文档归属集中到 documents，结果保存集中到 planning，文档校验与可选配置集中到 tools；删除重复说明、通用工程训诫和审查执行编排。参考文档从 14 份减至 10 份，全部 skill Markdown 的 UTF-8 大小从 51,614 降至 42,338 字节。schema、12 份模板、CLI 实现与测试未改动。

- 分发与读取：实际构建未安装到任何客户端的临时 skill 包；23 份 Markdown 的 61 个本地链接及 20 个标题片段均有效，10 份参考均可从 SKILL 入口到达。包内实际读取 plan/zh-Hans、spec/en profile，使用包内 CLI 查询本仓库计划，返回正确的计划、任务来源及本次待办；没有启动模型会话。
- 源文档检查：`tao verify --format json` 按各文档声明的 schema 校验 36 份受管理文档、105 个定义和 104 个引用，无诊断。skill 指令不是受管理 schema 文档，由上述链接检查与内容核对覆盖。未提供删除基线，deletion_checked=false，不证明历史删除追溯完整。
- 既有测试结果：精简前的测试调整记录为 321 项通过、1 项原生客户端发现跳过，Ruff 与依赖导出核对通过，合并覆盖率 87%；隔离 CLI 已检查非默认计划目录、退役记录重复键与空行，故障注入已撤销。本轮未复跑这些代码检查，不将既有结果视为当前文案或客户端行为的验证。
- 审查与限制：核对了合并后的文档管理契约与职责边界，未执行独立审查、真实客户端发现、模型行为、跨平台或 HTML 出版检查。临时分发包与 smoke 检查均已清理，无全局安装或配置改动。
