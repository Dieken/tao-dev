---
schema: tao.project.evidence/v0.1
id: "DOC_20260921_VK6SBV5JBMCY4WT8"
title: "调度前置条件复核报告"
locale: "zh-Hans"
status: draft
created: "2026-09-21"
evidence: "EVD_20260921_0C51DWFCMBWZV1PB"
change: "CHG_20260921_Y6MW6AX39S9RJHGZ"
recorded_at: "2026-09-21T10:11:00+08:00"
result: "passed"
coverage: "partial"
---

# 调度前置条件复核报告

<!-- tao:section scope -->
## 目标与边界

本批次第 2 轮，也是最后一轮。范围限于提交 `236677c` 对审查调度前置条件的记述与 `review_runs.py` 的相关实现；并借本轮实测批次记录排除后 finish 闸门是否可达——批次导航页与父级入口已在本轮开始前就位并提交。

**审查执行时间与依据:** 2026-09-21 10:05:16 至 10:06:56（本地时间），实测耗时 99.612 秒，来源为调度脚本记录的 `elapsed_seconds`。本轮此前有一次尝试未调用模型即被拒绝，原因见下。

<!-- tao:section inputs -->
## 输入与环境

<!-- tao:field fingerprint -->
**受检输入引用:** Git 树对象 `c3f999730f6247299118affce5424a9242fd3353`，即提交 `236677c` 的树；基准提交 `d8b599dd5a8712d654d2909fc48ed1f89b8762e7`。审查调度记录的输入摘要为 `e20cbba4f36ca5fe…`。派发三份：审查调度页、`review_runs.py`、实施计划。

<!-- tao:field environment -->
**环境:** 审查者为模型，`claude-sonnet-5`；会话 `b9118bf0-7a8a-4e4d-b01e-37b9f8e8ad81`，与作者及第 1 轮审查者均不同。调用方式为 `scripts/review_claude.py` 受限子进程，`--safe-mode`、`--effort low`、`--tools ''`、`--max-turns 3`，超时 300 秒、费用上限 4 美元。结论中的绑定与本轮请求逐字一致。

本轮未取得机器可校验的 attestation，因此未经 `tao review --from` 导入，必需审查仍以第 1 轮的记录为准。两次尝试的实际原因：其一，个人访问令牌剩余 869 秒，短于超时 900 秒加 120 秒余量，脚本按既有约束拒绝执行且不尝试刷新，模型未被调用；其二，改用 300 秒超时后模型完整执行并给出结论，但隔离核对判定运行期间个人客户端配置发生变化而不出具记录。该机器同时运行多个客户端进程，变化来源无法由本次证据区分，故不作归因；结论按 [审查记录](../../../../../../plugins/tao-dev/skills/tao-dev/references/review-receipts.md) 保留为真实报告并说明未导入，不改称人工审查。

<!-- tao:section checks -->
## 检查记录

<!-- tao:field command -->
**命令或观察步骤:** 主审核实 F1 的前提——读取 `taolib/project.py` 的异常类定义，并实际构造 `ConflictError` 检验 `except (OSError, ValueError)` 是否捕获。

<!-- tao:field expected -->
**预期:** 若 `ConflictError` 不是 `ValueError` 子类，F1 成立；若是，则现有捕获已覆盖，登记失败的路径不受阻。

<!-- tao:field observed -->
**实际观察:** `class ConflictError(ValueError)`，方法解析顺序为 `ConflictError → ValueError → Exception`；实测 `except (OSError, ValueError)` 捕获该异常。因此历史变化触发的 `ConflictError` 会落入 `finish()` 既有的处理分支并记入 `input_error`，[审查调度](../../../../../../plugins/tao-dev/skills/tao-dev/references/review-runs.md) 所述行为成立，F1 的缺陷主张不成立。

<!-- tao:field reports -->
**报告:** 原始事件流保存在忽略目录 `tmp/tao/review-runs/1789956316455661000/`。

<!-- tao:section findings -->
## 发现与限制

<!-- tao:field limits -->
**限制:** 审查者自述四条：只读三份受供文件，`project.py`、`workflows.py`、`git_workflow.py` 等未提供，被调用助手按调用点采信；未执行代码；计划中 {need}`TASK_20260921_TZZTYV40TK3Q0TTV` 未勾选而结果叙述描述已实现，其判断为按计划正文属待实测状态而非缺陷，故未报为发现；两项指导规则任务的目标文件未提供，未予评估。

第一条限制是本轮 F1 的直接成因，也是同类误报的第三次：此前两轮亦因未见 `project.py` 的异常层次而把已被覆盖的分支报为缺口。这是派发范围的问题，不是审查者的问题。

### 缺陷

本轮无成立的缺陷级发现。

### 风险

无。

### 非阻断建议

无。

### 已接受限制

`project.py` 等被调用模块不在本轮派发范围。该取舍本身已被证明产生重复误报，处置见同批次主审裁决。

### 未解决事项

闸门可达性的实测结论见裁决。

**对下一步的影响:** 本轮无成立的阻断。必需审查以第 1 轮的导入记录为准，本轮不改变其状态。

<!-- tao:section retention -->
## 证据保存

<!-- tao:field retention -->
**保存位置与期限:** 随事项长期保留，与同批次前两份文件同目录。
