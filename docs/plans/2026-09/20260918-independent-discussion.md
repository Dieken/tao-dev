---
schema: tao.project.plan/v0.1
id: "DOC_20260918_VEC8NPDT4SQ38NSX"
title: "所有讨论中的独立判断与提问风格"
locale: "zh-Hans"
status: draft
created: "2026-09-18"
spec_docs: ["DOC_20260914_4C7N0XHQSP7CY69P"]
design_docs: ["DOC_20260914_AG3NSZ8RBSFA0YHW"]
change: "CHG_20260918_FPP13TB4CW7VYVAP"
---

# 所有讨论中的独立判断与提问风格

<!-- tao:section scope -->
## 目标与边界

按用户批准的方向改进讨论风格，适用于所有讨论，不限于 spec、design。区分提议、决定和授权；重要提议给出独立判断、可行替代、推荐及改选条件；按依赖提问并明确收敛边界。本次为已授权的局部运行指令维护，不修改 CLI、schema、安装或全局客户端配置。

<!-- tao:section references -->
## 规格引用

沿用 {need}`REQ_20260914_M05MAGDARWBY5D44` 与 {need}`UC_20260914_GFFHGA8RGYGRNGAN`，保留既有 ID 并补充非文档阶段的讨论场景。

<!-- tao:section design -->
## 设计

沿用 {need}`DOC_20260914_AG3NSZ8RBSFA0YHW`。skill 入口要求必读共同讨论原则，workflow 集中维护风格与授权，engineering 保留工程判断依据，删除重复的通用约束。不引入固定对抗轮次或新的决定台账。

<!-- tao:section tasks -->
## 任务

- [x] `TASK_20260918_E929GDAWP6R3BXJK` 更新共同讨论规则、同步规格设计并验证读取范围和文档完整性。
  - relates: ["CHG_20260918_FPP13TB4CW7VYVAP"]
  - depends_on: []
  - verify: 核对入口及原有授权约束，检查试探提议、事实冲突、合理方案、知情决定、已授权行动和依赖问题等场景；运行 skill 格式、仓库文档与分发回归及本地 HTML 检查。
  - evidence: [验证记录](#DOC_20260918_VEC8NPDT4SQ38NSX--verification)

<!-- tao:section verification -->
## 验证

日志保存在忽略的 tmp/tao/independent-discussion/。使用项目本地 Python 执行 skill-creator quick_validate，frontmatter 与命名检查通过；仓库文档、分发、独立 skill 和客户端读取记录回归共 14 项通过（39.91 秒）。未修改运行代码或测试，不新增仅匹配指令措辞的测试，未重跑此前已经完成的全部代码回归。

入口、workflow 和 engineering 已逐项回读：所有讨论都会读取共同原则；试探提议不升级为授权；事实冲突先核查；重要提议给判断与真实替代，没有可行替代时说明依据；合理方案可赞同；知情决定与已有授权不反复确认；前置未定不暗含答案。以上是作者对文本及情境的静态核对，未进行独立模型演练或原生客户端服从性验收，不证明迎合行为已经消除，也不满足完整独立审查门槛。

44 份显式受管理文档无 error；一条既有 warning 来自 [命令设计](../../engineering/cli-design.md) 的 handoff 文件命名示例，未作为可导航引用。未提供历史删除基线，deletion_checked=false。既有规格、设计的 DOC／REQ／UC ID 保留。HTML 构建完成，核对修改页的稳定锚点、计划到规格的 need 链接及实际目标；未部署。

<!-- tao:section questions -->
## 待确认事项

无。用户已批准方向，并明确扩展到所有讨论。
