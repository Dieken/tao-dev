---
schema: tao.project.design/v0.1
id: "DOC_20261108_5AH1TA6VTGQQHAA8"
title: "项目级纯 skill 架构"
locale: "zh-Hans"
status: draft
created: "2026-11-08"
spec_docs: ["DOC_20261108_ZT37NM8REHBYC520"]
---

# 项目级纯 skill 架构

<!-- tao:section overview -->
## 概述

以 skill 负责开发方法，以 plan 负责工作进度，以工具负责 ID、文档和出版。规格见 {need}`DOC_20261108_ZT37NM8REHBYC520`。

<!-- tao:section architecture -->
## 架构

源码位于 skills/tao-dev/。安装器只复制 skill 到客户端原生项目 skill 目录，项目内保存必要所有权记录。辅助 CLI 提供 doctor、id、show、new、status、handoff、verify、docs 及必要项目设置；review/refine/continue/implement 是 skill 动作，由 agent 依据文档与代码执行。

<!-- tao:section contracts -->
## 接口与数据契约

核心文档使用 v0.1 的结构、ID 和引用形态，校验必要语义章节，允许章节重排。plan 通常内联任务，也可显式关联一份 tasks 附件，两者只选其一。status 返回计划、任务计数、未完成项、当前摘要及建议，不作交付认证。handoff 接受普通 Markdown，在项目忽略的 temporary/handoffs 下按 plan 的 CHG/DOC 保存一份摘要。ID 支持批量生成。

status/show 不因无关草稿诊断阻断读取；返回 partial 和 documents_valid=false。所选任务集合缺失、错绑或损坏时返回 unavailable、task_set_valid=false、task_counts=null，不把部分可解析任务冒充全部任务。handoff 的 CHG/DOC 必须是归属于所选计划的有效唯一索引定义。ID 分配扫描已有文档与退役记录中的标识即可，不以前置全书校验阻断写作。

<!-- tao:section invariants -->
## 不变量

不修改用户级配置；安装不覆盖非归属内容；目录符号链接不能逃出项目。status 不写盘、不运行检查。所有任务勾选只表示实现进度，不代表审查通过。普通 evidence/review 不自动建档或提交。保留有长期价值的已有文档与稳定 ID；删除过时契约时同步引用和导航，不为不兼容接口保留 shim。

<!-- tao:section errors -->
## 错误与恢复

文档歧义如实列候选，不按 mtime 猜测。缺交接不阻断恢复，损坏计划给出路径和诊断，不覆盖用户文件。安装替换失败时回滚替换前的目录树；已提交后的清理失败明确报告状态与残留路径，仍独立释放锁，不伪称回滚。卸载遇到用户改动拒绝破坏；只在显式调用时运行检查。

<!-- tao:section verification -->
## 验证

文档审查核对要求覆盖和所有权边界，代码审查关注路径逃逸、无状态查询、错误完成推断和客户端发现。schema、模板、解析器、引用与书籍导航保持一致。集中执行定向与完整回归，临时项目真实 CLI smoke、书籍构建；结果只在计划保留当前摘要。

