---
schema: tao.project.plan/v0.1
id: "DOC_20260918_F8YYWKH5QY1KXPHE"
title: "Skill 评审回归修正"
locale: "zh-Hans"
status: draft
created: "2026-09-18"
spec_docs: ["DOC_20260914_4C7N0XHQSP7CY69P"]
design_docs: ["DOC_20260914_P1G9T0KSCC0FTBM1", "DOC_20260914_7RJ1YVEC0CP478BY"]
change: "CHG_20260918_94AXFPY6YV3H18VM"
---

# Skill 评审回归修正

<!-- tao:section scope -->
## 目标与边界

对 `7c4b033..5b723eb` 七个提交做一次以 skill 编写实践为视角的复查，按用户逐项确认的方案修正 13 项发现。范围限于 skill 入口、运行参考、模板、本地化资源、相关开发文档与维护回归，不改 CLI 行为、schema 契约与已记录的历史结果。

复查确认的既有正确改动保持不变：`--output` 输入输出分离、evidence 结果枚举扩充、出版器内部机制迁回文档契约、evidence 字段语义合并到证据保存。

<!-- tao:section references -->
## 规格引用

沿用 {need}`REQ_20260914_4CS6P421MGW68PME` 的工程规程加载要求与 {need}`REQ_20260914_M05MAGDARWBY5D44` 的独立判断要求；保留现有 DOC、CHG、TASK、EVD 标识与下游引用。

<!-- tao:section design -->
## 设计

必读路径按实际加载单位拆分。前一批已用行为试验确认"读取相关小节"仍导致整篇加载，并据此拆分工程规程；同一结论未施加于 workflow，而它是最大且每次必读的参考。入口与授权、讨论与进度留在原页，各动作移入独立页面，入口不再声称部分读取。斜杠命令派发单个动作，直接链接动作页；需要授权或讨论依据的链接仍指向原页。工程专题维持单文件，其场景索引改为不暗示分段加载——该页按需读取，拆成七份会把一次读取变成多次读取与多次判断。

审查模板按既有 evidence 约定收敛。`result`、`coverage` 原为合法终值，作者遗漏即静默通过，改为占位符后由枚举校验承担；模板不被任何生成器消费，`skeleton()` 只渲染 plan profile，因此无回归面。发现与处置分类的本地化字符串此前未被任何模板引用，分类只能自拟且双语可能分叉，现作为可删的三级骨架进入模板；裁决保持默认单表。占位符名回到其余模板的短语义槽约定，写作规则由报告写法维护；其中唯一没有任何参考覆盖的约束单独补入该页。

重复指向合并到权威位置：只读审查者不再读取其无权执行的保存与命名规则，纯指针小节与同段重复链接删除，引用段保留写作时的正面规则，豁免情形交给诊断自带的双语 remediation。

<!-- tao:section tasks -->
## 任务

- [x] `TASK_20260918_CH85RPD05DY5MSH4` 拆分流程参考并删除重复路由，补回局部修复路由的回归保护。
  - relates: ["CHG_20260918_94AXFPY6YV3H18VM"]
  - depends_on: []
  - verify: 运行维护回归；核对全仓 Markdown 链接解析、受管理文档校验与该提交单独可通过。
  - evidence: [验证记录](#DOC_20260918_F8YYWKH5QY1KXPHE--verification)
- [x] `TASK_20260918_7CKBPN9JW8K54TP1` 收敛审查模板的结果、分类与占位符约定。
  - relates: ["CHG_20260918_94AXFPY6YV3H18VM"]
  - depends_on: ["TASK_20260918_CH85RPD05DY5MSH4"]
  - verify: 双语渲染两份模板；核对本地化资源无未使用与缺失键；检查未填结果被拒绝。
  - evidence: [验证记录](#DOC_20260918_F8YYWKH5QY1KXPHE--verification)

<!-- tao:section verification -->
## 验证

<!-- tao:results -->
维护回归 490 passed、5 skipped，耗时 466.29 秒。5 项跳过的是未启用的原生客户端安装探针，不计入通过。`tao verify --only docs` 对 48 份显式受管理文档通过，只保留 cli-design 中 handoff 命名示例的一条既有 TAO-LINK-002 warning，无新增诊断；deletion_checked=false。全仓 `plugins/`、`docs/` 与 README 的相对 Markdown 链接全部解析成功。

第一个提交用 `git stash --keep-index` 单独验证，36 项相关检查通过，确认其不依赖第二个提交。未填 `result` 的报告被枚举校验拒绝，诊断列出全部允许值。两份模板在 en 与 zh-Hans 下渲染，本地化资源的未使用键与缺失键均为 0；出版回归改为断言四个本地化处置取值实际进入 HTML。

必读底座由 SKILL.md 加 workflow.md 的 9,880 字节降至 6,537 字节。这是静态体积，不等于模型实际 token 消耗；本次未执行修改前后的行为对照试验，读取路径变化与报告质量变化均未实测。分类骨架是否改善真实报告未度量。

两条链接扫描测试原先对整份文本匹配，新增的填写样例因此被判为越界资源引用；改为跳过围栏代码后通过，与 skill 自身"围栏代码示例不属于该检查"的规则一致。

耗时剖析：`test_runtime.py` 139.4 秒、`test_installed_runtime.py` 74.3 秒、`test_reviews.py` 45.4 秒、`test_codex_reviews.py` 42.6 秒、`test_verification.py` 26.9 秒、`test_standalone_skill.py` 20.4 秒，六者合计 349 秒占 75%，其余 33 个文件 393 个用例合计 115 秒。call 阶段 443.7 秒、setup 阶段 20.7 秒，说明 module 级 fixture 已在复用，成本在用例体内的真实 venv 准备、整插件复制与子进程启动。该结果供后续取舍参考，本次未改测试组织。
<!-- /tao:results -->

<!-- tao:section questions -->
## 待确认事项

测试执行时间的优化未决：是否引入并行执行，以及 `test_runtime.py` 中仅验证复用与不修改基座的用例能否共享一个已准备环境，待单独确认后处理。工作区的 `uv.lock` 被本地工具改写为镜像地址，与本次工作无关，未纳入提交。
