# tao-dev · 协作开发之道

让 AI 与人围绕可验收的结果协作开发：明确需求，选择简单方案，小步实现，用实际检查支撑交付，并留下能接手的知识。

tao-dev 包含 **agent skill、共享文档模板和确定性 CLI**。适用于新功能、缺陷修复、重构及交接；局部小改动直接使用项目已有工具，复杂变更再补充必要的规格、设计和证据。

## 核心能力

- **控制复杂度**：区分用户目标与实现建议，比较收益、代价及更简单的替代方案；按风险安排独立审查。
- **需求到交付可追踪**：用稳定 ID 关联需求、用例、决策、任务和验证记录，改名或移动时保持引用。
- **检查结果有依据**：接入项目已有测试与静态检查，识别证据过期、按条件复用结果，并汇总任务和必需审查。局部检查通过只代表其覆盖范围。
- **文档可直接使用**：提供中英文模板、格式与关系校验、本地 HTML 书籍和稳定链接；项目沿用自己的语言与目录。
- **会话可恢复**：保存目标、决定、实际状态、证据和下一步，接手时核对当前文件与检查结果。

## 快速开始

当前提供源码试用，尚未公开发布。目标客户端是 Codex CLI 和 Claude Code CLI；已测组合与限制见下方支持状态。

### 1. 在目标项目中使用规程

取得本仓库后，在目标项目的客户端会话中指定 skill 的实际绝对路径，例如：

> 请先读取 `/绝对路径/tao-dev/plugins/tao-dev/skills/tao-dev/SKILL.md`，用 tao-dev 为当前项目的“导出取消”功能制定计划。

agent 会读取相关实现、明确范围与验收，按需创建并填写计划。你提供目标即可，无需预先准备文件名或模板。计划草稿不代表已经实现；需要继续编码时，可在同一请求中明确授权。

这条路径直接使用仓库中的规程。原生操作入口、reviewer 和 hook 需要按客户端加载插件；包格式及加载验收方法见 [插件设计](docs/engineering/plugin-design.md) 和 [客户端试验](tests/acceptance/README.md)。

### 2. 按需准备 tao 工具

只使用工程规程不需要 Python。调用 tao CLI 时，需要 **Python 3.11–3.14、venv 和 ensurepip**；插件使用者无需 uv。

agent 先调用 skill 内的 `scripts/tao.py doctor` 检查环境与能力，再在已有安装授权内执行 `setup`。依赖放在独立运行环境中；普通命令不自动下载依赖。离线准备、路径选择和故障处理见 [运行环境规程](plugins/tao-dev/skills/tao-dev/references/runtime.md)。

首次接入文档或项目检查时，agent 复用已有目录、语言和测试命令，按需建立 `.tao/config.toml`。配置示例见 [工具规程](plugins/tao-dev/skills/tao-dev/references/tools.md)；尚未接入的内容会明确报告检查范围。

### 3. 描述下一步目标

| 你可以这样说 | 操作意图 | 得到什么 |
|---|---|---|
| 用 tao-dev 为导出取消功能制定计划 | new | 已填写目标、范围、已知验收和下一步的草稿 |
| 检查这次修改是否满足交付条件 | verify | 实际检查结果、覆盖范围、阻碍和未验证项 |
| 查看这次变更的进度和证据是否过期 | status | 只读状态，不重新运行行为检查 |
| 保存当前进度，方便下次继续 | handoff | 可恢复的交接摘要及证据入口 |

以上是操作意图，不要求记忆斜杠语法。Claude 插件提供对应操作入口；Codex 通过已加载的 skill 执行。检查范围由 agent 按当前任务和项目策略选择。

## 支持状态

核心文档操作、配置驱动的验证与证据复用、独立审查记录导入、本地 HTML 出版已有实现。审查记录导入核对来源和输入一致性；CLI 本身不调度模型。

| 范围 | 当前依据与限制 |
|---|---|
| macOS 客户端 | Codex CLI 0.154.0、Claude Code 2.1.268 的限定包格式与场景有行为验收记录 |
| Codex 原生 hook | 0.154.0 需要生成 `codex-legacy` 兼容包；源码公共包可发现 skill，但该版本不发现其中的 hook |
| 其他平台与版本 | 原生 Windows 验收未完成；Python 运行环境的测试矩阵不等于客户端兼容矩阵 |
| 发布就绪 | 当前源码的完整独立审查仍待完成；已有结果不构成所有平台、版本和场景的支持承诺 |

具体受检版本、环境、结果和剩余工作以 [运行环境验收记录](docs/changes/2026-09/20260914-portable-runtime.md) 为准。HTML 构建不包含外部站点部署，当前未实现 PDF 出版。

## 参与开发

开发 tao-dev 需要 **uv、Python 3.11–3.14 和 Node.js**。Node.js 用于出版链接的回归检查。进入本仓库后：

```sh
uv sync --no-config --locked --extra publication
uv run --no-config --locked --extra publication python tests/acceptance/runtime.py --download
uv run --no-config --locked --extra publication python -m pytest
```

第二步显式下载测试所需 wheel；准备后普通回归离线运行，不调用模型。环境隔离、文档校验、手册构建、依赖导出和打包命令见 [开发指南](docs/engineering/development.md)。

本仓库通过 [AGENTS.md](AGENTS.md) 使用自身的 skill；运行材料在 `plugins/tao-dev/`，仅供维护的资料在 `docs/`。

## 深入阅读

- [开发手册](docs/index.md)：产品需求、工程设计、长期决定与变更记录。
- [工程规程](plugins/tao-dev/skills/tao-dev/references/engineering.md)：需求、设计、编码、验证和演进的判断原则。
- [文档规程](plugins/tao-dev/skills/tao-dev/references/documents.md)：模板、格式、稳定 ID 与文档组织。
- [独立判断与审查](plugins/tao-dev/skills/tao-dev/references/review.md)：审查强度、证据裁决与停止条件。
