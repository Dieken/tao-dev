# tao-dev · 协作开发之道

让 AI 与人围绕可验收的结果协作开发：明确需求，选择简单方案，小步实现，用实际检查支撑交付，并留下能接手的知识。

tao-dev 包含 **agent skill、共享文档模板和确定性 CLI**。

## 核心能力

- **控制复杂度**：区分用户目标与实现建议，比较收益、代价及更简单的替代方案；按风险安排独立审查。
- **需求到交付可追踪**：用稳定 ID 关联需求、用例、决策、任务和验证记录，改名或移动时保持引用。
- **检查结果有依据**：接入项目已有测试与静态检查，识别证据过期、按条件复用结果，并汇总任务和必需审查。局部检查通过只代表其覆盖范围。
- **文档可直接使用**：提供中英文模板、格式与关系校验、本地 HTML 书籍和稳定链接；项目沿用自己的语言与目录。
- **会话可恢复**：保存目标、决定、实际状态、证据和下一步，接手时核对当前文件与检查结果。

## 安装与快速开始

需要 **Python 3.11–3.14（含 pip、venv）、Git**，以及已安装并登录的 Claude Code 或 Codex CLI。安装器会准备 tao 的全部 Python 依赖（含 HTML 出版），配置插件与 hook，最后自动执行 doctor；无需设置 TAO 环境变量。

### 从 GitHub 安装

在目标项目目录执行一条命令。以下安装到 Codex 的项目范围；换成 `--client claude` 可安装到 Claude Code：

```sh
curl -fsSL https://raw.githubusercontent.com/Dieken/tao-dev/main/install.sh | sh -s -- --client codex --scope project
```

<details>
<summary>Windows PowerShell</summary>

```powershell
& ([scriptblock]::Create((Invoke-RestMethod https://raw.githubusercontent.com/Dieken/tao-dev/main/install.ps1))) -Client codex -Scope project
```

当前 hook 需要 Git for Windows 提供的 `sh`；原生 Windows 完整验收尚未完成，也可在 WSL 中按 Linux 方式使用。

</details>

默认通过仓库的 marketplace 安装完整插件，包括 [skill](plugins/tao-dev/skills/tao-dev/SKILL.md)、CLI、模板及客户端组件。安装结束会输出版本、生效范围、插件和运行环境位置、写入的文件／目录，以及简短使用指南。

### 从本地 Git 工作目录安装

在本地 tao-dev 仓库运行，直接使用当前工作目录中的内容，包括未提交修改：

```sh
python3 tao.py install --client codex --scope project --source .
```

安装到其他项目时加 `--project /path/to/project`。Windows 将 `python3` 换成可用的 Python 命令，如 `py -3`。本地来源不依赖在线 marketplace；安装器会生成客户端所需的本地清单。

### 范围、来源与升级

| 参数 | 含义 |
|---|---|
| `--client claude` / `--client codex` | 选择客户端 |
| `--scope user` | 当前用户的所有项目 |
| `--scope project` | 指定项目；配置可以与团队共享 |
| `--scope local` | Claude：当前项目、仅自己使用；Codex：等同 project |
| `--scope repo` | Codex 的 project 别名 |
| `--source <目录或 Git URL>` | 使用指定插件／仓库来源，自动生成本地安装清单 |
| `--marketplace <目录或 GitHub 来源>` | 使用指定 marketplace；与 --source 互斥 |
| `--wheelhouse <目录>` | 只从本地 wheel 安装依赖，用于离线安装 |

**重复执行同一条安装命令即可升级**，已有且匹配的依赖环境会复用。本地工作目录的内容变化也会更新已安装副本。安装器同时提供 `tao` 命令；位置显示在安装摘要中，若其目录未在 PATH 中，可直接使用摘要中的完整路径。

```sh
tao install --client codex --scope project
tao install --client claude --scope local --source /path/to/tao-dev
```

未重新指定来源时，沿用该客户端和范围已有的安装来源。无需手工重新打包、修改客户端配置或运行 setup。离线机器需要提前准备源码、客户端、Python 与对应平台的锁定 wheel，详见 [安装管理说明](docs/engineering/installation.md)。

### 开始使用

安装成功后，在目标项目启动新的 `claude` 或 `codex` 会话：

- Claude Code：使用 `/tao-dev:tao-dev`。
- Codex：从 `/skills` 或 `$` 选择 tao-dev。
- 例如：让 tao-dev 为一个小功能制定计划，明确验收条件，再继续实现和验证。

首次接入项目时，可让 agent 建立适合该项目的 tao 配置；短文档 hook 在项目已有 `.tao/config.toml` 时提供反馈。

### 卸载

指定客户端后，安装器会发现用户级、当前及客户端已知项目中的安装，列出各份安装的范围与文件，提示选择并确认删除：

```sh
tao uninstall --client codex
tao uninstall --client claude
```

也支持已有的手工 marketplace／本地安装。共享配置只清理对应项目；其他安装仍在使用的缓存保留。无法确认归属的旧 Python 环境会保留并说明；共享 `tao` 命令保留，方便再次安装。

只查看用 `--list`；自动化删除指定一份用 `--id <列表中的安装 ID> --yes`。完整属于 tao-dev 的目录只列目录本身，不展开内部文件。

### 自举体验：用 tao-dev 为 tao-dev 开发新功能

**这个练习的开发对象是 tao-dev 本身。** 在 tao-dev 源码根目录完成上述安装后，启动客户端；可先点击阅读 [SKILL.md](plugins/tao-dev/skills/tao-dev/SKILL.md)，再输入：

> 请使用 tao-dev，为 tao-dev 自身新增 `tao docs serve` 命令制定开发计划：在本机预览生成的文档书籍，并在 Markdown 修改后重新构建和刷新页面。先检查现有实现，明确范围、验收场景和必要设计，生成并填写变更计划；本轮只规划，暂不编码。

这是一项示例新需求，当前已有 `tao docs build`，尚无 `tao docs serve`。要继续体验实现、测试和审查，可随后要求 agent 按计划继续开发。

## 支持状态

核心文档操作、配置驱动的验证与证据复用、独立审查记录导入、本地 HTML 出版已有实现。审查记录导入核对来源和输入一致性；CLI 本身不调度模型。

| 范围 | 当前依据与限制 |
|---|---|
| macOS 客户端 | Codex CLI 0.154.0、Claude Code 2.1.270 的安装、升级、回滚和卸载已在隔离环境验证；其他场景见验收记录 |
| Codex 原生 hook | 安装器使用兼容 manifest 并检查原生 skill、hook 与信任状态；公共格式仍供单独打包使用 |
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
