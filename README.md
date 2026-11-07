# tao-dev · 协作开发之道

项目级、文档驱动的 coding-agent skill：明确需求，选择简单设计，以计划推进实现，用真实检查支持结论，留下可维护的长期知识。

## 开发主线

**new（spec → design → plan）→ review doc → implement → review code**，支持 refine、status、continue、handoff。

在目标项目加载 tao-dev 后，可以直接说：

> 使用 tao-dev，为导出功能增加取消操作；完成规格、设计、计划、文档审查、实现和代码审查。

已有授权内连续推进，不要求逐篇文档批准或 workflow 注册。每个动作给出实际结果和下一步选项；安装和使用限定在目标项目内。

- **结构化知识**：保留现有文档 profile、稳定 ID、正向引用与 Sphinx book；章节按实际需要组织，不强制无关内容。
- **唯一进度来源**：任务内联 plan 或唯一 tasks 附件；status 只读，不跑检查、不写状态。任务全勾选不代表已审查或已交付。
- **轻量记录**：长期结论回到规格、设计、ADR；计划只存当前结果摘要。详细 review/evidence 默认临时，不自动建报告或提交。
- **无状态恢复**：continue 核对计划和实际文件；显式 handoff 只替换一份临时 Markdown，不是恢复前置条件。

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

同一客户端不要放置重复副本。更新前保存本地改动，再完整替换旧目录，避免叠加复制遗留废弃文件；移除只针对 skill 目录，不删除项目文档或配置。来源与版本由项目 Git 或所选安装工具记录；手工复制没有修改保护或失败回滚。

也可自行使用 [通用 skills CLI](https://github.com/vercel-labs/skills)，在目标项目内显式选择 skill、客户端与项目作用域；它不是 tao 的依赖。具体用法、旧副本迁移及验证边界见 [客户端接入](docs/user/clients.md)。

只有运行辅助命令才需要 Python 3.11–3.14。显式创建项目 `.venv` 并安装该 skill 的 `scripts/requirements.txt`；构建 HTML 另需 `scripts/requirements-publication.txt`。使用所选环境的 Python 调用实际 skill 的 `scripts/tao.py`，不依赖全局 launcher，不因读取或复制 skill 自动准备依赖。

## 支持与验证边界

文件部署、客户端发现与模型行为是不同层次；官方目录依据不证明 skill 的真实运行。只有实际执行的组合才可报告通过，缺客户端、认证或依赖明确标为未运行。参见 [兼容性边界](docs/engineering/client-compatibility.md)。

## 开发与文档

从 [AGENTS.md](AGENTS.md) 与 [开发指南](docs/engineering/development.md) 开始。显式准备项目环境后，`just check` 执行代码检查及锁定依赖导出核对，`just docs` 校验并构建文档，`just package <新目录>` 打包完整 skill。

- [用户工作方式](docs/user/workflow.md)
- [文档书籍入口](docs/index.md)
- [当前纯 skill 规格](docs/product/project-skill.md) · [设计](docs/engineering/project-skill.md) · [实施计划](docs/plans/2026-11/20261108-project-skill.md)
- [共享 skill](skills/tao-dev/SKILL.md)

## 许可

见 [LICENSE](LICENSE)。
