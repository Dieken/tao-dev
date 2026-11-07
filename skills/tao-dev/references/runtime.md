# 运行环境与项目安装

阅读、复制 `SKILL.md` 及完整资源不需要 Python、文档解析依赖或出版工具。tao 只提供文档管理辅助命令，不管理安装生命周期。

完整技能包包括 `SKILL.md`、`references`、`assets` 和 `scripts`。辅助命令支持 Python 3.11–3.14，调用规则与能力检查见 [工具入口](tools.md)。文档命令可能需要解析依赖，HTML 构建另外需要出版依赖；依赖准备必须显式授权，不因读取或安装技能而触发。

源码与发布包使用 `skills/tao-dev`。复制完整技能包到项目发现目录，不修改用户级配置或其他项目；也可自行选择通用技能管理工具，这些工具不是 tao 的运行依赖。

## 显式准备辅助工具

需要文档命令时在目标项目用 `python3 -m venv .venv` 创建环境，再用该环境的 Python 执行 `-m pip install --require-hashes -r <skill>/scripts/requirements.txt`；HTML 构建另装 `scripts/requirements-publication.txt`。随后用同一解释器调用 `<skill>/scripts/tao.py`。安装文件本身不触发 pip。

## 项目发现目录

Claude Code 使用 `.claude/skills/tao-dev/`，Codex 和 Cursor 可共用 `.agents/skills/tao-dev/`，Kiro 使用 `.kiro/skills/tao-dev/`。同一客户端不要重复放置同名副本。路径来自客户端约定，不保证所有版本已实际加载。

复制前确认目标为项目内新目录且不经符号链接指向项目外。手工更新先保存本地改动，再完整替换旧副本；不要叠加覆盖而留下废弃文件。来源与版本由项目 Git 或所选工具记录；移除只针对技能目录，不删除项目文档和配置。手工复制没有自动修改保护或失败回滚，第三方工具的行为以其文档和实测为准。
