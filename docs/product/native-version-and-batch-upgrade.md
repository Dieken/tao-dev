---
schema: tao.project.spec/v0.1
id: "DOC_20261107_F6HNNP5XE5133SM9"
title: "Native 版本发现与批量升级"
locale: "zh-Hans"
status: draft
created: "2026-11-07"
---

# Native 版本发现与批量升级

<!-- tao:section scope -->
## 目标与边界

本变更修正 Codex 与 Cursor project cache 的版本发现，避免使用目录修改时间推断最新版；同时扩展 `tao upgrade --client <client>`，允许一次升级该 client 的全部 tao 管理安装。默认无 `--all` 的升级行为保持不变，只选择当前 `--project` 对应的单个安装。

范围包括 `tao list` 的 text/JSON 版本字段、Codex/Cursor native discovery、批量升级参数与结果、相关测试和安装管理文档。不改变客户端自身的 cache 生命周期，不自动升级未被 tao receipt 管理的 native 安装。

<!-- tao:section terms -->
## 术语

- **安装记录版本**：tao receipt 中保存的 `version`，表示 tao 最近成功记录的安装版本。
- **native 发现版本**：客户端配置和插件 manifest 当前发现的版本，可能因客户端或外部操作而不同于安装记录版本。
- **受管安装**：存在有效 tao receipt 的安装；native-only 行不属于受管安装。
- **批量升级**：`--all` 逐项升级同一 client 的全部受管安装，每项仍使用现有单项事务和回滚边界。

<!-- tao:section requirements -->
## 需求

```{req} 使用语义版本发现 Codex 与 Cursor cache
:id: REQ_20261107_A307JYYYWTYPDZMW
:status: proposed

当 Codex 或 Cursor project native discovery 从同一插件 cache 找到多个带 manifest 的版本目录时，系统应按 SemVer precedence 选择最新版，而不是按目录修改时间选择；正式版本应高于预发布版本，build metadata 不改变 precedence；无法解析为 SemVer 的版本应排在有效版本之后，并使用稳定路径顺序打破平局。

<!-- tao:field acceptance -->
**验收：** 在隔离 cache 中以反向 mtime 创建正式版、预发布版、build metadata 和无效版本目录；执行对应 native discovery，观察返回的 plugin path 和 version 与规定的 SemVer 选择一致。

<!-- tao:field source -->
**来源：** 用户要求修正 tao list 的最新版发现；当前 mtime 选择会把目录触碰时间误当作版本顺序。
```

```{req} 区分安装记录版本与 native 发现版本
:id: REQ_20261107_R3MBRP0VSP65JMKX
:status: proposed

当 `tao list` 展示受管安装时，系统应分别提供安装记录版本和 native discovery 版本；当某一版本不存在时应明确显示未知或空值，不得把 native 版本静默覆盖为唯一的 `version` 含义。native-only 安装应显示没有安装记录版本。

<!-- tao:field acceptance -->
**验收：** 构造 receipt 版本与 native manifest 版本不同、相同、缺失和 native-only 四种输入；执行 text 与 JSON list，观察两种来源均可独立识别且路径、scope、project 保持正确。

<!-- tao:field source -->
**来源：** 用户要求在 tao list 结果中区分两个版本来源；之前的合并逻辑只在内存中覆盖 receipt 的 `version`。
```

```{req} 支持全部受管安装的批量升级
:id: REQ_20261107_AGB8YQ12FYY6HN9F
:status: proposed

当用户执行 `tao upgrade --client <client> --all` 时，系统应按稳定顺序升级该 client 的全部 tao 受管安装记录，包括 user 安装和 project 安装；系统不得把没有 tao receipt 的 native-only 安装纳入批量升级。无 `--all` 时，系统应继续只升级当前 `--project` 对应的单个安装；`--all` 与 `--id` 互斥。

<!-- tao:field acceptance -->
**验收：** 在隔离安装记录中创建多个 project、user 和 native-only 行；分别执行无 `--all`、`--all`、`--id --all`，观察无 `--all` 只调用当前目标，`--all` 只调用所有受管记录且稳定排序，互斥参数被拒绝。

<!-- tao:field source -->
**来源：** 用户要求增加 `--all`，同时保持默认单 project 升级。
```

```{req} 批量升级逐项回滚并报告部分结果
:id: REQ_20261107_J6SWVFTRGDW0T956
:status: proposed

当批量升级中的单个安装失败时，系统应使用现有单项事务恢复该安装的 source、cache、activation 和 receipt，继续处理剩余安装，并在 text/JSON 结果中逐项报告成功与失败；全部成功返回退出码 0，存在失败返回退出码 2，不能把部分成功报告为整体通过。

<!-- tao:field acceptance -->
**验收：** 注入中间安装、doctor 或 CLI 失败，观察失败项恢复到原状态，后续项仍被处理，JSON 保留每项结果，text 输出汇总成功和失败数量，退出码为 2。

<!-- tao:field source -->
**来源：** 用户同意批量实现；现有单项 install 已提供原子回滚，批量层应复用而不建立跨项目全局回滚。
```

<!-- tao:section cases -->
## 场景

```{uc} 语义版本胜过目录修改时间
:id: UC_20261107_9831GMXTK2PEH5AF
:status: proposed
:verifies: REQ_20261107_A307JYYYWTYPDZMW

<!-- tao:field given -->
**给定：** 同一 Codex 或 Cursor project cache 中存在多个合法 manifest，最高 SemVer 目录的 mtime 早于较低版本目录。

<!-- tao:field when -->
**当：** 执行对应 client 的 native discovery 或 `tao list`。

<!-- tao:field then -->
**则：** 返回最高有效 SemVer 的 plugin path/version；mtime 不改变结果，无法解析的版本不超过有效版本。
```

```{uc} list 显示两种版本来源
:id: UC_20261107_GGCVE9KF4YY45F19
:status: proposed
:verifies: REQ_20261107_R3MBRP0VSP65JMKX

<!-- tao:field given -->
**给定：** 一个受管 receipt 记录 `0.16.0`，native discovery 发现 `0.16.1`，另有一行没有 receipt 的 native-only 安装。

<!-- tao:field when -->
**当：** 执行 `tao list --client <client> --format text` 和 `--format json`。

<!-- tao:field then -->
**则：** 受管行同时显示 `recorded_version=0.16.0` 与 `native_version=0.16.1`；native-only 行的 recorded version 为空，两个输出格式表达同一结果。
```

```{uc} 批量升级保持单项边界
:id: UC_20261107_FYE3G5PH03QYJ2AQ
:status: proposed
:verifies: REQ_20261107_AGB8YQ12FYY6HN9F, REQ_20261107_J6SWVFTRGDW0T956

<!-- tao:field given -->
**给定：** 同一 client 有多个受管安装，其中一个升级会失败，另一个可成功升级。

<!-- tao:field when -->
**当：** 执行 `tao upgrade --client <client> --all`。

<!-- tao:field then -->
**则：** 系统按稳定顺序处理全部受管安装；失败项单独回滚，成功项保留成功结果，整体返回部分失败状态和非零退出码；不处理 native-only 行。
```

<!-- tao:section questions -->
## 未决问题

无。批量范围采用全部 tao 受管记录，包含 user scope；批量失败采用逐项继续、逐项回滚和部分失败退出码 2；`version` 不作为兼容字段保留，输出使用明确的 recorded/native 版本字段。
