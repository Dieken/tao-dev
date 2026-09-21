---
schema: tao.project.evidence/v0.1
id: "DOC_20260921_MGDDJBM03YSBQ6G3"
title: "必需审查定向复核报告"
locale: "zh-Hans"
status: draft
created: "2026-09-21"
evidence: "EVD_20260921_G0DSK09WS0DMZZ8R"
change: "CHG_20260921_Y6MW6AX39S9RJHGZ"
recorded_at: "2026-09-21T11:55:00+08:00"
result: "passed"
coverage: "partial"
---

# 必需审查定向复核报告

<!-- tao:section scope -->
## 目标与边界

本批次第 2 轮，也是最后一轮。范围为第 1 轮 F1 的处置是否落地落对，并在本轮取得可导入的记录。派发五份：`project.py`、`review_runs.py`、`coverage.py`、`tests/test_review_runs.py` 与审查调度页。

**审查执行时间与依据:** 2026-09-21 11:49 前后，实测耗时 102.729 秒，来源为调度脚本记录的 `elapsed_seconds`。

<!-- tao:section inputs -->
## 输入与环境

<!-- tao:field fingerprint -->
**受检输入引用:** Git 树对象 `2a88127d4aaa66a999daf52e98596379d12b3b5b`，基准提交 `d8b599dd5a8712d654d2909fc48ed1f89b8762e7`，审查调度记录的输入摘要为 `ec9ada4974d773c7…`。

<!-- tao:field environment -->
**环境:** 审查者为模型，`claude-sonnet-5`，供应商 `firstParty`（由客户端事件观察得到）。会话上下文 `b26caa98-62f1-43c0-8329-e2ca20671a76`，与作者及此前各轮审查者均不同。调用方式为 `scripts/review_claude.py` 受限子进程，`--safe-mode`、`--effort low`、`--tools ''`、`--max-turns 3`，超时 600 秒、费用上限 4 美元。估算费用 0.224904 美元，实际账单未知。

隔离核对三项全部通过：个人客户端配置未变、变更文件列表为空、凭据未刷新、工作目录权限受限。此前两次未取得记录的原因是该机器并发运行多个客户端进程而改动会话元数据，用户暂停后不再出现。本轮 attestation 已经 `tao review --from` 实际导入，记录文件存在于忽略目录 `tmp/tao/reviews/` 下。

<!-- tao:section checks -->
## 检查记录

<!-- tao:field command -->
**命令或观察步骤:** 导入本轮 attestation 后执行 `tao verify CHG_20260921_Y6MW6AX39S9RJHGZ`。

<!-- tao:field expected -->
**预期:** 必需审查取得对应本受检树的记录；完整判定各项成立。

<!-- tao:field observed -->
**实际观察:** 退出码 0，status passed，coverage complete，readiness checks-satisfied，耗时 636.7 秒。目标任务开放项为空；需求承接核对为 evaluated 且未承接项为空；`diagnostics-locale` 20.9 秒、`python-tests` 612.3 秒、`python-lint` 0.3 秒均通过；当前证据可复用；必需审查为 satisfied；诊断 0 条。

<!-- tao:field reports -->
**报告:** 原始事件流保存在忽略目录 `tmp/tao/review-runs/1789962571373284000/`。

<!-- tao:section findings -->
## 发现与限制

<!-- tao:field limits -->
**限制:** 审查者自述三条：未执行任何代码或测试；`workflows.py`、`git_workflow.py`、`documents.py`、`verification.py`、`project_setup.py`、`tao_messages.py` 未提供，因此 `mutate()` 的事务性、`admitted()` 所用的排除集合与文档校验内部无法核实；结构性检查只由源码逻辑与测试预期评估，不来自已认证或已执行的运行。

第二条为本轮范围的实际缺口，与前几轮同因：控制单轮输入规模。本轮特意包含了 `project.py`，因为此前三轮各提出一条「某异常不在捕获元组内」的发现且三条均不成立，成因都是看不到异常类层次；本轮未再出现同类发现。

### 缺陷

本轮无缺陷级发现。审查者确认输入绑定、失败行为与隔离三处内部一致且有对应测试覆盖。

### 风险

无。

### 非阻断建议

无。

### 已接受限制

未派发的被调用模块不在本轮范围。

### 未解决事项

无。

**对下一步的影响:** 必需审查 `independent-implementation-review` 已取得对应受检树 `2a88127` 的记录并实际导入。本报告与批次导航落盘属本批次自身记录，不改变该轮结论。

<!-- tao:section retention -->
## 证据保存

<!-- tao:field retention -->
**保存位置与期限:** 随事项长期保留。原始事件流与导入的机器记录只在忽略目录保存。
