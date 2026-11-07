---
schema: tao.project.plan/v0.1
id: DOC_20260916_02VZ80J4JY1C51GT
title: Agent 工作流行为测试实施计划
locale: zh-Hans
status: draft
created: "2026-09-16"
change: CHG_20260916_JT1P74T8YB727X82
spec_docs: ["DOC_20260914_4C7N0XHQSP7CY69P"]
design_docs: ["DOC_20260916_9JTJ8914RCDARFGJ"]
updated: "2026-09-17"
---

# Agent 工作流行为测试实施计划

> 历史计划：保留当时的目标、任务与实测范围，不作为当前操作规程；当前纯 skill 契约见 [项目级重构](../2026-11/20261108-project-skill.md)。旧机制的历史通过不证明当前版本通过。

<!-- tao:section scope -->
## 目标与边界

实现可执行行为契约、多轮场景、确定性判定器、LLM 语义置信度、违规注入测试和汇总报告，并通过真实 Claude Code CLI 与 Codex CLI 验收 tao-dev 的文档加载、工作流和交互行为。其他 coding agent CLI 暂不实现。

每个任务采用测试先行，完成相称验证后单独提交。当时普通 pytest 不调用模型；当前 Cursor/Kiro hook 探针在 CLI 已安装且已登录时由普通 pytest 自动运行，保持隔离、45 秒硬超时、可计费并保存脱敏证据。其他真实 CLI 长流程仍显式启动。工作分支为 `codex/agent-behavior-testing`，基线为 `1dd6d47`，基线回归为 382 passed、5 skipped。

人工复核默认仅处理低置信度、评审分歧、未知事件和持续基础设施阻断；高风险授权与写入规则必须优先确定性化。

<!-- tao:section references -->
## 规格依据

关联 {need}`REQ_20260914_BFNMKT34JF1BSGW2`、{need}`REQ_20260914_0J68SDKV86ENKER2`、{need}`REQ_20260914_4GKT5JRVBJNCQ05X`、{need}`REQ_20260914_BWAY1ZF6HNPM855Y` 与 {need}`REQ_20260914_4CS6P421MGW68PME`。详细边界和数据契约见 {need}`DOC_20260916_9JTJ8914RCDARFGJ`。

<!-- tao:section design -->
## 设计引用

采用独立行为契约、自然场景、标准事件、确定性时序判定和保守语义置信度。现有 `tests/acceptance/clients.py` 的认证、隔离、日志权限和进程终止机制继续复用；新增模块按契约加载、事件判定、语义聚合和运行编排拆分，不把所有职责继续堆入单文件。

<!-- tao:section tasks -->
## 任务

- [x] `TASK_20260916_A27CQHC5PS2F2DXM` 固化行为测试设计、实施计划和导航入口。
  - relates: ["REQ_20260914_4GKT5JRVBJNCQ05X", "CHG_20260916_JT1P74T8YB727X82"]
  - depends_on: []
  - verify: 运行受管理文档验证，确认设计、计划、规格关系和导航均可解析；提交只包含文档。
  - evidence: [验证记录](#DOC_20260916_02VZ80J4JY1C51GT--verification)

- [x] `TASK_20260916_GPHMFW1YFH133KHB` 实现可执行行为契约、场景 schema 和覆盖门禁。
  - relates: ["REQ_20260914_4GKT5JRVBJNCQ05X", "CHG_20260916_JT1P74T8YB727X82"]
  - depends_on: ["TASK_20260916_A27CQHC5PS2F2DXM"]
  - verify: 先新增缺规则、重复 ID、非法 oracle 和无场景覆盖的失败测试，再实现 `tests/acceptance/behavior_contract.py`、契约与场景 YAML；定向 pytest 全部通过。
  - evidence: [验证记录](#DOC_20260916_02VZ80J4JY1C51GT--verification)

- [x] `TASK_20260916_1B81NB6QNKZE2GAA` 实现标准事件、真实读取证据和确定性工作流 oracle。
  - relates: ["REQ_20260914_0J68SDKV86ENKER2", "REQ_20260914_4CS6P421MGW68PME", "CHG_20260916_JT1P74T8YB727X82"]
  - depends_on: ["TASK_20260916_GPHMFW1YFH133KHB"]
  - verify: 先用授权前写入、仅提及路径、漏读／多读、验证后修改和不支持完成声明的合成 trace 观察失败，再实现 `tests/acceptance/behavior_trace.py` 并通过定向回归。
  - evidence: [验证记录](#DOC_20260916_02VZ80J4JY1C51GT--verification)

- [x] `TASK_20260916_KQBQCS7VV58XQ2CG` 实现确定性多轮场景运行器和 Claude／Codex 会话适配。
  - relates: ["REQ_20260914_BFNMKT34JF1BSGW2", "REQ_20260914_BWAY1ZF6HNPM855Y", "CHG_20260916_JT1P74T8YB727X82"]
  - depends_on: ["TASK_20260916_1B81NB6QNKZE2GAA"]
  - verify: 先以伪进程证明会话 ID 丢失、独立调用冒充接续、意外写入和用户脚本条件不匹配会失败，再实现 `tests/acceptance/behavior_clients.py` 与 `behavior_runner.py`；普通测试不启动真实模型。
  - evidence: [验证记录](#DOC_20260916_02VZ80J4JY1C51GT--verification)

- [x] `TASK_20260916_TGDQX3JKZVGFHHCR` 实现 LLM 语义评审、校准置信度和人工升级决策。
  - relates: ["REQ_20260914_0J68SDKV86ENKER2", "REQ_20260914_M05MAGDARWBY5D44", "CHG_20260916_JT1P74T8YB727X82"]
  - depends_on: ["TASK_20260916_KQBQCS7VV58XQ2CG"]
  - verify: 先覆盖模型自评分无效、证据缺失、双评审分歧、校准不足及严重度门槛，再实现 `tests/acceptance/behavior_judgment.py`；定向测试确认 pass、fail、review、blocked 分离。
  - evidence: [验证记录](#DOC_20260916_02VZ80J4JY1C51GT--verification)

- [x] `TASK_20260916_3MS6AF05Z6TQWE9P` 实现违规注入、行为向量和汇总／待复核队列报告。
  - relates: ["REQ_20260914_0J68SDKV86ENKER2", "REQ_20260914_4GKT5JRVBJNCQ05X", "CHG_20260916_JT1P74T8YB727X82"]
  - depends_on: ["TASK_20260916_TGDQX3JKZVGFHHCR"]
  - verify: 对八类已知违规逐项注入并要求检出，验证契约覆盖、已知违规检出率、客户端矩阵、置信度和人工队列摘要；定向 pytest 与重放测试通过。
  - evidence: [验证记录](#DOC_20260916_02VZ80J4JY1C51GT--verification)

- [x] `TASK_20260916_X73FES5FJJNJF7Z0` 完成双 CLI 真实行为验收、全量回归和维护说明。
  - relates: ["REQ_20260914_BWAY1ZF6HNPM855Y", "REQ_20260914_4CS6P421MGW68PME", "CHG_20260916_JT1P74T8YB727X82"]
  - depends_on: ["TASK_20260916_3MS6AF05Z6TQWE9P"]
  - verify: 在全新隔离 workspace 中分别运行 Claude Code CLI 2.1.270 与 Codex CLI 0.154.0 的关键自然／多轮场景，保存实际版本、事件、差异、费用、置信度和结论；再运行全量 pytest、Ruff、文档、链接、HTML 与包验证。
  - evidence: [验证记录](#DOC_20260916_02VZ80J4JY1C51GT--verification)

<!-- tao:section verification -->
## 验证

每项先运行新增测试并确认因缺少行为而失败，再编写最小实现、运行定向回归和相关既有测试。提交前检查实际 diff 和工作树；每项使用独立英文提交消息，正文说明上下文、用户影响、实现与验证，按 72 列换行。

真实客户端验收不以客户端退出码代替行为判断。Claude 与 Codex 分别验证 skill 调用、必要 reference 读取、禁止读取、写入范围、阶段顺序、检查执行和最终声明。认证、服务端、超时或必要遥测失败记为 blocked；本计划要求两端真实运行通过后才完成。

<!-- tao:results -->
行为验收契约、事件归一化、多轮运行器、语义裁决及报告已实现。确定性检查覆盖12条规则、9个场景，八类已知违规注入检出8/8；伪造证据、混合会话、条件不匹配、遥测缺失及低置信度均有拒绝边界，不能由模型自评分取得通过。

最终真实会话使用Claude Code2.1.270与Codex0.154.0。两端routing只加载SKILL、workflow与engineering，修复后编译通过且保护文件与监测配置未变；材料未知场景均首轮零写入提问，在同一session完成第二轮且不重复提问。Claude两例事件标识claude-sonnet-5，Codex配置为gpt-5.6-sol而事件未独立确认模型；CLI估算不等于账单。

完整pytest为428 passed、5原生探针 skipped；配置Ruff、受管理文档、HTML稳定链接、依赖清单及两种包检查通过。额外全规则Ruff扫描的218项既有诊断未纳入本次门槛，不以格式化掩盖基线。真实会话只证明上述客户端版本与合成场景，不代表所有行为规则已获真实模型验收或完整产品交付。原始事件在忽略临时目录，不保证长期可还原。

<!-- /tao:results -->

<!-- tao:section questions -->
## 待确认事项

无。
