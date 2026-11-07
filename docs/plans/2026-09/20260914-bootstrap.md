---
schema: tao.project.plan/v0.1
id: DOC_20260914_8MPMXBCGKMRS74T4
title: 实现协作开发核心能力
locale: zh-Hans
status: draft
created: '2026-09-14'
change: CHG_20260914_Y3TJ3KDYR2Y8AGMF
spec_docs: ["DOC_20260914_4C7N0XHQSP7CY69P", "DOC_20260914_E1B61A3F8V1TYAZB"]
design_docs: ["DOC_20260914_AG3NSZ8RBSFA0YHW", "DOC_20260914_0VF190409FQCN197", "DOC_20260914_7RJ1YVEC0CP478BY", "DOC_20260914_P1G9T0KSCC0FTBM1"]
updated: "2026-09-17"
---

# 实现协作开发核心能力

> 历史计划：保留当时的目标、任务与实测范围，不作为当前操作规程；当前纯 skill 契约见 [项目级重构](../2026-11/20261108-project-skill.md)。旧机制的历史通过不证明当前版本通过。

<!-- tao:section scope -->
## 目标与边界

实现本项目已定义的协作开发核心能力；不引入通用项目管理平台或全局安装。

<!-- tao:section references -->
## 规格依据

{need}`DOC_20260914_4C7N0XHQSP7CY69P`；{need}`DOC_20260914_E1B61A3F8V1TYAZB`。

<!-- tao:section design -->
## 实现约束

设计依据：{need}`DOC_20260914_AG3NSZ8RBSFA0YHW`；{need}`DOC_20260914_0VF190409FQCN197`；{need}`DOC_20260914_7RJ1YVEC0CP478BY`；{need}`DOC_20260914_P1G9T0KSCC0FTBM1`。

使用统一的版本化文档契约，以可复现的小增量验证工具和流程；运行源码与开发资料分开。具体接口见 [命令设计](../../engineering/cli-design.md)。

独立审查采用只读输入请求与显式记录导入；按配置名称绑定 CHG、当前输入和策略摘要，核对原始结论、会话及实际模型信息。结构化记录保留发现处置和限制，verify/status 不调度模型。缺失、过期、无效及未解决阻断均不能满足交付门槛；本地记录只提供一致性检查，不宣称身份认证。实现与反例覆盖归入核心 CLI 任务，完整客户端验收仍独立保留。

退役写入沿用现有 JSONL 契约，默认预览，显式应用后先保存记录再移除完整条目；文档级退役覆盖其拥有的全部定义。校验最终集合与引用关系，单文件原子替换配合可检测、可恢复的中间状态，不新增事务台账。

书籍章节迁移通过 documents.section_redirects 配置旧 DOC／章节键到当前 DOC／章节键的直接映射；目标来自同一索引，拒绝未知章节与跳转链，普通校验和退役共用约束。发布页生成按片段跳转及可读后备链接，不改文档的既有 ID 或维护第二份正文。

诊断使用完整英文模板及中文消息资源，参数与渲染文字分开；显式诊断参数覆盖项目界面配置，未配置时文档按自身 locale 呈现。启动层只依赖标准库，共用翻译资源；外部原始错误不改写，未知消息如实回退。自动检查翻译覆盖与占位集合，测试语言切换不改变规则、位置、退出码及检查范围。

<!-- tao:section tasks -->
## 既有研发任务

- [x] `TASK_20260914_067XEKJC4WFF87HQ` 评审并确定最小文档契约
  - relates: ["REQ_20260914_42AXMZ2KH2RAZ8M3", "REQ_20260914_5Y6CWDE3MFMKJXSB", "REQ_20260914_GDY8F3KPE6XBGWGD"]
  - depends_on: []
  - verify: 文档规程、格式注册表与模板一致；关键语法、索引边界、诊断级别与语言解耦有决定；不存在阻断校验器实现的问题。
  - evidence: [校验器与格式回归](#DOC_20260914_8MPMXBCGKMRS74T4--verification)

- [x] `TASK_20260914_1PBCZHJT2VM7EWNW` 建立最小校验器、核心命令与独立反例集
  - relates: ["REQ_20260914_42AXMZ2KH2RAZ8M3", "REQ_20260914_MG6TN8H5GBTAZZR3", "REQ_20260914_GDY8F3KPE6XBGWGD"]
  - depends_on: ["TASK_20260914_067XEKJC4WFF87HQ"]
  - verify: 正常、重复 ID、悬空引用、非法章节、非法任务及未知版本样例得到预期诊断；中英文显示标签不影响结构解析；代码围栏中的示例不会误入正式索引；doctor、id new、show 和 verify 文档子集的能力、退出码、partial 标记及无 VCS／无 rg 场景可验证。
  - evidence: [核心命令验收](#DOC_20260914_8MPMXBCGKMRS74T4--verification)

- [x] `TASK_20260914_0ZR8RND5PZ6136WX` 打通单个变更的实现、证据与恢复
  - relates: ["REQ_20260914_BFNMKT34JF1BSGW2", "REQ_20260914_0J68SDKV86ENKER2", "REQ_20260914_6YZ1XE1GC369655H", "REQ_20260914_4GKT5JRVBJNCQ05X", "REQ_20260914_4CS6P421MGW68PME", "REQ_20260914_M05MAGDARWBY5D44"]
  - depends_on: ["TASK_20260914_1PBCZHJT2VM7EWNW"]
  - verify: 一个真实变更可被新会话接手，代码变化令旧证据过期，工具不可用不会产生通过声明，并记录流程成本。
  - evidence: [执行、恢复与计量验收](#DOC_20260914_8MPMXBCGKMRS74T4--verification)

- [x] `TASK_20260914_VCY68YN0NM3ZSD6B` 验证出版组合与双 CLI 插件适配
  - relates: ["REQ_20260914_3JQXRKWXKAZSNJ5R", "REQ_20260914_95193C19C90NRXV4", "REQ_20260914_NN0AEQ2E1GTVSMTV", "REQ_20260914_GDY8F3KPE6XBGWGD", "REQ_20260914_BWAY1ZF6HNPM855Y"]
  - depends_on: ["TASK_20260914_0ZR8RND5PZ6136WX"]
  - verify: 同源文档形成可导航书籍与可解析 ID；模板遵循使用方语言；分发包不含开发资料且无此类运行依赖；Codex CLI 与 Claude Code CLI 分别通过插件加载、已声明组件和功能路径验收，禁用 hook 后显式检查仍可运行。
  - evidence: [出版及限定版本客户端验收](20260914-portable-runtime.md#DOC_20260914_3541E3H7SN5V7MS5--verification)

<!-- tao:section verification -->
## 验证记录

本计划的历史验证覆盖文档解析、核心CLI、出版、检查回执与审查接入；维护命令见[检查入口](../../../tests/acceptance/quality.py)。固定实现及主要观察如下，不将不同版本结果合并为一次完整通过：

| 固定输入 | 实际验证 | 范围与限制 |
|---|---|---|
| 044f86c | 75项测试通过；Python3.12.13、markdown-it-py4.2.0、PyYAML6.0.3、pytest9.1.1 | 11种profile、中英文模板与独立副本；不是CLI或客户端验收 |
| 72746fd | 101项测试通过；Sphinx9.1.0、MyST5.1.0、book theme1.4.0 | 16份开发文档、53定义的HTML与稳定入口；不含PDF和跨DOC章节别名 |
| b59329d | 198项测试通过；Ruff与HTML通过 | 诊断语言、独立入口、hook、并发及回退；跨环境结果见运行环境计划 |
| e4e1eaa | 218项测试通过，346.28秒；代码检查349.078秒，Ruff/Node.js/HTML通过 | 覆盖率60.36%受隔离子进程观测限制；完整verify仍not_run/blocked |

客户端执行方法见[客户端试验](../../../tests/acceptance/README.md)，分平台与包格式的限定结果见[运行环境验收](20260914-portable-runtime.md#DOC_20260914_3541E3H7SN5V7MS5--verification)。本节仅保留与核心交付有关的观察：

- macOS的Claude Code2.1.268与Codex0.154.0在隔离合成项目中发现共享资源、执行doctor/status，并检查项目外不可见。Claude原生Write触发诊断；Codex完整插件和hook保证须以运行环境计划中的对应包格式验收为准。
- 两个独立上下文均复现覆盖已有文件的缺陷并建议排他创建；Claude事件报告claude-opus-5[1m]/firstParty，Codex配置为gpt-6-astra/openai，后者并非服务端确认。该反例不代表全面独立审查。
- 实际handoff恢复保留DOC/CHG/TASK和原验收条件，识别旧证据并运行回归。Codex个人配置模式会写全局projects信任条目，不能凭调用级override声明隔离；维护验收改用独立客户端状态及宿主字节监测。
- 固定树206c01dcf338447c0b345074fdea02cb2f3f6940的Claude只读审查未发现所供审查接入代码的门槛绕过；监测到个人市场元数据变化，因此未生成可导入回执。七项建议按反例处理，不以静态报告满足必需审查。

历史完整交付仍受客户端组合任务与有效独立审查门槛阻断；局部回归、模型调用成功或文档存在不能替代该门槛。覆盖率只表示可观测路径，CLI估算不等于实际账单。固定版本后的逐次测试计数及执行经过留在Git；原始日志未长期保存，不能由本文重建当前通过证据。

<!-- tao:section questions -->
## 待确认事项

无。
