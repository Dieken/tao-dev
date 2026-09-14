# tao-dev · 协作开发之道

面向 AI 与人的协作开发 skill 项目，覆盖需求、交付、运行与持续改进。

当前包含需求与设计草案、skill 规程、使用方文档格式注册表和可填写模板。完整自动校验器、模板生成器、hook、出版站点和双 CLI 行为验收尚未完成。

## 阅读入口

1. [协作开发协议](docs/protocol.md)：项目目标、需求、流程、文档职责、设计取舍、验收用例和自举路线。
2. [术语与缩写](docs/glossary.md)：统一概念、ID 类型前缀及常用缩写。
3. [Markdown 文档契约](docs/document-contract.md)：解析器实现、现有文档的迁移边界及随包规范入口。
4. [文档组织与产物保存](docs/document-layout.md)：本项目组织设计与随包规则的关系。
5. [插件打包与运行环境](docs/plugin-design.md)：Agent Plugins 标准结构、平台组件映射和双 CLI 验收。
6. [tao 命令与流程接入](docs/cli-design.md)：拟议命令的输入、输出、副作用、调用时机和实施顺序。

运行材料从 [skill 入口](plugins/tao-dev/skills/tao-dev/SKILL.md) 进入，入口要求读取随包分发的 [工程规程](plugins/tao-dev/skills/tao-dev/references/engineering.md)。规程直接指导使用方项目的设计、编码、验证、评审和演进。

[文档规程](plugins/tao-dev/skills/tao-dev/references/documents.md) 定义使用方的统一格式，随包提供规格、设计、计划、任务、决策、用户说明、运维、术语、证据与交接模板，以及中英文显示资源。项目无需自定义 schema；未来 CLI 读取同一份格式注册表。

[流程操作规程](plugins/tao-dev/skills/tao-dev/references/workflow.md) 说明各阶段何时使用工具及能力缺失时如何继续。`tao` CLI 仍未实现，命令专篇是实现契约；当前不能按其中的命令示意直接运行，也不能声称自动校验已经完成。

拟议日常入口是 `tao new`、`tao verify` 和 `tao status`。中断或交接时用 `tao handoff` 保存恢复摘要。用户表达目标，agent 选择检查类型与范围；交付前的完整验证同时汇总收尾条件，不再要求额外的完成命令。

[独立判断与对抗式审查](plugins/tao-dev/skills/tao-dev/references/review.md) 约束需求取舍和各类产物评审：按风险优先跨模型或跨供应商，先独立判断，再用证据裁决，避免迎合、范围膨胀和无界讨论。当前提供规程，跨模型调度及行为效果尚未验收。

主协议目前同时承载需求与设计，二者通过条目类型和稳定 ID 区分；格式契约独立维护精确语法。暂不再创建内容重复的 spec、design 和 plan。

首批目标环境为 **Codex CLI 和 Claude Code CLI**。公共组件以 Agent Plugins 1.0.0 和 Agent Skills 为格式基线，agent、command、hook 按客户端原生扩展适配，两端分别实际验收。运行源码位于 `plugins/tao-dev/`，已有公共 manifest 和 Claude 兼容 manifest；尚未安装、发布或声明双 CLI 运行兼容。

## 开发文档与分发边界

通用规则是产品的一部分，在 `plugins/tao-dev/skills/tao-dev/` 中维护并随包分发；`docs/` 保存 tao-dev 自身的需求、实现设计、开发任务与验收依据。区分依据是内容职责，不是“文档都不发布”。

| 内容 | 权威位置 | 随 skill 分发 |
|---|---|---|
| 工程、流程、审查、文档编写与组织规则 | skill 的 references/ | 是，按任务读取 |
| 术语、诊断、本地化、出版链接规则 | skill 的 references/ | 是，按需读取 |
| 格式注册表、模板、显示资源 | skill 的 assets/ | 是，skill 与未来 CLI 共用 |
| 本项目需求、实现理由、研发任务和证据 | 项目 docs/ | 否，仅供开发维护 |

共享规则由 [文档规程](plugins/tao-dev/skills/tao-dev/references/documents.md) 导航。开发文档引用包内权威源，运行材料不反向引用开发文档；将来出版书籍复用同一源文件，不另复制一套规范。

分发内容中的 `SKILL.md`、运行参考、模板和脚本单独组织；发布采用明确的文件清单，不将整个开发仓库打包。发布包离开开发仓库后须能读到完整规则；不得依赖 `docs/` 或本地研究目录。第三方使用相同模板填写自己的内容，不接收本项目的研发条目。

开发文档维护当前目标、约束、设计理由和必要参考；对话经过、逐轮修改说明与临时检查流水不进入正文。一般修改历史由本项目的 Git 保留，仍有价值的取舍写入决策记录。

## 项目语言

tao-dev 以简体中文作为需求、设计和维护说明的权威正文；代码标识、文件名、schema 键、状态值、规则号和代码注释使用英文。`SKILL.md` 初期采用中文及必要的英文术语，运行效果通过真实案例评估。

文档日期采用记录时的本地日期，`created` 记录创建日期，无需配置项目时区。需要精确时间的执行记录使用带 UTC 偏移量或 `Z` 的 ISO 8601 时间戳，具体格式见文档契约。

这一选择只适用于 tao-dev 自身。模板和生成器须尊重使用方的项目语言；显示文字可本地化，机器结构与条目标识符不随语言变化。新文档的语言来自用户明确要求或目标项目约定，既有文档默认保留原语言。详细契约见 [随包本地化规程](plugins/tao-dev/skills/tao-dev/references/localization.md)。

## 自举方式

维护入口 [AGENTS.md](AGENTS.md) 指向本仓库内的 skill 源码，CLAUDE.md 导入同一入口；无需全局安装。新建交付文档使用随包 profile 与模板，本次实例见 [共享规则归位计划](docs/changes/20260914-001-shared-rules.md)。

现有六篇长期文档仍有内部 profile，属于待迁移范围，不能算作已通过共享格式。下一步单独规划条目拆分并保留已有 ID，再用正式解析器及独立反例集验收；完整工具、出版和双 CLI 行为验收仍未完成。自举使用同一产品规则，但不把本项目的需求与开发内容加入发布包。

本 README 是阅读导航，不纳入正文 profile 的结构校验。新增文档类型与正式工具时，再扩展 schema 和检查范围；不预建空目录或自动安装 skill。
