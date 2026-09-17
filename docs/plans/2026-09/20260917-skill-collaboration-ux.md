---
schema: tao.project.plan/v0.1
id: DOC_20260917_ZT7S6XFKH6HPSKGA
title: Skill 讨论、授权与审查改进
locale: zh-Hans
status: draft
created: "2026-09-17"
change: CHG_20260917_NGR1W1WDRWPA5HKJ
spec_docs: ["DOC_20260914_4C7N0XHQSP7CY69P"]
design_docs: ["DOC_20260914_0VF190409FQCN197"]
updated: "2026-09-17"
---

# Skill 讨论、授权与审查改进

<!-- tao:section scope -->
## 目标与边界

改写现有 skill 参考，明确讨论顺序、阶段授权、进度展示和以证据裁决异议的做法。保留可选与必需审查的区别、轮次预算及实际来源要求；不增加固定辩论轮次、问题配额、角色体系或 CLI 功能。运行脚本、格式和模板不变；同步修正中文措辞、章节显示名及已有文档的内容归属。

本次不扩大客户端兼容性或模型效果声明，不进行插件安装、推送或发布。

<!-- tao:section references -->
## 规格依据

沿用 {need}`DOC_20260914_4C7N0XHQSP7CY69P` 的协作协议。用户已批准实施、验证与审查，要求修改具有明确收益且文字简洁；本计划在隔离 worktree 中执行。

<!-- tao:section design -->
## 设计引用

沿用 {need}`DOC_20260914_0VF190409FQCN197`。workflow 集中维护讨论、授权和用户进度；engineering 约束方案取舍与失败处理；review 维护独立输入与发现裁决。正文写法、文档组织和接续入口仅同步必要约束，避免重复。

<!-- tao:section tasks -->
## 任务

- [x] `TASK_20260917_XKXC8MXTZNQB5RRG` 核对规则、受检基线与情境。
  - relates: ["CHG_20260917_NGR1W1WDRWPA5HKJ"]
  - depends_on: []
  - verify: 检查基线、引用与打包测试；演练授权、提问、进度及异议处理情境，记录验证限制。
  - evidence: [验证记录](#DOC_20260917_ZT7S6XFKH6HPSKGA--verification)
- [x] `TASK_20260917_ZEBYQMQS5ZV4AB7V` 改善讨论、阶段授权和进度展示。
  - relates: ["CHG_20260917_NGR1W1WDRWPA5HKJ"]
  - depends_on: ["TASK_20260917_XKXC8MXTZNQB5RRG"]
  - verify: 文档完成不扩大授权，已有明确授权不重复询问；有依赖的问题先问前置，继续和长任务展示真实进度。
  - evidence: [验证记录](#DOC_20260917_ZT7S6XFKH6HPSKGA--verification)
- [x] `TASK_20260917_5KCQ66M0WW3GM4ZX` 细化反证、复杂度和审查裁决规则。
  - relates: ["CHG_20260917_NGR1W1WDRWPA5HKJ"]
  - depends_on: ["TASK_20260917_XKXC8MXTZNQB5RRG"]
  - verify: 核对具体场景、简单替代、失败可达性、首轮输入隔离与先核实后修复；保留审查预算和来源限制。
  - evidence: [验证记录](#DOC_20260917_ZT7S6XFKH6HPSKGA--verification)
- [x] `TASK_20260917_P30SMGN347BG2W8D` 消除矛盾、修正中文措辞与章节归属，检查篇幅。
  - relates: ["CHG_20260917_NGR1W1WDRWPA5HKJ"]
  - depends_on: ["TASK_20260917_ZEBYQMQS5ZV4AB7V", "TASK_20260917_5KCQ66M0WW3GM4ZX"]
  - verify: 统一局部维护边界和检查用词；核对待确认事项、范围和验证内容归属，保留 ID 与章节键；比较文本规模。
  - evidence: [验证记录](#DOC_20260917_ZT7S6XFKH6HPSKGA--verification)
- [x] `TASK_20260917_HE342KRCCKTRHEVF` 完成验证、独立复查和提交。
  - relates: ["CHG_20260917_NGR1W1WDRWPA5HKJ"]
  - depends_on: ["TASK_20260917_P30SMGN347BG2W8D"]
  - verify: 运行仓库回归、受管理文档校验和出版检查；记录独立复查与情境演练的实际范围，再提交。
  - evidence: [验证记录](#DOC_20260917_ZT7S6XFKH6HPSKGA--verification)

<!-- tao:section verification -->
## 验证

检查原有约束是否保留，以及新增指令能否在具体场景中执行。复用现有回归，不增加仅匹配措辞的测试。开发计划按共享 profile 校验；skill 参考检查内容、链接与打包。情境演练不等同于原生客户端、跨模型或跨供应商实测。

<!-- tao:results -->
基线为 0c6deee6d32ad951d909ca4ae2e419f531558943；doctor 确认核心与出版环境可用。基线仓库、打包、独立 skill 与引用读取测试共 13 项通过（61.76 秒）。

修改涉及十份现有参考、中文标题资源及开发文档归类；入口与全部参考的 Unicode 字符数由 38,269 增至 39,576（+1,307，3.4%），不是 token 数或效果指标。已有检查、审查预算与来源规则保留；文档完成不扩大授权，已有明确的后续授权及跳过可选审查的决定不重复确认。

两位代理各完成修改前、后七个情境的应用演练：旧规则下均未展示进度表，提问顺序及强势要求下的取舍处理有差异；修改后均展示真实进度表、先问实际场景并给出具体代价和替代。授权、发现裁决与来源限制在两版均能遵循。新建独立上下文受会话代理数量上限阻止，演练复用已有研究上下文，没有无指导对照或五次独立重复；这些观察不能证明模型效果提升。

一位未读作者演练输出的代理独立复查全部改动，未发现具体缺陷；75 个本地链接目标存在，锚点不在该次检查范围内。该审查也复用已有研究上下文，不属于跨模型或跨供应商评审。Ruff 与首轮 42 份受管理文档检查通过；文档检查为 partial／not-evaluated，不代表完整交付门槛通过。

原文快照、情境和原始验证输出保存在忽略的 tmp/tao/collaboration-ux/，不长期分发。首轮 HTML 构建及新增导航、验证章节锚点、固定入口与本地脚本检查通过。使用项目本地 Python 3.12.13 执行 tests/acceptance/quality.py，433 项通过、5 项原生客户端探针按默认配置跳过（907.65 秒），覆盖率汇总完成且命令退出码为 0。未运行原生客户端或跨供应商模型实验。用户批准的中文措辞与章节归类调整完成。补充 60 项文档、语言、打包、独立 skill 与引用读取回归全部通过（108.64 秒）；新生成中文计划使用“待确认事项”，questions 键保留。42 份文档及 HTML 构建通过，逐一核对 13 处改名章节的标题、稳定锚点与文档入口。全部已修改的既有 Markdown 文件保留原 ID／引用与章节键；未改历史任务完成状态。独立定向复核未发现遗漏的限制或无依据取消的待定事项。本轮仅改文字、标题资源和文档归类，未重跑此前已通过的全部代码回归。
<!-- /tao:results -->

<!-- tao:section questions -->
## 待确认事项

无。
