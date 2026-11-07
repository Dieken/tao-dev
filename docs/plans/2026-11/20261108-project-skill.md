---
schema: tao.project.plan/v0.1
id: "DOC_20261108_XMAKAG6QHVS1575K"
title: "项目级纯 skill 重构实施计划"
locale: "zh-Hans"
status: draft
created: "2026-11-08"
change: "CHG_20261108_BDAZPV3E7WVCF92X"
spec_docs: ["DOC_20261108_ZT37NM8REHBYC520"]
design_docs: ["DOC_20261108_5AH1TA6VTGQQHAA8"]
tasks_doc: "DOC_20261108_SJVF6ABRNSPFGRBF"
---

# 项目级纯 skill 重构实施计划

<!-- tao:section scope -->
## 范围

在 main 主工作区完成不兼容切换。先保持现有文档形态，再同步放宽 schema 和检查器；不在旧检查器下提前产生新格式。

<!-- tao:section references -->
## 参考

规格：[项目级纯 skill 重构](../../product/project-skill.md)。设计：[项目级纯 skill 架构](../../engineering/project-skill.md)。任务：{need}`DOC_20261108_SJVF6ABRNSPFGRBF`。

<!-- tao:section design -->
## 设计

按契约先行、并行修改独立子系统、集中路径切换与验收推进。安装、CLI 状态、文档检查与知识规程各自有明确文件所有者，集成者统一处理源码移动、发布、CI 和回归。

<!-- tao:section tasks -->
## 任务

任务唯一维护于 [任务附件](20261108-project-skill/tasks.md)，不在此复制进度。

<!-- tao:section verification -->
## 验证

0.18.0 已在 main 主工作区完成不兼容切换。源码为 skills/tao-dev；保留核心文档 v0.1 与稳定 ID，移除 hook、插件、全局安装、workflow 状态及 finish。详细检查输出仅留 tmp/tao，不另建审查或 evidence 文档。

- `just check`：384 项通过、1 项显式原生发现默认跳过；lint 与锁定依赖导出核对通过。最后一次本机完整入口约 8.9 秒，pytest 约 7.5 秒；仅为此次观测，不是跨机器性能承诺。
- 真实 CLI：无配置 status、批量 ID、计划创建、任务完成推断、临时交接覆盖通过；无关草稿及重复 ID 不阻断所选有效计划交接。损坏任务集合返回 unavailable；非法事项身份拒绝写入；全勾选仍为 review unknown。
- 安装：四种客户端项目生命周期及用户内容保护回归通过；独立纯 skill 包在禁用第三方包的解释器下完成安装、升级、list、卸载；本地 install.sh 入口通过，隔离用户目录未变化。
- Codex：独立运行真实 app-server skills/list，项目内发现、相邻项目隔离、卸载后消失均通过；未调用模型或使用认证。
- 文档：59 份文档、359 个含退役项的定义通过源校验；book 构建与稳定链接检查通过，浏览器确认新规格布局及跨文档 ID 跳转。历史计划对退役 ADR 的两条警告保留历史语义，不作为当前规程。
- 独立代码审查发现的任务完成误判、交接身份冲突、安装清理锁泄漏及无关文档门禁已修复并有回归；复审无剩余阻断。另修复放宽章节后可能吞掉后续条目的未闭合正式围栏。

限制：本机为 macOS/Python 3.14；未执行 Windows/其他 Python 的 CI 矩阵、远程下载安装或 Claude/Cursor/Kiro 原生发现，也未验证模型是否遵循 skill。保留上游 mini-racer 的 Python 3.14 弃用警告与 xdist 主进程无覆盖数据提示；合并覆盖结果有效。既有个人／全局安装与其他项目未迁移。

<!-- tao:section questions -->
## 未决问题

无。四份 spec/design/plan/tasks 已通过切换前的源校验（4 documents、21 definitions）；独立文档审查确认要求覆盖、项目隔离、知识保留和切换顺序无阻断。该结论不代表实现验收通过；后续结果在验证节更新，不创建独立审查报告。

