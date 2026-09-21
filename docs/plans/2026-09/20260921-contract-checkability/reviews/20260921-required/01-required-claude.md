---
schema: tao.project.evidence/v0.1
id: "DOC_20260921_HW89D1JH1577AR23"
title: "必需审查第 1 轮报告"
locale: "zh-Hans"
status: draft
created: "2026-09-21"
evidence: "EVD_20260921_NG0JV38JV7P3WBKZ"
change: "CHG_20260921_Y6MW6AX39S9RJHGZ"
recorded_at: "2026-09-21T11:35:00+08:00"
result: "failed"
coverage: "partial"
---

# 必需审查第 1 轮报告

<!-- tao:section scope -->
## 目标与边界

由用户明确发起的新批次第 1 轮，受检对象为提交 `4b9d604`。派发七份：`project.py`、`coverage.py`、`review_runs.py`、`reviews.py`、`documents.py`、`tests/test_coverage.py` 与实施计划。

本轮派发首次包含 `project.py`。此前三轮曾各提出一条「某异常不在捕获元组内」的发现，三条均不成立，成因相同：审查者看不到 `ConfigurationError` 与 `ConflictError` 均为 `ValueError` 子类。本轮包含该文件后未再出现同类发现，而提出了一条成立的阻断。

**审查执行时间与依据:** 2026-09-21 11:05 前后，实测耗时 96.446 秒，来源为调度脚本记录的 `elapsed_seconds`。

<!-- tao:section inputs -->
## 输入与环境

<!-- tao:field fingerprint -->
**受检输入引用:** Git 树对象 `ce78bd2a964cd8e0564f54e4f4682ab5f168398e`，即提交 `4b9d604` 的树；基准提交 `d8b599dd5a8712d654d2909fc48ed1f89b8762e7`。审查调度记录的输入摘要为 `073c0c04c0fd739e…`，受检文件 31 份；本轮预留输出为本文件。

<!-- tao:field environment -->
**环境:** 审查者为模型，`claude-sonnet-5`，调用方式为 `scripts/review_claude.py` 受限子进程，`--safe-mode`、`--effort low`、`--tools ''`、`--max-turns 3`，超时 600 秒。结论中的绑定与本轮请求逐字一致。

本轮未取得机器可校验的 attestation：运行期间 `.claude.json` 发生变化，隔离核对据此拒绝出具记录。该机器同时运行多个客户端进程，凭据与工作目录两项核对均通过，变化限于会话与项目元数据。按 [审查记录](../../../../../../plugins/tao-dev/skills/tao-dev/references/review-receipts.md)，结论保留为真实报告并说明未导入，不改称人工审查；必需证据因此仍未满足，由本批次后续轮次承担。

<!-- tao:section checks -->
## 检查记录

<!-- tao:field command -->
**命令或观察步骤:** 主审核实 F1：读取 `finish()` 中取诊断的表达式与 `Project.sources()` 的范围来源，并构造一份位于 `documents.include` 之外的畸形报告执行登记。

<!-- tao:field expected -->
**预期:** 若诊断取自受管理文档集合，则范围外的报告不会被分析，畸形报告可通过登记。

<!-- tao:field observed -->
**实际观察:** 成立。`finish()` 以 `validate_documents(owner.root, owner.sources())` 取诊断，`sources()` 受 `documents.include` 约束；范围外的报告不产生任何诊断，既有存在性与非空检查无法替代结构校验，畸形报告得以登记。该缺口使 {need}`TASK_20260921_PJ4W5TTCCGBNJ9T4` 的验收在该情形下不成立。

<!-- tao:field reports -->
**报告:** 原始事件流保存在忽略目录 `tmp/tao/review-runs/1789959954077142000/`。

<!-- tao:section findings -->
## 发现与限制

<!-- tao:field limits -->
**限制:** 审查者未执行代码，结论基于静态阅读；未读取指导页与格式注册表。主审已就 F1 实测复现，不依赖静态推断。

### 缺陷

#### F1：登记前的报告校验对管理范围外的报告不生效

- **严重性与阻断条件:** 阻断。处置见同批次主审裁决。
- **定位:** [审查调度模块](../../../../../../plugins/tao-dev/skills/tao-dev/scripts/taolib/review_runs.py) 的 `finish()`。
- **约束:** {need}`TASK_20260921_PJ4W5TTCCGBNJ9T4` 要求登记前对所提交报告执行受管理文档校验，不合格则拒绝登记。
- **触发条件:** 报告保存在 `documents.include` 匹配范围之外。
- **证据或待证假设:** 已复现。诊断取自受管理文档集合，范围外文件不被分析，`faults` 恒为空。
- **后果:** 未经任何结构校验的报告连同摘要与审查者信息一并登记，读起来与已校验的报告无异。
- **最小改动或验证:** 直接按报告路径校验，或在记录中逐份标明该报告是否经过校验。

### 风险

无。

### 非阻断建议

无。

### 已接受限制

指导页与格式注册表不在本轮派发范围。

### 未解决事项

无。F1 已处置，见裁决。

**对下一步的影响:** 本轮结论为需要修改。修复后须以新一轮对最终树复核，并在该轮取得可导入的 attestation，必需审查方才具备记录。

<!-- tao:section retention -->
## 证据保存

<!-- tao:field retention -->
**保存位置与期限:** 随事项长期保留。原始事件流只在忽略目录保存。
