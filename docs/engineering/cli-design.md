---
schema: tao.project.design/v0.1
id: DOC_20260914_0VF190409FQCN197
title: 确定性文档与计划 CLI
locale: zh-Hans
status: draft
spec_docs: ["DOC_20260914_4C7N0XHQSP7CY69P"]
---

# 确定性文档与计划 CLI

<!-- tao:section overview -->
## 职责

技能管理文档语义与知识生命周期，智能体自行管理执行并回写成果；CLI 只处理文件、ID、查询与显式检查，不调用模型、不选择下一开发阶段、不认定交付完成。精确命令见 [工具规程](../../skills/tao-dev/references/tools.md)。

<!-- tao:section architecture -->
## 数据来源

唯一任务来源是计划中的内联任务或 `tasks_doc` 指定的附件。CHG 由计划定义；没有计划时，规格与设计仍作为规划材料保留，不自动创建计划。`status` 读取指定项目内的文档，不查询全局索引或发现其他 Git 工作树，不创建配置、执行检查或修复文件。

`new --slug` 只写计划骨架；`id new TYPE --count N` 返回 `outputs.ids`。`show` 读取正式对象。辅助命令配置可选，路径均受选定项目边界约束。

<!-- tao:section contracts -->
## 公开接口

`status [CHG|DOC|项目相对计划路径]`：省略目标时列出全部计划和未关联计划的规划材料。固定提供任务计数、`pending_tasks`、源文件位置及推断进度 `planning`、`pending`、`in_progress`、`tasks_complete`。已完成任务通过计数表达；输出不包含完整任务列表或验证正文，不生成审查结论。需要判断验证与审查时，读取计划路径中的实际记录，不能从全部勾选推断已验证、已审查或已交付。

`verify [--baseline <项目相对 JSON>]`：只读校验受管理文档，原生 JSON 固定返回 `valid`、`counts`、`deletion_checked` 与诊断，不构造完整索引再裁剪。调用方可提供带版本和来源修订的显式 ID 基线；此时额外返回基线摘要，并将未经退役的缺失 ID 作为错误。没有基线时明确报告未执行删除检查，不读取或猜测 Git 状态。`--format sarif` 将同一诊断映射为 SARIF 2.1.0，并在 run properties 保留 tao 状态与原生输出；它只适用于 `verify`，不替代其他命令的 JSON 协议。需要完整索引时使用 `validate_documents.py --format json` 入口。检查成功只表示实际文档范围内的结果，不代替文档语义审查或项目测试。

提供 `doctor`、`show`、`docs build`、`project inspect`、`project configure` 与正式对象退役命令 `retire`。入口的帮助与版本查询只用标准库；文档命令缺依赖时明确诊断，不自动准备环境。安装生命周期不属于 CLI。

`.tao/config.toml` 只管理文档、语言、出版与项目内输出路径；`project inspect` 只读这些配置及摘要，`project configure` 校验并显式应用草稿。测试、代码静态检查、构建等命令由 justfile、Makefile、项目清单或 CI 管理，tao 不发现或保存候选命令。

<!-- tao:section invariants -->
## 边界

查询无副作用；有歧义时列出候选，不按文件修改时间猜测；损坏文档报告路径与原因，不静默覆盖。工具结果不授予写入、发布或客户端权限。审查与验证的详细材料默认临时保存，计划只保留当前摘要。JSON 与文本输出表达相同事实，`new` 和 `status` 不提供执行建议。`status` 和 `show` 遇到无关草稿损坏可返回 `partial` 与 `documents_valid=false` 并保留诊断，不要求整本文档有效才能读取。模型预算、词元（token）用量报告及其预检不属于当前 CLI。

<!-- tao:section verification -->
## 验证设计

覆盖零计划、唯一/多个计划、内联/附件任务、所有任务完成但验证或审查未知、无配置只读、无流程建议输出、路径越界、格式错误与缺依赖。文档校验输出不能冒充项目测试、语义审查、实际客户端加载或独立审查。执行结果由当前计划维护。
