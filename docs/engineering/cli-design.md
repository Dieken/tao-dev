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

skill 管理文档语义与知识生命周期，agent 自行管理执行并回写成果；CLI 只处理文件、ID、查询与显式检查，不调用模型、不选择下一开发阶段、不认证交付。精确命令见 [工具规程](../../skills/tao-dev/references/tools.md)。

<!-- tao:section architecture -->
## 数据来源

唯一任务源是 plan 内联任务或 tasks_doc 指定的附件。CHG 由 plan 定义；没有 plan 时保留 spec/design 为规划材料，不自动建计划。status 读取明确项目内文档，不查询全局索引或发现其他 worktree，不创建配置、执行检查或修复文件。

new --slug 只写计划骨架；id new TYPE --count N 返回 outputs.ids。show 读取正式对象。辅助命令配置可选，路径均受选定项目边界约束。

<!-- tao:section contracts -->
## 公开接口

`status [CHG|DOC|项目相对计划路径]`：省略目标列全部计划和未关联计划的规划材料。固定提供任务计数、pending_tasks、源文件位置及推断进度 planning/pending/in_progress/tasks_complete。已完成任务通过计数表达，不再复制 tasks 列表；不输出验证正文或固定的 review 占位。需要判断验证与审查时，读取计划路径中的实际记录，不能从全部勾选推断已验证、已审查或已交付。

`verify`：只校验受管理文档，固定返回 valid、counts、deletion_checked 与诊断，不构造完整索引再裁剪。没有 simplified/summary 模式或 dry-run；验证本身只读，空的 planned 不提供范围或结果价值。明确需要完整索引时使用既有 validate_documents.py --format json 入口。检查成功只表示实际文档范围内的结果，不代替文档语义审查或项目测试。

提供 doctor、show、docs build、project inspect/configure 与正式对象 retire。入口的帮助与版本查询只用标准库；文档命令缺依赖时明确诊断，不自动准备环境。安装生命周期不属于 CLI。

.tao/config.toml 只管理文档、语言、出版与项目内输出路径；project inspect 只读这些配置及摘要，project configure 校验并显式应用草稿。测试、lint、构建等命令由 justfile、Makefile、项目 manifest 或 CI 管理，tao 不发现或保存候选命令。

<!-- tao:section invariants -->
## 边界

查询无副作用；歧义列候选而不按 mtime 猜测；损坏文档报告路径与原因，不静默覆盖。工具结果不授予写入、发布或客户端权限。详细 review/evidence 默认临时，计划只保留当前摘要。JSON 与文本输出表达相同事实，new/status 不返回 next_actions。status/show 遇到无关草稿损坏可返回 partial 与 documents_valid=false 并保留诊断，不把整本书有效性作为读取门槛。模型预算、token 用量报告及其预检不属于当前 CLI。

<!-- tao:section verification -->
## 验证设计

覆盖零计划、唯一/多个计划、内联/附件任务、所有任务完成但验证或审查未知、无配置只读、无流程建议输出、路径越界、格式错误与缺依赖。文档校验输出不能冒充项目测试、语义审查、实际客户端加载或独立审查。执行结果由当前计划维护。
