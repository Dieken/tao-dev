# tao-dev · 协作开发之道

让 AI 与人围绕可验收的结果协作开发：明确需求，选择简单方案，小步实现，用实际检查支撑交付，并留下能接手的知识。

tao-dev 包含 **agent skill、共享文档模板和确定性 CLI**。适用于新功能、缺陷修复、重构及交接；局部小改动直接使用项目已有工具，复杂变更再补充必要的规格、设计和证据。

## 核心能力

- **控制复杂度**：区分用户目标与实现建议，比较收益、代价及更简单的替代方案；按风险安排独立审查。
- **需求到交付可追踪**：用稳定 ID 关联需求、用例、决策、任务和验证记录，改名或移动时保持引用。
- **检查结果有依据**：接入项目已有测试与静态检查，识别证据过期、按条件复用结果，并汇总任务和必需审查。局部检查通过只代表其覆盖范围。
- **文档可直接使用**：提供中英文模板、格式与关系校验、本地 HTML 书籍和稳定链接；项目沿用自己的语言与目录。
- **会话可恢复**：保存目标、决定、实际状态、证据和下一步，接手时核对当前文件与检查结果。

## 安装与快速开始

项目源码已公开托管于 [GitHub](https://github.com/Dieken/tao-dev)。下面安装完整的 **tao-dev skill 目录**，包含 [SKILL.md](plugins/tao-dev/skills/tao-dev/SKILL.md)、参考、模板和 CLI 脚本；无需先安装完整插件。原生插件的独立操作入口、reviewer 和 hook 另见 [插件设计](docs/engineering/plugin-design.md)。

### 1. 准备客户端、Python 和 pip

先安装并登录你要使用的 [Claude Code CLI](https://code.claude.com/docs/en/setup) 或 [Codex CLI](https://developers.openai.com/codex/cli/)，并准备 [Git](https://git-scm.com/downloads)。客户端本身能启动，不代表 tao 的 Python 环境已准备好。

**机器上没有 Python 和 pip 时，先按系统完成以下步骤。** tao 支持 Python 3.11–3.14；新安装可选 Python 3.13，插件使用者无需 uv。

| 系统 | 安装方法 |
|---|---|
| macOS | 从 [Python 官网](https://www.python.org/downloads/macos/) 下载 Python 3.13 的 `.pkg` 安装器，按默认选项安装 Python 和 pip；随后运行 `/Applications/Python 3.13/Install Certificates.command`，完成 HTTPS 证书配置。见 [官方安装说明](https://docs.python.org/3.13/using/mac.html)。 |
| Windows | 从 [Python 官网](https://www.python.org/downloads/windows/) 下载 Python 3.13 的完整安装器，勾选 **Add python.exe to PATH**，保留 pip 和 Python Launcher，选择为当前用户安装。使用完整安装器，不选缺少 pip 的 embeddable ZIP。见 [官方安装说明](https://docs.python.org/3.13/using/windows.html)。 |
| Ubuntu 24.04／Debian 12 及其后续受支持版本 | 执行下方 apt 命令。其他 Linux 发行版用其包管理器安装 Python、pip 和 venv，并确认 Python 版本在 3.11–3.14 范围内。 |

```sh
sudo apt-get update
sudo apt-get install python3 python3-venv python3-pip git
```

安装后重新打开终端，确认版本及标准库模块可用：

```sh
# macOS / Linux
python3 --version
python3 -m pip --version
python3 -c "import venv, ensurepip"
```

```powershell
# Windows PowerShell
py -3.13 --version
py -3.13 -m pip --version
py -3.13 -c "import venv, ensurepip"
```

后续 `tao setup` 会在独立虚拟环境中准备自己的 pip 和锁定依赖，无需向系统 Python 执行 `pip install tao-dev`。

### 2. 选择客户端和安装范围

每个客户端选择一种范围；**项目本地安装不会关闭已经存在的用户级副本**。只想在某个项目启用时，使用项目目录，并先将同名用户级副本移出 skill 搜索目录。

| 客户端 | 用户级：当前用户的所有项目 | 项目本地：当前项目及其子目录 |
|---|---|---|
| Claude Code CLI | `~/.claude/skills/tao-dev/` | `<项目根>/.claude/skills/tao-dev/` |
| Codex CLI | `~/.agents/skills/tao-dev/` | `<项目根>/.agents/skills/tao-dev/` |

以下路径和调用方式依据 [Claude Code skills](https://code.claude.com/docs/en/skills#choose-where-skills-load) 与 [Codex skills](https://developers.openai.com/codex/skills/) 官方说明。复制整个目录，不能只复制 SKILL.md。

#### macOS / Linux

取得源码并记住位置；下文在同一终端执行：

```sh
git clone https://github.com/Dieken/tao-dev.git
cd tao-dev
TAO_SOURCE_DIR="$PWD"
```

此时项目根就是 tao-dev，适合下方自举体验。安装到其他项目时，先 `cd` 到那个项目根目录，保留 TAO_SOURCE_DIR。**从下表选一条赋值命令执行**：

| 安装方式 | 命令 |
|---|---|
| Claude Code 用户级 | `TAO_SKILL_DIR="$HOME/.claude/skills/tao-dev"` |
| Claude Code 项目本地 | `TAO_SKILL_DIR="$PWD/.claude/skills/tao-dev"` |
| Codex 用户级 | `TAO_SKILL_DIR="$HOME/.agents/skills/tao-dev"` |
| Codex 项目本地 | `TAO_SKILL_DIR="$PWD/.agents/skills/tao-dev"` |

再执行首次安装；已有同名目录时停止，先核对已有版本：

```sh
(
  set -eu
  : "${TAO_SKILL_DIR:?请先从上表选择安装目录}"
  test ! -e "$TAO_SKILL_DIR" || { echo "安装目录已存在：$TAO_SKILL_DIR"; exit 1; }
  mkdir -p "$TAO_SKILL_DIR"
  cp -R "$TAO_SOURCE_DIR/plugins/tao-dev/skills/tao-dev/." "$TAO_SKILL_DIR/"
)
```

<details>
<summary>Windows PowerShell 安装步骤</summary>

```powershell
git clone https://github.com/Dieken/tao-dev.git
Set-Location tao-dev
$TaoSourceDir = (Get-Location).Path
```

要安装到其他项目，先 `Set-Location` 到其根目录，保留 TaoSourceDir。从下表选一条命令执行：

| 安装方式 | 命令 |
|---|---|
| Claude Code 用户级 | `$TaoSkillDir = Join-Path $env:USERPROFILE '.claude/skills/tao-dev'` |
| Claude Code 项目本地 | `$TaoSkillDir = Join-Path (Get-Location).Path '.claude/skills/tao-dev'` |
| Codex 用户级 | `$TaoSkillDir = Join-Path $env:USERPROFILE '.agents/skills/tao-dev'` |
| Codex 项目本地 | `$TaoSkillDir = Join-Path (Get-Location).Path '.agents/skills/tao-dev'` |

```powershell
if (-not $TaoSkillDir) { throw '请先从上表选择安装目录' }
if (Test-Path $TaoSkillDir) { throw "安装目录已存在：$TaoSkillDir" }
New-Item -ItemType Directory -Path $TaoSkillDir -ErrorAction Stop | Out-Null
Copy-Item -Path "$TaoSourceDir/plugins/tao-dev/skills/tao-dev/*" -Destination $TaoSkillDir -Recurse -ErrorAction Stop
```

后面的 Windows 命令继续在同一 PowerShell 中执行。原生 Windows 客户端的整体行为验收仍未完成，支持范围见下文。

</details>

项目副本可纳入版本控制供团队共享；只在本机使用时，将对应的 `/.claude/skills/tao-dev/` 或 `/.agents/skills/tao-dev/` 加入该项目的 `.git/info/exclude`。

#### 从 GitHub 直接安装（可选）

**Codex CLI 支持通过内置 `$skill-installer` 从其他仓库下载 skill。** 完成第 1 节准备后，可在 Codex 会话中使用以下任一提示，替代上面的克隆和复制步骤。来源是 [GitHub 上的完整 skill 目录](https://github.com/Dieken/tao-dev/tree/main/plugins/tao-dev/skills/tao-dev)，不是单个 SKILL.md。见 [Codex 安装说明](https://developers.openai.com/codex/skills/#install-curated-skills-for-local-use)。

用户级：

> $skill-installer 请先将 Dieken/tao-dev 的 main 分支解析为完整 commit SHA，再按该 SHA 安装 plugins/tao-dev/skills/tao-dev，目标为我的用户主目录下 .agents/skills/tao-dev。请下载完整目录并报告来源 SHA；已有同名目录时先报告，不覆盖。

项目本地（在目标项目根启动 Codex）：

> $skill-installer 请先将 Dieken/tao-dev 的 main 分支解析为完整 commit SHA，再按该 SHA 安装 plugins/tao-dev/skills/tao-dev，目标为当前项目根目录下 .agents/skills/tao-dev。仅安装到此项目，不写入用户级 skill 目录。请下载完整目录并报告来源 SHA；已有同名目录时先报告，不覆盖。

安装器的默认目录可能是 `~/.codex/skills`，所以上面明确指定与本指南一致的目标。安装完成后，在终端按前表设置 TAO_SKILL_DIR（PowerShell 为 TaoSkillDir），指向安装器报告的实际路径，再继续第 3、4 节；无需重复复制。自举练习仍需克隆 tao-dev 源码。若客户端没有提供 `$skill-installer`，使用前面的手动安装步骤。

**Claude Code CLI 的官方 GitHub 安装路径是插件 marketplace。** 它要求仓库提供 `.claude-plugin/marketplace.json`，然后添加 marketplace、安装其中的插件；这与安装一个 skill 目录不同。当前 tao-dev 仓库没有该清单，不能直接使用 `/plugin marketplace add Dieken/tao-dev`。Claude Code 用户沿用上面的克隆、复制方式。见 [Claude Code GitHub 安装说明](https://code.claude.com/docs/en/discover-plugins#add-from-github)。

#### 安装版本与更新

当前没有发布 tag，`main` 指向持续变化的开发内容；这不影响从 GitHub 安装。需要复现同一版本时，指定**完整 commit SHA**：手动安装在源码目录先执行 `git checkout --detach <完整 commit SHA>` 再复制；使用 `$skill-installer` 时把提示中的 `main` 换成该 SHA。安装时记录来源仓库和 SHA，不能只用 CLI 报告的版本号区分不同开发提交。

安装副本不会随源码仓库的 `git pull` 自动更新。更新时先选定来源提交，将已有副本移出 skill 搜索目录，再安装完整的新副本并重新运行 setup、doctor。发布 tag 与版本字段的维护方式见 [开发指南](docs/engineering/development.md)。

### 3. 准备 tao 的运行环境

skill 的可见范围由上面的安装位置决定。运行依赖默认保存在用户数据目录，可供多个项目复用。若希望运行数据也只留在当前项目，先选择下面的项目本地设置；这与 skill 是否启用是两件事。

```sh
# 仅项目本地运行需要；用户级共享运行环境可跳过
export TAO_RUNTIME_DIR="$PWD/tmp/tao/runtime"
```

然后使用已经安装的 Python 准备核心依赖：

```sh
export TAO_PYTHON="$(python3 -c 'import sys; print(sys.executable)')"
"$TAO_PYTHON" "$TAO_SKILL_DIR/scripts/tao.py" doctor --project "$PWD" --format json
"$TAO_PYTHON" "$TAO_SKILL_DIR/scripts/tao.py" setup
"$TAO_PYTHON" "$TAO_SKILL_DIR/scripts/tao.py" doctor --project "$PWD" --format json
```

首次 doctor 报告环境未准备是预期结果；显式 setup 会联网下载锁定依赖，成功后 doctor 应报告核心环境 ready。需要构建 HTML 时再执行同一入口的 `setup --publication`。离线准备使用 `setup --wheelhouse <目录>`，详见 [运行环境规程](plugins/tao-dev/skills/tao-dev/references/runtime.md)。

<details>
<summary>Windows PowerShell 运行环境准备</summary>

```powershell
# 仅项目本地运行需要；用户级共享运行环境可跳过
$env:TAO_RUNTIME_DIR = Join-Path (Get-Location).Path 'tmp/tao/runtime'
```

```powershell
$env:TAO_PYTHON = py -3.13 -c "import sys; print(sys.executable)"
& $env:TAO_PYTHON "$TaoSkillDir/scripts/tao.py" doctor --project (Get-Location).Path --format json
& $env:TAO_PYTHON "$TaoSkillDir/scripts/tao.py" setup
& $env:TAO_PYTHON "$TaoSkillDir/scripts/tao.py" doctor --project (Get-Location).Path --format json
```

这里直接调用 Python，不需要修改 PowerShell 脚本执行策略。

</details>

从同一终端启动客户端，使其继承 TAO_PYTHON 和可选的 TAO_RUNTIME_DIR。以后新开终端时重新设置这些变量；自定义 Python 路径不要写入团队共享配置。项目本地运行时，将 `tmp/tao/` 加入项目忽略规则，tao-dev 仓库已经配置。

### 4. 在客户端启用并确认

**Claude Code CLI：** 在目标项目根运行 `claude`，输入 `/skills`，确认列表中出现 tao-dev；若被关闭，将状态设为 on。输入 `/tao-dev` 可显式调用，也可在任务中写“使用 tao-dev”。用户级副本默认对各项目可见，项目副本只在该项目范围内加载；无需执行插件安装命令。见 [启用状态说明](https://code.claude.com/docs/en/skills#override-skill-visibility-from-settings)。

**Codex CLI：** 在目标项目根运行 `codex`，输入 `/skills` 或键入 `$` 选择 tao-dev，用 `$tao-dev` 显式调用。新复制的 skill 默认可发现；如果此前通过 `~/.codex/config.toml` 的 `[[skills.config]]` 禁用过该路径，将对应 `enabled` 改为 `true` 并重启。首次打开项目时按客户端提示确认信任。见 [Codex 启用说明](https://developers.openai.com/codex/skills/#enable-or-disable-local-codex-skills)。

未发现 skill 时重启客户端，检查其搜索目录中是否直接包含 `tao-dev/SKILL.md`，以及当前目录是否属于目标项目。只做项目本地安装时，在另一个无 tao-dev 安装的项目中启动新会话，列表中应没有 tao-dev。

### 5. 自举体验：用 tao-dev 为 tao-dev 开发新功能

**这个练习的开发对象就是 tao-dev 本身。** 沿用第 2 节留在 tao-dev 仓库根目录的安装路径，按上节启动客户端并调用 skill。若此前安装到了其他项目，先回到 tao-dev 根目录：项目级 skill 需按第 2 节在此重新安装；若设置了项目本地运行目录，也需按第 3 节重新设置 TAO_RUNTIME_DIR 并准备环境。可以先点击阅读 [SKILL.md](plugins/tao-dev/skills/tao-dev/SKILL.md)，再输入：

> 请使用 tao-dev，为 tao-dev 自身新增 `tao docs serve` 命令制定开发计划：在本机预览生成的文档书籍，并在 Markdown 修改后重新构建和刷新页面。先检查现有实现，明确范围、验收场景和必要设计，生成并填写变更计划；本轮只规划，暂不编码。

这是一项示例新需求，当前 CLI 只有 `tao docs build`，尚无 `tao docs serve`。agent 应交付填写好的计划和未决事项；你无需预先准备文件名或模板。要继续体验实现、测试和审查，可随后要求它按计划继续开发。维护 tao-dev 的开发依赖与检查命令见 [开发指南](docs/engineering/development.md)。

| 后续目标 | 操作意图 | 得到什么 |
|---|---|---|
| 为 tao-dev 的文档预览命令制定计划 | new | 已填写目标、范围、已知验收和下一步的草稿 |
| 检查这次修改是否满足交付条件 | verify | 实际检查结果、覆盖范围、阻碍和未验证项 |
| 查看这次变更的进度和证据是否过期 | status | 只读状态，不重新运行行为检查 |
| 保存当前进度，方便下次继续 | handoff | 可恢复的交接摘要及证据入口 |

这些是操作意图，由 skill 选择实际工具和参数，不是要求两个客户端使用相同的斜杠命令。首次在其他项目接入时，agent 复用其目录、语言和检查命令，按需建立 `.tao/config.toml`；示例见 [工具规程](plugins/tao-dev/skills/tao-dev/references/tools.md)。

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
