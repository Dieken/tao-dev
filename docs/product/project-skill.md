---
schema: tao.project.spec/v0.1
id: "DOC_20261108_ZT37NM8REHBYC520"
title: "项目级文档驱动 skill"
locale: "zh-Hans"
status: draft
created: "2026-11-08"
---

# 项目级文档驱动 skill

<!-- tao:section scope -->
## 目标与边界

tao-dev 是项目级文档驱动 skill，以结构化知识、单一计划进度和确定性辅助工具支持开发。安装及项目操作限定在明确授权的项目内，不修改其他项目、个人配置或全局安装。

<!-- tao:section terms -->
## 术语

skill 由 SKILL.md、按需参考、模板及确定性辅助脚本组成。计划进度只表示任务状态；审查未知不得推断通过。

<!-- tao:section requirements -->
## 需求

```{req} 项目级纯 skill
:id: REQ_20261108_QYFN37DN0SHS8376
:status: proposed

分发完整 skill，由使用者复制到项目级发现目录或选择通用 skills 工具；tao 不提供安装生命周期、所有权记录或客户端配置管理。复制不要求 Python，不隐式准备依赖。

<!-- tao:field acceptance -->
**验收：** 隔离项目内复制完整包、从副本运行辅助命令并移除副本；确认项目文档、项目外客户端配置及用户目录不变。实际客户端发现另行验证项目内可见、项目外缺席，不以复制结果代替。

<!-- tao:field source -->
**来源：** 用户的项目级 skill 与简化协作要求。
```

```{req} 保留文档驱动主线
:id: REQ_20261108_6FN7VP6CB598Y1DV
:status: proposed

保留 new（spec → design → plan）、review doc、implement、review code，支持 refine、status、continue、handoff；每个动作提示下一步，已有授权内连续推进，不要求逐步批准。

<!-- tao:field acceptance -->
**验收：** 核对 skill 动作和真实 CLI 辅助入口；完成小型计划的状态读取与显式交接。

<!-- tao:field source -->
**来源：** 用户的项目级 skill 与简化协作要求。
```

```{req} 计划是进度唯一来源
:id: REQ_20261108_EQQAQ6NE9CBMT5SP
:status: proposed

任务及未完成项以 plan 和显式 tasks 附件为准，只维护一个任务源。任务完成不能自动证明测试或审查通过。

<!-- tao:field acceptance -->
**验收：** 只有 plan/tasks 的项目可以只读查询；删除临时交接后仍能恢复任务；全部勾选时审查未记录仍显示未知。

<!-- tao:field source -->
**来源：** 用户的项目级 skill 与简化协作要求。
```

```{req} 结构化知识与书籍
:id: REQ_20261108_C06F8GD5AWHTY6AD
:status: proposed

文档采用稳定唯一 ID、正向引用和 book 导航；校验基本结构、必要语义章节、唯一 ID、引用和导航完整性，允许章节重排及与当前文档无关的可选章节缺省。

<!-- tao:field acceptance -->
**验收：** 现有核心文档仍可校验和构建；重排可选章节不失败，重复 ID、悬空引用及导航环仍失败。

<!-- tao:field source -->
**来源：** 用户的项目级 skill 与简化协作要求。
```

```{req} 临时证据与最小交接
:id: REQ_20261108_M77FHDMQ112NKMDP
:status: proposed

review/evidence 详细输出不自动成为正式文档或提交；长期结论进入规格、设计或计划当前摘要。handoff 显式写项目临时目录，不产生 DOC/EVD，不阻断 continue。

<!-- tao:field acceptance -->
**验收：** 交接覆盖同一事项摘要且不改 plan；status 不运行测试或写文件；book 不自动收录执行记录。

<!-- tao:field source -->
**来源：** 用户的项目级 skill 与简化协作要求。
```

```{req} 当前接口与分发一致
:id: REQ_20261108_2KN2TMG33K5M47TV
:status: proposed

schema、模板、校验器、文档、测试和打包共同表达当前 skill 契约；分发资源及每个公开接口都有明确的当前消费者，项目操作限定在授权范围。

<!-- tao:field acceptance -->
**验收：** 运行当前命令、项目复制 smoke、文档验证、book 构建和回归；核对接口、资源及文档一致，用户目录与项目外配置保持不变。

<!-- tao:field source -->
**来源：** 用户的项目级 skill 与简化协作要求。
```



<!-- tao:section cases -->
## 场景

```{uc} 项目隔离
:id: UC_20261108_N9H9WRFKXP27AJ2W
:status: proposed
:verifies: REQ_20261108_QYFN37DN0SHS8376

<!-- tao:field given -->
**给定：** 两个临时项目与隔离用户目录。

<!-- tao:field when -->
**当：** 只向第一个项目复制完整 skill、运行辅助工具并移除副本。

<!-- tao:field then -->
**则：** 第二个项目和用户配置保持不变，非归属文件不被删除。
```

```{uc} 无状态恢复
:id: UC_20261108_7S9B1Y91CBPVRZXH
:status: proposed
:verifies: REQ_20261108_EQQAQ6NE9CBMT5SP

<!-- tao:field given -->
**给定：** 已有 spec/design/plan/tasks，未保存临时交接。

<!-- tao:field when -->
**当：** 查询 status 并显式 handoff。

<!-- tao:field then -->
**则：** 任务可定位，交接仅临时保存，审查没有记录则未知。
```

```{uc} 文档结构与导航校验
:id: UC_20261108_V5DFY36HGWZVS6P2
:status: proposed
:verifies: REQ_20261108_C06F8GD5AWHTY6AD

<!-- tao:field given -->
**给定：** 具有现有结构与唯一 ID 的文档书籍。

<!-- tao:field when -->
**当：** 按当前模板编写文档，重排可选章节并执行校验与构建。

<!-- tao:field then -->
**则：** 核心引用仍可解析，可选章节重排不影响校验，重复 ID 和导航错误仍被检测。
```



<!-- tao:section questions -->
## 未决问题

无产品边界待决。客户端项目 skill 发现能力须如实验证；无法确认项目隔离时报告未验证，不回退全局配置。

