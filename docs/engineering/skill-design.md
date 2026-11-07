---
schema: tao.project.design/v0.1
id: DOC_20260914_7RJ1YVEC0CP478BY
title: 技能打包与运行依赖
locale: zh-Hans
status: draft
spec_docs: ["DOC_20260914_4C7N0XHQSP7CY69P", "DOC_20260914_E1B61A3F8V1TYAZB"]
---

# 技能打包与运行依赖

<!-- tao:section overview -->
## 分发边界

产品是项目级文档与知识管理技能，源码位于 `skills/tao-dev`。分发只包含用户项目中的智能体实际读取的 [SKILL.md](../../skills/tao-dev/SKILL.md)、`references`、`assets` 和执行需要的 `scripts`，覆盖文档生命周期与持久项目计划。内部规格、设计、计划、通用工程开发规程、研发测试及研究资料不打包；共享资源必须确有读者或运行时调用方。稳定 ID、结构化文档与文档出版能力保留。

<!-- tao:section architecture -->
## 包与入口

`scripts/package_skill.py --output <新目录>` 复制技能的权威源码目录 `skills/tao-dev`，`just package <新目录>` 提供同一入口。完整包可手工复制到指定项目的技能发现目录，或由使用者选择通用工具；具体边界见 [分发设计](installation.md)。

[SKILL.md](../../skills/tao-dev/SKILL.md) 按需加载文档语义、持久计划、文档审查与工具参考，不能依赖开发仓库的 `docs` 才能完成使用方的文档工作，也不携带通用实现或代码审查动作。模板和文档注册表来自同包，不另维护客户端专用版本。

<!-- tao:section contracts -->
## 依赖与执行

阅读与复制技能不需要 Python 或文档解析库。辅助命令使用调用者选择的 Python；明确需要时在项目 `.venv` 安装 `scripts/requirements.txt`，HTML 出版额外使用 `scripts/requirements-publication.txt`。没有 `env prepare` 或自动依赖下载，不写入系统 Python、用户数据目录或业务环境。

开发依赖由 `pyproject.toml` 与 `uv.lock` 锁定，发布依赖清单由现有导出工具产生并核对一致性；读取技能不触发这些工具。缺少依赖而不可用的功能由 `doctor` 和实际错误明确报告。

<!-- tao:section invariants -->
## 保证

构建包不包含维护者临时文件与外部项目资料。源码与已安装资源使用相对链接；包内引用不得依赖本机绝对路径。平台支持依赖实测而非清单声明，文件复制成功不等于真实模型行为成功。

<!-- tao:section verification -->
## 验证

在仓库外检查完整包的资源、引用、项目复制路径及使用显式依赖环境的 CLI。真实客户端按 [兼容边界](client-compatibility.md) 分层报告实际运行结果与未覆盖项。
