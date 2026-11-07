---
schema: tao.project.user-guide/v0.1
id: DOC_20260916_SKR6D957EQWVEQGK
title: 在 agent 会话中完成开发
locale: zh-Hans
status: draft
created: "2026-09-16"
updated: "2026-09-24"
---

# 在 agent 会话中完成开发

<!-- tao:section scope -->
## 适用范围

在目标项目加载 tao-dev skill，以现有文档和实际代码协作；无需插件、hook、逐阶段批准或流程注册。操作名是自然语言 skill 动作，不是 slash command 保证。安装见 [客户端接入](clients.md)。

<!-- tao:section steps -->
## 开发主线

| 输入示例 | 行为与下一步 |
|---|---|
| 使用 tao-dev，new：增加可取消的导出，并完成文档审查与实现。 | 依次写或更新 spec、design、plan；已有授权内连续推进。下一步 review doc，可选 refine。 |
| review doc：核对导出方案与任务。 | 审查目标覆盖、设计取舍、任务与验证；修正问题。下一步 implement，可选 refine。 |
| implement：执行当前计划。 | 根据唯一任务集实现，记录真实检查与限制。下一步 review code。 |
| review code：检查本次导出改动。 | 对照要求审查实现、调用方、测试及失败路径，核实和修复发现。下一步定向复核或报告当前成果。 |

选项不是审批关卡；完整授权内继续，只有真实范围冲突、重要决定或未授权操作需要询问。小改动可复用适用文档，不为齐全流程生成空文件。new 的规格、设计、计划由 agent 编排，CLI new 只生成计划骨架。

## 随时使用

- refine：修订同一权威材料和受影响任务，保持稳定 ID；下一步按影响选择文档审查、实现或代码审查。
- status：只读计划和任务，列未完成项及当前摘要；无计划时显示规划材料。下一步选目标 continue。
- continue：核对计划、唯一任务集和实际文件后恢复；不要求交接或状态库。下一步执行真正剩余工作。
- handoff：显式保存一份普通 Markdown 到 temporary/handoffs/<CHG-or-DOC>.md；不改计划、不建正式文档、不自动提交。下一步新会话 continue。

## 结果与知识

计划的任务计数只表示实现进度，全部完成不代表测试或审查通过；审查没有记录就是未知。实际结果在计划 verification 合并为当前摘要，详细 review/evidence 默认临时；长期要求、设计决定与操作知识回到原文档。需要独立长期引用的证据才显式使用 evidence profile 并进入 book。没有 finish，也不自动合并、推送、发布或清理工作区。
