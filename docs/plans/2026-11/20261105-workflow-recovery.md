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
恢复CLI实现基线为 `ac99d89`：正式 workflow 记录保存恢复必需事实，当前记录为 65 行、1,882 字节；本地 JSON 保持忽略，完整执行历史不进入正式记录。任务 1–9 已完成，任务 10 未完成；不得执行 completed 收尾。用户已将本轮平台范围限定为本机可做部分，Windows 无可用验收环境。

| 检查范围 | 受检输入与结果 | 复用或覆盖限制 |
|---|---|---|
| 确定性维护回归 | 最小恢复记录实现，769 passed、2 Windows 条件 skipped、2 warnings | 排除 live acceptance 与 native sessions；最后的协调边界修正另由下行覆盖 |
| 最终恢复相关检查 | 与 ac99d89 相同的恢复代码，75 passed | 覆盖额度不重置、缺失控制、写入中断、旧格式、输入绑定及非法字段，不替代模型验收 |
| CLI 恢复 | 隔离副本只复制项目资料，不复制 JSON；预览与摘要绑定应用通过 | 已用5/上限5和1200秒、无CLI费用阈值均保留；未补造历史尝试，额外派发被拒绝 |
| 当前文档维护 | 声明范围内的源校验、HTML稳定入口及28项文档/资源/出版回归通过，skill元数据校验通过；包内入口与参考按源码核对 | 仅验证本次文档和分发结构，不重跑完整代码门禁，也不证明新指令的模型服从性 |
| 完整配置检查 | 固定输入 4aac26e：793 passed、1 failed、2 Windows skipped、2 warnings，覆盖率78.66%；诊断本地化12项及lint通过 | Codex双轮行为缺少必需的协议标记，第二轮未启动；整体未通过。Claude裸名解析修复经26项定向检查、原始日志重放及本轮真实routing验收通过；修复前完整检查及原始报告保持失败，不改写结果 |
| Claude 双轮定向复验 | 完整检查后源码和断言未改时，1 passed、33.80秒；会话连续、回复前无写入、无重复提问 | 此前两次标记协议失败保留为历史结果；定向通过不改写完整检查失败 |
| 必需独立审查 | 既有真实审查及 REC-01 定向复核曾通过；本次改动后回执为 stale | 当前输入仍需新的有效审查；不以 Markdown 报告存在或旧通过代替 |
| 平台与客户端 | macOS 的已测客户端结果按下表及原始报告限定；4aac26e完整检查中Kiro本机检查通过 | Windows 原生行为未验收；本机通过不代替其他平台覆盖 |

### 已执行的功能场景

下表保存本事项原实现阶段的实际 CLI／会话观察，部分收尾使用明确标注的合成 fixture。原记录未逐项固定独立修订，表格不作为当前输入的完整通过凭据；后续最小恢复记录格式的恢复检查见上表。

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

### 审查结论与处置依据

正式文档及实现审查见[文档批次](20261105-workflow-recovery/reviews/20261105-recovery-contract/index.md)与[实现批次](20261105-workflow-recovery/reviews/20261105-implementation/index.md)。[第三轮定向复核](20261105-workflow-recovery/reviews/20261105-implementation/05-validation-adjudication.md)确认 I4 已闭合；DIAG-01、SEL-01、FIN-01、FIN-02 的后续机器复核确认修复，原始机器报告留在忽略临时目录。REC-01/FU-01 的实际结论与裁决如下，不改写原模型意见：

| 编号 | 级别 | 处置 | 依据 |
|---|---|---|---|
| REC-01 | suggestion | 采用并修复，实际定向复核确认 | 候选匹配与文件系统 glob 对照测试、嵌套目录及排除测试通过；原报告处置不改写 |
| REC-01-FU-01 | suggestion | 不采纳 | 官方 [CPython 3.11.14](https://raw.githubusercontent.com/python/cpython/v3.11.14/Lib/pathlib.py) 和 [3.12.12](https://raw.githubusercontent.com/python/cpython/v3.12.12/Lib/pathlib.py) 的 _make_selector 均明确拒绝非整段 **；已提取并执行这两个官方选择器分支，均抛 ValueError，反驳“旧版会按普通通配符选择”的前提。未声称实际运行完整旧版解释器或 Windows；保留模型原建议及其静态推测限制 |

### 有效限制与保存

用户批准的维护试验参数为 TAO_ACCEPTANCE_MODEL_TIMEOUT=1200、TAO_CLAUDE_MAX_BUDGET_USD=none；默认参数及 Cursor/Kiro 的45秒限制保持原策略。历史完整检查出现过600秒超时、CLI费用阈值与上游额度拒绝，不构成当前通过或服务时延保证。取消回归覆盖 SIGTERM 清理与双轮共享时限；强制 SIGKILL 仍不能保证任意脱离进程组的后代被清理。

运行日志、模型事件、快照及机器回执仅保存在忽略临时存储，不保证跨机器可取得，不能据本文重建有效通过证据。结构化任务与未完成条件保持，历史检查结果不因日志过期而改写。

<!-- /tao:results -->

<!-- tao:section questions -->
## 待确认事项

无需求或设计范围未决项。平台覆盖、完整检查与结束条件以验证章节及当前完整 verify 的实际结果为准。
