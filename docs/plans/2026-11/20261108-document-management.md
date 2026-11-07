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

skill 从文档需求选择材料，不再提供通用 implement、review code、continue、handoff 或强制阶段主线。CLI 移除 handoff 与 new/status 的 next_actions 编排字段；保留 new 计划骨架、只读 status、ID/索引、退役、出版及文档校验。status 继续区分任务进度、验证摘要与未知审查，不把全部勾选等同交付。

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

<!-- tao:section verification -->
## 验证

本次补充全部 schema 字段审查与项目命令职责切换；长期字段矩阵与取舍见 [文档契约](../../engineering/documentation/contract.md)，命令及缓存归属见 [架构决定](../../engineering/decisions/per-check-reuse.md)。保留已有 DOC/CHG/TASK ID、真实日期、有效关系和计划结果摘要。

- 字段：created 改可选并从全部十类模板移除；evidence.coverage 改可选，默认用正文说明范围；plan/tasks 模板省略空依赖和重复所属 CHG。移除无消费者的 results 成对标记和 handoff 模板，不删除身份、生命周期、验收或追溯关系。
- 命令：.tao/config.toml 仅保留版本、语言与文档配置；原 Python 测试、Ruff 命令及报告路径迁到 justfile，check 另保留依赖导出核对。CLI 删除通用执行、缓存、指标和候选扫描，verify 仅校验文档；旧配置、选择器与执行参数拒绝。
- 实际 CLI smoke：en/zh-Hans 各通过十类模板的独立生成与校验，每组 10 份文档、17 个定义、2 个引用；无需 created 或 coverage，未写入受检文件。错误 coverage、旧 --only 与 verification 配置被拒绝，无命令执行或文件副作用。
- 实际计划 smoke：new → 填写 → verify → status 返回 pending；勾选后新进程返回 tasks_complete，验证正文准确且 review 仍为 unknown。默认骨架不含日期、空依赖或重复 CHG；隔离项目已清理。
- 项目检查：`just check` 实际通过，323 项测试通过、1 项原生发现按默认策略跳过；包括全部 profile/locale、日期与 coverage 边界、文档关系、状态、退役、出版、复制及旧接口拒绝。Ruff 的 E9/F63/F7/F82 结果为空，依赖清单核对通过；覆盖率合并报告为 88%，原始数据保留 tmp/tao。
- 文档：`just docs` 通过，当前 36 份文档、99 个定义、99 个引用，HTML 构建与 99 个稳定入口校验通过。未提供历史基线，deletion_checked=false，不证明历史删除追溯完整。浏览器实际点击字段最小集，确认表格可读，并从导航打开开发指南核对项目命令归属。
- 审查：只读审查覆盖全部十类 profile、基础字段、REQ/UC/ADR/TASK、术语、导航和退役记录；集成者核对代码与文档一致性。没有独立代码审查或真实模型行为验收。

限制：仅在本机 Python 3.14 运行；未实测 Windows、其他 Python 版本、真实客户端发现或模型会话。并发测试中上游 mini-racer 产生 36 条弃用警告，coverage 的父进程提示无数据，但子进程数据合并及最终报告成功；未压制警告。个人配置和其他项目未改动；普通检查日志与 HTML 留在忽略的临时目录，不另建证据文档。
