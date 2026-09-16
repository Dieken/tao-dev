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
---

# Agent 工作流行为测试实施计划

<!-- tao:section scope -->
## 目标与边界

实现可执行行为契约、多轮场景、确定性 oracle、LLM 语义置信度、变异测试和汇总报告，并通过真实 Claude Code CLI 与 Codex CLI 验收 tao-dev 的文档加载、工作流和交互行为。其他 coding agent CLI 暂不实现。

每个任务采用测试先行，完成相称验证后单独提交。普通 pytest 不调用模型；真实 CLI 运行保持显式、隔离、限时、可计费并保存脱敏证据。工作分支为 `codex/agent-behavior-testing`，基线为 `1dd6d47`，基线回归为 382 passed、5 skipped。

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

- [ ] `TASK_20260916_3MS6AF05Z6TQWE9P` 实现违规变异、行为向量和汇总／可疑队列报告。
  - relates: ["REQ_20260914_0J68SDKV86ENKER2", "REQ_20260914_4GKT5JRVBJNCQ05X", "CHG_20260916_JT1P74T8YB727X82"]
  - depends_on: ["TASK_20260916_TGDQX3JKZVGFHHCR"]
  - verify: 对八类已知违规逐项注入并要求检出，验证契约覆盖、mutation detection rate、客户端矩阵、置信度和人工队列摘要；定向 pytest 与 replay 测试通过。

- [ ] `TASK_20260916_X73FES5FJJNJF7Z0` 完成双 CLI 真实行为验收、全量回归和维护说明。
  - relates: ["REQ_20260914_BWAY1ZF6HNPM855Y", "REQ_20260914_4CS6P421MGW68PME", "CHG_20260916_JT1P74T8YB727X82"]
  - depends_on: ["TASK_20260916_3MS6AF05Z6TQWE9P"]
  - verify: 在全新隔离 workspace 中分别运行 Claude Code CLI 2.1.270 与 Codex CLI 0.154.0 的关键自然／多轮场景，保存实际版本、事件、差异、费用、置信度和结论；再运行全量 pytest、Ruff、文档、链接、HTML 与包验证。

<!-- tao:section verification -->
## 验证

每项先运行新增测试并确认因缺少行为而失败，再编写最小实现、运行定向回归和相关既有测试。提交前检查实际 diff 和工作树；每项使用独立英文提交消息，正文说明上下文、用户影响、实现与验证，按 72 列换行。

真实客户端验收不以客户端退出码代替行为判断。Claude 与 Codex 分别验证 skill 调用、必要 reference 读取、禁止读取、写入范围、阶段顺序、检查执行和最终声明。认证、服务端、超时或必要遥测失败记为 blocked；本计划要求两端真实运行通过后才完成。

<!-- tao:results -->
基线：在隔离 worktree 中准备锁定 wheelhouse 与独立运行环境；完整 pytest 为 382 passed、5 skipped，耗时 593.18 秒。5 项 skip 均为需显式开启的既有原生安装探针，基线无失败。
任务 1：新增行为测试设计、七项实施计划及工程／计划导航入口；41 份受管理文档通过结构、ID、关系和导航检查，无诊断。
任务 2：新增 12 条行为规则、9 个自然场景及严格 catalog loader；重复规则、非法严重度／oracle、未知客户端／规则、单客户端覆盖缺口和 prompt 泄漏均在模型启动前拒绝。13 项契约与既有 reference 读取回归通过。
任务 3：新增 Claude／Codex JSONL 标准事件、保守的真实资源读取判定、workspace 哈希差异和八类确定性 oracle；路径存在性检查只记为提及，命令生命周期去重，遥测不完整统一阻断。21 项轨迹、契约与既有 reference 读取回归通过，定向 Ruff 无诊断。
任务 4：新增仅支持 Claude Code 与 Codex 的命令适配、显式会话接续、条件式确定用户回复和有界进程组清理；真实会话 ID 缺失／变化、条件不匹配、超时和退出失败统一阻断，逐轮文件差异进入同一 trace。29 项运行器、轨迹、契约与兼容回归通过，定向 Ruff 无诊断。
任务 5：新增严格语义评审 schema、双评审一致性、事件证据校验和按评审器／规则来源去重的 Wilson 置信下界；模型自评分不参与决策，样本不足、低于严重度门槛、分歧、未知项、伪造证据和非法输出均进入人工复核，遥测缺失保持阻断。38 项行为回归通过，定向 Ruff 无诊断。
<!-- /tao:results -->

<!-- tao:section questions -->
## 未决问题

无。人工复核默认仅处理低置信度、评审分歧、未知事件和持续基础设施阻断；高风险授权与写入规则必须优先确定性化。
