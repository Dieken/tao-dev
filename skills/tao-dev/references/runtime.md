# 运行环境与项目安装

阅读、复制 `SKILL.md` 及完整资源不需要 Python、文档解析依赖或出版工具。tao 只提供文档管理辅助命令，不管理安装生命周期。

完整技能包包括 `SKILL.md`、`references`、`assets` 和 `scripts`。辅助命令支持 Python 3.11–3.14，调用规则与能力检查见 [工具入口](tools.md)。文档命令可能需要解析依赖，HTML 构建另外需要出版依赖；依赖准备必须显式授权，不因读取或安装技能而触发。

源码与发布包使用 `skills/tao-dev`。复制完整技能包到项目发现目录，不修改用户级配置或其他项目；也可自行选择通用技能管理工具，这些工具不是 tao 的运行依赖。

## 显式准备辅助工具

需要文档命令时，默认在目标项目根目录显式创建专用环境 `tmp/venv-tao`，不复用业务项目的 `.venv`。将 `tmp/venv-tao/` 加入项目忽略规则；清理该目录后需重新显式准备依赖。以下为 POSIX shell 示例，`SKILL` 改为实际加载的技能目录：

```sh
SKILL=.agents/skills/tao-dev
python3 -m venv tmp/venv-tao
PY=tmp/venv-tao/bin/python
"$PY" -m pip install --require-hashes -r "$SKILL/scripts/requirements.txt"
"$PY" "$SKILL/scripts/tao.py" --project . doctor --format json
```

HTML 构建另用同一解释器执行 `-m pip install --require-hashes -r "$SKILL/scripts/requirements-publication.txt"`。Windows 使用 `python -m venv tmp/venv-tao` 创建环境，随后通过 `tmp/venv-tao/Scripts/python.exe` 安装依赖和调用脚本。

命令始终使用调用者指定的解释器，不自动创建、发现或切换环境，也不在 `~/.local`、`~/Library/Application Support` 等用户级目录安装环境。安装技能文件本身不触发 pip。

## 项目发现目录

Claude Code 使用 `.claude/skills/tao-dev/`，Codex 和 Cursor 可共用 `.agents/skills/tao-dev/`，Kiro 使用 `.kiro/skills/tao-dev/`。同一客户端不要重复放置同名副本。路径来自客户端约定，不保证所有版本已实际加载。

复制前确认目标为项目内新目录且不经符号链接指向项目外。手工更新先保存本地改动，再完整替换旧副本；不要叠加覆盖而留下废弃文件。来源与版本由项目 Git 或所选工具记录；移除只针对技能目录，不删除项目文档和配置。手工复制没有自动修改保护或失败回滚，第三方工具的行为以其文档和实测为准。
