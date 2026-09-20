---
schema: tao.project.evidence/v0.1
id: "DOC_20260920_8937WEA3X7MH8PWD"
title: "标识符校验复核报告"
locale: "zh-Hans"
status: draft
created: "2026-09-20"
evidence: "EVD_20260920_Y70VSD30TPEZYFSZ"
change: "CHG_20260920_Y0WCT88THT8JXXS2"
recorded_at: "2026-09-20T22:45:00+08:00"
result: "unknown"
coverage: "partial"
---

# 标识符校验复核报告

<!-- tao:section scope -->
## 目标与边界

本批次第 2 轮，也是最后一轮。范围限于合入前尚未经任何独立审查的两次提交：`a6a93f5` 为 AGENTS.md 增加 `uv` 必须带 `--no-config` 的约束，`27caa46` 在 `path_for()` 内校验 CHG 标识符与审查名称并补 9 项回归。不重做初审。

本轮开始前，批次的墙钟预算已耗尽（7200 秒预算、实际 9589 秒），由用户明确决定追加至 14400 秒后才登记。超出主要来自完整回归执行与讨论等待，不是审查调用本身。

**审查执行时间与依据:** 2026-09-20 22:25:11 至 22:26:47（本地时间），实测耗时 95.921 秒，来源为调度脚本记录的 `elapsed_seconds`。

<!-- tao:section inputs -->
## 输入与环境

<!-- tao:field fingerprint -->
**受检输入引用:** Git 树对象为提交 `27caa46c` 的树，基准提交 `c5a72550416669f40f312f5b06657b13d7b815a3`。审查调度记录的输入摘要为 `fadfa015fa64190f…`，受检文件 27 份；本轮预留输出为本文件，已排除。派发四份：`taolib/reviews.py`、`tests/test_reviews.py`、[仓库约定](../../../../../../AGENTS.md)、`assets/locales/diagnostics.zh-Hans.json`，覆盖这两次提交的全部改动面。

<!-- tao:field environment -->
**环境:** 审查者为模型，`claude-sonnet-5`，供应商 `firstParty`（由客户端事件观察得到）。会话上下文 `6eed1890-dcea-4383-9eec-b6e14f5be29c`，与作者及此前五轮审查者均不同。调用方式为 `scripts/review_claude.py` 受限子进程，`--safe-mode`、`--effort low`、`--tools ''`、`--max-turns 3`，超时 900 秒、费用上限 4 美元。运行后个人客户端配置未变、凭据未刷新、工作目录权限受限。估算费用 0.22594 美元，实际账单未知。同供应商、不同会话。轮次：第 2 轮，上限 2 轮，至此用尽。

<!-- tao:section checks -->
## 检查记录

<!-- tao:field command -->
**命令或观察步骤:** 导入本轮 attestation 后、本报告落盘前，执行 `tao verify CHG_20260920_Y0WCT88THT8JXXS2`。

<!-- tao:field expected -->
**预期:** 若本轮无阻断级发现，该项必需审查应为 satisfied，完整判定应返回 complete 与 checks-satisfied。

<!-- tao:field observed -->
**实际观察:** 退出码 0，status passed，coverage complete，readiness checks-satisfied，目标任务开放项为空，证据可复用，必需审查 satisfied，诊断 0 条。`python-tests` 实际重新执行 977.06 秒，结果 528 passed、5 skipped；`python-lint` 0.25 秒、0 条诊断。该次重跑不是因输入变化，而是上一次执行距此已超过 `reuse_seconds`，逐行时效判定使其过期——本事项所实现的机制在真实策略上的又一次生效观察。

<!-- tao:field reports -->
**报告:** 原始事件流保存在忽略目录 `tmp/tao/review-runs/1789914311734670000/`。本轮 attestation 已经 `tao review --from` 导入；其唯一发现为建议级，故该项必需审查显示 satisfied。

<!-- tao:section findings -->
## 发现与限制

<!-- tao:field limits -->
**限制:** 审查者自述三条：只读了四份受供文件，`project.py`、`verification.py`、`review_sources.py`、`workflows.py` 与 CLI 层未提供，其契约按用法采信；未执行任何代码或测试；摘要字段的结构校验只确立形状，不确立审查者身份真实或结论语义正确。

本报告的 result 为 unknown：审查者返回的结构化结论不含总体判定字段，不能由「无阻断发现」推断 passed。

### 缺陷

本轮无缺陷级发现。审查者确认输入绑定、`mutation_lock` 下的过期与竞态处理、发现与审查者字段校验三处内部一致并与其测试相符。

### 风险

无。

### 非阻断建议

#### F1：`status()` 在异常保护之外调用会抛异常的 `path_for()`

- **严重性与阻断条件:** 建议，非阻断。
- **定位:** [审查模块](../../../../../../plugins/tao-dev/skills/tao-dev/scripts/taolib/reviews.py) 的 `status()`。
- **约束:** 本模块其余处理畸形持久状态的位置一律退化为安全默认值或 invalid 行，不抛异常；本事项设计亦写明形状不可读时应退化而非崩溃。
- **触发条件:** `status()` 收到一个形状足以传入、却不匹配 `path_for()` 严格 CHG 模式的标识符。
- **证据或待证假设:** `path_for()` 在本轮受检的 `27caa46` 中新增了 `ConfigurationError`，而 `status()` 的逐项循环把它放在捕获 `(ValueError, KeyError, TypeError, AttributeError, OSError)` 的 try 之外。可达性取决于调用方是否先校验，而 CLI 层不在本轮受检集合内，审查者已声明未能确认。
- **后果:** 若该前提失效，`tao status` 与完整 `tao verify` 会崩溃，而不是报出该行的状态。
- **最小改动或验证:** 把 `path_for()` 的调用移入同一 try，使标识符不合规时该行记为 invalid；或在该处单独捕获 `ConfigurationError`。

### 已接受限制

`project.py`、`verification.py`、`workflows.py`、`review_sources.py` 与 CLI 层不在本轮派发范围，与本事项此前各轮同因：控制单轮输入规模。

### 未解决事项

F1 处置为延期，去向见同批次主审裁决。

**对下一步的影响:** 本轮未发现阻断级问题，合入前的两次未审提交至此获得覆盖。本报告与其批次导航落盘后，该项必需审查将因导航改动显示为过期；上文实际观察的时点在此之前。

<!-- tao:section retention -->
## 证据保存

<!-- tao:field retention -->
**保存位置与期限:** 随事项长期保留，与同批次前两份文件同目录。
