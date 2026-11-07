---
schema: tao.project.user-guide/v0.1
id: DOC_20260916_J7HZD61YYQTTYBW0
title: 在 coding agent 项目中接入 tao-dev
locale: zh-Hans
status: draft
---

# 在 coding agent 项目中接入 tao-dev

<!-- tao:section scope -->
## 项目级接入

把完整文档与知识管理 skill 复制到明确项目的发现目录，保持用户级配置不变。项目文档及持久 plan/tasks 可由不同客户端读取，客户端临时任务不是另一份项目进度源。文件部署、客户端发现与模型实际执行是三个独立结果。

<!-- tao:section prerequisites -->
## 准备条件

读取与复制 skill 不需要 Python。只有辅助命令需要 Python 3.11–3.14；文档命令的依赖在显式创建的项目 .venv 中准备，出版依赖另装。不要求 uv、全局客户端配置或自动环境准备。

<!-- tao:section steps -->
## 复制到项目

从可信的源码版本或发布包取得完整 `skills/tao-dev/`，保留 [SKILL.md](../../skills/tao-dev/SKILL.md)、`references/`、`assets/`、`scripts/`：

| 客户端 | 项目发现目录 | 官方依据 |
|---|---|---|
| Claude Code | `.claude/skills/tao-dev/` | [Claude Code skills](https://code.claude.com/docs/en/skills) |
| Codex | `.agents/skills/tao-dev/` | [Codex skills](https://developers.openai.com/codex/skills) |
| Cursor | `.agents/skills/tao-dev/` | [Cursor skills](https://cursor.com/docs/skills.md) |
| Kiro | `.kiro/skills/tao-dev/` | [Kiro skills](https://kiro.dev/docs/skills/) |

例如在 tao-dev 源码目录为 Codex / Cursor 复制。先确认目标项目已存在，父目录不通过符号链接指向项目外：

```sh
mkdir -p /path/to/project/.agents/skills
test ! -e /path/to/project/.agents/skills/tao-dev &&
test ! -L /path/to/project/.agents/skills/tao-dev &&
cp -R skills/tao-dev /path/to/project/.agents/skills/tao-dev
```

Windows 可用文件管理器复制同一完整目录。项目 Git 可记录副本及其来源版本。不要把维护者的临时缓存当作发布资源；需要干净包时使用源码仓库的 `just package <新目录>`。

重启或按客户端文档刷新 skill 列表，确认实际加载路径；再要求 agent 使用 tao-dev。Codex 和 Cursor 可共用一份 `.agents/skills/tao-dev/`。同一客户端不要同时保留多个发现路径下的同名副本。

### 可选：通用 skills 工具

[Vercel skills CLI](https://github.com/vercel-labs/skills) 提供通用安装、查看、更新和移除。它不是 tao 的依赖，Node.js 要求和各版本行为以[上游文档](https://github.com/vercel-labs/skills/blob/main/docs/commands.md)为准。以下是按上游接口编写的本地来源示例，不代表本项目已验证该第三方版本：

```sh
# 在目标项目内执行；来源是另一个 tao-dev 源码目录
npx skills add /path/to/tao-dev/skills/tao-dev --skill tao-dev --agent codex --copy
```

显式选客户端，不使用 `--global`、`--all` 或自动确认；执行前检查预览中的目的地。来源不能是目标目录自身。该工具默认项目级，但具体复制、链接、锁文件、覆盖保护与更新策略由工具负责；不要假定等同于手工复制或具有事务回滚。受它管理的副本按其文档更新和移除，不叠加另一套管理方式。

### 更新与移除

手工复制不检查文件归属、不自动保护本地改动，也不提供失败回滚：

1. 更新前记录来源版本，把旧副本及个人改动备份到所有客户端发现目录之外。
2. 确认目标只含该 skill，再移走整个旧目录，复制完整新版本；不要叠加覆盖留下废弃文件。
3. 移除仅针对已确认的 skill 目录，不删除项目文档、`.tao` 配置、其他 skill 或用户级目录。

这些步骤仅处理用户选定的副本，不扫描或修改其他项目。

## 能力边界

官方路径依据、文件部署测试与真实 agent 行为验收分别报告。表中是接入路径，不是 tao 安装适配 API，也不证明所有客户端版本已兼容。隔离试验必须同时核对项目内发现与项目外缺席，缺 CLI 或认证就报告未运行，不能回退全局配置。通用安装器未实测时明确标为未验证。见 [兼容性边界](../engineering/client-compatibility.md)。
