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

计划验收包含项目隔离安装升级卸载、plan/tasks 状态与交接、ID/引用/导航错误检测、书籍 HTML、移除旧接口和全量测试。详细日志留 tmp/tao。当前尚未执行实现验收。

<!-- tao:section questions -->
## 未决问题

无。四份 spec/design/plan/tasks 已通过切换前的源校验（4 documents、21 definitions）；独立文档审查确认要求覆盖、项目隔离、知识保留和切换顺序无阻断。该结论不代表实现验收通过；后续结果在验证节更新，不创建独立审查报告。

