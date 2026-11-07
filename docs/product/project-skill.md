---
schema: tao.project.spec/v0.1
id: "DOC_20261108_ZT37NM8REHBYC520"
title: "项目级纯 skill 重构"
locale: "zh-Hans"
status: draft
created: "2026-11-08"
---

# 项目级纯 skill 重构

<!-- tao:section scope -->
## 目标与边界

将 tao-dev 从工作流执行引擎改为项目级文档驱动 skill。直接在 main 主工作区实施，不改其他项目或本机已有全局安装；旧部署不自动迁移。本次是破坏性切换，不保留旧运行接口。

<!-- tao:section terms -->
## 术语

纯 skill 指 SKILL.md、按需参考、模板及确定性辅助脚本，不包含 hook 或插件注册。计划进度不是审批状态；审查未知不得推断通过。

<!-- tao:section requirements -->
## 需求

```{req} 项目级纯 skill
:id: REQ_20261108_QYFN37DN0SHS8376
:status: proposed

仅安装项目内 skill 和必要资源，不安装 hook、原生插件、marketplace、用户级启动器或全局索引。保留安装、升级、查看和卸载，安全保护用户文件。

<!-- tao:field acceptance -->
**验收：** 隔离项目内安装、重复升级和卸载；确认项目外客户端配置及用户目录不变，外部项目无 activation。

<!-- tao:field source -->
**来源：** 用户明确的纯 skill 简化与不兼容重构要求。
```

```{req} 保留文档驱动主线
:id: REQ_20261108_6FN7VP6CB598Y1DV
:status: proposed

保留 new（spec → design → plan）、review doc、implement、review code，支持 refine、status、continue、handoff；每个动作提示下一步，已有授权内连续推进，不要求逐步批准。

<!-- tao:field acceptance -->
**验收：** 核对 skill 动作和真实 CLI 辅助入口；完成小型计划的状态读取与交接，不调用 workflow 或 finish。

<!-- tao:field source -->
**来源：** 用户明确的纯 skill 简化与不兼容重构要求。
```

```{req} 计划是进度唯一来源
:id: REQ_20261108_EQQAQ6NE9CBMT5SP
:status: proposed

任务及未完成项以 plan 和显式 tasks 附件为准，不维护 workflow Markdown/JSON、审批、revision 或 review 调度数据库。任务完成不能自动证明测试或审查通过。

<!-- tao:field acceptance -->
**验收：** 只有 plan/tasks 的项目可以只读查询；删除临时交接后仍能恢复任务；全部勾选时审查未记录仍显示未知。

<!-- tao:field source -->
**来源：** 用户明确的纯 skill 简化与不兼容重构要求。
```

```{req} 结构化知识与书籍
:id: REQ_20261108_C06F8GD5AWHTY6AD
:status: proposed

保持现有文档风格、稳定唯一 ID、正向引用和 book 导航，放宽强制标题顺序及无关格式门禁；只验证基本结构、唯一 ID、引用和导航完整性。

<!-- tao:field acceptance -->
**验收：** 现有核心文档仍可校验和构建；重排可选章节不失败，重复 ID、悬空引用及导航环仍失败。

<!-- tao:field source -->
**来源：** 用户明确的纯 skill 简化与不兼容重构要求。
```

```{req} 临时证据与最小交接
:id: REQ_20261108_M77FHDMQ112NKMDP
:status: proposed

review/evidence 详细输出不自动成为正式文档或提交；长期结论进入规格、设计或计划当前摘要。handoff 显式写项目临时目录，不产生 DOC/EVD，不阻断 continue。

<!-- tao:field acceptance -->
**验收：** 交接覆盖同一事项摘要且不改 plan；status 不运行测试或写文件；book 不自动收录执行记录。

<!-- tao:field source -->
**来源：** 用户明确的纯 skill 简化与不兼容重构要求。
```

```{req} 不兼容一次切换
:id: REQ_20261108_2KN2TMG33K5M47TV
:status: proposed

删除旧 hook、插件、全局安装和 workflow/finish 接口及其调用方；同步 schema、模板、校验器、文档、测试和打包，不保留兼容 shim。

<!-- tao:field acceptance -->
**验收：** 运行当前命令、安装 smoke、文档验证、book 构建和回归；旧 workflow 与 user scope 参数明确不支持。

<!-- tao:field source -->
**来源：** 用户明确的纯 skill 简化与不兼容重构要求。
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
**当：** 只向第一个项目安装、升级、卸载 skill。

<!-- tao:field then -->
**则：** 第二个项目和用户配置保持不变，非归属文件不被删除。
```

```{uc} 无状态恢复
:id: UC_20261108_7S9B1Y91CBPVRZXH
:status: proposed
:verifies: REQ_20261108_EQQAQ6NE9CBMT5SP

<!-- tao:field given -->
**给定：** 已有 spec/design/plan/tasks，无 workflow 数据。

<!-- tao:field when -->
**当：** 查询 status 并显式 handoff。

<!-- tao:field then -->
**则：** 任务可定位，交接仅临时保存，审查没有记录则未知。
```

```{uc} 格式切换
:id: UC_20261108_V5DFY36HGWZVS6P2
:status: proposed
:verifies: REQ_20261108_C06F8GD5AWHTY6AD

<!-- tao:field given -->
**给定：** 具有现有结构与唯一 ID 的文档书籍。

<!-- tao:field when -->
**当：** 切换模板与检查器并构建。

<!-- tao:field then -->
**则：** 核心引用仍可解析，格式放宽不放弃重复 ID 和导航错误检测。
```



<!-- tao:section questions -->
## 未决问题

无产品边界待决。客户端项目 skill 发现能力须如实验证；不支持的客户端明确报错，不回退全局配置。

