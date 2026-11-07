---
schema: tao.project.spec/v0.1
id: DOC_20261105_27RJ5NTQG9BNBJHX
title: 工作流状态恢复与事项生命周期
locale: zh-Hans
status: draft
created: "2026-11-05"
---

# 工作流状态恢复与事项生命周期

<!-- tao:section scope -->
## 目标与边界

面向跨目录、跨机器或并行开发的 tao-dev 用户，使本地 workflow JSON 丢失后仍可基于项目正式资料识别、恢复和结束原事项。本文细化[开发协议](protocol.md)的恢复与并行边界；对应的 CLI 入口与记录格式见[恢复与持久生命周期设计](../engineering/workflow-recovery.md)。

范围包含 CLI 诊断与恢复、skill 的自动调用边界、多事项定位与切换、从开始到收尾的持久记录、旧事项兼容以及对应 schema、模板和文档的一致性。无需提交 .tao/workflows/；不提供跨机器文件同步、进程迁移、丢失讨论还原或隐式合入、推送、清理。记录格式、路径和 CLI 收尾入口的具体组织由设计文档定义；不得通过预先创建空计划覆盖计划前场景。

<!-- tao:section terms -->
## 术语

沿用[项目术语](../glossary.md)。生命周期表示事项是否仍在进行、暂停、完成或取消；阶段表示 spec 至 complete 的工作位置；文档自身 status 不代表事项生命周期。正式记录是版本管理中的可迁移依据，本地状态是执行协调记录，会话选择只表达本会话的目标。

<!-- tao:section requirements -->
## 需求

```{req} 本地执行状态与持久依据分离
:id: REQ_20261105_12M6WAZSDRR4857Y
:status: proposed

系统应将事项生命周期和无法由产物推导的关键决定保存在 docs/ 的正式结构化记录中，从事项开始即建立，并将频繁检查点、操作输出和大体积快照保留为不要求提交的本地状态。

<!-- tao:field acceptance -->
**验收：** 仅复制版本管理内的正式资料至新目录，移除全部 workflow JSON，仍能发现尚无 plan 的事项及其持久决定；普通检查点不改写正式记录。

<!-- tao:field source -->
**来源：** 用户关于本地状态不入版本管理、恢复、并行事项和结构化收尾的要求及已确认的改进建议。
```

```{req} 状态缺失和异常的可操作诊断
:id: REQ_20261105_DQY5T199SD08CF93
:status: proposed

当命令需要的 workflow state 不存在时，系统应指出预期文件的绝对路径、目标 CHG、已发现的文档或 worktree，以及带明确项目位置的 recover 命令；损坏、多个副本和缺乏权威定义应分别诊断。

<!-- tao:field acceptance -->
**验收：** 对缺失、无效 JSON、重复副本、仅有引用分别执行查询与写命令，核对路径、原因和下一步；依赖状态的写命令不得继续写入。

<!-- tao:field source -->
**来源：** 用户关于本地状态不入版本管理、恢复、并行事项和结构化收尾的要求及已确认的改进建议。
```

```{req} 显式可预览的状态重建
:id: REQ_20261105_GAXA5RZZ60Y774BM
:status: proposed

当执行 tao workflow recover <CHG-ID> 时，系统应只读预览依据、可恢复事实、候选阶段和缺口；带 --apply 时才创建本地状态，沿用原 CHG、产物及任务进度，不覆盖已有或损坏状态。

<!-- tao:field acceptance -->
**验收：** 比较预览前后的工作区内容；应用后检查原 CHG、任务勾选和文档未变；重复应用或并发创建不得覆盖已存在状态。

<!-- tao:field source -->
**来源：** 用户关于本地状态不入版本管理、恢复、并行事项和结构化收尾的要求及已确认的改进建议。
```

```{req} 恢复保持批准与证据边界
:id: REQ_20261105_3C64CBKGB4T22MFR
:status: proposed

系统应只恢复有明确持久依据及适用内容绑定的批准和审查记录；文件存在、文档 status、任务勾选、旧报告或当前 HEAD 均不得单独推导阶段批准、当前验证通过、原始基准或剩余审查额度。

<!-- tao:field acceptance -->
**验收：** 修改已批准产物、丢失审查轮次或基准后恢复，分别报告失效或未知；不自动推进、不重置额度派发、不自动重跑已完成操作。

<!-- tao:field source -->
**来源：** 用户关于本地状态不入版本管理、恢复、并行事项和结构化收尾的要求及已确认的改进建议。
```

```{req} 按命令职责触发恢复
:id: REQ_20261105_AVBWR8XFXC786KXY
:status: proposed

status 应自动发现文档事项并保持只读；skill continue 在目标唯一、恢复依据无冲突且已有继续授权时可自动预览并应用恢复，其余状态依赖写命令应提示显式恢复；不依赖状态的文档操作不应被阻断。

<!-- tao:field acceptance -->
**验收：** 分别调用 status、continue、checkpoint 和独立文档校验；仅满足条件的 continue 可自动创建状态；发现冲突时不得自动应用。

<!-- tao:field source -->
**来源：** 用户关于本地状态不入版本管理、恢复、并行事项和结构化收尾的要求及已确认的改进建议。
```

```{req} 并行事项的发现与目标选择
:id: REQ_20261105_83CKHP6YN12QZQHX
:status: proposed

系统应依据正式 CHG 定义和结构化关系发现事项，并依次使用显式 CHG、会话已选 CHG、当前 worktree 唯一可信关联和当前范围唯一未结束事项定位目标；仍有歧义时列出候选供选择，不用最近修改时间或全项目单一活动指针决定写入目标。

<!-- tao:field acceptance -->
**验收：** 构造两个并行事项、共享设计、历史结束事项及正文 CHG 引用；核对候选去重、生命周期、目录和目标选择；两个会话选择不得互相覆盖。

<!-- tao:field source -->
**来源：** 用户关于本地状态不入版本管理、恢复、并行事项和结构化收尾的要求及已确认的改进建议。
```

```{req} 切换事项不强制结束
:id: REQ_20261105_TE6PX7VZYYKSEQN6
:status: proposed

当用户明确切换到另一事项时，系统应保留原事项生命周期、任务及运行操作，必要时保存检查点并提示仍运行的操作；只有具备收尾条件而尚未结束时才建议 finish，不因切换、时间经过或任务全部勾选自动结束。

<!-- tao:field acceptance -->
**验收：** 在 A 仍有运行操作时切换至 B，核对 A 未结束且进程未被停止；只在交付检查和审查条件满足时出现收尾建议。

<!-- tao:field source -->
**来源：** 用户关于本地状态不入版本管理、恢复、并行事项和结构化收尾的要求及已确认的改进建议。
```

```{req} 持久且可重试的收尾
:id: REQ_20261105_NFBV51FB4SS7W5QD
:status: proposed

当用户授权结束事项时，系统应在 docs/ 保存结构化收尾记录，区分已完成、已取消和仍未结束的暂停，记录结束时间、结果、检查与审查依据以及未完成事项的处置；正式记录可靠保存后再同步本地状态，中断重试不得重复结束或丢失结果。

<!-- tao:field acceptance -->
**验收：** 在正式记录保存后、本地同步前中断，重试后两者一致；删除本地状态后仍能识别结束结果；取消不得表示交付完成，过期证据不抹去历史结束结果。

<!-- tao:field source -->
**来源：** 用户关于本地状态不入版本管理、恢复、并行事项和结构化收尾的要求及已确认的改进建议。
```

```{req} 旧事项兼容与文档一致性
:id: REQ_20261105_SPDKCTWSX7PVDNDK
:status: proposed

当既有事项只有 plan 或旧 JSON、没有新的生命周期记录时，系统应保留已有 ID 与关系，区分未记录和已结束，允许预览可迁移依据而不自动批量改写历史文档；CLI、用户指南及 skill 应一致说明恢复、选择、切换和结束规则。

<!-- tao:field acceptance -->
**验收：** 使用旧计划、仅有旧状态、缺失状态三组资料，核对不会误判全部进行中或已完成；仅有无定义引用时说明不足，迁移与恢复不生成替代 CHG。

<!-- tao:field source -->
**来源：** 用户关于本地状态不入版本管理、恢复、并行事项和结构化收尾的要求及已确认的改进建议。
```

<!-- tao:section cases -->
## 用例与性质

```{uc} 本地执行状态与持久依据分离
:id: UC_20261105_MN5FGBTN6BXX1NER
:status: proposed
:verifies: REQ_20261105_12M6WAZSDRR4857Y

<!-- tao:field given -->
**给定：** 事项处于 spec 阶段，尚未创建计划，已保存正式记录和关键决定。

<!-- tao:field when -->
**当：** 将已提交资料复制到另一机器或目录，不复制 .tao/workflows/。

<!-- tao:field then -->
**则：** 能够发现原 CHG 和已记录阶段；未提交或未记录内容明确为未知，不要求提交 JSON。
```

```{uc} 状态缺失和异常的可操作诊断
:id: UC_20261105_CMB2P2PF02KQWTMC
:status: proposed
:verifies: REQ_20261105_DQY5T199SD08CF93

<!-- tao:field given -->
**给定：** 同一事项存在正式文档，本地 JSON 缺失；另有 JSON 损坏和另一 worktree 存在状态的变体。

<!-- tao:field when -->
**当：** 执行 status 及需要 revision 的写命令。

<!-- tao:field then -->
**则：** status 展示可读文档及诊断；写命令停止；损坏文件保持原样，实际 worktree 可定位，歧义列出候选。
```

```{uc} 显式可预览的状态重建
:id: UC_20261105_8Y3Y4XGFN7BAD7G1
:status: proposed
:verifies: REQ_20261105_GAXA5RZZ60Y774BM

<!-- tao:field given -->
**给定：** 原状态缺失，spec、design、plan、tasks、review 和 handoff 中有可解析的适用材料。

<!-- tao:field when -->
**当：** 先预览再应用恢复，并重复执行应用。

<!-- tao:field then -->
**则：** 预览无写入；首次应用恢复可证实信息；重复应用保留已有状态并说明原因，不生成新事项或重做任务。
```

```{uc} 恢复保持批准与证据边界
:id: UC_20261105_XJ24SY45FGPD7QT5
:status: proposed
:verifies: REQ_20261105_3C64CBKGB4T22MFR

<!-- tao:field given -->
**给定：** 任务已勾选且存在通过报告，但批准绑定缺失或输入已变化，审查轮次及原始 Git 基准不能确认。

<!-- tao:field when -->
**当：** 恢复并请求继续工作。

<!-- tao:field then -->
**则：** 保留任务事实，列出批准、证据、轮次和基准缺口；仅受影响操作等待协调，恢复不制造授权。
```

```{uc} 按命令职责触发恢复
:id: UC_20261105_HMF6V781VZFC5JBS
:status: proposed
:verifies: REQ_20261105_AVBWR8XFXC786KXY

<!-- tao:field given -->
**给定：** 事项明确且缺失本地状态，另有多个候选或正式资料冲突的变体。

<!-- tao:field when -->
**当：** 调用上述不同职责的入口。

<!-- tao:field then -->
**则：** 查询和文档校验不写状态，普通写命令返回恢复指引；continue 仅在明确目标且无冲突时恢复，缺失批准不被自动补齐。
```

```{uc} 并行事项的发现与目标选择
:id: UC_20261105_A7F5PXHGNYY66GN0
:status: proposed
:verifies: REQ_20261105_83CKHP6YN12QZQHX

<!-- tao:field given -->
**给定：** docs/ 包含两个未结束 CHG、一个已结束 CHG和共享 spec/design，两个会话分别选择不同事项。

<!-- tao:field when -->
**当：** 查询并在各会话继续，随后在无上下文的新会话继续。

<!-- tao:field then -->
**则：** 原会话保持各自目标；新会话展示标题、CHG、生命周期、阶段和目录并请求选择，不把共享材料或正文引用注册为新事项。
```

```{uc} 切换事项不强制结束
:id: UC_20261105_KPKK6DYRDK1JPEZ7
:status: proposed
:verifies: REQ_20261105_TE6PX7VZYYKSEQN6

<!-- tao:field given -->
**给定：** A 未结束且记录运行操作，B 也是未结束事项。

<!-- tao:field when -->
**当：** 用户明确切换至 B。

<!-- tao:field then -->
**则：** 后续明确针对 B 操作，A 保持原状态；展示需要核对的运行操作，不强制 finish A。
```

```{uc} 持久且可重试的收尾
:id: UC_20261105_PR634MNDDP1D86B8
:status: proposed
:verifies: REQ_20261105_NFBV51FB4SS7W5QD

<!-- tao:field given -->
**给定：** 事项满足相应结束条件并获授权，或用户明确取消而尚有未完成任务。

<!-- tao:field when -->
**当：** 执行 finish 并模拟两次写入之间中断，再重试；随后在另一目录只读取正式记录。

<!-- tao:field then -->
**则：** 正式结束结果可见且不重复，未完成事项有处置；已结束事项通常无需恢复本地 JSON即可查询，合入、推送和清理仍按各自授权执行。
```

```{uc} 旧事项兼容与文档一致性
:id: UC_20261105_SZBX3KSRH79BBFKS
:status: proposed
:verifies: REQ_20261105_SPDKCTWSX7PVDNDK

<!-- tao:field given -->
**给定：** 仓库含没有生命周期元数据的旧计划和仍可读取的旧 workflow JSON。

<!-- tao:field when -->
**当：** 查询候选并对选定事项预览恢复或迁移。

<!-- tao:field then -->
**则：** 旧状态可继续识别，未知生命周期明确显示；未选事项保持不变，格式校验覆盖新增正式记录及其关系。
```

<!-- tao:section questions -->
## 待确认事项

无。记录格式、迁移协议、恢复冲突与写入一致性的实现方案在设计阶段确定，不改变上述恢复和授权边界。
