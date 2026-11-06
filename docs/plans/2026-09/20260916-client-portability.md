---
schema: tao.project.plan/v0.1
id: DOC_20260916_0YR9S9FD7ZJSA155
title: 跨客户端 skill 与审查入口兼容
locale: zh-Hans
status: draft
created: "2026-09-16"
change: CHG_20260916_6ZAC0XQF0ZNGC2CZ
spec_docs: ["DOC_20260914_4C7N0XHQSP7CY69P"]
design_docs: ["DOC_20260914_P1G9T0KSCC0FTBM1", "DOC_20260914_0VF190409FQCN197"]
updated: "2026-09-17"
---

# 跨客户端 skill 与审查入口兼容

<!-- tao:section scope -->
## 目标与边界

执行用户批准的 D1–D7、A1–A6、M1–M6、E1–E5 建议，并评估 Codex 原生 TOML reviewer。保持一份共享 skill，区分文档可读、CLI 可运行、原生入口与证据导入；每项完成用表格报告。继续当前 codex/trim-skill-docs 分支，基线 612ae3c，无未提交改动。

不发布，不安装或配置个人客户端。原生实验只在临时项目和已验证的隔离配置中运行，保持项目外不可见。缺 CLI、认证或隔离能力的验收写明未运行。自动安装扩展以已有客户端、原生接口及实际需求为条件，不为未知平台添加名义支持。

安装管理暂不扩展其他客户端。

<!-- tao:section references -->
## 规格依据

沿用 {need}`DOC_20260914_4C7N0XHQSP7CY69P`，用户已批准具体改动表与执行。保留既有文档 ID、阶段授权、来源诚实性及完整插件生命周期约束。

<!-- tao:section design -->
## 设计引用

沿用 {need}`DOC_20260914_P1G9T0KSCC0FTBM1` 与 {need}`DOC_20260914_0VF190409FQCN197`。共享 skill 只维护消费者所需操作，使用说明和兼容矩阵在 docs。Markdown 链接按所在文件解析，脚本定位与项目根分离，资源 URI 使用客户端解析机制。

审查来源在现有 tao.review/v0.1 下扩展显式格式 codex-exec-jsonl，核对原始 exec 事件、成功结束和匹配结论；没有观测到的模型和供应商只能记 unknown，不从 CLI、配置或模型自述推断。TOML reviewer 复用共享审查规程，作为可选原生入口；验证注册路径，不声称插件目录里的 TOML 自动生效。

<!-- tao:section tasks -->
## 任务

- [x] `TASK_20260916_RMAP7AP1X0A5ZGE0` 建立兼容性任务、阅读基线与本机 CLI 清单。
  - relates: ["CHG_20260916_6ZAC0XQF0ZNGC2CZ"]
  - depends_on: []
  - verify: 记录 612ae3c 基线、独立阅读与可用客户端；运行打包和审查来源基线。
  - evidence: [验证记录](#DOC_20260916_0YR9S9FD7ZJSA155--verification)

- [x] `TASK_20260916_D9AJD24HNR5HX5WE` 精简共享入口、路径、运行说明和审查能力边界。
  - relates: ["CHG_20260916_6ZAC0XQF0ZNGC2CZ"]
  - depends_on: ["TASK_20260916_RMAP7AP1X0A5ZGE0"]
  - verify: 覆盖 D1–D7：修改 SKILL.md、workflow、tools、runtime、review、review-receipts；链接检查与独立阅读复核。
  - evidence: [验证记录](#DOC_20260916_0YR9S9FD7ZJSA155--verification)

- [x] `TASK_20260916_WCDPVEKSQQYXWFDD` 整理接入指南、安装设计与客户端兼容矩阵。
  - relates: ["CHG_20260916_6ZAC0XQF0ZNGC2CZ"]
  - depends_on: ["TASK_20260916_RMAP7AP1X0A5ZGE0"]
  - verify: 覆盖 M1–M6、A1–A6：README、用户流程、plugin-design、cli-design、installation 与新指南、矩阵；文档与导航验证。
  - evidence: [验证记录](#DOC_20260916_0YR9S9FD7ZJSA155--verification)

- [x] `TASK_20260916_2546R68CR02ZCDV4` 验证独立 skill 的资源、Python 运行与项目定位。
  - relates: ["CHG_20260916_6ZAC0XQF0ZNGC2CZ"]
  - depends_on: ["TASK_20260916_RMAP7AP1X0A5ZGE0"]
  - verify: 覆盖 E1–E2：完整 skill 复制到含空格目录，不复制插件入口；不同 `cwd` 下运行 `tao doctor`、检查未准备诊断、显式运行 `tao setup` 和局部检查，资源无写入。
  - evidence: [验证记录](#DOC_20260916_0YR9S9FD7ZJSA155--verification)

- [x] `TASK_20260916_JH1M9NSTB2FYRM46` 增加 Codex 原始审查输出适配并验证拒绝边界。
  - relates: ["CHG_20260916_6ZAC0XQF0ZNGC2CZ"]
  - depends_on: ["TASK_20260916_RMAP7AP1X0A5ZGE0"]
  - verify: 覆盖 E4：先成功与拒绝测试并观察旧实现失败，再适配原始 exec JSONL；未知身份不得虚构，保留输入、会话和结果绑定。
  - evidence: [验证记录](#DOC_20260916_0YR9S9FD7ZJSA155--verification)

- [x] `TASK_20260916_C0KRGK3MSRTX5HCA` 评估并提供可验证的 Codex 原生 reviewer 入口。
  - relates: ["CHG_20260916_6ZAC0XQF0ZNGC2CZ"]
  - depends_on: ["TASK_20260916_RMAP7AP1X0A5ZGE0"]
  - verify: 按 0.154.0 原生发现机制提供复用共享规程的 TOML；避免覆盖已有角色、不固化模型；验证项目内发现与项目外缺席。
  - evidence: [验证记录](#DOC_20260916_0YR9S9FD7ZJSA155--verification)

- [x] `TASK_20260916_Z2FM1RBCPRZN06RX` 执行可用客户端探针并记录安装扩展决策。
  - relates: ["CHG_20260916_6ZAC0XQF0ZNGC2CZ"]
  - depends_on: ["TASK_20260916_RMAP7AP1X0A5ZGE0"]
  - verify: 覆盖 E3、E5：只运行已安装且可隔离的 CLI；未发现的九种 CLI 不安装、记录未运行；自动安装扩展按实际需求与验证条件决定。
  - evidence: [验证记录](#DOC_20260916_0YR9S9FD7ZJSA155--verification)

- [x] `TASK_20260916_J92Y84NZR8X21H60` 完成独立复核、全量回归、打包与交付记录。
  - relates: ["CHG_20260916_6ZAC0XQF0ZNGC2CZ"]
  - depends_on: ["TASK_20260916_RMAP7AP1X0A5ZGE0"]
  - verify: 运行 pytest、静态检查、受管理文档与 HTML、两种包；独立审查最终差异与阅读场景，记录未运行范围。
  - evidence: [验证记录](#DOC_20260916_0YR9S9FD7ZJSA155--verification)

<!-- tao:section verification -->
## 验证

文档先独立阅读基线，再复核实际场景；代码适配先验证失败，再实现与回归。覆盖成功导入、失败或截断、会话混合、结论不一致、输入变动和未证实身份。独立 skill 检查含空格目录、不同 cwd 和无客户端安装。

<!-- tao:results -->
共享skill与包资源已通过含空格/中文路径、无外层manifest、另一cwd、空PATH及离线准备的独立副本检查。Codex来源解析覆盖完成/截断/失败/混合会话/重复键/未结束item、输入变化及未证实身份；未执行的客户端不从文档支持推导原生保证。

| 实际范围 | 历史结果与限制 |
|---|---|
| Codex0.154.0 | 隔离项目内具名reviewer读取共享规程并复现除零错误，项目外skill与角色缺席，原始exec输出通过来源解析 |
| Claude2.1.270 | 模型探针被服务端403拒绝，监测配置未变；该次加载后行为未验收，未重登或修改个人安装 |
| 其余九种CLI | 当时无可用CLI，未运行原生验收；后续接入须单独验证隔离及作用域 |
| 维护回归 | 381 passed、1 failed、5 skipped；失败为新诊断缺中文翻译，补齐后11项语言测试及last-failed单项复验通过，不改称单次全绿 |
| 文档和分发 | 39份文档、213个本地链接、HTML稳定入口、两种包字节、Ruff及依赖一致性检查通过；21项Codex定向检查通过 |

当时依据实测采用720秒测试上限、750秒总预算，检查范围不变。未执行全量tao verify或发布验收，不声称全部必需门禁、原生客户端或平台通过。该轮静态文本由63,979缩至38,548字符（约39.7%），不是token或服从性收益。Codex TOML reviewer为显式项目注册的可选组件。原始报告与调用事件不长期保存。

<!-- /tao:results -->


<!-- tao:section questions -->
## 待确认事项

无。
