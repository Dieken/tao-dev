---
schema: tao.project.evidence/v0.1
id: "DOC_20260920_HE0A54RDHB23AHT1"
title: "形状加固复核裁决"
locale: "zh-Hans"
status: draft
created: "2026-09-20"
evidence: "EVD_20260920_HC5ECNN93CVTMGJN"
change: "CHG_20260920_Y0WCT88THT8JXXS2"
recorded_at: "2026-09-20T19:27:00+08:00"
result: "passed"
coverage: "partial"
---

# 形状加固复核裁决

<!-- tao:section scope -->
## 目标与边界

对本批次第 1 轮的 1 条发现裁决。受检对象与范围同来源报告。

本裁决的 result 为 passed：本轮登记为 passed，无阻断级发现，上一批次遗留的阻断修复经复核未再发现缺陷。这不扩大覆盖范围——`project.py`、`workflows.py` 等仍不在受检集合内。

**审查执行时间与依据:** 同来源报告，2026-09-20 19:05:03 至 19:06:52，实测 109.136 秒。本裁决形成于同日 19:27。

<!-- tao:section inputs -->
## 输入与环境

<!-- tao:field fingerprint -->
**受检输入引用:** Git 树对象为提交 `e730d6d3` 的树，输入摘要 `558c3850ccb4136d…`。

<!-- tao:field environment -->
**环境:** 主审为本事项作者 agent，不具备独立性；其自身核实在检查记录中单独列出。

| 报告 | 关注点 | 审查者、模型与供应商 | 调用方式与强度 | 独立性 | 轮次 |
|---|---|---|---|---|---|
| [复核报告](01-followup-claude.md) | 形状加固与措辞订正 | `claude-sonnet-5`，firstParty（由客户端事件观察） | `review_claude.py` 受限子进程，无工具、`--effort low`、`--max-turns 3` | 独立上下文，同供应商；与前四轮均为不同会话 | 新批次第 1 轮，上限 2 轮 |

<!-- tao:section checks -->
## 检查记录

<!-- tao:field command -->
**命令或观察步骤:** 见来源报告的检查记录，主审的可达性核实与完整交付判定均记录在那里，本处不重复。

<!-- tao:field expected -->
**预期:** F1 若可达则为缺陷，若不可达则为加固建议。

<!-- tao:field observed -->
**实际观察:** 不可达。两个调用点均校验 `change` 属于受管理索引且以 `CHG_` 开头，注册表 ID 模式的字符集不含路径分隔符。

<!-- tao:field reports -->
**报告:** 见上表链接。

<!-- tao:section findings -->
## 发现与限制

<!-- tao:field limits -->
**限制:** 本裁决只处置本批次记载的编号发现。上一批次的两条发现由其自身裁决处置，不在此重复。

| 来源发现 | 处置与范围 | 依据与理由 | 剩余工作或复查条件 |
|---|---|---|---|
| [F1](01-followup-claude.md) `path_for()` 的安全性只由注释承担 | 不采用为缺陷，采用为后续加固建议 | 审查者对模块内的观察成立且已实测复现：`contained()` 只挡逃出项目根，挡不住逃出 reviews 目录。但当前不可达——`review` 与 `status` 两个调用点都先校验 `change` 属于受管理索引且以 `CHG_` 开头，而 ID 模式的字符集不含 `/` 与 `.`。不在本次修复的理由是成本：该函数本次未改动，修改它会再次移动审查绑定并需要另开一轮复核，用一整轮审查换一个不可达的加固不相称 | 建议后续事项在 `path_for()` 内直接按 CHG ID 模式校验，使安全性不依赖注释而依赖代码。本次不做，如实记录 |

### 未解决事项

无阻断。F1 作为后续加固建议保留，不构成本次交付阻断。

**对下一步的影响:** 上一批次遗留的阻断已修复并经复核。本裁决不代表交付授权；发布与合入仍由用户判断。

<!-- tao:section retention -->
## 证据保存

<!-- tao:field retention -->
**保存位置与期限:** 随事项长期保留，与来源报告同批。
