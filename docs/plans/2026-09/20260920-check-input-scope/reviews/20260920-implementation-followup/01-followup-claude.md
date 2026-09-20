---
schema: tao.project.evidence/v0.1
id: "DOC_20260920_55V9R69RV5272N5R"
title: "形状加固复核报告"
locale: "zh-Hans"
status: draft
created: "2026-09-20"
evidence: "EVD_20260920_V6EK46XV55N3TQFH"
change: "CHG_20260920_Y0WCT88THT8JXXS2"
recorded_at: "2026-09-20T19:26:00+08:00"
result: "unknown"
coverage: "partial"
---

# 形状加固复核报告

<!-- tao:section scope -->
## 目标与边界

新批次第 1 轮。上一批次两轮用尽时，其第 2 轮的阻断级发现尚未修复；用户明确发起本批次，复核该修复本身。范围限于 `2f0d25d` 对 `declared_outputs()` 的形状加固与其 7 项参数化回归，以及 `e730d6d` 对任务检查措辞的订正是否与实测一致。上一批次的记录完整保留在事项状态的 `review_history`，未被清零。

派发给审查者的是四份文件：`taolib/reviews.py`、`tests/test_reviews.py`、`taolib/verification.py`、实施计划。

**审查执行时间与依据:** 2026-09-20 19:05:03 至 19:06:52（本地时间），实测耗时 109.136 秒，来源为调度脚本记录的 `elapsed_seconds`。

<!-- tao:section inputs -->
## 输入与环境

<!-- tao:field fingerprint -->
**受检输入引用:** Git 树对象为提交 `e730d6d3` 的树，基准提交 `c5a72550416669f40f312f5b06657b13d7b815a3`。审查调度记录的输入摘要为 `558c3850ccb4136d…`，受检文件 23 份；本轮预留三份输出，已排除。

<!-- tao:field environment -->
**环境:** 审查者为模型，`claude-sonnet-5`，供应商 `firstParty`（由客户端事件观察得到）。会话上下文 `b4c9868e-cfc8-40c8-9033-e402a22ed0fb`，与作者及此前四轮审查者均不同。调用方式为 `scripts/review_claude.py` 受限子进程，`--safe-mode`、`--effort low`、`--tools ''`、`--max-turns 3`，超时 900 秒、费用上限 4 美元。运行后个人客户端配置未变、凭据未刷新、工作目录权限受限。估算费用 0.241988 美元，实际账单未知。同供应商、不同会话。轮次：新批次第 1 轮，上限 2 轮。

<!-- tao:section checks -->
## 检查记录

<!-- tao:field command -->
**命令或观察步骤:** 主审核实 F1 是否可达：读取 `cli.py` 中 `review` 与 `status` 两个调用点的前置校验，以及格式注册表的 ID 模式；并以越界 `change` 直接调用 `path_for()` 观察返回值。随后按 `tao review --from` 导入本轮 attestation，并执行 `tao verify CHG_20260920_Y0WCT88THT8JXXS2`。

<!-- tao:field expected -->
**预期:** 若两个调用点都校验 `change` 属于受管理索引且以 `CHG_` 开头，而 ID 模式不含路径分隔符，则 F1 所述路径不可达。

<!-- tao:field observed -->
**实际观察:** `path_for()` 对越界 `change` 确实返回 `tmp/tao/reviews/../../escape/independent.json` 这类路径，`contained()` 只挡逃出项目根、不挡逃出 reviews 目录，审查者对模块内的观察成立。但两个调用点均先校验 `args.change in result.definitions and startswith('CHG_')`，而注册表 ID 模式为 `^(DOC|REQ|UC|ADR|TASK|CHG|EVD)_[0-9]{8}_[0-9A-HJKMNP-TV-Z]{16}$`，字符集不含 `/` 与 `.`，因此该路径当前不可达。

完整交付判定：`tao verify CHG_20260920_Y0WCT88THT8JXXS2` 返回退出码 0、status passed、coverage complete、readiness checks-satisfied，目标任务开放项为空，证据可复用，必需审查 satisfied，诊断 0 条，耗时 3.0 秒（整份回执复用）。该结果的观察时点为本报告落盘之前。

<!-- tao:field reports -->
**报告:** 原始事件流保存在忽略目录 `tmp/tao/review-runs/1789902303583799000/`。本轮 attestation 已经 `tao review --from` 导入；其唯一发现为建议级，因此该项必需审查在导入后显示 satisfied。

<!-- tao:section findings -->
## 发现与限制

<!-- tao:field limits -->
**限制:** 审查者自述四条：未执行任何代码或测试；`project.py`、`workflows.py`、`review_sources.py`、`tao_messages.py` 未提供，其行为按用法采信；结构与类型校验只确立 attestation 的形状与自洽，不确立审查会话或人的身份真实；未把计划正文的测试数量、耗时与摘要数值与实际执行重新核对，按所述采信。

第四条对应的数值，主审已在本文件与计划的验证记录中给出实际来源与观察时点。

本报告的 result 为 unknown：审查者返回的结构化结论不含总体判定字段，不能由「无阻断发现」推断 passed。

### 缺陷

本轮无缺陷级发现。审查者确认所追踪的路径与已记录设计一致：空范围失败关闭、畸形工作流状态退化、排除限于最近一轮、逐行过期、声明须为策略范围的子集。

### 风险

无。

### 非阻断建议

#### F1：`path_for()` 的安全性只由一条注释承担

- **严重性与阻断条件:** 建议，非阻断。
- **定位:** [审查模块](../../../../../../plugins/tao-dev/skills/tao-dev/scripts/taolib/reviews.py) 的 `path_for()`。
- **约束:** 写入位置须限制在项目内明确目录，路径解析后不得越界。
- **触发条件:** 未经校验的 `change` 到达 `import_review()`、`status()` 或 `binding()`。
- **证据或待证假设:** 该函数直接用 `change` 拼接路径，本模块内无任何校验，只有一句注释声称调用方已校验；实测以 `../../escape` 调用返回逃出 reviews 目录的路径。可达性未在本轮核实——审查者已声明 CLI 层不在其受检集合内。
- **后果:** 若该前提在后续修改中失效，审查记录可被写到 reviews 目录之外。
- **最小改动或验证:** 在该函数内直接按 CHG ID 模式校验 `change`，使安全性不依赖注释。

### 已接受限制

`project.py`、`workflows.py`、`review_sources.py`、`tao_messages.py` 不在本轮派发范围，与前两轮同因：控制单轮输入规模。

### 未解决事项

无。F1 的处置见同批次主审裁决。

**对下一步的影响:** 本轮未发现阻断级问题，上一批次遗留的阻断修复经本轮复核未再发现缺陷。本轮结论对应受检树 `e730d6d3`；本报告与其批次导航落盘后，该项必需审查将因导航改动显示为过期，此为审查调度规程所述的后续文档变更，不改写本轮结论。

<!-- tao:section retention -->
## 证据保存

<!-- tao:field retention -->
**保存位置与期限:** 随事项长期保留。原始事件流只在忽略目录保存，清理后本文件记载的历史结论不因此失效。
