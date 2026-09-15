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

hook 直接使用安装器选定的 Python，不要求 Git for Windows 提供 `sh`。原生 Windows 完整验收尚未完成，也可在 WSL 中按 Linux 方式使用。

</details>

引导脚本从 GitHub 取得 tao-dev，再由 `tao install` 安装完整插件，包括 [skill](plugins/tao-dev/skills/tao-dev/SKILL.md)、CLI、模板及客户端组件。安装结束会输出版本、生效范围、插件和运行环境位置、写入的文件／目录，以及简短使用指南。

### 从本地 Git 工作目录安装

在本地 tao-dev 仓库运行，直接使用当前工作目录中的内容，包括未提交修改：

```sh
python3 plugins/tao-dev/skills/tao-dev/scripts/tao.py install \
  --client codex --scope project --source .
```

安装到其他项目时加 `--project /path/to/project`。Windows 将 `python3` 换成可用的 Python 命令，如 `py -3`。本地来源不访问 GitHub；`tao install` 会生成并注册客户端所需的本地清单。

### `tao install` 与 `tao setup`

`tao install` 是面向使用者的完整安装和升级入口。它选择客户端与生效范围，取得并注册插件，创建独立 Python 虚拟环境，安装核心与出版依赖，将 hook 绑定到已验证的 Python 和插件路径，最后运行 doctor。安装成功后可以直接开始使用。

`tao setup` 是低层的运行环境准备命令，供维护、修复或预置依赖使用。它一次创建或复用彼此隔离的核心与出版环境，但不安装或启用客户端插件，不选择 scope，不写 hook 绑定，也不代替 `tao install`。正常安装时无需手工运行 setup。

### `tao` 命令在哪里

安装器会创建一个独立的 `tao` 启动器，默认位置是：

- macOS／Linux：`~/.local/bin/tao`
- Windows：`%USERPROFILE%\.local\bin\tao.cmd`

安装器会在安装摘要中显示实际绝对路径，但不会修改 shell 的 PATH。`~/.local/bin` 已在 PATH 中时可以直接使用 `tao`；否则使用摘要中的路径或默认完整路径。例如：

```sh
$HOME/.local/bin/tao --project "$PWD" doctor
```

```powershell
& "$HOME\.local\bin\tao.cmd" --project "$PWD" doctor
```

README 后面的 `tao` 表示这个安装器生成的启动器，不是 `python3 /path/to/tao.py` 的简写。只有从 tao-dev 本地源码目录执行首次安装时，才需要直接运行 `plugins/tao-dev/skills/tao-dev/scripts/tao.py`。

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
$HOME/.local/bin/tao install --client codex --scope project
$HOME/.local/bin/tao install --client claude --scope local --source /path/to/tao-dev
```

未重新指定来源时，沿用该客户端和范围已有的安装来源。无需手工重新打包、修改客户端配置或运行 setup。离线机器需要提前准备源码、客户端、Python 与对应平台的锁定 wheel，详见 [安装管理说明](docs/engineering/installation.md)。

### 在 agent 中调用 tao-dev

安装成功后，在目标项目启动新的 `claude` 或 `codex` 会话。skill 调用和请求内容要放在**同一条消息**中；不要先单独发送 `/tao-dev:tao-dev` 或 `$tao-dev`，再发送任务。

粘贴到 Claude Code：

```text
/tao-dev:tao-dev 请检查当前项目的语言、目录、测试、静态检查和文档构建方式。若项目还没有 .tao/config.toml，请创建一份只接入现有检查的最小配置；若已经存在，请核对而不要重置。然后使用安装好的 tao 启动器运行 doctor，并说明配置了哪些检查、哪些内容仍需人工决定。本轮只完成项目接入，不创建功能计划。
```

粘贴到 Codex：

```text
$tao-dev 请检查当前项目的语言、目录、测试、静态检查和文档构建方式。若项目还没有 .tao/config.toml，请创建一份只接入现有检查的最小配置；若已经存在，请核对而不要重置。然后使用安装好的 tao 启动器运行 doctor，并说明配置了哪些检查、哪些内容仍需人工决定。本轮只完成项目接入，不创建功能计划。
```

这条消息让 agent 创建或核对 `.tao/config.toml`；目前没有单独的 `tao init` 命令。项目存在这份配置后，随插件安装的短文档 hook 会在 agent 写入 Markdown 时自动检查并反馈，无需手工运行 hook。

### 完整示例：用 tao-dev 为 tao-dev 开发一个 feature

下面以新增 `tao docs serve` 为例，演示一次完整开发周期。开发对象是 tao-dev 自身；当前已有 `tao docs build`，尚无 `tao docs serve`。在 tao-dev 源码根目录完成安装并执行上面的首次接入后，按顺序操作。

#### 1. 创建变更文档骨架（终端，只执行一次）

macOS／Linux：

```sh
$HOME/.local/bin/tao --project "$PWD" new --slug docs-serve --locale zh-Hans
```

Windows PowerShell：

```powershell
& "$HOME\.local\bin\tao.cmd" --project "$PWD" new --slug docs-serve --locale zh-Hans
```

命令会输出新建的变更文档路径和稳定 ID。若同名变更已经存在，不要重复创建，让 agent 继续使用已有文档。

#### 2. 制定计划（发给 agent 的一条新消息）

粘贴到 Claude Code：

```text
/tao-dev:tao-dev 请为刚创建的 docs-serve 变更制定计划。先检查 tao docs build、运行环境和 Sphinx 出版实现，再填写现有变更文档。目标是增加 tao docs serve：先构建本地 HTML book，再启动仅监听本机的预览服务；受管理 Markdown 变化后重新构建；输出访问 URL 和构建目录；Ctrl+C 后干净退出。验收必须覆盖初次构建、修改后重建、构建失败、端口占用和进程退出，不依赖真实浏览器或外部网络。本轮只完善需求、设计、任务和验证方案，不修改实现代码。
```

粘贴到 Codex：

```text
$tao-dev 请为刚创建的 docs-serve 变更制定计划。先检查 tao docs build、运行环境和 Sphinx 出版实现，再填写现有变更文档。目标是增加 tao docs serve：先构建本地 HTML book，再启动仅监听本机的预览服务；受管理 Markdown 变化后重新构建；输出访问 URL 和构建目录；Ctrl+C 后干净退出。验收必须覆盖初次构建、修改后重建、构建失败、端口占用和进程退出，不依赖真实浏览器或外部网络。本轮只完善需求、设计、任务和验证方案，不修改实现代码。
```

#### 3. 实现计划（计划确认后再发一条消息）

粘贴到 Claude Code：

```text
/tao-dev:tao-dev 请按 docs-serve 变更文档中已经确认的计划开始实现。逐项完成任务，添加能验证行为的测试，并使用项目配置中的检查命令。只有实际检查通过后才能更新对应任务和证据；若实现需要改变已确认范围，先停下来说明原因。
```

粘贴到 Codex：

```text
$tao-dev 请按 docs-serve 变更文档中已经确认的计划开始实现。逐项完成任务，添加能验证行为的测试，并使用项目配置中的检查命令。只有实际检查通过后才能更新对应任务和证据；若实现需要改变已确认范围，先停下来说明原因。
```

#### 4. 查看状态并运行确定性检查（终端）

以下命令使用 tao CLI，不会调用模型：

```sh
$HOME/.local/bin/tao --project "$PWD" status
$HOME/.local/bin/tao --project "$PWD" verify --only code
$HOME/.local/bin/tao --project "$PWD" verify --only docs
$HOME/.local/bin/tao --project "$PWD" docs build
```

Windows PowerShell：

```powershell
& "$HOME\.local\bin\tao.cmd" --project "$PWD" status
& "$HOME\.local\bin\tao.cmd" --project "$PWD" verify --only code
& "$HOME\.local\bin\tao.cmd" --project "$PWD" verify --only docs
& "$HOME\.local\bin\tao.cmd" --project "$PWD" docs build
```

`tao docs build` 使用安装时准备的 publication venv 运行 Sphinx，并在输出中给出 book 的 HTML 入口，默认位于 `tmp/tao/book/`。实现 `tao docs serve` 后，可再直接验证新命令；浏览完成后按 Ctrl+C：

```sh
$HOME/.local/bin/tao --project "$PWD" docs serve
```

#### 5. 核对交付（检查通过后发给 agent 的一条新消息）

粘贴到 Claude Code：

```text
/tao-dev:tao-dev 请核对 docs-serve 变更的实现、任务状态、验证输出和文档。只根据当前文件和实际检查结果更新完成状态与证据，指出尚未覆盖的平台或场景，并生成一份下一位开发者可以直接接手的简短交接摘要。不要把未运行的检查写成通过。
```

粘贴到 Codex：

```text
$tao-dev 请核对 docs-serve 变更的实现、任务状态、验证输出和文档。只根据当前文件和实际检查结果更新完成状态与证据，指出尚未覆盖的平台或场景，并生成一份下一位开发者可以直接接手的简短交接摘要。不要把未运行的检查写成通过。
```

可先点击阅读 [SKILL.md](plugins/tao-dev/skills/tao-dev/SKILL.md)，了解上述消息触发的协作规则。skill 负责判断、规划和推进；`tao` CLI 负责创建文档、检查状态、执行确定性验证和构建 Sphinx book。

### 卸载

指定客户端后，安装器会发现用户级、当前及客户端已知项目中的安装，列出各份安装的范围与文件，提示选择并确认删除：

```sh
$HOME/.local/bin/tao uninstall --client codex
$HOME/.local/bin/tao uninstall --client claude
```

共享配置只清理对应项目；其他安装仍在使用的缓存保留。无法确认归属的旧 Python 环境会保留并说明；共享 `tao` 命令保留，方便再次安装。

只查看用 `--list`；自动化删除指定一份用 `--id <列表中的安装 ID> --yes`。完整属于 tao-dev 的目录只列目录本身，不展开内部文件。

## 支持状态

核心文档操作、配置驱动的验证与证据复用、独立审查记录导入、本地 HTML 出版已有实现。审查记录导入核对来源和输入一致性；CLI 本身不调度模型。

| 范围 | 当前依据与限制 |
|---|---|
| macOS 客户端 | Codex CLI 0.154.0、Claude Code 2.1.270 的安装、升级、回滚和卸载已在隔离环境验证；其他场景见验收记录 |
| Codex 原生 hook | 安装器使用兼容 manifest，并检查 skill、hook 与信任状态 |
| 其他平台与版本 | 原生 Windows 验收未完成；Python 运行环境的测试矩阵不等于客户端兼容矩阵 |
| 发布就绪 | 当前源码的完整独立审查仍待完成；已有结果不构成所有平台、版本和场景的支持承诺 |

具体受检版本、环境、结果和剩余工作以 [运行环境验收记录](docs/plans/2026-09/20260914-portable-runtime.md) 为准。HTML 构建不包含外部站点部署，当前未实现 PDF 出版。

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
