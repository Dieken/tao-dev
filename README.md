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

需要 Python 3.11–3.14；阅读 skill 无需 Python 或出版依赖。在本仓库运行：

```sh
python3 skills/tao-dev/scripts/tao.py install --project /path/to/project --client codex
python3 skills/tao-dev/scripts/tao.py list --project /path/to/project
python3 skills/tao-dev/scripts/tao.py upgrade --project /path/to/project --client codex --source /path/to/new-checkout
python3 skills/tao-dev/scripts/tao.py uninstall --project /path/to/project --client codex
```

支持 `claude`、`codex`、`cursor`、`kiro`，分别部署到项目 `.claude/skills/tao-dev`、`.agents/skills/tao-dev`、`.cursor/skills/tao-dev`、`.kiro/skills/tao-dev`。install/upgrade/uninstall 显式选 client；list 可列本项目全部四种。不修改用户配置或其他项目。客户端可能按自身规则发现其他原生目录，不承诺同一项目内仅一个客户端可见。

install/upgrade 的 --source 接受本地仓库或完整 skill，省略使用当前运行副本；升级前取得新源码。根 install.sh/install.ps1 可从本地源码或临时抓取的仓库转交同一安装器。修改过的受管文件、未知文件和符号链接会阻止覆盖或卸载；先保存个人改动，不能强制删除。卸载不删除项目文档。

安装只用标准库，不自动准备依赖。需要文档辅助命令时，显式创建项目 `.venv` 并安装该 skill 的 `scripts/requirements.txt`；构建 HTML 另需 `scripts/requirements-publication.txt`。使用所选环境的 Python 调用实际 skill 的 scripts/tao.py，不依赖全局 launcher。详见 [客户端接入](docs/user/clients.md)。

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
