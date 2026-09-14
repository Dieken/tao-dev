---
schema: tao.project.change/v0.1
id: DOC_20260914_8MPMXBCGKMRS74T4
title: 实现协作开发核心能力
locale: zh-Hans
status: draft
created: '2026-09-14'
change: CHG_20260914_Y3TJ3KDYR2Y8AGMF
---

# 实现协作开发核心能力

<!-- tao:section scope -->
## 目标与边界

实现本项目已定义的协作开发核心能力；不引入通用项目管理平台或全局安装。

<!-- tao:section references -->
## 规格依据

项目需求见 {need}`DOC_20260914_4C7N0XHQSP7CY69P`；设计见 {need}`DOC_20260914_AG3NSZ8RBSFA0YHW`。

<!-- tao:section design -->
## 实现约束

使用统一的版本化文档契约，以可复现的小增量验证工具和流程；运行源码与开发资料分开。具体接口见 [命令设计](../../engineering/cli-design.md)。

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

- [ ] `TASK_20260914_0ZR8RND5PZ6136WX` 打通单个变更的实现、证据与恢复
  - relates: ["REQ_20260914_BFNMKT34JF1BSGW2", "REQ_20260914_0J68SDKV86ENKER2", "REQ_20260914_6YZ1XE1GC369655H", "REQ_20260914_4GKT5JRVBJNCQ05X", "REQ_20260914_4CS6P421MGW68PME", "REQ_20260914_M05MAGDARWBY5D44"]
  - depends_on: ["TASK_20260914_1PBCZHJT2VM7EWNW"]
  - verify: 一个真实变更可被新会话接手，代码变化令旧证据过期，工具不可用不会产生通过声明，并记录流程成本。

- [ ] `TASK_20260914_VCY68YN0NM3ZSD6B` 验证出版组合与双 CLI 插件适配
  - relates: ["REQ_20260914_3JQXRKWXKAZSNJ5R", "REQ_20260914_95193C19C90NRXV4", "REQ_20260914_NN0AEQ2E1GTVSMTV", "REQ_20260914_GDY8F3KPE6XBGWGD", "REQ_20260914_BWAY1ZF6HNPM855Y"]
  - depends_on: ["TASK_20260914_0ZR8RND5PZ6136WX"]
  - verify: 同源文档形成可导航书籍与可解析 ID；模板遵循使用方语言；分发包不含开发资料且无此类运行依赖；Codex CLI 与 Claude Code CLI 分别通过插件加载、已声明组件和功能路径验收，禁用 hook 后显式检查仍可运行。

<!-- tao:section verification -->
## 验证记录

源文件校验器与独立测试已在固定版本 `044f86c` 提交：`tmp/tao/venv/bin/python -m pytest -q`，75 项通过；环境为 Python 3.12.13、markdown-it-py 4.2.0、PyYAML 6.0.3、pytest 9.1.1。覆盖 11 种共享 profile、中英文模板及隔离运行副本。检查仅涉及文档源格式和关系；核心 CLI、出版及双客户端行为尚未验收。原始日志未长期保存，测试源码随版本保留。

固定版本 `10c9ab7` 提供核心命令。`tmp/tao/venv/bin/python -m pytest -q` 的 92 项测试通过，涵盖无 VCS 项目的文档子集、能力列表、JSON 错误、partial／完整能力缺失、ID 编码与三次碰撞上限、同名并发创建保护。依赖版本同前；检查不调用 rg，原始日志未长期保存。记录时间：2026-09-14T13:47:54+08:00。

<!-- tao:section questions -->
## 未决项

各命令和平台能力以实际验收为准；缺少能力不能通过空实现或改小验收范围消除。
