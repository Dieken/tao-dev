# tao-dev · 协作开发之道

面向 AI 与人的协作开发 skill 项目，覆盖需求、交付、运行与持续改进。

当前包含需求与设计草案、skill 规程、文档格式注册表、可填写模板，以及可运行的文档源文件校验器和回归测试。核心 CLI 与变更骨架生成可用；短文档 hook 与 Claude 操作／审查入口已定义；本地 HTML 书籍构建可用；已支持配置驱动的代码检查、覆盖率／lint 度量及证据复用；独立审查凭据适配和完整双 CLI 行为验收尚未完成。

## 阅读入口

1. [协作开发协议](docs/product/protocol.md)：项目目标、需求、验收场景和公共来源；[流程设计](docs/engineering/protocol-design.md) 维护协作方式及架构决定，[实施计划](docs/changes/2026-09/20260914-bootstrap.md) 维护既有研发任务。
2. [术语与缩写](docs/glossary.md)：统一概念、ID 类型前缀及常用缩写。
3. [Markdown 文档契约](docs/engineering/document-contract.md)：解析器设计、文档检查范围及 skill 规范入口。
4. [文档组织与产物保存](docs/engineering/document-layout.md)：本项目文档组织的设计依据及规则入口。
5. [插件打包与运行环境](docs/engineering/plugin-design.md)：Agent Plugins 标准结构、平台组件映射和双 CLI 验收。
6. [tao 命令与流程接入](docs/engineering/cli-design.md)：拟议命令的输入、输出、副作用、调用时机和实施顺序。

运行材料从 [skill 入口](plugins/tao-dev/skills/tao-dev/SKILL.md) 进入，入口要求读取 [工程规程](plugins/tao-dev/skills/tao-dev/references/engineering.md)。规程直接指导使用方项目的设计、编码、验证、评审和演进。

[文档规程](plugins/tao-dev/skills/tao-dev/references/documents.md) 定义使用方的统一格式，skill 提供规格、设计、计划、任务、决策、用户说明、运维、术语、证据与交接模板，以及中英文显示资源。项目无需自定义 schema；CLI 读取同一份格式注册表。

[文档组织规程](plugins/tao-dev/skills/tao-dev/references/document-layout.md) 支持书、篇、单页或多页章的分层组织；navigation 模板以 MyST toctree 维护唯一阅读顺序。目录按实际内容增长，既有文件可映射；导航格式、模板和源图检查已提供，Sphinx 书籍构建和稳定入口检查已实现。

[流程操作规程](plugins/tao-dev/skills/tao-dev/references/workflow.md) 说明各阶段何时使用工具及能力缺失时如何继续。[tao CLI](plugins/tao-dev/skills/tao-dev/scripts/tao.py) 已实现 doctor、id new、show、new、status、handoff 和 verify 文档子集；配置和保障边界见 [工具规程](plugins/tao-dev/skills/tao-dev/references/tools.md)。完整 verify 在必需能力缺失时返回未完成。

开发者日常向 skill 描述目标，或使用客户端适配后的 new、verify、status、handoff 操作入口；例如“用 tao-dev 为导出取消功能制定计划”。new 接受自然语言，由 agent 提炼 slug、创建并填写计划草稿；底层 `tao new --slug <slug>` 只负责确定性生成，不是要求用户准备文件名的日常入口。客户端斜杠入口仍待双端验收。检查范围由 agent 选择，完整验证同时汇总收尾条件。

[独立判断与对抗式审查](plugins/tao-dev/skills/tao-dev/references/review.md) 约束需求取舍和各类产物评审：按风险优先跨模型或跨供应商，先独立判断，再用证据裁决，避免迎合、范围膨胀和无界讨论。当前提供规程，跨模型调度及行为效果尚未验收。

开发文档与第三方采用相同的共享 profile：协议承载需求与用例，流程设计承载 ADR，实施计划承载研发任务；专题设计引用各自权威规则，同一事实不抄写多份。

首批目标环境为 **Codex CLI 和 Claude Code CLI**。公共组件以 Agent Plugins 1.0.0 和 Agent Skills 为格式基线，agent、command、hook 按客户端原生扩展适配，两端分别实际验收。运行源码位于 `plugins/tao-dev/`，已有公共 manifest 和 Claude 兼容 manifest；尚未安装、发布或声明双 CLI 运行兼容。

## 开发文档与分发边界

是否随 skill 发布，以第三方项目使用 tao-dev 时的运行用途为准：内容会作为 prompt 被其 LLM 按需读取，或会被 tao CLI／运行组件加载、执行、渲染或用于校验，才放入分发目录。仅用于开发、测试或维护 tao-dev 自身的文档保留在顶层 `docs/`；“具有通用性”或“自举时会用到”本身不是分发理由。

| 内容 | 权威位置 | 随 skill 分发 |
|---|---|---|
| 工程、流程、审查、文档编写与组织规则 | skill 的 references/ | 是，按任务读取 |
| 术语、诊断、本地化、出版链接规则 | skill 的 references/ | 是，按需读取 |
| 格式注册表、模板、显示资源 | skill 的 assets/ | 是，skill 与 CLI 共用 |
| 本项目需求、实现理由、研发任务和证据 | 项目 docs/ | 否，仅供开发维护 |

共享规则由 [文档规程](plugins/tao-dev/skills/tao-dev/references/documents.md) 导航。开发文档引用包内权威源，运行材料不反向引用开发文档；出版书籍复用同一源文件，不另复制一套规范。

每份随 skill 发布的资源应有明确的 prompt 读取入口或运行调用方；只有 CLI 使用的资源无需读入 LLM 上下文。描述“如何实现 tao CLI”的设计文档不等于“tao CLI 运行时使用的资源”；尚未实现的调用方要标明计划用途，不能声称已经调用。混合两类内容的文件按段落职责拆分，不因其中一部分需要分发就把整份研发文档加入包。

使用方项目中的 .tao/ 仅存放 CLI 或 skill 配置；规格、计划、证据与 docs/retired/ 下的退役记录属于项目文档资产，临时报告、书籍输出与可重建缓存默认放在 tmp/tao/，可映射到项目已有生成目录。tao-dev 自身也按这个边界组织，未发生退役或不需要配置时不预建目录。

分发内容中的 `SKILL.md`、运行参考、模板和脚本单独组织；发布采用明确的文件清单，不将整个开发仓库打包。发布包离开开发仓库后须能读到完整规则；不得依赖 `docs/` 或本地研究目录。第三方使用相同模板填写自己的内容，不接收本项目的研发条目。

开发文档维护当前目标、约束、设计理由和必要参考；对话经过、逐轮修改说明与临时检查流水不进入正文。一般修改历史由本项目的 Git 保留，仍有价值的取舍写入决策记录。

## 项目语言

tao-dev 以简体中文作为需求、设计和维护说明的权威正文；代码标识、文件名、schema 键、状态值、规则号和代码注释使用英文。`SKILL.md` 初期采用中文及必要的英文术语，运行效果通过真实案例评估。

文档日期采用记录时的本地日期，`created` 记录创建日期，无需配置项目时区。需要精确时间的执行记录使用带 UTC 偏移量或 `Z` 的 ISO 8601 时间戳，具体格式见文档契约。

这一选择只适用于 tao-dev 自身。模板和生成器须尊重使用方的项目语言；显示文字可本地化，机器结构与条目标识符不随语言变化。新文档的语言来自用户明确要求或目标项目约定，既有文档默认保留原语言。详细契约见 [本地化规程](plugins/tao-dev/skills/tao-dev/references/localization.md)。

## 自举方式

维护入口 [AGENTS.md](AGENTS.md) 指向本仓库内的 skill 源码，CLAUDE.md 导入同一入口；无需全局安装。交付文档使用 skill 提供的 profile 与模板，变更计划按 `docs/changes/<yyyy-mm>/<yyyymmdd>-<slug>.md` 保存，简短验证结论直接写入计划，独立摘要与附件按需放在同月的同名目录内；原始日志默认不纳入 VCS。

自举表示使用本仓库的 skill、规则与模板开发 tao-dev，校验范围以 [文档契约](docs/engineering/document-contract.md) 为准；本项目形成的需求、设计、计划、测试报告和维护说明仍留在顶层 docs/，不因自举而成为分发内容。

本 README 是阅读导航，不纳入正文 profile 的结构校验。新增文档类型与正式工具时，再扩展 schema 和检查范围；不预建空目录或自动安装 skill。

## 运行文档校验与回归测试

需要 Python 3.11 或以上版本。在项目自己的临时虚拟环境安装依赖：

```sh
python3 -m venv tmp/tao/venv
tmp/tao/venv/bin/python -m pip install -r requirements-dev.txt
tmp/tao/venv/bin/python -m pytest
```

[源文件校验入口](plugins/tao-dev/skills/tao-dev/scripts/validate_documents.py) 随 skill 分发，读取同包格式注册表；[测试](tests/) 留在开发仓库。校验器显式接收项目目录和纳入管理的文件，支持 `--format json`，不执行项目代码或写入文档。第三方只需安装脚本目录中的 requirements.txt，无需 pytest。

```sh
tmp/tao/venv/bin/python plugins/tao-dev/skills/tao-dev/scripts/tao.py doctor --format json
tmp/tao/venv/bin/python plugins/tao-dev/skills/tao-dev/scripts/tao.py verify --only docs --format json
```

单独检查一个文件可能报告范围外的引用；跨文档关系需要一起传入相关文件。仓库回归测试会纳入 docs/ 下的全部 Markdown。校验器支持注册表中的 11 种共享 profile，覆盖 Markdown 结构、元数据、正式条目、任务、引用、退役及导航关系。指定 `--book-root <导航文件>` 才检查整本书的可达性；检查历史删除需要调用方提供基线。源文件锚点可解析不代表生成 HTML 或复制链接已经验收，语义、代码行为和费用也不由格式检查判定。

## 构建开发手册

开发依赖已包含可选出版组件。运行以下命令，按输出的 index 打开 HTML；也可用本地 HTTP 服务器预览 tmp/tao/book/。构建不会发布外部站点，生成文件默认不纳入 VCS。

```sh
tmp/tao/venv/bin/python plugins/tao-dev/skills/tao-dev/scripts/tao.py docs build --format json
```

## 运行项目检查

本项目的 .tao/config.toml 配置实际 Python 回归、子进程分支覆盖率与 Ruff 错误检查；运行 `tao.py verify --only code` 可执行或复用它们，`tao.py status` 只读比较证据。度量结果、原始日志和缓存都在 tmp/tao/；配置与规则见 [验证规程](plugins/tao-dev/skills/tao-dev/references/verification.md)。覆盖率是观察值，当前没有随意设定一个通过百分比。

完整 `tao.py verify <CHG-ID>` 仍会报告尚未完成的任务及必需审查适配缺口，不能把局部检查通过当成交付。实际客户端和恢复试验需显式运行，方法见 [试验说明](tests/acceptance/README.md)，普通 pytest 不调用模型。
