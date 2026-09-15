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

下面安装完整的 **tao-dev 插件及运行依赖**：包含 [SKILL.md](plugins/tao-dev/skills/tao-dev/SKILL.md)、工程规程、模板、CLI、HTML 出版、客户端操作与审查入口，以及自动短文档检查 hook。两种客户端使用各自支持的组件格式，安装完成后逐项确认生效。

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

### 2. 从 GitHub marketplace 安装（推荐）

选择自己的客户端完成安装，再执行第 4 节准备运行依赖和第 6 节确认组件。需要离线安装时，从第 3 节开始。

#### Claude Code CLI

仓库已提供 [marketplace 清单](.claude-plugin/marketplace.json)，直接分发完整插件。无需克隆源码或手工打包。在目标项目根目录打开终端，选择安装范围：`user` 对当前用户的所有项目启用，`project` 写入团队共享配置，`local` 仅自己在当前项目启用。

```sh
# 将 user 换成 project 或 local，可选择项目级安装
TAO_SCOPE=user
export TAO_PYTHON="$(python3 -c 'import sys; print(sys.executable)')"
claude plugin marketplace add Dieken/tao-dev --scope "$TAO_SCOPE"
claude plugin install tao-dev@tao-dev --scope "$TAO_SCOPE"
```

读取客户端实际安装路径，后续从这个完整插件准备运行环境：

```sh
TAO_PLUGIN_DIR="$(claude plugin list --json | "$TAO_PYTHON" -c 'import json,sys; rows=[p for p in json.load(sys.stdin) if p["id"]=="tao-dev@tao-dev" and p["scope"]==sys.argv[1]]; assert len(rows)==1, "请核对安装范围"; print(rows[0]["installPath"])' "$TAO_SCOPE")"
```

<details>
<summary>Windows PowerShell</summary>

```powershell
$TaoScope = 'user' # 或 project、local
$env:TAO_PYTHON = py -3.13 -c "import sys; print(sys.executable)"
claude plugin marketplace add Dieken/tao-dev --scope $TaoScope
claude plugin install tao-dev@tao-dev --scope $TaoScope
$TaoPluginDir = (claude plugin list --json | ConvertFrom-Json | Where-Object { $_.id -eq 'tao-dev@tao-dev' -and $_.scope -eq $TaoScope }).installPath
if (-not $TaoPluginDir) { throw '未找到所选范围的插件安装路径' }
```

当前 hook 使用 `sh`，需让 Git for Windows 的 shell 可从 PATH 找到（可用 `sh --version` 检查）。原生 Windows 完整验收尚未完成；也可在 WSL 内按 Linux 步骤安装和启动客户端。

</details>

接着执行**第 4 节准备运行环境**，从同一终端运行 `claude`，再按**第 6 节确认组件**；跳过第 3 节本地打包和第 5 节本地安装。安装插件不会自动准备 Python 依赖。以后重新安装或升级后，应重新读取 installPath。

从旧本地 marketplace 迁移时，先用 `claude plugin uninstall tao-dev@tao-dev-local --scope <原范围> --keep-data` 移除原插件，再按上面安装；沿用原 TAO_RUNTIME_DIR。若还保留独立 skill 副本，将其移出 skill 搜索目录，避免两个入口同时加载。见 [官方安装说明](https://code.claude.com/docs/en/discover-plugins#add-from-github)。

##### Claude Code 后续升级

选择与安装时相同的范围，再执行：

```sh
TAO_SCOPE=user # 或 project、local
claude plugin marketplace update tao-dev
claude plugin update tao-dev@tao-dev --scope "$TAO_SCOPE"
```

PowerShell 设置 `$TaoScope` 并传给 `--scope`。升级后重新读取 installPath，按第 4 节执行两次 setup 和 doctor；从同一终端启动 `claude`，已有会话按提示 `/reload-plugins` 或重启。

要自动获取后续插件版本，可在 `/plugin` → Marketplaces → tao-dev 中开启 **Enable auto-update**；第三方 marketplace 默认不开启自动更新。自动更新插件文件不会自动安装新的 Python 依赖，依赖变化时仍需执行上述准备步骤。见 [自动更新说明](https://code.claude.com/docs/en/discover-plugins#configure-auto-updates)。

默认跟随仓库的默认分支，插件版本由 manifest 管理。Git tag 不是安装或升级的前提；若将来源固定为某个 tag，后续更新仍停留在该 tag，需要主动更换来源版本。

#### Codex CLI

仓库提供 [Codex marketplace 清单](.agents/plugins/marketplace.json)，与 Claude 清单引用同一份完整插件。以下命令按 Codex CLI 0.154.0 核对；无需先克隆或打包源码。

在目标项目根目录执行：

```sh
export TAO_PYTHON="$(python3 -c 'import sys; print(sys.executable)')"
codex plugin marketplace add Dieken/tao-dev
TAO_PLUGIN_DIR="$(codex plugin add tao-dev@tao-dev --json | "$TAO_PYTHON" -c 'import json,sys; print(json.load(sys.stdin)["installedPath"])')"
```

<details>
<summary>Windows PowerShell</summary>

```powershell
$env:TAO_PYTHON = py -3.13 -c "import sys; print(sys.executable)"
codex plugin marketplace add Dieken/tao-dev
$TaoPluginDir = (codex plugin add tao-dev@tao-dev --json | ConvertFrom-Json).installedPath
if (-not $TaoPluginDir) { throw '未找到插件安装路径' }
```

hook 同样需要 Git for Windows 提供的 `sh`；原生 Windows 完整验收尚未完成。

</details>

以上默认写入用户级启用。**仅当前项目使用时，启动 Codex 前先完成第 5 节的项目启用配置，将其中 `tao-dev@tao-dev-local` 换成 `tao-dev@tao-dev`。** Codex 没有 `--scope project/local`；在项目目录执行安装命令不会自动限制范围。

接着执行第 4 节的两次 setup 和 doctor，从同一终端用 `codex --enable hooks` 启动，确认项目信任，并在 `/hooks` 中检查、信任 tao-dev 的 hook。跳过第 3 节打包和第 5 节的本地注册命令。[官方 marketplace 说明](https://developers.openai.com/plugins/build/plugins)

##### Codex 后续升级

```sh
codex plugin marketplace upgrade tao-dev
TAO_PLUGIN_DIR="$(codex plugin add tao-dev@tao-dev --json | "$TAO_PYTHON" -c 'import json,sys; print(json.load(sys.stdin)["installedPath"])')"
```

PowerShell 执行同一条 marketplace upgrade，再按上面的安装命令重新读取 `$TaoPluginDir`。`plugin add` 会再次写入用户级启用；项目级用户需重新应用用户级 false、项目级 true 配置。随后重跑第 4 节的 setup 和 doctor，启动新会话并复核 hook 信任。固定 Git ref 的安装不会自动跟随其他版本。

### 3. 本地／离线安装源

每个客户端选择用户级或项目级安装。**用户级对当前用户的各项目启用；项目级仅对指定项目启用。** 客户端仍可能把插件副本放在用户缓存中，安装范围不等于所有文件的物理存放位置。只想项目级启用时，也要关闭此前的用户级安装及独立 skill 副本。

两端均可使用本地流程，不依赖 GitHub 或在线 marketplace。本节生成包含完整运行材料的本地 JSON 目录清单，再交给客户端安装；Codex 原生插件安装仍需要这份本地清单。打包只需 Python 标准库，不依赖 pip 包或 uv；输出目录必须尚不存在。

联网准备源码时执行以下命令；离线机器可直接使用提前下载的仓库副本，或接收本节生成的完整安装源目录（包含隐藏文件），无需在离线机器上执行 git clone。

```sh
git clone https://github.com/Dieken/tao-dev.git
cd tao-dev
TAO_SOURCE_DIR="$PWD"
export TAO_PYTHON="$(python3 -c 'import sys; print(sys.executable)')"
```

当前目录是 tao-dev 仓库，适合下方自举练习。要给其他项目安装，先切换到那个项目根目录，保留 TAO_SOURCE_DIR。从下表选一个目录赋值执行：

| 客户端／范围 | 安装源目录 |
|---|---|
| Claude Code 用户级 | `TAO_MARKETPLACE="$HOME/.local/share/tao-dev/claude"` |
| Claude Code 项目级 | `TAO_MARKETPLACE="$PWD/.local/tao-dev/claude"` |
| Codex 用户级 | `TAO_MARKETPLACE="$HOME/.local/share/tao-dev/codex"` |
| Codex 项目级 | `TAO_MARKETPLACE="$PWD/.local/tao-dev/codex"` |

按客户端执行对应的一条打包命令：

```sh
# Claude Code：skill、CLI、模板、commands、reviewer 与 hook
"$TAO_PYTHON" "$TAO_SOURCE_DIR/scripts/package_plugin.py" --format public --marketplace --output "$TAO_MARKETPLACE"
```

```sh
# Codex CLI 0.154.0：skill、CLI、模板与原生 hook
"$TAO_PYTHON" "$TAO_SOURCE_DIR/scripts/package_plugin.py" --format codex-legacy --marketplace --output "$TAO_MARKETPLACE"
```

Codex 0.154.0 使用 codex-legacy 包加载 skill 与 hook；GitHub 安装源已采用同样的兼容 manifest。Codex 的操作及审查通过 skill 和原生子代理执行，不加载 Claude 的 commands／agent 注册文件。两端完整组件的映射见 [插件设计](docs/engineering/plugin-design.md)。

<details>
<summary>Windows PowerShell：取得源码与打包</summary>

```powershell
git clone https://github.com/Dieken/tao-dev.git
Set-Location tao-dev
$TaoSourceDir = (Get-Location).Path
$env:TAO_PYTHON = py -3.13 -c "import sys; print(sys.executable)"
```

安装到其他项目时，先 Set-Location 到其根目录。选一个目录赋值：

| 客户端／范围 | 安装源目录 |
|---|---|
| Claude Code 用户级 | `$TaoMarketplace = Join-Path $env:LOCALAPPDATA 'tao-dev/claude'` |
| Claude Code 项目级 | `$TaoMarketplace = Join-Path (Get-Location).Path '.local/tao-dev/claude'` |
| Codex 用户级 | `$TaoMarketplace = Join-Path $env:LOCALAPPDATA 'tao-dev/codex'` |
| Codex 项目级 | `$TaoMarketplace = Join-Path (Get-Location).Path '.local/tao-dev/codex'` |

按客户端执行一条命令：

```powershell
# Claude Code
& $env:TAO_PYTHON "$TaoSourceDir/scripts/package_plugin.py" --format public --marketplace --output $TaoMarketplace
# Codex CLI 0.154.0
& $env:TAO_PYTHON "$TaoSourceDir/scripts/package_plugin.py" --format codex-legacy --marketplace --output $TaoMarketplace
```

当前 hook 使用 `sh` 启动。在同一 PowerShell 中运行 `sh --version`，确认 Git for Windows 提供的 shell 可从 PATH 找到；只有 Python 可用不足以证明 hook 能运行。原生 Windows 的完整客户端验收尚未完成；也可在 WSL 中按 Linux 步骤安装，并在 WSL 内启动客户端。

</details>

本地打包完成后设置插件路径：POSIX shell 执行 `TAO_PLUGIN_DIR="$TAO_MARKETPLACE/plugins/tao-dev"`，PowerShell 执行 `$TaoPluginDir = Join-Path $TaoMarketplace 'plugins/tao-dev'`。GitHub 安装使用第 2 节从各自客户端读取的路径。

#### 离线安装前准备依赖

在与离线目标具有相同系统、CPU 架构和 Python 次版本的联网机器上，先准备第 1 节的客户端、Python 安装材料及系统依赖，并从同一版本的插件下载锁定 wheel：

```sh
"$TAO_PYTHON" -m pip download --only-binary=:all: --require-hashes --dest "$TAO_MARKETPLACE/wheelhouse" -r "$TAO_PLUGIN_DIR/skills/tao-dev/scripts/requirements.txt"
"$TAO_PYTHON" -m pip download --only-binary=:all: --require-hashes --dest "$TAO_MARKETPLACE/wheelhouse" -r "$TAO_PLUGIN_DIR/skills/tao-dev/scripts/requirements-publication.txt"
```

PowerShell 将调用前缀换成 `& $env:TAO_PYTHON`，路径变量换成 `$TaoMarketplace`、`$TaoPluginDir`。将完整安装源目录连同 wheelhouse 复制到目标机器，按目标位置重新设置这些变量；按第 4 节使用 `--wheelhouse`，再执行第 5 节的本地注册。Python、pip／venv、客户端和所需 shell 也必须提前安装；离线准备不代表模型服务可以断网使用。

### 4. 准备 CLI、出版与 hook 共用的运行环境

在同一终端设置运行目录，避免终端 setup 与插件 hook 使用不同环境。选择一种范围：

```sh
# 用户级：多个项目共享
export TAO_RUNTIME_DIR="$HOME/.local/share/tao-dev/runtime"
```

```sh
# 项目级：只保存在当前项目
export TAO_RUNTIME_DIR="$PWD/tmp/tao/runtime"
```

准备完整运行依赖，包括 HTML 出版：

```sh
"$TAO_PYTHON" "$TAO_PLUGIN_DIR/skills/tao-dev/scripts/tao.py" setup
"$TAO_PYTHON" "$TAO_PLUGIN_DIR/skills/tao-dev/scripts/tao.py" setup --publication
"$TAO_PYTHON" "$TAO_PLUGIN_DIR/skills/tao-dev/scripts/tao.py" doctor --project "$PWD" --format json
```

两次 setup 分别准备核心环境和出版环境，显式联网下载锁定依赖，写入独立虚拟环境；doctor 应报告两者 ready。离线安装将上面的两条 setup 分别改为 `setup --wheelhouse "$TAO_MARKETPLACE/wheelhouse"` 和 `setup --publication --wheelhouse "$TAO_MARKETPLACE/wheelhouse"`（PowerShell 使用 `$TaoMarketplace/wheelhouse`），不访问包索引。详见 [运行环境规程](plugins/tao-dev/skills/tao-dev/references/runtime.md)。

<details>
<summary>Windows PowerShell：运行环境</summary>

选择一个运行目录：

```powershell
# 用户级
$env:TAO_RUNTIME_DIR = Join-Path $env:LOCALAPPDATA 'tao-dev/runtime'
# 或项目级
$env:TAO_RUNTIME_DIR = Join-Path (Get-Location).Path 'tmp/tao/runtime'
```

然后执行：

```powershell
& $env:TAO_PYTHON "$TaoPluginDir/skills/tao-dev/scripts/tao.py" setup
& $env:TAO_PYTHON "$TaoPluginDir/skills/tao-dev/scripts/tao.py" setup --publication
& $env:TAO_PYTHON "$TaoPluginDir/skills/tao-dev/scripts/tao.py" doctor --project (Get-Location).Path --format json
```

</details>

以后启动客户端前重新设置 TAO_PYTHON、TAO_RUNTIME_DIR，或在个人 shell 配置中保存用户级设置；项目级变量必须指向当前项目。不要把本机绝对路径写入团队共享配置。仅本机使用的 `.local/tao-dev/` 与 `tmp/tao/` 应加入项目忽略规则；安装源目录需要保留，客户端更新时还会读取它。

### 5. 从本地安装源安装并启用

GitHub 安装跳过本节的本地注册命令；Codex 项目级用户仍需完成本节下方的启用配置。以下命令在**目标项目根目录**执行。PowerShell 将 `$TAO_MARKETPLACE` 换成 `$TaoMarketplace`；其余客户端命令相同。

#### Claude Code CLI

从下列三组中选择一组，marketplace 和插件使用相同范围：

```sh
# 用户级：当前用户的所有项目
claude plugin marketplace add "$TAO_MARKETPLACE" --scope user
claude plugin install tao-dev@tao-dev-local --scope user
```

```sh
# 项目级：团队共享，写入 .claude/settings.json
claude plugin marketplace add "$TAO_MARKETPLACE" --scope project
claude plugin install tao-dev@tao-dev-local --scope project
```

```sh
# 项目级：仅自己使用，写入 .claude/settings.local.json
claude plugin marketplace add "$TAO_MARKETPLACE" --scope local
claude plugin install tao-dev@tao-dev-local --scope local
```

团队配置若包含本机安装源的绝对路径，其他成员需按自己的路径重新注册；不要直接提交该路径。安装后运行 `claude plugin list --json` 核对范围及 enabled 状态，再从当前终端启动 `claude`。已打开的会话按提示 `/reload-plugins` 或重启。启用已关闭的插件用 `claude plugin enable tao-dev@tao-dev-local --scope <所选范围>`。见 [Claude 安装范围](https://code.claude.com/docs/en/plugins-reference#plugin-installation-scopes)。

#### Codex CLI

本节命令已按 Codex CLI 0.154.0 的 `--help` 核对；该版本使用 `plugin add`，没有 `plugin install` 或 `--scope project`。

```sh
codex plugin marketplace add "$TAO_MARKETPLACE"
codex plugin add tao-dev@tao-dev-local --json
```

**用户级到此完成安装与启用。**

##### Codex 项目启用配置（GitHub 与本地安装通用）

若只在当前项目启用，安装后还需完成下面两项配置。以下以本地安装的 `tao-dev@tao-dev-local` 为例，GitHub 安装将两个表名均换成 `tao-dev@tao-dev`。合并到已有表，不覆盖配置文件或重复添加同名 TOML 表：

1. 在 `~/.codex/config.toml`（自定义 CODEX_HOME 时为其下的 config.toml）中，将这次安装写入的用户级状态改为：

   ```toml
   [plugins."tao-dev@tao-dev-local"]
   enabled = false
   ```

2. 在目标项目 `.codex/config.toml` 中加入：

   ```toml
   [plugins."tao-dev@tao-dev-local"]
   enabled = true
   ```

安装缓存仍由用户目录管理；受信任项目的配置覆盖用户级默认值，实现仅本项目启用。仅在项目目录运行 `plugin add` 不会自动限制范围。使用 `codex --enable hooks` 启动客户端，按提示确认项目信任，再在 `/hooks` 中查看并信任 tao-dev 的实际 hook 定义；代码变化后需要重新审阅。见 [项目启用配置](https://developers.openai.com/plugins/build/plugins#enable-or-disable-a-plugin-for-a-repo) 与 [hook 信任](https://learn.chatgpt.com/docs/hooks#review-and-trust-hooks)。

### 6. 确认完整安装生效

| 检查 | Claude Code CLI | Codex CLI |
|---|---|---|
| 流程入口 | `/tao-dev:tao-dev`；操作包装如 `/tao-dev:new` | `/skills` 或 `$` 选择 tao-dev，用 `$tao-dev` 调用 |
| 独立审查 | `/agents` 中能看到插件的 reviewer | 由 skill 使用原生子代理审查；没有 Claude 的具名 agent 注册 |
| 短文档检查 | `/hooks` 中能看到 tao-dev 的 PostToolUse hook | `/hooks` 中能看到已启用、已信任的 tao-dev hook |
| CLI 与出版 | 从已安装插件入口运行 doctor，核心与出版环境均 ready | 同左 |

安装列表中出现 skill 还不够；同时检查 hook 及对应客户端入口。原生安装路径可从 Claude 的 `plugin list --json` 的 installPath、Codex 的 `plugin add --json` 的 installedPath 获取。该路径下也应有 `skills/tao-dev/scripts/tao.py`，可用第 4 节的环境执行 doctor。

hook 只在项目已有 `.tao/config.toml` 时进行短文档反馈。首次接入其他项目，可要求 agent 使用 tao-dev 建立适合该项目的配置，再通过一次受管理 Markdown 的修改检查 hook 输出；它不会替代完整 verify。项目级安装还应在另一个未启用 tao-dev 的项目中启动新会话，确认 skill 和 hook 均未加载。

#### GitHub、版本与更新

Claude Code 与 Codex 均可按第 2 节从 GitHub marketplace 安装与升级完整插件。`$skill-installer` 只安装 skill 目录，不能代替完整插件安装。GitHub 的 `tao-dev` 与本地的 `tao-dev-local` 是不同来源；切换方式时移除或禁用旧入口，避免重复加载。

以下更新步骤适用于本地安装源。需要固定源码版本时，在源码目录先执行 `git checkout --detach <完整 commit SHA>` 再打包，并记录该 SHA。`git pull` 不会自动更新已安装副本。更新前记录安装范围；生成新的安装源目录并按第 5 节更新 marketplace 来源，再执行客户端更新：

- Claude：`claude plugin update tao-dev@tao-dev-local --scope <原范围>`。同版本开发快照若仍命中旧缓存，用 `claude plugin uninstall tao-dev@tao-dev-local --scope <原范围> --keep-data` 保留运行数据，再按原范围重新安装。
- Codex：更换安装源目录时，先执行 `codex plugin marketplace remove tao-dev-local`，再 `codex plugin marketplace add <新安装源目录>`，然后重新执行 `codex plugin add tao-dev@tao-dev-local`。它会再次写入用户级启用，项目级用户必须重新完成第 5 节的用户级 false、项目级 true 配置。

更新后重跑两次 setup 和 doctor，并复核 hook 信任。版本字段和发布 tag 的维护见 [开发指南](docs/engineering/development.md)。

### 7. 自举体验：用 tao-dev 为 tao-dev 开发新功能

**这个练习的开发对象就是 tao-dev 本身。** GitHub marketplace 用户先克隆 [tao-dev 源码](https://github.com/Dieken/tao-dev)。进入源码根目录，设置第 4 节的运行环境，然后启动 `claude` 或 `codex --enable hooks` 并调用插件。若此前给其他项目做了项目级安装，先为 tao-dev 完成相同的启用配置，并按第 4 节设置它自己的项目运行目录。可以先点击阅读 [SKILL.md](plugins/tao-dev/skills/tao-dev/SKILL.md)，再输入：

> 请使用 tao-dev，为 tao-dev 自身新增 `tao docs serve` 命令制定开发计划：在本机预览生成的文档书籍，并在 Markdown 修改后重新构建和刷新页面。先检查现有实现，明确范围、验收场景和必要设计，生成并填写变更计划；本轮只规划，暂不编码。

这是一项示例新需求，当前 CLI 只有 `tao docs build`，尚无 `tao docs serve`。agent 应交付填写好的计划和未决事项；要继续体验实现、测试和审查，可随后要求它按计划继续开发。开发依赖与检查命令见 [开发指南](docs/engineering/development.md)。

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
