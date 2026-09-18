---
schema: tao.project.plan/v0.1
id: "DOC_20260918_JBRE6CXEJK6RMS2A"
title: "操作状态核验与审查文档管理"
locale: "zh-Hans"
status: draft
created: "2026-09-18"
spec_docs: ["DOC_20260914_4C7N0XHQSP7CY69P"]
design_docs: ["DOC_20260914_P1G9T0KSCC0FTBM1", "DOC_20260914_Y5RR8BVF6065JTYP"]
change: "CHG_20260918_TZG032GMJ2B1S07P"
---

# 操作状态核验与审查文档管理

<!-- tao:section scope -->
## 目标与边界

补足命令报告成功与目标状态完成的区别，统一正式审查报告的 schema、归属与引用。检查本仓库 Markdown 管理边界及外部消费项目的报告样例；外部项目仅只读调查，不修改其文件。本次为用户直接授权的局部规程与校验器修复，复用已有规格与设计。

<!-- tao:section references -->
## 规格引用

沿用 {need}`DOC_20260914_4C7N0XHQSP7CY69P` 的协作与文档约束。

<!-- tao:section design -->
## 设计

沿用 {need}`DOC_20260914_P1G9T0KSCC0FTBM1` 与 {need}`DOC_20260914_Y5RR8BVF6065JTYP`。正式审查复用 evidence profile，审查模板由报告作者读取；不新建实体或机器回执格式。校验器提示正文中未链接的完整 ID 与明确的 Markdown 文件代码片段，代码示例不自动注册引用；无法可靠识别的缩写与任意路径由内容审查负责。

<!-- tao:section tasks -->
## 任务

- [x] `TASK_20260918_WZXHY67Z5RM4CEBC` 完善状态核验、审查模板及引用诊断，核对文档管理范围并验证。
  - relates: ["CHG_20260918_TZG032GMJ2B1S07P"]
  - depends_on: []
  - verify: 运行项目回归、显式受管理源校验和 HTML 构建；检查生成报告页面的实际 href 与目标锚点；核对工作区和每项预期改动。
  - evidence: [验证记录](#DOC_20260918_JBRE6CXEJK6RMS2A--verification)

<!-- tao:section verification -->
## 验证

原始日志保存在忽略的 tmp/tao/operation-review-evidence/；结论在此记录，不另存常规证据报告。

初始盘点 91 份跟踪 Markdown：42 份 docs/ 正式文档均使用受支持 schema；49 份范围外资料包括 18 份运行参考、14 份模板、11 份 command、1 份 agent、1 份 skill 入口、2 份客户端开发指令及 2 份 README，均有明确读取职责。未发现其他遗漏的正式文档类型；新增范围回归阻止正式报告悄然落入未声明目录。本次另增计划和审查模板，前者纳入 docs/，后者是生成 evidence 的输入资源。

外部消费项目仅只读调查：四份正式报告均无 frontmatter、无 need 角色且位于 docs 范围外；其中一份含 15 个不存在的临时快照文件链接。AST 片段调查发现 133 处未链接完整 ID 和 96 处代码形式的 Markdown 文件引用，不含缩写 ID 或普通文本路径；这不是对外部项目进行 schema 验证，也未修改其报告或确认原审查结论。

新增规则要求依赖操作结果前回读状态、逐项核对批量修改，明确只读观察覆盖后置条件时停止，不无限递归。该规则经文本与具体情境自查，未进行模型服从性实验，不能声称已证明消除误判。

定向回归 33 项通过，覆盖审查模板的双语 evidence 结构、引用索引、实际 HTML href／目标锚点、裸引用提示与示例豁免、原有链接错误、仓库管理边界和诊断本地化。修正首轮测试中对带冒号文件路径的诊断预期：无目录前缀时会解析为 URI scheme，应报 TAO-REF-004；快照目录内的不存在文件报 TAO-REF-001。

43 份显式受管理文档无 error，Ruff 报告为空。新诊断促使四处文件引用改为实际链接；剩余一条 TAO-LINK-002 位于 [命令设计](../../engineering/cli-design.md) 的 handoff 输出命名说明，表示尚未生成的文件名，不是可导航对象，人工核对后保留。检查未提供历史删除基线，deletion_checked=false，不等于完整交付验收。

使用项目本地 Python 执行 tests/acceptance/quality.py，459 项通过、5 项原生客户端探针按默认配置跳过，耗时 594.00 秒；覆盖率汇总完成，命令退出码为 0。回归运行期间补充的显式锚点／客户端导入语法豁免、模板注册路径及仓库范围守卫由上述 33 项定向回归另行验证。未运行原生客户端模型调用或独立实现审查，不声明完整交付门槛已满足。

本地 HTML 构建完成，实际读取契约与计划页面，确认稳定章节锚点、refs 入口和审查模板链接的目标文件存在；审查报告夹具另外确认 need 引用与文件章节链接均生成正确 href，并在目标页找到相应锚点。保存的只是本地出版结果，没有部署。既有文档定义 ID 保留。操作状态核验规则已单独提交；本计划记录本轮两项改动的验证，不包含随后讨论中尚未获准的协作方式调整。

<!-- tao:section questions -->
## 待确认事项

无。独立审查与原生客户端验收不由本次本地检查替代。
