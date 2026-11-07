---
schema: tao.project.design/v0.1
id: DOC_20260914_0VF190409FQCN197
title: 确定性文档与计划 CLI
locale: zh-Hans
status: draft
created: '2026-09-14'
updated: "2026-09-24"
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

`status [CHG|DOC|项目相对计划路径]`：省略目标列全部计划和未关联计划的规划材料。提供任务计数、未完成项、验证正文及推断进度 planning/pending/in_progress/tasks_complete；review 无记录为 unknown。任务可表示任何项目成果，不能从全部勾选推断已验证、已审查或已交付。

`verify [计划目标] --only docs|code|docs,code`：默认 docs,code；显式执行文档检查及项目已配置的代码检查，允许真实本地结果复用，但不提供审查导入、任务完成门槛或流程 gate。检查成功只表示实际运行范围内的结果，不代替文档语义审查。

提供 doctor、show、docs build、project inspect/configure 与正式对象 retire。入口的帮助与版本查询只用标准库；文档命令缺依赖时明确诊断，不自动准备环境。安装生命周期不属于 CLI。

<!-- tao:section invariants -->
## 边界

查询无副作用；歧义列候选而不按 mtime 猜测；损坏文档报告路径与原因，不静默覆盖。工具结果不授予写入、发布或客户端权限。详细 review/evidence 默认临时，计划只保留当前摘要。JSON 与文本输出表达相同事实，new/status 不返回 next_actions。status/show 遇到无关草稿损坏可返回 partial 与 documents_valid=false 并保留诊断，不把整本书有效性作为读取门槛。模型预算、token 用量报告及其预检不属于当前 CLI。

<!-- tao:section verification -->
## 验证设计

覆盖零计划、唯一/多个计划、内联/附件任务、所有任务完成但验证或审查未知、无配置只读、无流程建议输出、路径越界、格式错误与缺依赖。检查 docs/code 输出不能冒充语义审查、实际客户端加载或独立审查。执行结果由当前计划维护。
