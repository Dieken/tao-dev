---
schema: tao.project.plan/v0.1
id: DOC_20261105_VN5X9G1X9DN0QJWR
title: 工作流状态恢复与生命周期实施计划
locale: zh-Hans
status: draft
created: "2026-11-05"
change: CHG_20261105_YJ2MG6FEGJ4GMXA8
spec_docs: [DOC_20261105_27RJ5NTQG9BNBJHX]
design_docs: [DOC_20261105_0H6V7T4BYCRJW79H]
---

# 工作流状态恢复与生命周期实施计划

<!-- tao:section scope -->
## 目标与边界

本计划完整覆盖已批准规格的九项需求，不分期延后：状态缺失诊断、持久记录、显式及条件自动恢复、多事项定位、切换、收尾与旧资料兼容。工作在 tao/workflow-recovery 分支和隔离 worktree 内进行。正式任务内嵌本计划；不提交本地 workflow JSON，不修改全局 agent 配置，不自动合入、推送或清理其他事项。

项目已有 .tao/config.toml 检查策略，包含诊断本地化、维护回归、lint 和必需独立实现审查。运行环境 doctor 已确认核心及出版 runtime 可用；本阶段没有运行行为基线，不把依赖可用表述为检查通过。使用项目本地 Python，uv 始终传 --no-config。

<!-- tao:section references -->
## 依据

- [工作流恢复规格](../../product/workflow-recovery.md)定义用户承诺与验收场景。
- [工作流恢复设计](../../engineering/workflow-recovery.md)定义记录、CLI、身份兼容和写入协议。
- [文档契约](../../engineering/documentation/contract.md)约束新增 profile、模板与源校验。
- [开发与维护指南](../../engineering/development.md)定义维护检查和平台覆盖边界。

<!-- tao:section design -->
## 方案与取舍

实现遵循对应设计；本次审查修订后须重新批准设计，不在任务内另定产品方案。两文件写入的幂等性是优先验证风险，先建立可执行状态转换和故障注入测试，后续写入实现依赖该任务；暂不引入额外形式化语言或服务，现有 Python 测试可穷举本次有限故障点与重试序列。若反例推翻批准方案，先回到设计修订，不以放宽测试消除反例。

### 需求覆盖

| 需求 | 本计划覆盖任务 |
|---|---|
| {need}`REQ_20261105_12M6WAZSDRR4857Y` | {need}`TASK_20261105_VXBFM3S2RZ5VV5Q8`、{need}`TASK_20261105_A84TSV410Y934TBB`、{need}`TASK_20261105_3ETWP4BF6KC6XRRR`、{need}`TASK_20261105_YDCTK70MVYQGTGYJ`、{need}`TASK_20261105_455AQNSXP6M85JY9` |
| {need}`REQ_20261105_DQY5T199SD08CF93` | {need}`TASK_20261105_5H468EW00RFPK2GH`、{need}`TASK_20261105_418VEP86Q1JHHQ0E`、{need}`TASK_20261105_YDCTK70MVYQGTGYJ`、{need}`TASK_20261105_455AQNSXP6M85JY9` |
| {need}`REQ_20261105_GAXA5RZZ60Y774BM` | {need}`TASK_20261105_WMJ4JPXDPTWMDN6J`、{need}`TASK_20261105_YDCTK70MVYQGTGYJ`、{need}`TASK_20261105_455AQNSXP6M85JY9` |
| {need}`REQ_20261105_3C64CBKGB4T22MFR` | {need}`TASK_20261105_VXBFM3S2RZ5VV5Q8`、{need}`TASK_20261105_3ETWP4BF6KC6XRRR`、{need}`TASK_20261105_1DNQEGHVKFRXT8PJ`、{need}`TASK_20261105_WMJ4JPXDPTWMDN6J`、{need}`TASK_20261105_YDCTK70MVYQGTGYJ`、{need}`TASK_20261105_455AQNSXP6M85JY9` |
| {need}`REQ_20261105_AVBWR8XFXC786KXY` | {need}`TASK_20261105_WMJ4JPXDPTWMDN6J`、{need}`TASK_20261105_418VEP86Q1JHHQ0E`、{need}`TASK_20261105_YDCTK70MVYQGTGYJ`、{need}`TASK_20261105_455AQNSXP6M85JY9` |
| {need}`REQ_20261105_83CKHP6YN12QZQHX` | {need}`TASK_20261105_5H468EW00RFPK2GH`、{need}`TASK_20261105_418VEP86Q1JHHQ0E`、{need}`TASK_20261105_YDCTK70MVYQGTGYJ`、{need}`TASK_20261105_455AQNSXP6M85JY9` |
| {need}`REQ_20261105_TE6PX7VZYYKSEQN6` | {need}`TASK_20261105_418VEP86Q1JHHQ0E`、{need}`TASK_20261105_YDCTK70MVYQGTGYJ`、{need}`TASK_20261105_455AQNSXP6M85JY9` |
| {need}`REQ_20261105_NFBV51FB4SS7W5QD` | {need}`TASK_20261105_VXBFM3S2RZ5VV5Q8`、{need}`TASK_20261105_KYSYWBB6PZJ810YC`、{need}`TASK_20261105_YDCTK70MVYQGTGYJ`、{need}`TASK_20261105_455AQNSXP6M85JY9` |
| {need}`REQ_20261105_SPDKCTWSX7PVDNDK` | {need}`TASK_20261105_A84TSV410Y934TBB`、{need}`TASK_20261105_5H468EW00RFPK2GH`、{need}`TASK_20261105_WMJ4JPXDPTWMDN6J`、{need}`TASK_20261105_418VEP86Q1JHHQ0E`、{need}`TASK_20261105_YDCTK70MVYQGTGYJ`、{need}`TASK_20261105_455AQNSXP6M85JY9` |

### 设计决定覆盖

按事项基线以来实际修改的设计文件核对，目前只有工作流恢复设计，没有新增 ADR。以下按其权威章节对应任务，不复制方案正文。

| 设计章节中的决定 | 覆盖任务 |
|---|---|
| 数据归属、模块职责、profile 与 CHG 定义兼容 | {need}`TASK_20261105_A84TSV410Y934TBB`、{need}`TASK_20261105_3ETWP4BF6KC6XRRR`、{need}`TASK_20261105_YDCTK70MVYQGTGYJ` |
| 批准摘要、审查输入归一与额度 | {need}`TASK_20261105_3ETWP4BF6KC6XRRR`、{need}`TASK_20261105_1DNQEGHVKFRXT8PJ` |
| 命令职责、事项选择、切换及诊断 | {need}`TASK_20261105_5H468EW00RFPK2GH`、{need}`TASK_20261105_WMJ4JPXDPTWMDN6J`、{need}`TASK_20261105_418VEP86Q1JHHQ0E` |
| 恢复过程、显式 migrate 与 legacy unknown 表示 | {need}`TASK_20261105_A84TSV410Y934TBB`、{need}`TASK_20261105_WMJ4JPXDPTWMDN6J` |
| 两类写入、中断、并发及收尾 | {need}`TASK_20261105_VXBFM3S2RZ5VV5Q8`、{need}`TASK_20261105_3ETWP4BF6KC6XRRR`、{need}`TASK_20261105_1DNQEGHVKFRXT8PJ`、{need}`TASK_20261105_KYSYWBB6PZJ810YC` |
| 分发资源的消费者与内部文档边界 | {need}`TASK_20261105_418VEP86Q1JHHQ0E`、{need}`TASK_20261105_YDCTK70MVYQGTGYJ` |
| 不变量、失败处理和验证 | {need}`TASK_20261105_VXBFM3S2RZ5VV5Q8`、{need}`TASK_20261105_YDCTK70MVYQGTGYJ`、{need}`TASK_20261105_455AQNSXP6M85JY9` |

<!-- tao:section tasks -->
## 任务

- [x] `TASK_20261105_VXBFM3S2RZ5VV5Q8` 验证两文件持久事件协议及故障点，固定可执行状态转换测试
  - relates: ["REQ_20261105_12M6WAZSDRR4857Y", "REQ_20261105_3C64CBKGB4T22MFR", "REQ_20261105_NFBV51FB4SS7W5QD"]
  - depends_on: []
  - verify: 使用项目 Python 的确定性状态转换测试枚举正式写入前后、本地替换前后失败及重试；检查事件不重复、正式失败本地不前进、revision 相同内容不同可识别；测试先于依赖实现建立，保留代表性失败反例。
  - evidence: [验证记录](#DOC_20261105_VN5X9G1X9DN0QJWR--verification)

- [x] `TASK_20261105_A84TSV410Y934TBB` 新增 workflow profile、模板和 CHG 索引兼容规则
  - relates: ["REQ_20261105_12M6WAZSDRR4857Y", "REQ_20261105_SPDKCTWSX7PVDNDK"]
  - depends_on: ["TASK_20261105_VXBFM3S2RZ5VV5Q8"]
  - verify: 运行源校验与关系测试，覆盖嵌套字段、枚举、一个正式 CHG 关联一个旧 plan、重复定义、路径越界、计划前身份、旧 plan 导入的新记录允许带 legacy 来源的 unknown、非 legacy unknown 被拒绝，以及损坏 JSON 不阻断独立文档检查。
  - evidence: [验证记录](#DOC_20261105_VN5X9G1X9DN0QJWR--verification)

- [x] `TASK_20261105_3ETWP4BF6KC6XRRR` 实现重要事件持久写入、start 与阶段决定同步
  - relates: ["REQ_20261105_12M6WAZSDRR4857Y", "REQ_20261105_3C64CBKGB4T22MFR"]
  - depends_on: ["TASK_20261105_VXBFM3S2RZ5VV5Q8", "TASK_20261105_A84TSV410Y934TBB"]
  - verify: 对 start、advance、revise 和生命周期转换注入文件写入失败；正式记录先保存，本地显式同步后只执行一次；checkpoint 不改正式记录，DOC 绑定随计划及 tasks 契约变化正确失效。
  - evidence: [验证记录](#DOC_20261105_VN5X9G1X9DN0QJWR--verification)

- [x] `TASK_20261105_1DNQEGHVKFRXT8PJ` 持久化审查批次、尝试与额度并验证输入绑定
  - relates: ["REQ_20261105_3C64CBKGB4T22MFR"]
  - depends_on: ["TASK_20261105_3ETWP4BF6KC6XRRR"]
  - verify: 审查开始派发前已保存尝试；失败尝试仍计数；自己的运行字段不使输入变化，批准和范围变化必须使绑定失效；未知轮次不取得新额度，缺快照只影响当前可重放性。
  - evidence: [验证记录](#DOC_20261105_VN5X9G1X9DN0QJWR--verification)

- [x] `TASK_20261105_5H468EW00RFPK2GH` 统一事项发现、目标定位和带路径的诊断
  - relates: ["REQ_20261105_DQY5T199SD08CF93", "REQ_20261105_83CKHP6YN12QZQHX", "REQ_20261105_SPDKCTWSX7PVDNDK"]
  - depends_on: ["TASK_20261105_A84TSV410Y934TBB"]
  - verify: CLI 集成测试覆盖显式 CHG、多个 worktree 同身份、空格路径、无状态旧计划、仅正文引用、共享文档及损坏状态；文本含真实路径和恢复命令，JSON 含稳定诊断与命令参数数组。
  - evidence: [验证记录](#DOC_20261105_VN5X9G1X9DN0QJWR--verification)

- [x] `TASK_20261105_WMJ4JPXDPTWMDN6J` 实现 recover、显式 migrate 和 resume 协调
  - relates: ["REQ_20261105_GAXA5RZZ60Y774BM", "REQ_20261105_3C64CBKGB4T22MFR", "REQ_20261105_AVBWR8XFXC786KXY", "REQ_20261105_SPDKCTWSX7PVDNDK"]
  - depends_on: ["TASK_20261105_3ETWP4BF6KC6XRRR", "TASK_20261105_1DNQEGHVKFRXT8PJ", "TASK_20261105_5H468EW00RFPK2GH"]
  - verify: 以真实临时 Git 项目删除或移动本地状态，先预览确认无写入再应用；保持 CHG 和任务勾选，source digest 改变、并发创建、损坏或现存状态均不覆盖；旧事项仅迁移选定 CHG，缺批准保持阻断；JSON-only/JSON+plan 经 migrate 绑定 revision 和原字节摘要，保留未知字段、批准、轮次及基准，正式成功本地失败后 resume 不重复迁移；plan-only 经 recover 创建合法 unknown 记录并跨目录重读，不误判 active。
  - evidence: [验证记录](#DOC_20261105_VN5X9G1X9DN0QJWR--verification)

- [x] `TASK_20261105_KYSYWBB6PZJ810YC` 实现 finish 正式收尾和历史结果查询
  - relates: ["REQ_20261105_NFBV51FB4SS7W5QD"]
  - depends_on: ["TASK_20261105_3ETWP4BF6KC6XRRR", "TASK_20261105_1DNQEGHVKFRXT8PJ", "TASK_20261105_5H468EW00RFPK2GH", "TASK_20261105_WMJ4JPXDPTWMDN6J"]
  - verify: CLI 验收 completed 满足检查和审查策略、cancelled 有未完成项处置；正式收尾成功而本地失败后重试不重复；advance 共用入口；复制正式资料到新目录后可读历史结束，过期证据不抹去历史结果。
  - evidence: [验证记录](#DOC_20261105_VN5X9G1X9DN0QJWR--verification)

- [x] `TASK_20261105_418VEP86Q1JHHQ0E` 同步 skill 与用户文档的恢复、选择、切换和结束规则
  - relates: ["REQ_20261105_DQY5T199SD08CF93", "REQ_20261105_AVBWR8XFXC786KXY", "REQ_20261105_83CKHP6YN12QZQHX", "REQ_20261105_TE6PX7VZYYKSEQN6", "REQ_20261105_SPDKCTWSX7PVDNDK"]
  - depends_on: ["TASK_20261105_5H468EW00RFPK2GH", "TASK_20261105_WMJ4JPXDPTWMDN6J", "TASK_20261105_KYSYWBB6PZJ810YC"]
  - verify: 检查所有维护入口并运行行为契约测试；覆盖两个会话分别选择、歧义时不写入、continue 条件恢复、切换不执行 git switch 或停止 A、收尾条件满足才建议 finish；真实客户端验证按既有隔离规则记录覆盖与缺口。
  - evidence: [验证记录](#DOC_20261105_VN5X9G1X9DN0QJWR--verification)

- [x] `TASK_20261105_YDCTK70MVYQGTGYJ` 集成发布资源、文档导航并执行九组端到端验收
  - relates: ["REQ_20261105_12M6WAZSDRR4857Y", "REQ_20261105_DQY5T199SD08CF93", "REQ_20261105_GAXA5RZZ60Y774BM", "REQ_20261105_3C64CBKGB4T22MFR", "REQ_20261105_AVBWR8XFXC786KXY", "REQ_20261105_83CKHP6YN12QZQHX", "REQ_20261105_TE6PX7VZYYKSEQN6", "REQ_20261105_NFBV51FB4SS7W5QD", "REQ_20261105_SPDKCTWSX7PVDNDK"]
  - depends_on: ["TASK_20261105_A84TSV410Y934TBB", "TASK_20261105_3ETWP4BF6KC6XRRR", "TASK_20261105_1DNQEGHVKFRXT8PJ", "TASK_20261105_5H468EW00RFPK2GH", "TASK_20261105_WMJ4JPXDPTWMDN6J", "TASK_20261105_KYSYWBB6PZJ810YC", "TASK_20261105_418VEP86Q1JHHQ0E"]
  - verify: 本地打包并检查 profile、模板及运行模块包含而内部设计不包含；构建 HTML 检查新增导航和 CHG 锚点；通过 CLI 驱动复制受跟踪资料的跨目录恢复、多事项和故障场景，逐项记录九个 UC 的实际结果。
  - evidence: [验证记录](#DOC_20261105_VN5X9G1X9DN0QJWR--verification)

- [ ] `TASK_20261105_455AQNSXP6M85JY9` 运行维护回归、独立实现审查并核对交付缺口
  - relates: ["REQ_20261105_12M6WAZSDRR4857Y", "REQ_20261105_DQY5T199SD08CF93", "REQ_20261105_GAXA5RZZ60Y774BM", "REQ_20261105_3C64CBKGB4T22MFR", "REQ_20261105_AVBWR8XFXC786KXY", "REQ_20261105_83CKHP6YN12QZQHX", "REQ_20261105_TE6PX7VZYYKSEQN6", "REQ_20261105_NFBV51FB4SS7W5QD", "REQ_20261105_SPDKCTWSX7PVDNDK"]
  - depends_on: ["TASK_20261105_YDCTK70MVYQGTGYJ"]
  - verify: 运行配置的诊断本地化、维护回归、lint、依赖一致性检查与完整 verify；按授权完成必需独立实现审查并关联实际输入；未覆盖的平台或客户端、阻断和未通过结果保持未完成，不能用源检查代替交付。

<!-- tao:section verification -->
## 验证

### 验收层次和通过条件

每个规格 UC 在实际 CLI 临时项目上执行，不能仅以工具函数单元测试代表用户路径。记录分配的真实 CHG、源资料、命令、输出和副作用；比较预览前后文件及任务状态。状态转换与故障注入测试提供写入边界和反例覆盖；CLI 验收负责源资料发现、路径、错误与恢复的组合行为。

| 规格场景 | 执行层及观察 |
|---|---|
| 持久依据分离 | 临时 Git 项目只复制受跟踪资料，验证无 plan、无 JSON 时仍发现事项 |
| 可操作诊断 | CLI 文本与 JSON 输出，覆盖缺失、损坏、跨 worktree 和空格路径 |
| 预览重建 | CLI 预览无写入、应用后状态一致、重复和并发应用不覆盖 |
| 批准与证据边界 | 修改输入、丢失轮次或基准后恢复，旧事实保留而当前通过不伪造 |
| 按职责恢复 | CLI 验证只读入口；skill 行为检查验证 continue 的触发与授权边界 |
| 多事项选择 | 两个事项、共享材料和历史事项的 CLI 发现，加会话选择行为检查 |
| 切换不结束 | 会话行为验收观察目标变化，原事项生命周期与运行操作不变 |
| 持久收尾 | CLI 完成与取消、写入中断重试、跨目录查询历史结果 |
| 旧资料兼容 | JSON-only、JSON+plan 的 migrate 预览/应用/失败恢复，与 plan-only 的 recover 应用和新目录查询；校验 unknown 及未知字段保留 |

客户端实测使用现有 CLI 与认证，仅在隔离实验项目加载，验证实验外未启用；不能通过重装或全局配置取得测试条件。缺少隔离能力或对应平台时记录 blocked/未覆盖。脚本化行为契约检查不能冒充真实客户端验收。项目既有 Windows 客户端与独立审查缺口不因本次文档检查而消失。

实现过程中运行受影响的定向测试；交付时运行配置的维护回归、lint、诊断目录检查和依赖一致性，以及本地文档构建和完整 verify。必需独立实现审查在另行确认范围与调用预算后开展；尚未授权的模型调用不由计划创建触发。

### 文档审查与实施入口

覆盖自查：九项需求全部落到任务；设计各项决定已有实现和验证任务；持久写入的高风险假设先验证；无孤立任务、无分期遗漏。文档源校验只说明格式和引用满足契约，第一轮独立语义审查提出旧 JSON 迁移入口和未知生命周期两项缺口；已获准修订，本轮定向复核其闭合及影响，不重置审查轮次。项目必需的实现审查仍保留。

<!-- tao:results -->
规格、修订设计与计划已获用户批准，实现已完成。新增正式 workflow profile、recover/migrate/resume/finish、带路径的诊断和 skill 选择规则；本地 JSON 保持忽略。两文件故障、批准绑定、额度、收尾及跨目录恢复均有确定性回归。文档审查两轮通过；[第三轮实现定向复核](20261105-workflow-recovery/reviews/20261105-implementation/05-validation-adjudication.md)确认 I4 已闭合。后续验收发现并修复主目录无法定位缺失状态的子 worktree，统一查询及写命令路径；同时防止无效计划身份破坏发现和检查点。

最新确定性回归使用项目 Python 执行 `-m pytest -q --ignore tests/test_live_acceptance.py --ignore tests/test_native_sessions.py`：687 passed、2 Windows 条件 skipped、2 warnings。来源、选择、迁移收尾和相关文档、审查、诊断测试 149 passed（原生会话模型项排除）；Kiro/ Cursor 原生会话及相关单元检查 7 passed。Ruff 配置规则、依赖一致性、两个包格式的当前运行模块、profile、模板及开发文档排除边界检查通过；测试包未在个人全局状态安装。当前文档检查和出版结果以提交前执行输出为准。

配置的完整代码检查在 40a5dbc 输入上实际运行 1892 秒：681 passed、4 failed、2 skipped，覆盖率 78%，故整体未通过。Claude recover/plan 分别在 48/47 轮后耗尽各 2 美元调用预算；Codex 行为场景收到保留期限后询问尚未给定的清理触发方式；Kiro 原生写入/hook 会话在 45 秒内未取得证据。没有隐去失败或自动提高预算。已补齐行为场景用户回复中的清理触发及后台任务边界，保持不重复提问断言；实际 Codex 复验及相关测试 14 passed。用户随后明确批准仅将 Claude recover/plan 的每次调用预算阈值从 2 调至 4 美元；两项实际重跑均通过（2 passed，1015 秒），全局配置摘要均不变。旧失败记录保留，不以定向重跑替代最终输入的配置检查。Kiro 超时定位为新版 workspace 信任提示，见下文修复及原生结果。

原生隔离范围：Claude 2.1.274 和 Codex 0.166.0 的安装、启停、更新、移除及实验外无启用检查通过。Codex 验收脚本曾将组合 hook 摘要直接写 TOML，已复用安装器原生编辑器，信任及生命周期回归 82 passed、2 Windows 条件 skipped。随后两项 Codex 写入/恢复真实验收通过，Claude 单独恢复验收通过。原先无法归因的全局配置字节变化不计通过；本轮全部已完成隔离实验全局摘要均不变，未回写全局配置。Kiro 的 workspace 提示此前未被旧 PTY 适配器处理；改用 CLI 支持的 --trust-workspace 启动参数，仅在独立项目和隔离 KIRO_HOME 中启用且不保存决定，保留原 45 秒上限。实际原生写入及 hook 反馈通过，个人配置摘要不变；对不支持该参数的旧客户端不注入未知选项。Windows 原生客户端未覆盖。

| 规格用例 | 实际执行与观察 |
|---|---|
| {need}`UC_20261105_MN5FGBTN6BXX1NER` | 真实 CLI 创建无 plan 事项，仅复制 docs 到另一目录，发现同一 CHG 和阶段，不复制 JSON。 |
| {need}`UC_20261105_CMB2P2PF02KQWTMC` | 含空格的真实 Git worktree；从主目录查询丢失/损坏状态及尝试 advance，定位子目录绝对路径并提供 recover 命令，损坏字节保留。 |
| {need}`UC_20261105_8Y3Y4XGFN7BAD7G1` | CLI 预览无写入、携摘要应用、拒绝重复覆盖；共享 spec/design 与持久审查事实可重新读取。 |
| {need}`UC_20261105_XJ24SY45FGPD7QT5` | CLI 旧 plan 恢复保留已勾选任务；生命周期、批准、基准和额度仍未知或阻断，默认 review-begin 被拒绝。合成 completed 门禁 fixture 丢失 JSON 后保留历史审查并标识 recovered_context，不冒充本事项独立回执。 |
| {need}`UC_20261105_HMF6V781VZFC5JBS` | 查询/源校验不恢复；真实 Claude 会话明确 Alpha 后恢复且不批准、不推进阶段；歧义首轮未写状态。 |
| {need}`UC_20261105_A7F5PXHGNYY66GN0` | CLI 两个活跃事项、一个历史取消事项和共享 spec/design，仅列三个 CHG，不把正文引用注册为事项。真实两个会话分别选择 Alpha/Beta，原会话保留 Beta，未写状态或全局 active 指针。 |
| {need}`UC_20261105_KPKK6DYRDK1JPEZ7` | 真实 Claude 切换后 Alpha 记录不变；额外真实进程 fixture 中提示待核对操作，不停止 Alpha 的进程、不结束或推进任一事项；测试调用方随后清理自己拥有的进程。 |
| {need}`UC_20261105_PR634MNDDP1D86B8` | CLI cancelled 在正式记录成功/本地替换失败之间注入故障，原 JSON 保留；同命令重试不重复结束，新目录只读历史无需 JSON。completed 使用明确标注的合成审查阶段 fixture，通过实际配置检查和当前调度绑定；未模拟必需独立机器回执。 |
| {need}`UC_20261105_SZBX3KSRH79BBFKS` | CLI migrate 预览/应用保留旧 JSON 扩展；plan-only 创建合法 unknown 记录，其他事项不变；格式/关系校验及包含隐式 workflow 导航的 HTML 构建通过。 |

CLI 集成主脚本在最新源码上执行 15 次调用通过；补充 worktree、共享发现、旧批准边界、故障收尾和 completed fixture 的命令与结果分别保存在忽略的 tmp/tao 中。真实会话、输入和原始日志同样保存在忽略临时存储；不保留原始输出到版本管理。实际 Claude CLI 首轮机器审查原始回执已导入，受检版本 d7dc517，结论为 changes-requested：DIAG-01 正式来源损坏误报 JSON、SEL-01 worktree 文档遮蔽活跃状态、FIN-01 旧 JSON-only 收尾缺持久记录、FIN-02 生命周期未知标记未清除。均已采用并加入回归；旧原始报告与 open 处置保持不变，最终处置必须来自实际复核。必需独立审查的原始机器回执按当前 `tao status` 的输入绑定结果核对，Markdown 报告存在不等于满足该条件。

任务 10 仍未完成：当前预算阈值下两项 Claude 定向验收已通过，Kiro 也由定向原生检查解除；Windows 原生验收未覆盖，配置检查以最新回执为准；当前不得执行 completed 收尾。历史失败不由后来定向通过改写。
预算调整提交 `42e94fa` 上的完整配置代码检查实际执行 2624 秒：703 passed、1 failed、2 Windows 条件 skipped，覆盖率 78%；诊断语言及 Ruff 检查通过。Claude recover/plan 在完整运行中再次通过，唯一失败为 Claude 多轮行为验收第二轮触发外层 720 秒超时，不能以定向通过替代整体结论。预算差异复核第一轮因登记失败后误启动而中止，已追记失败且未作有效证据；登记成功的剩余一轮触发 1 美元 CLI 预算阈值（客户端报告估算 1.14164 美元），没有最终结论，未导入回执。两次失败均保留，不自动增加轮次、预算或时限；前次完整实现审查历史保留，但对新输入的必需审查状态为 stale。当前仍不得 completed，Windows 原生验收仍未覆盖。原始输出及调度记录保存在忽略临时目录，未提交原始日志。

后续定位到验收包装器的取消缺陷：外层 720 秒终止 Python 后，另建进程组的 Claude 仍在执行，原始第二轮日志后来才报告服务超时，不能把外层退出视为完整进程清理。现已在单轮、多轮、维护审查和原生 hook 适配器中处理 SIGTERM，使既有清理路径执行；外层等待清理后再用 SIGKILL 升级。双轮行为验收共享默认 600 秒总时限，耗尽后不启动下一轮，无第二轮日志时仍可保存 blocked 摘要。旧实现的取消回归先实际失败，修复后三个入口的合成模型及后代清理通过；确定性回归 695 passed、2 Windows 条件 skipped，最终相关检查 40 passed、2 真实原生会话项 deselected，Ruff 及编译检查通过。真实默认强度探针在 600.144 秒正确保存 timed-out/blocked，全局摘要不变且无实验模型进程残留；小型交互探针随后采用与 plan/routing 相同的低推理强度，保持每次 2 美元预算阈值、行为断言和 600 秒总时限，真实两轮验收通过（536.976 秒，pytest 1 passed），无首轮写入、无重复问题、会话连续且全局摘要不变。这只证明该次低强度探针结果，不证明默认强度的耗时保证。原始日志和摘要留在忽略临时目录，最终配置检查及必需审查以当前回执为准，Windows 原生验收仍未覆盖。

最终冻结提交 `d8ec53f` 上的配置代码检查实际执行 2526 秒：709 passed、3 failed、2 Windows 条件 skipped，覆盖率约 78%；诊断语言检查和 Ruff 通过。Claude recover/plan 分别在 600.061/600.077 秒触发原有时限，均正常保存失败摘要且全局配置摘要不变；此前通过结果保留，不代替本次失败。Claude 双轮行为验收在约 534 秒被上游 API 的 422 额度错误终止（服务端报告费用 5.0、预算 5.0），未计通过；Codex 写入、恢复、路由及双轮行为通过，Cursor/Kiro 原生写入及 hook 通过，监测配置摘要均不变。工具禁用的定向独立复核另在 300 秒终止，未生成可导入结论，已按第三次失败保留在原批次。用户随后批准额外一次复核不设 CLI 费用限制、超时 20 分钟；得知服务端额度阻断后，用户明确选择先保留复核待办。该额外一次尚未登记或调用，后续恢复时沿用已批准参数并保留前三次失败，不重置轮次。任务 10 及 Windows 原生验收仍未完成，当前不执行 finish/completed；CLI 费用参数不能解除上游额度限制。原始日志、完整执行摘要和调度记录均留在忽略临时存储，本文仅保存验证范围及结果。

<!-- /tao:results -->

<!-- tao:section questions -->
## 待确认事项

无需求或设计范围未决项。平台覆盖、完整检查与结束条件以验证章节及当前完整 verify 的实际结果为准。
