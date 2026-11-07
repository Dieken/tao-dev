---
schema: tao.project.tasks/v0.1
id: "DOC_20261108_SJVF6ABRNSPFGRBF"
title: "项目级 skill 任务"
locale: "zh-Hans"
status: draft
change: "CHG_20261108_BDAZPV3E7WVCF92X"
---

# 项目级 skill 任务

<!-- tao:section scope -->
## 范围

本附件是计划的唯一任务集合。

<!-- tao:section tasks -->
## 任务

- [x] `TASK_20261108_ZWXC8S9PME6AJG19` 规格、设计与当前功能契约一致
  - relates: ["REQ_20261108_QYFN37DN0SHS8376", "REQ_20261108_6FN7VP6CB598Y1DV", "REQ_20261108_EQQAQ6NE9CBMT5SP", "REQ_20261108_C06F8GD5AWHTY6AD", "REQ_20261108_M77FHDMQ112NKMDP", "REQ_20261108_2KN2TMG33K5M47TV"]
  - depends_on: []
  - verify: 用现有源校验器检查四份文档；对照六项需求完成设计审查。
- [x] `TASK_20261108_N4R3A5GM531K0A68` 文档模型与检查器支持当前结构契约
  - relates: ["REQ_20261108_C06F8GD5AWHTY6AD"]
  - depends_on: ["TASK_20261108_ZWXC8S9PME6AJG19"]
  - verify: 测试章节弹性、重复 ID、引用完整性及书籍构建。
- [x] `TASK_20261108_MMKNQPHDYMZHAX11` 提供项目级完整 skill 接入
  - relates: ["REQ_20261108_QYFN37DN0SHS8376"]
  - depends_on: ["TASK_20261108_ZWXC8S9PME6AJG19"]
  - verify: 在隔离项目放置和移除完整 skill，确认用户文档、相邻 skill 及用户目录不变。
- [x] `TASK_20261108_CVCXYSAEQPP91CZ9` 计划状态来自文档中的唯一任务集
  - relates: ["REQ_20261108_EQQAQ6NE9CBMT5SP"]
  - depends_on: ["TASK_20261108_ZWXC8S9PME6AJG19"]
  - verify: 直接读取计划及其任务；全部勾选不推断审查通过；客户端临时摘要不进入 docs。
- [x] `TASK_20261108_RZASEDJRQT8B3HA6` 统一 skill、长期文档和源码发布入口
  - relates: ["REQ_20261108_6FN7VP6CB598Y1DV"]
  - depends_on: ["TASK_20261108_ZWXC8S9PME6AJG19"]
  - verify: 全部动作不要求登记，源码与打包只提供项目 skill 入口，文档引用和导航有效。
- [x] `TASK_20261108_5D6MNDAKW3XB1K9J` 完成回归、真实路径验证和代码审查
  - relates: ["REQ_20261108_QYFN37DN0SHS8376", "REQ_20261108_6FN7VP6CB598Y1DV", "REQ_20261108_EQQAQ6NE9CBMT5SP", "REQ_20261108_C06F8GD5AWHTY6AD", "REQ_20261108_M77FHDMQ112NKMDP", "REQ_20261108_2KN2TMG33K5M47TV"]
  - depends_on: ["TASK_20261108_N4R3A5GM531K0A68", "TASK_20261108_MMKNQPHDYMZHAX11", "TASK_20261108_CVCXYSAEQPP91CZ9", "TASK_20261108_RZASEDJRQT8B3HA6"]
  - verify: 集中执行完整测试及真实 CLI smoke；修复审查问题并在计划记录真实结果。
- [x] `TASK_20261108_Q94VAN43D1DSSYP1` 精简现行文档与开发记录
  - relates: ["REQ_20261108_M77FHDMQ112NKMDP"]
  - depends_on: ["TASK_20261108_RZASEDJRQT8B3HA6"]
  - verify: 文档仅保留当前契约与有效知识；源校验、HTML 导航与稳定链接有效，项目 skill 安装路径可运行。
- [x] `TASK_20261108_C0TTHNPFK8V0F8QH` 分发采用完整复制与可选通用工具
  - relates: ["REQ_20261108_QYFN37DN0SHS8376", "REQ_20261108_2KN2TMG33K5M47TV"]
  - depends_on: ["TASK_20261108_MMKNQPHDYMZHAX11"]
  - verify: 契约与接入说明一致；验证完整包复制后的 CLI、项目隔离、回归与文档结构。


