---
schema: tao.project.user-guide/v0.1
id: DOC_20260916_J7HZD61YYQTTYBW0
title: 在 coding agent 项目中接入 tao-dev
locale: zh-Hans
status: draft
created: "2026-09-16"
---

# 在 coding agent 项目中接入 tao-dev

<!-- tao:section scope -->
## 项目级接入

只安装完整 skill 目录，不安装 hook、插件、marketplace 或用户级 launcher。安装命令仅复制文件，不能据此宣称客户端已实际加载或执行成功。

<!-- tao:section prerequisites -->
## 准备条件

读取 skill 无需 Python 依赖；安装管理需要 Python 3.11–3.14。文档辅助命令可在显式创建的项目 .venv 中安装锁定清单；出版依赖另行准备。不要求 uv、全局客户端配置或依赖自动安装。

<!-- tao:section steps -->
## 安装与管理

在 tao-dev 源码目录执行，项目必须已存在：

```sh
python3 skills/tao-dev/scripts/tao.py install --project /path/to/project --client codex
python3 skills/tao-dev/scripts/tao.py list --project /path/to/project
python3 skills/tao-dev/scripts/tao.py upgrade --project /path/to/project --client codex
python3 skills/tao-dev/scripts/tao.py uninstall --project /path/to/project --client codex
```

install/upgrade 可用 `--source /path/to/repo-or-skill` 指定来源，默认当前运行 skill。install/upgrade/uninstall 必须指定 client，list 不指定则列本项目四种受支持客户端。没有 --scope、--all 或 --yes。

| client | 项目原生 skill 目录 | 官方依据 |
|---|---|---|
| claude | .claude/skills/tao-dev | [Claude Code skills](https://code.claude.com/docs/en/skills) |
| codex | .agents/skills/tao-dev | [Codex skills](https://developers.openai.com/codex/skills) |
| cursor | .cursor/skills/tao-dev | [Cursor skills](https://cursor.com/docs/skills.md) |
| kiro | .kiro/skills/tao-dev | [Kiro skills](https://kiro.dev/docs/skills/) |

选择客户端原生 skill 入口或要求 agent 读取项目内 SKILL.md。保持 references、assets、scripts 完整；同一客户端避免重复副本。安装记录 `.tao-install.json` 只在受管 skill 内；不修改客户端全局配置。遇到非受管目录、符号链接或用户改动时保留现场，不强制覆盖。卸载仅移除受管安装，不删项目文档。

## 能力边界

官方路径依据、文件部署测试与真实 agent 行为验收分别报告；新项目纯 skill 的运行结果不能从旧插件测试继承。只支持表中安装适配，不声称其他客户端已支持。隔离试验必须同时核对项目内发现与项目外缺席，缺 CLI 或认证就报告未运行，不能回退全局配置。见 [兼容性边界](../engineering/client-compatibility.md)。
