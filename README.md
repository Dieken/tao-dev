# tao-dev · 项目知识与文档协作

面向项目的文档与知识管理技能（skill）：维护需求、设计和决策，用持久计划记录跨会话、跨客户端的项目进度，并将实际结果写入相关文档。

## 文档与持久计划

tao-dev 负责文档的创建、修订、语义审查、关联、查询、退役与出版，不编排通用开发流程。智能体（agent）自行管理执行，并把实际成果、验证结果和阻碍写回项目文档。

不要求每次改动都新建规格、设计和计划。小改动复用适用文档；跨会话、多人协作或需要持续跟踪的工作使用持久计划。

- **文档职责**：规格定义行为与验收，设计说明方案与边界，架构决策记录（ADR）保存长期取舍；格式校验不代替内容审查。
- **项目进度只维护一份**：任务默认写在计划内，必要时移到唯一的任务附件；任务描述可验证成果，不抄录客户端的临时执行步骤。
- **记录实际结果**：智能体核对事实后更新任务与计划摘要。`status` 只读，不运行检查、不写入状态；任务全部勾选不代表已验证、已审查或已交付。
- **保留长期有效的信息**：已完成计划作为变更记录保留；当前有效的要求和结论写入规格、设计、架构决策记录或指南。稳定 ID、正向引用和文档导航便于在切换会话或客户端后继续工作。

项目测试、代码静态检查、构建与缓存由项目的 justfile、Makefile、项目配置清单或持续集成（CI）管理；`.tao/config.toml` 仅保存文档配置，`tao verify` 只校验文档。执行结果写回计划，不在 tao 重复注册命令。

## 项目安装

复制完整 `skills/tao-dev/` 到目标项目的发现目录，无需 Python 或安装器：

| 客户端 | 项目目录 |
|---|---|
| Codex / Cursor | `.agents/skills/tao-dev/` |
| Claude Code | `.claude/skills/tao-dev/` |
| Kiro | `.kiro/skills/tao-dev/` |

例如在本仓库为 Codex / Cursor 复制；先确认项目已存在、目标路径没有指向项目外的符号链接：

```sh
mkdir -p /path/to/project/.agents/skills
test ! -e /path/to/project/.agents/skills/tao-dev &&
test ! -L /path/to/project/.agents/skills/tao-dev &&
cp -R skills/tao-dev /path/to/project/.agents/skills/tao-dev
```

同一客户端不要放置重复副本。更新前保存本地改动，再完整替换旧目录，避免叠加复制遗留废弃文件；移除时只删除技能目录，不删除项目文档或配置。来源与版本由项目 Git 或所选安装工具记录；手工复制不提供本地修改保护或失败回滚。

也可自行使用 [通用 skills 命令行工具](https://github.com/vercel-labs/skills)，在目标项目内显式选择技能、客户端与项目作用域；它不是 tao 的依赖。具体用法、副本更新与移除及验证边界见 [客户端接入](docs/user/clients.md)。

只有运行辅助命令才需要 Python 3.11–3.14。显式创建项目 `.venv` 并安装该技能的 `scripts/requirements.txt`；构建 HTML 另需 `scripts/requirements-publication.txt`。使用所选环境的 Python 调用技能所在目录的 `scripts/tao.py`，不依赖全局启动程序，也不因读取或复制技能而自动准备依赖。

## 常用用法

### 在智能体中使用

技能被客户端发现后，可以直接用自然语言说明目标、文档范围和操作限制：

| 场景 | 示例提示 |
|---|---|
| 查找约定 | 使用 tao-dev，查找导出取消行为的规格、设计和相关决策，列出权威来源。 |
| 更新文档 | 使用 tao-dev，更新导出功能的取消行为约定；复用现有规格与设计，不为小改动新建整套文档。 |
| 恢复项目进度 | 使用 tao-dev，读取我指定的计划，核对当前文件与验证结果，列出剩余任务和阻塞，不直接开始实施。 |
| 回写成果 | 使用 tao-dev，将本次实际完成的工作、验证范围和未覆盖项写回现有计划，不把任务完成当作交付通过。 |
| 语义审查 | 使用 tao-dev，审查 docs/product/ 下的规格，核对依据与一致性；只报告问题，不修改文件。 |
| 格式校验 | 使用 tao-dev，校验项目受管理文档，报告实际检查范围；不要运行业务测试或构建。 |

支持自动选择技能的客户端可根据任务与技能描述匹配；是否实际触发取决于客户端版本、配置和加载状态。需要明确选择时：

| 客户端 | 显式调用示例 |
|---|---|
| Claude Code | `/tao-dev 审查 docs/product/ 下的规格，只报告问题` |
| Codex CLI / IDE 扩展 | `$tao-dev 审查 docs/product/ 下的规格，只报告问题`，或通过 `/skills` 选择 |
| Cursor / Kiro | 使用客户端提供的技能选择入口，或明确要求“使用 tao-dev”；不要假定所有客户端都支持 `/tao-dev` |

调用语法依据 [Claude Code skills](https://code.claude.com/docs/en/skills) 与 [Codex skills](https://developers.openai.com/codex/skills)，不代表本项目已实测所有客户端版本。tao-dev 没有固定的技能参数或子命令协议；调用后的文字是任务要求，不是直接传给 Python 脚本的参数。Claude Code 即使没有 `$ARGUMENTS` 占位符，也会将附加文字传给技能。

tao-dev 不自带或注册客户端事件钩子（hook）。加载技能不会自动安装依赖、运行检查或在编辑后回写计划；这些操作由智能体在已授权的任务范围内执行。若另行配置客户端 hook 调用辅助脚本，其触发条件和权限由客户端管理。

### 直接运行辅助命令

以下为 POSIX shell 示例，在项目根目录执行，前提是已显式准备 Python 环境及依赖。`SKILL` 必须指向实际加载的技能目录；Claude Code 使用 `.claude/skills/tao-dev`，Kiro 使用 `.kiro/skills/tao-dev`，在本源码仓库直接使用 `skills/tao-dev`。Windows 使用项目环境的 `.venv/Scripts/python.exe` 调用相同脚本。

```sh
PY=.venv/bin/python
SKILL=.agents/skills/tao-dev

# 只读查看可用能力与计划进度
"$PY" "$SKILL/scripts/tao.py" --project . doctor --format json
"$PY" "$SKILL/scripts/tao.py" --project . status --format json

# 按项目配置校验文档，不运行项目测试
"$PY" "$SKILL/scripts/tao.py" --project . verify --format json

# 读取计划格式及中文模板；只输出 JSON，不创建文件
"$PY" "$SKILL/scripts/read_profile.py" plan --locale zh-Hans
```

需要写入时，分别显式执行以下命令，不必按顺序运行：

```sh
# 创建计划草稿；仍需补全内容，不创建规格或设计
"$PY" "$SKILL/scripts/tao.py" --project . new --slug export-cancel --locale zh-Hans

# 构建本地 HTML；需出版依赖及已配置的 documents.book_root，不部署
"$PY" "$SKILL/scripts/tao.py" --project . docs build --format json
```

`status` 可追加计划的 CHG、DOC 或项目相对路径。`status`／`show` 返回 `partial` 时，应核对诊断与 `outputs.documents_valid`，不能仅凭退出码认定文档有效。更多查询、ID 分配、配置和退役命令见 [工具入口](skills/tao-dev/references/tools.md)，环境准备见 [运行环境](skills/tao-dev/references/runtime.md)。

## 支持与验证边界

文件部署、客户端发现与模型行为需要分别验证；官方规定的目录不能证明技能已实际运行。只有实际执行的组合才可报告通过，缺少客户端、认证或依赖时应明确标为未运行。参见 [兼容性边界](docs/engineering/client-compatibility.md)。

## 开发与文档

从 [AGENTS.md](AGENTS.md) 与 [开发指南](docs/engineering/development.md) 开始。显式准备项目环境后，`just check` 执行代码检查及锁定依赖导出核对，`just docs` 校验并构建文档，`just package <新目录>` 打包完整技能。

- [文档协作指南](docs/user/workflow.md)
- [文档书籍入口](docs/index.md)
- [当前技能规格](docs/product/project-skill.md) · [设计](docs/engineering/project-skill.md) · [文档管理计划](docs/plans/2026-11/20261108-document-management.md)
- [共享技能](skills/tao-dev/SKILL.md)

## 许可

见 [LICENSE](LICENSE)。
