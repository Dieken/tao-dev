---
schema: tao.project.user-guide/v0.1
id: DOC_20260915_EGTG403AY0XK9WME
title: 开发与维护指南
locale: zh-Hans
status: draft
created: "2026-09-15"
---

# 开发与维护指南

<!-- tao:section scope -->
## 目标与边界

本文供 tao-dev 维护者准备环境、运行检查、构建手册和生成发布包。消费项目的使用入口见 [README](../../README.md)，运行环境规则见 [插件运行环境](../../plugins/tao-dev/skills/tao-dev/references/runtime.md)。

本目录是独立 Git 仓库。遵循 [AGENTS.md](../../AGENTS.md)，使用仓库内的 skill、共享 profile 和模板开发；CLAUDE.md 导入同一维护入口，无需全局安装。文档职责与校验范围见 [文档契约](documentation/contract.md)，分发边界见 [插件设计](plugin-design.md)。

项目以简体中文维护权威正文，代码标识、文件名、schema 键、状态值、规则号及代码注释使用英文；语言取舍见 [项目语言决定](decisions/project-language.md)。消费项目按自己的语言约定生成内容。

<!-- tao:section prerequisites -->
## 前置条件

需要 uv、Python 3.11–3.14 和 Node.js。开发依赖由 pyproject.toml 声明、uv.lock 锁定，环境位于忽略的 .venv/。Node.js 用于执行生成页面的重定向脚本，不是分发插件的依赖。

在仓库根目录准备环境和离线测试材料：

```sh
uv sync --no-config --locked --extra publication
uv run --no-config --locked --extra publication python tests/acceptance/runtime.py --download
```

第二条命令显式下载带锁定哈希的 wheel 到 tmp/tao/wheels；普通回归离线使用它们，缺少时报告前提未满足。测试通过真实独立 venv 验证运行入口，不向业务环境安装依赖。

<!-- tao:section steps -->
## 操作步骤

### 日常回归

```sh
uv run --no-config --locked --extra publication python -m pytest
```

普通 pytest 不调用模型。覆盖率及配置化检查通过仓库的 `.tao/config.toml` 接入；度量是观察值，门槛由原生命令执行。真实客户端试验单独按 [验收说明](../../tests/acceptance/README.md) 显式运行。

安装相关回归可单独运行：

```sh
.venv/bin/python -m pytest tests/test_installed_runtime.py tests/test_install_clients.py tests/test_installation.py
```

这些测试覆盖记录与作用域选择、无 TAO 环境变量的运行入口、原生客户端适配、安装更新与卸载边界；模拟客户端的测试不能替代真实客户端验收。运行资料和客户端配置使用临时目录，依赖使用离线 wheel。原生试验必须另外遵循 AGENTS.md，使用独立 CODEX_HOME、CLAUDE_CONFIG_DIR、Git 配置与实验项目，不修改个人客户端、认证或全局插件配置，并检查项目内加载与项目外缺席。

### 在本仓库使用 tao

通过 install 安装的用户直接使用安装器提供的 tao 命令，无需设置 TAO 环境变量。维护本仓库的源码入口不要求注册插件；以下 POSIX shell 示例用显式覆盖将源码自举环境限定在项目临时目录，后续命令在同一 shell 中运行。Windows 在 PowerShell 中设置对应环境变量，并使用 `.venv/Scripts/python.exe`。

```sh
export TAO_RUNTIME_DIR="$PWD/tmp/tao/runtime"
export TAO_PYTHON="$PWD/.venv/bin/python"
.venv/bin/python plugins/tao-dev/skills/tao-dev/scripts/tao.py setup --wheelhouse tmp/tao/wheels
.venv/bin/python plugins/tao-dev/skills/tao-dev/scripts/tao.py doctor --format json
.venv/bin/python plugins/tao-dev/skills/tao-dev/scripts/tao.py verify --only docs --format json
```

`verify --only docs` 检查配置纳入的全部开发文档、跨文档关系和书籍导航。独立校验器的参数及结果范围见 [诊断规程](../../plugins/tao-dev/skills/tao-dev/references/document-diagnostics.md)。README、运行 prompt 和模板使用各自格式，不套用开发正文 profile。

需要执行项目策略时，使用同一入口的 `verify --only code`；`status` 只读比较证据。完整 `verify <CHG-ID>` 还汇总目标任务、依赖及必需审查，不能用局部结果代替。结果、日志与缓存保存规则见 [验证规程](../../plugins/tao-dev/skills/tao-dev/references/verification.md)。

### 构建开发手册

沿用上面的环境变量，准备出版环境后构建：

```sh
.venv/bin/python plugins/tao-dev/skills/tao-dev/scripts/tao.py setup --wheelhouse tmp/tao/wheels
.venv/bin/python plugins/tao-dev/skills/tao-dev/scripts/tao.py docs build --format json
```

按 JSON 输出的 index 打开 HTML，或用本地 HTTP 服务器预览 tmp/tao/book/。构建只生成本地产物，输出默认不纳入 VCS。稳定链接与旧入口的检查方法见 [出版规程](../../plugins/tao-dev/skills/tao-dev/references/publication.md)。

### 更新依赖和打包

修改开发依赖并更新锁文件后，重新导出运行清单；发布前使用 --check 检查同步：

```sh
uv run --no-config --locked --extra publication python scripts/export_dependencies.py
uv run --no-config --locked --extra publication python scripts/export_dependencies.py --check
```

生成新目录中的插件包：

```sh
.venv/bin/python scripts/package_plugin.py --format public --output tmp/tao/public-plugin
.venv/bin/python scripts/package_plugin.py --format codex-legacy --output tmp/tao/codex-plugin
```

按目标客户端选择所需格式；输出目录必须尚不存在。这些命令只打包，不安装或注册。兼容包的适用版本及组件差异见 [插件设计](plugin-design.md)，客户端验收与当前缺口见 [运行环境记录](../plans/2026-09/20260914-portable-runtime.md)。

给上述命令添加 `--marketplace`，输出变为含 `plugins/tao-dev/` 的完整本地安装源：public 生成 Claude 的 `.claude-plugin/marketplace.json`，codex-legacy 生成 Codex 的 `.agents/plugins/marketplace.json`，目录索引名均为 `tao-dev-local`。这个选项只生成文件，实际安装、启用范围和运行环境准备按 [README](../../README.md) 执行。两种格式分别生成到不同的新目录，不合并为一个安装源。

### 维护安装实现

源码与分发插件共用 scripts/tao.py 的 install/uninstall 实现；这两个命令在独立运行环境准备之前由标准库入口处理。install 一次完成取得来源、准备核心与出版依赖、原生安装与范围配置、写入绑定和 doctor 检查；普通命令与 hook 不自动下载。安装参数与边界见 [安装设计](installation.md)。

--source 接受完整插件目录、仓库目录或 Git 来源；安装器复制插件，按内容生成本机专用 marketplace 和版本后缀，再调用客户端原生安装。原始源码目录不属于可删除资源。--marketplace 使用已有目录清单，两者互斥；重复 install 默认沿用已记录来源，也可明确切换来源。--wheelhouse 只限制依赖获取，不使远程 Git 或客户端操作自动离线。

安装记录模块负责验证安装身份、工具数据归属和运行绑定，客户端适配模块负责原生缓存及共享配置。共享 CLI 按当前目录或 --project 从两个客户端的记录中选择安装，先转交对应原生插件入口，使不同项目沿用各自版本的依赖清单；install/uninstall 继续使用共享安装器。运行数据目录优先采用显式 TAO 覆盖，其次采用匹配的安装记录，再回退到 Claude 数据目录和平台默认目录。记录中的解释器及运行位置不写进项目共享配置；未知或符号链接重定向的归属不能成为递归删除依据。共享 CLI 在最后一份安装卸载后仍保留，以便再次安装。

Claude 保留 user、project、local 三种原生范围。Codex 的 repo、local 参数均归一为 project，与 user 构成两个有效范围；不能把 local 描述为额外的个人项目配置。修改安装流程时同步相关行为测试，并分别报告模拟适配测试、实际依赖准备与原生客户端验收的范围。

### 版本与发布 tag

Claude Code 与 Codex 的 GitHub 安装入口分别为仓库根 [Claude 清单](../../.claude-plugin/marketplace.json) 和 [Codex 清单](../../.agents/plugins/marketplace.json)，目录名为 `tao-dev`，以相对路径引用完整插件。目录清单不重复声明插件版本，版本取自插件 manifest。每次发布影响插件内容的更新，必须递增 manifest 版本并同步下表中的字段；仅推送代码或创建 Git tag 不会使已安装的同版本插件升级。用户按 README 重复 install 刷新来源并更新原作用域的安装；本地 --source 的内容变化由专用目录清单和版本后缀区分。Codex 的 GitHub 清单引用兼容源码，公共格式仍由打包器生成，不将生成副本提交进仓库。

skill、模板、CLI 和插件作为一个 tao-dev 版本一起发布，以 [pyproject.toml](../../pyproject.toml) 的 `project.version` 为主版本。无需在 SKILL.md 中另设独立版本；[Agent Skills 规范](https://agentskills.io/specification#metadata-field)允许可选的 `metadata.version`，但不要求提供，也不定义安装和更新行为。

开发中的不同内容用完整 commit SHA 区分；无需为每次提交递增版本，也不为支持 GitHub 安装而提前标记正式发布。准备可供用户固定安装的版本时，先完成对应范围的验收、独立审查和支持限制说明，再为该提交创建 `v<版本号>` tag；已经公开的 tag 不移动，修订另发新版本。

修改版本时，同步以下位置；这是一组发布同步步骤，当前没有自动覆盖所有字段的同步工具：

| 位置 | 维护方式 |
|---|---|
| `pyproject.toml` 的 `project.version` | 先修改主版本，再更新 `uv.lock` |
| `plugins/tao-dev/.codex-plugin/plugin.json` 与 `plugins/tao-dev/.claude-plugin/plugin.json` | 将两个客户端 manifest 的 `version` 同步为主版本 |
| `plugins/tao-dev/skills/tao-dev/scripts/taolib/__init__.py` | 将 `__version__` 同步为主版本，用于 CLI 报告 |
| `plugins/tao-dev/skills/tao-dev/scripts/runtime.json` | 运行前述 `scripts/export_dependencies.py` 生成，不手工修改 |

发布前运行依赖导出的 `--check`、相关回归和打包检查，并核对上述版本一致；其中 `--check` 只校验生成的运行策略与依赖清单，不检查全部 manifest 和 CLI 版本。生成的公共 manifest 由打包脚本继承 Codex manifest 的版本，无需单独维护。回归与验收脚本中固定旧版本的预期也应核对。

`protocol_version`、文档 schema 的 `/v0.1` 和 `.tao/config.toml` 的格式版本各自表示数据契约，不能随项目发布版本一并替换。

<!-- tao:section troubleshooting -->
## 排障

- **缺少 wheel 或依赖**：先确认显式下载步骤和锁文件是否同步，再运行所需 setup；普通测试不会自动联网补齐。
- **运行环境不可用**：先检查 doctor 输出、当前项目和安装记录；使用源码自举或显式覆盖时再检查 TAO_RUNTIME_DIR、TAO_PYTHON。按运行环境规程处理，不清理仍被其他进程使用的锁或目录。
- **文档引用无法解析**：确认管理范围包含定义所在文件；单独检查一个文件不能代替跨文档检查。未提供历史基线时也不能证明所有历史删除均已检测。
- **出版链接回归缺少 Node.js**：准备维护环境中的 Node.js 后重跑，不把缺少运行前提当作插件运行依赖。
- **完整验证受阻**：按报告区分未完成任务、审查缺失或过期及工具故障。当前版本的总体发布状态由实际验收记录维护，不通过降低策略取得通过结果。
