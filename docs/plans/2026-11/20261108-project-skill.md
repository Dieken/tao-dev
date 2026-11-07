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

维护项目级 skill 的规格、实现、文档及发布资源，保持文档模型、检查器与当前命令契约一致。

<!-- tao:section references -->
## 参考

规格：[项目级文档驱动 skill](../../product/project-skill.md)。设计：[项目级纯 skill 架构](../../engineering/project-skill.md)。任务：{need}`DOC_20261108_SJVF6ABRNSPFGRBF`。

<!-- tao:section design -->
## 设计

按契约先行、并行修改独立子系统、集中路径切换与验收推进。安装、CLI 状态、文档检查与知识规程各自有明确文件所有者，集成者统一处理源码移动、发布、CI 和回归。

<!-- tao:section tasks -->
## 任务

任务唯一维护于 [任务附件](20261108-project-skill/tasks.md)，不在此复制进度。

<!-- tao:section verification -->
## 验证

源码为 skills/tao-dev；文档采用核心 v0.1 profile 与稳定 ID。文档维护只保留当前契约、有效设计依据和当前计划；运行原始输出不作为长期文档保存。

- 回归：`.venv/bin/python -m pytest -q`，384 项通过、1 项显式原生发现默认跳过；上游 mini-racer 在 Python 3.14 下产生两条弃用警告。
- 源校验：`tao verify --only docs --simplified --format json` 通过，覆盖 35 份文档、90 个定义、86 个引用，无诊断。未提供历史基线，`deletion_checked=false`；该结果只证明当前集合一致，不证明历史删除追溯完整。
- 出版：`tao docs build --format json` 通过，90 个稳定入口检查通过；浏览器确认打包设计页面、两个改名文档的稳定 ID 跳转及交付导航。
- 安装：`.venv/bin/python tests/acceptance/project_skills.py --client codex` 的隔离项目文件安装、升级、查看和卸载通过；未运行原生发现。
- 状态：`tao status --simplified --format json` 只列出现行计划，文档集合有效；任务完成与审查状态仍分别报告。

限制：本次为文档维护及对应回归，未执行 Windows/其他 Python 的 CI 矩阵、远程下载安装、真实客户端发现或模型会话；个人配置与其他项目不在维护范围。

<!-- tao:section questions -->
## 未决问题

无。四份 spec/design/plan/tasks 已通过切换前的源校验（4 documents、21 definitions）；独立文档审查确认要求覆盖、项目隔离、知识保留和切换顺序无阻断。该结论不代表实现验收通过；后续结果在验证节更新，不创建独立审查报告。

