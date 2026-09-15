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

### 在本仓库使用 tao

以下 POSIX shell 示例将自举运行环境限定在项目临时目录；后续命令在同一 shell 中运行。Windows 在 PowerShell 中设置对应环境变量，并使用 `.venv/Scripts/python.exe`。

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
.venv/bin/python plugins/tao-dev/skills/tao-dev/scripts/tao.py setup --publication --wheelhouse tmp/tao/wheels
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

按目标客户端选择所需格式；输出目录必须尚不存在。这些命令只打包，不安装或注册。兼容包的适用版本及组件差异见 [插件设计](plugin-design.md)，客户端验收与当前缺口见 [运行环境记录](../changes/2026-09/20260914-portable-runtime.md)。

<!-- tao:section troubleshooting -->
## 排障

- **缺少 wheel 或依赖**：先确认显式下载步骤和锁文件是否同步，再运行所需 setup；普通测试不会自动联网补齐。
- **运行环境不可用**：检查 TAO_RUNTIME_DIR、TAO_PYTHON 与 doctor 输出，按运行环境规程处理；不要清理仍被其他进程使用的锁或目录。
- **文档引用无法解析**：确认管理范围包含定义所在文件；单独检查一个文件不能代替跨文档检查。未提供历史基线时也不能证明所有历史删除均已检测。
- **出版链接回归缺少 Node.js**：准备维护环境中的 Node.js 后重跑，不把缺少运行前提当作插件运行依赖。
- **完整验证受阻**：按报告区分未完成任务、审查缺失或过期及工具故障。当前版本的总体发布状态由实际验收记录维护，不通过降低策略取得通过结果。
