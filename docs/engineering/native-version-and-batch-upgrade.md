---
schema: tao.project.design/v0.1
id: "DOC_20261107_AXTBBST6KW3DDGHQ"
title: "Native 版本发现与批量升级设计"
locale: "zh-Hans"
status: draft
created: "2026-11-07"
spec_docs: ["DOC_20261107_F6HNNP5XE5133SM9"]
---

# Native 版本发现与批量升级设计

<!-- tao:section overview -->
## 概述

设计覆盖安装管理脚本中的 native discovery、list 结果模型和 upgrade 批量协调。受管 receipt 继续保存 tao 所有权、来源、运行环境和最近成功安装版本；native discovery 继续观察客户端当前状态，但不再把 native 版本覆盖为唯一的 `version` 字段。

版本选择只影响 Codex project 和 Cursor project cache。Claude registry、Cursor user local activation 和 Kiro marker 已经直接提供路径与版本，保持其发现路径，只统一返回字段。

<!-- tao:section architecture -->
## 架构

`installation.discover` 读取受管 records 后调用 `install_clients.discover`。每个 native row 统一携带 `native_version`，受管 row 统一携带 `recorded_version`；匹配的受管 row 同时更新 native path、enabled 和 native version，不修改磁盘 receipt。native-only row 的 `recorded_version` 为 null，`native_version` 来自客户端发现。

Codex 和 Cursor project cache 使用共享的标准库 SemVer key：major、minor、patch 按数值比较，预发布版本按标识符比较并低于正式版本，build metadata不参与 precedence。有效版本优先于无效版本；所有候选都无效时按规范化路径排序。选择函数返回完整候选，不依赖 mtime。

`upgrade` 参数解析新增 `--all`。`--id` 与 `--all` 在解析阶段互斥。无 `--all` 继续使用 `applies_to` 选择单项；有 `--all` 从 `state.records(client)` 取得全部受管记录，按 id 稳定排序，并为每条记录构造现有 `install` namespace。native-only 行不在 records 中，因此不进入批量升级。

批量协调器逐项调用现有 `install(selected)`。单项 install 的 source/cache/activation/receipt/CLI 回滚保持不变；批量不建立跨安装全局回滚。每项结果包含 id、scope、project、status、installation 或 error。text 和 JSON 共用结果模型，批量有成功、失败和总数汇总；全部成功为 passed/0，有失败为 partial/2。

<!-- tao:section contracts -->
## 接口与数据契约

`tao list --client <client> [--project <dir>] [--format text|json]` 的每个安装行包含：

- `recorded_version`：受管 receipt 版本；native-only 为 null；
- `native_version`：客户端当前发现版本；无 native 行为 null；
- `plugin_path`、`enabled` 和现有 scope/project/id 字段；
- 受管行不再输出兼容性的单一 `version` 字段。

text 输出在版本位置明确打印：

```text
recorded=0.16.0 | native=0.16.1
```

`tao upgrade --client <client> --all [--ref ...] [--wheelhouse ...] [--timeout ...]` 升级全部受管 records；`--id` 与 `--all` 互斥。JSON 批量结果在 `outputs.results` 保存逐项结果，并提供 `total`、`succeeded`、`failed`；每项失败保留诊断字符串和实际 files（若有）。text 输出逐项状态和最终汇总。单项命令继续返回现有 installation 摘要，但版本字段使用新 recorded/native 语义时只影响 list rows，避免改变 install/upgrade 成功摘要。

<!-- tao:section invariants -->
## 不变量

- 单项无 `--all` 的选择规则和 `--id` 跨项目行为不变。
- 批量只处理有效 tao receipt，不把 native-only 安装当成可升级来源。
- 每个安装的 source、managed runtime、native activation 和 receipt 仍由单项 install 事务独立保护。
- 批量失败不得回滚已成功的其他安装，也不得把部分成功标为通过。
- 版本排序不读取或修改 mtime；同版本候选使用稳定路径排序。
- list 只在内存中合并 native 状态，不写回 receipt。
- 版本字段命名明确，native 版本不再隐式覆盖记录版本。

<!-- tao:section errors -->
## 错误与恢复

解析阶段拒绝 `--id --all`。没有受管记录的 `--all` 沿用 no installation 诊断并返回非零。单项失败由既有 install rollback 处理；批量捕获该项异常并继续下一项。单项失败的 files 和诊断归入该项，不阻断后续项。全部成功返回 `passed`/0；存在失败返回 `partial`/2；进程级参数、状态读取或批量准备错误无法形成逐项结果时返回 `not_run`/2。

无效 manifest version 不使 discovery 崩溃：作为无效候选排在有效 SemVer 后；所有候选都无效时选择稳定路径结果并返回原始显示值。缺失版本显示 `unknown`，不伪造语义版本。

<!-- tao:section verification -->
## 验证

单元测试覆盖 SemVer 正式版、预发布版、build metadata、无效版本和反向 mtime；分别验证 Codex project 与 Cursor project。list 测试覆盖受管行版本不同时的 text/JSON 双字段、相同版本、缺失 native 和 native-only。upgrade 测试覆盖默认单项选择、`--all` 全部受管记录、user/project 混合、`--id --all` 拒绝、稳定顺序、部分失败继续和退出状态。

现有单项 install 失败回滚测试继续执行，确认批量协调器复用而非旁路回滚。文档验证覆盖安装设计、CLI 设计和 README 的接口说明。完成后运行目标 pytest 子集、项目 lint 和受管理文档验证；不把真实客户端配置或模型会话作为本次必要验收。
