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

维护项目级 skill 的规格、实现、文档及发布资源，保持文档模型、检查器与当前命令契约一致。本次将分发简化为完整复制与可选通用工具，移除 tao 安装生命周期及包装脚本，不新增插件或安装器依赖。

<!-- tao:section references -->
## 参考

规格：[项目级文档驱动 skill](../../product/project-skill.md)。设计：[项目级纯 skill 架构](../../engineering/project-skill.md)。任务：{need}`DOC_20261108_SJVF6ABRNSPFGRBF`。

<!-- tao:section design -->
## 设计

skill 提供方法与资源，CLI 只保留领域辅助命令；文件分发交给项目复制或使用者选择的通用工具。运行入口与版本维护、复制验收与 CI 分开修改，集成者统一更新契约、指南并执行验证。

<!-- tao:section tasks -->
## 任务

任务唯一维护于 [任务附件](20261108-project-skill/tasks.md)，不在此复制进度。

<!-- tao:section verification -->
## 验证

源码为 skills/tao-dev；文档采用核心 v0.1 profile 与稳定 ID。文档维护只保留当前契约、有效设计依据和当前计划；运行原始输出不作为长期文档保存。

- 回归：`.venv/bin/python -m pytest -q`，339 项通过、1 项显式原生发现默认跳过；上游 mini-racer 在 Python 3.14 下产生两条弃用警告。复制后文档校验使用真实规格输入，不把空文档范围误判为可通过。
- 静态与发布：Ruff 的 E9/F63/F7/F82 检查、`scripts/export_dependencies.py --check` 通过；`scripts/bump_version.py --dry-run` 正确列出版本源与生成文件，未写入版本。
- 源校验：`tao verify --only docs --simplified --format json` 通过，覆盖 35 份文档、91 个定义、89 个引用。未提供历史基线，`deletion_checked=false`；只证明当前集合一致，不证明历史删除追溯完整。
- 出版：`tao docs build --format json` 通过，91 个稳定入口检查通过；浏览器确认客户端复制指南、可选工具与旧副本迁移说明，以及分发设计的稳定 ID 入口。
- 复制：隔离项目文件复制／移除验收通过。另用打包产物经实际 `cp -R` 复制到 Claude、Codex、Cursor、Kiro 的项目路径，分别从副本运行无依赖 help，以及已准备依赖环境下的 doctor、ID 分配、真实文档 verify 与 new；四个旧管理命令均被拒绝。移除副本保留项目文档，隔离 HOME 未改变，临时产物已清理。
- 审查：集成者自查运行入口、能力声明、版本工具、复制与原生发现验收边界，以及规格／设计／指南一致性；未另行执行独立审查。

限制：未执行 Windows／其他 Python 的 CI 矩阵、第三方 skills 安装工具、真实客户端发现或模型会话。路径 smoke 仅证明文件分发与辅助 CLI，不证明客户端加载；个人配置与其他项目未改动。

<!-- tao:section questions -->
## 未决问题

无。四份 spec/design/plan/tasks 已通过切换前的源校验（4 documents、21 definitions）；独立文档审查确认要求覆盖、项目隔离、知识保留和切换顺序无阻断。该结论不代表实现验收通过；后续结果在验证节更新，不创建独立审查报告。

