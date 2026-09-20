---
schema: tao.project.evidence/v0.1
id: "DOC_20260920_C9C2JTPP5PB6NB56"
title: "实现阶段定向复核报告"
locale: "zh-Hans"
status: draft
created: "2026-09-20"
evidence: "EVD_20260920_WDK3PMET9TK92PM1"
change: "CHG_20260920_Y0WCT88THT8JXXS2"
recorded_at: "2026-09-20T18:56:00+08:00"
result: "failed"
coverage: "partial"
---

# 实现阶段定向复核报告

<!-- tao:section scope -->
## 目标与边界

实现阶段批次第 2 轮，也是本批次最后一轮。范围限于提交 `342d651` 的两处改动及其回归：审查绑定排除本轮声明的报告输出，以及 `carried()` 拒绝不可解释的回执。不重做初审。

派发给审查者的是五份文件：`taolib/verification.py`、`taolib/reviews.py`、`tests/test_reviews.py`、`tests/test_verification.py`、实施计划。

**审查执行时间与依据:** 2026-09-20 18:52:12 至 18:53:52（本地时间），实测耗时 99.972 秒，来源为调度脚本记录的 `elapsed_seconds`。

<!-- tao:section inputs -->
## 输入与环境

<!-- tao:field fingerprint -->
**受检输入引用:** Git 树对象为提交 `342d651f` 的树，基准提交 `c5a72550416669f40f312f5b06657b13d7b815a3`。审查调度记录的输入摘要为 `7fbd6c195f2992c6…`，受检文件 22 份；本轮预留输出为本文件，已排除。

<!-- tao:field environment -->
**环境:** 审查者为模型，`claude-sonnet-5`，供应商 `firstParty`（由客户端事件观察得到）。会话上下文 `57dde2c1-987a-475a-ade8-45eab47f4c34`，与作者及前三轮审查者均不同。调用方式为 `scripts/review_claude.py` 受限子进程，`--safe-mode`、`--effort low`、`--tools ''`、`--max-turns 3`，超时 900 秒、费用上限 4 美元。运行后个人客户端配置未变、凭据未刷新、工作目录权限受限。估算费用 0.298282 美元，实际账单未知。同供应商、不同会话。轮次：第 2 轮，本批次上限 2 轮，至此用尽。

<!-- tao:section checks -->
## 检查记录

<!-- tao:field command -->
**命令或观察步骤:** 主审按发现构造畸形但可解析的工作流状态（`reviews.docs.runs` 为 `["not-a-dict"]`），直接调用 `declared_outputs()` 复现。

<!-- tao:field expected -->
**预期:** 按设计，状态不可读时应返回空列表、不排除任何文件。

<!-- tao:field observed -->
**实际观察:** 抛出 `AttributeError: 'str' object has no attribute 'get'`，未被捕获。发现成立，已复现。

<!-- tao:field reports -->
**报告:** 原始事件流保存在忽略目录 `tmp/tao/review-runs/1789901532330966000/`。本轮 attestation 已经 `tao review --from` 导入；其发现为阻断且处置为 open，因此该项必需审查显示为 changes-requested，这是正确结果。

<!-- tao:section findings -->
## 发现与限制

<!-- tao:field limits -->
**限制:** 审查者自述三条：只读了五份受供文件，`project.py`、`workflows.py`、`review_sources.py` 未提供，其异常层级与助手契约按用法与注释采信而非直接核实；未执行任何代码或测试；未逐项复核每个任务声称的测试覆盖，集中于两份改动库文件的控制流。

### 缺陷

#### F1：工作流状态畸形但可解析时崩溃，而非按设计退化为不排除

- **严重性与阻断条件:** 阻断。处置为 open，本报告成文时未修复。
- **定位:** [审查模块](../../../../../../plugins/tao-dev/skills/tao-dev/scripts/taolib/reviews.py) 的 `declared_outputs()`。
- **约束:** 本事项设计章节写明「工作流状态不可读时不排除任何文件……这一侧的失败使审查显示为过期，而不是显示为满足」。
- **触发条件:** 状态文件是合法 JSON，但 `runs[-1]` 或其 `request` 不是对象。
- **证据或待证假设:** 已复现。把 `reviews.docs.runs` 置为 `["not-a-dict"]` 后调用 `declared_outputs()`，抛出未捕获的 `AttributeError`。捕获元组只含 `(ConfigurationError, ValueError, KeyError, TypeError, OSError)`。
- **后果:** 异常逃出 `declared_outputs()` 与 `binding()`，使 `tao review`、`tao status` 与审查导入崩溃，而不是向安全侧退化。形状损坏与 JSON 损坏是同一类可读性失败，却得到完全不同的处理。
- **最小改动或验证:** 对 `runs`、`runs[-1]`、`request` 与 `output_files` 逐层做 `isinstance` 判定后再取值，并把 `AttributeError` 加入捕获元组作为后手；补一条以畸形但可解析的状态断言返回空列表且 `binding()` 不抛异常的回归。

### 风险

无。

### 非阻断建议

无。

### 已接受限制

`project.py`、`workflows.py`、`review_sources.py` 不在本轮派发范围，与第 1 轮同因：控制单轮输入规模。

### 未解决事项

F1 在本报告成文时为 open。本批次两轮已用尽，修复后的复核须由用户明确发起新批次。

**对下一步的影响:** 该阻断未处置前，项目必需的 `independent-implementation-review` 为 changes-requested，完整交付判定不成立。

<!-- tao:section retention -->
## 证据保存

<!-- tao:field retention -->
**保存位置与期限:** 随事项长期保留，与同批次前两份文件同目录。
