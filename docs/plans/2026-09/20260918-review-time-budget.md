---
schema: tao.project.plan/v0.1
id: "DOC_20260918_XCZ86X6EKD65FVKY"
title: "审查默认调度窗口延长至两小时"
locale: "zh-Hans"
status: draft
created: "2026-09-18"
spec_docs: ["DOC_20260914_4C7N0XHQSP7CY69P"]
design_docs: ["DOC_20260914_AG3NSZ8RBSFA0YHW"]
change: "CHG_20260918_P9JWERM113977VX4"
---

# 审查默认调度窗口延长至两小时

<!-- tao:section scope -->
## 目标与边界

将新审查批次默认时间预算从 1800 秒改为 7200 秒，为人的复查与讨论留出时间。保留显式预算及已有批次的累计窗口；不改变轮次上限、不修改消费项目状态。

<!-- tao:section references -->
## 规格引用

沿用 {need}`DOC_20260914_4C7N0XHQSP7CY69P` 的有界审查要求。

<!-- tao:section design -->
## 设计

沿用 {need}`DOC_20260914_AG3NSZ8RBSFA0YHW` 的持久审查批次。当前调度器不调用模型，也无模型调用起止事件；继续按批次墙钟计时，包含人工复查、讨论、修复和等待，不以 begin/end 的差值冒充 LLM 实际耗时。只改变新批次的默认值，不隐式扩充旧预算。

<!-- tao:section tasks -->
## 任务

- [x] `TASK_20260918_SYGJT5NW7ENEQBY4` 调整默认值和使用说明，验证两小时边界、显式预算、旧批次恢复及新批次行为。
  - relates: ["CHG_20260918_P9JWERM113977VX4"]
  - depends_on: []
  - verify: 用固定时钟执行真实批次创建、结束、恢复和新批次测试；确认超过原 30 分钟仍可继续，达到两小时仍受限，已有预算不被默认值覆盖；运行审查与工作流相关回归、lint、文档和 HTML 检查。

  - evidence: [验证记录](#DOC_20260918_XCZ86X6EKD65FVKY--verification)

<!-- tao:section verification -->
## 验证

<!-- tao:results -->
项目本地 Python 执行审查批次、工作流和独立审查回执相关测试，36 项通过（81.57 秒）。固定时钟检查新默认值为 7200 秒：40 分钟时仍能保存需修改的结论，7199 秒时可开始定向复核，7200 秒完成时记为 budget-exceeded。显式 1800／9000 秒批次恢复后保留原预算，新批次采用 7200 秒且历史预算保留；既有跨会话耗尽测试继续通过。

Ruff 配置致命规则无诊断；仓库文档与分发引用检查 3 项通过。46 份显式受管文档无 error，保留 [命令设计](../../engineering/cli-design.md) 的一条既有链接 warning；deletion_checked=false。HTML 构建完成，实际使用说明与预算规程页面均显示两小时及墙钟计时边界，未部署。前一项文档模板修改已执行完整维护回归；本次一行默认值变化另跑上述受影响回归，不重复整个套件。日志保存在忽略的 tmp/tao/review-report-contract/。未启用客户端调用，不把调度窗口解释为模型实测耗时；未修改消费项目的文件、审查状态或已确认预算。
<!-- /tao:results -->

<!-- tao:section questions -->
## 待确认事项

无。采用用户明确提出的两小时默认值；仅计 LLM 时间需要额外的可靠计时机制，不在本次局部修改中加入。
