---
schema: tao.project.plan/v0.1
id: DOC_20260916_VDYK8KF5Q3665DQY
title: Skill 文档精简与职责重整
locale: zh-Hans
status: draft
created: "2026-09-16"
change: CHG_20260916_XBKXDAF7KNN3Q0X3
spec_docs: ["DOC_20260914_4C7N0XHQSP7CY69P"]
design_docs: ["DOC_20260914_P1G9T0KSCC0FTBM1", "DOC_20260914_0VF190409FQCN197"]
updated: "2026-09-17"
---

# Skill 文档精简与职责重整

<!-- tao:section scope -->
## 目标与边界

按用户已批准的两轮审查建议，减少 skill 的重复、通用教学和内部实现说明，按消费项目的阅读场景归并参考。每完成一项向用户用表格报告状态。修改限于本仓库的 skill、相关开发说明、引用与必要验证，不安装或发布插件。

保持既有流程、格式、稳定 ID、授权边界、证据语义和客户端支持范围。精简规则表达不改变 CLI、模板或 schema 的执行行为。

<!-- tao:section references -->
## 规格依据

沿用 {need}`DOC_20260914_4C7N0XHQSP7CY69P` 的协作开发协议。用户已批准本次精简与文件归属方案，并明确要求整理任务清单后逐项执行；无需另建重复规格。

<!-- tao:section design -->
## 设计引用

沿用 {need}`DOC_20260914_P1G9T0KSCC0FTBM1` 与 {need}`DOC_20260914_0VF190409FQCN197`。documents 维护通用编写与检查；document-entries 合并条目语法和写法；retirement 按操作独立读取。document-layout 维护物理组织，publication 维护阅读导航和构建。project-setup 接收项目配置，tools 保留定位与索引。工程、流程、状态、审查调度、审查记录、验证与证据各保留独立职责并去重。localization 保留翻译专用约束；通用语言选择归 documents，术语只保留 tao 约定和易混淆概念。

诊断字段、算法、内部调度和出版器验收归入既有 docs/engineering 文档，不通过运行参考反向依赖开发文档。所有被移动内容同步调用方链接；已批准的约束不因压缩而丢失。

<!-- tao:section tasks -->
## 任务

- [x] `TASK_20260916_SZ2EWQCK7P6HBJ52` 建立任务清单、原文基线和验证范围。
  - relates: ["CHG_20260916_XBKXDAF7KNN3Q0X3"]
  - depends_on: []
  - verify: 记录原始提交、资源规模与三种阅读场景；doctor 和仓库、打包、引用解析基线检查。
  - evidence: [验证记录](#DOC_20260916_VDYK8KF5Q3665DQY--verification)

- [x] `TASK_20260916_RWHKPTK18BJ7GJWN` 重整文档编写规则，合并诊断与条目写法，拆出退役流程。
  - relates: ["CHG_20260916_XBKXDAF7KNN3Q0X3"]
  - depends_on: ["TASK_20260916_SZ2EWQCK7P6HBJ52"]
  - verify: 检查新入口可达、模板字段与既有契约一致、退役恢复约束保留；运行文档及退役相关测试。
  - evidence: [验证记录](#DOC_20260916_VDYK8KF5Q3665DQY--verification)

- [x] `TASK_20260916_2QKPJMGCDAZ6ZPHT` 分离文件组织和书籍导航，移出出版器回归要求。
  - relates: ["CHG_20260916_XBKXDAF7KNN3Q0X3"]
  - depends_on: ["TASK_20260916_RWHKPTK18BJ7GJWN"]
  - verify: 核对路径和阈值不变，日常构建不再要求人为移动文件；运行出版及重定向测试。
  - evidence: [验证记录](#DOC_20260916_VDYK8KF5Q3665DQY--verification)

- [x] `TASK_20260916_ERK5P7RVBS65CDPN` 归并项目配置，移出工具与运行环境内部细节。
  - relates: ["CHG_20260916_XBKXDAF7KNN3Q0X3"]
  - depends_on: ["TASK_20260916_2QKPJMGCDAZ6ZPHT"]
  - verify: 核对启动入口、配置键、依赖准备与故障恢复仍可操作；运行环境和项目接入测试。
  - evidence: [验证记录](#DOC_20260916_VDYK8KF5Q3665DQY--verification)

- [x] `TASK_20260916_GJ2QQMABGAWAKJBG` 去重阶段授权、恢复与审查流程。
  - relates: ["CHG_20260916_XBKXDAF7KNN3Q0X3"]
  - depends_on: ["TASK_20260916_ERK5P7RVBS65CDPN"]
  - verify: 保留阶段检查点、累计范围、有界轮次、来源和输入绑定；运行工作流、审查及接续测试。
  - evidence: [验证记录](#DOC_20260916_VDYK8KF5Q3665DQY--verification)

- [x] `TASK_20260916_YVCPXGFRXBASZ9FA` 集中证据保存、验证与复用规则。
  - relates: ["CHG_20260916_XBKXDAF7KNN3Q0X3"]
  - depends_on: ["TASK_20260916_GJ2QQMABGAWAKJBG"]
  - verify: 核对历史结果、原始材料与当前复用资格分离；运行验证、度量及任务证据测试。
  - evidence: [验证记录](#DOC_20260916_VDYK8KF5Q3665DQY--verification)

- [x] `TASK_20260916_CXYJA4DC7KG1495E` 精简工程规程、术语、本地化与入口。
  - relates: ["CHG_20260916_XBKXDAF7KNN3Q0X3"]
  - depends_on: ["TASK_20260916_YVCPXGFRXBASZ9FA"]
  - verify: 保留工程取舍及非显然约束；核对场景读取范围、语言规则和模板一致性。
  - evidence: [验证记录](#DOC_20260916_VDYK8KF5Q3665DQY--verification)

- [x] `TASK_20260916_YD2WC2Q6K5T5TA77` 完成引用、行为保留、打包与最终验证。
  - relates: ["CHG_20260916_XBKXDAF7KNN3Q0X3"]
  - depends_on: ["TASK_20260916_CXYJA4DC7KG1495E"]
  - verify: 检查全部相对链接、受管理文档、现有回归、HTML 与两种发布包；独立检查原文规则保留和三种阅读场景。
  - evidence: [验证记录](#DOC_20260916_VDYK8KF5Q3665DQY--verification)

<!-- tao:section verification -->
## 验证

逐项检查受影响文档与原文的约束对应关系，运行有关现有测试。最终检查打包后的引用自包含、开发文档格式和 HTML 构建。字符数仅表示分发文本规模，不替代行为判断；阅读场景由独立上下文核查，不声称已完成原生客户端或跨供应商验收。

<!-- tao:results -->
对入口及18份参考完成职责归并，运行脚本、模板与schema未改。静态Unicode字符数由63,979降至37,799（40.9%）；此值不表示token、模型性能或行为收益。原有104个正式ID及引用保持，新增10个仅属本计划。

文本规模比较起点为49e7362；受检分发基线为f7b00bc3bb10829fa2e3cf12860c613b0f9d2e3a，最终工作区另含新事项分派说明及计划验证摘要。Python3.12.13的完整回归359 passed、5原生探针 skipped，445.02秒；Ruff、依赖一致性、36份受管理文档及HTML通过。公共包128个、Codex包104个本地链接均在包内解析，分发文本与生成包字节一致。

独立上下文保留审查无发现，三种阅读演练及事项边界定向核对完成；属于静态场景应用，不是原生客户端或跨供应商实测。原生、Windows及跨供应商保证不由文档整理推导。原始快照、检查输出和审查摘要只在忽略临时目录，不保证长期还原；没有安装、推送或发布。

<!-- /tao:results -->

原生客户端、跨供应商和 Windows 验收不由文档重整结果推导。

<!-- tao:section questions -->
## 待确认事项

无。
