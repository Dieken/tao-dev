---
schema: tao.project.user-guide/v0.1
id: DOC_20260915_EGTG403AY0XK9WME
title: 开发与维护指南
locale: zh-Hans
status: draft
created: "2026-09-15"
updated: "2026-11-08"
---

# 开发与维护指南

<!-- tao:section scope -->
## 目标与边界

本仓库独立维护。先读 [AGENTS.md](../../AGENTS.md) 与 [skill 源码](../../skills/tao-dev/SKILL.md)，不需安装到个人客户端。开发文档留 docs，产品分发只含 skills/tao-dev 的运行资源。

<!-- tao:section prerequisites -->
## 显式环境准备

开发需要 uv 与 Python 3.11–3.14。使用 `uv sync --no-config --locked --extra publication` 准备项目 .venv；所有 uv 调用加 --no-config，避免机器镜像改写锁文件。依赖由 pyproject.toml 与 uv.lock 管理。读取 skill、安装文件不要求准备出版依赖。

<!-- tao:section steps -->
## 常用操作

- `just check`：配置的代码检查及锁定依赖导出核对。
- `just docs`：显式文档校验与书籍构建。
- `just package <新输出目录>`：调用 scripts/package_skill.py --output 生成纯 skill 包。
- `just tao <参数>`：调用源码辅助 CLI；也可用 `.venv/bin/python skills/tao-dev/scripts/tao.py`。
- 回归：在显式准备的项目环境执行维护测试；运行范围与结果如实记录，不把未运行的客户端测试写成通过。

recipe 不自动准备运行环境，没有 env prepare 前置步骤。真实客户端试验必须显式运行并限定隔离项目；当前 Codex 发现检查无需登录，不调用模型、不复用认证，也不修改个人安装或用户级配置。原生插件安装探针不再是项目 skill 的验收依据。

## 文档与交付

长期要求、设计、ADR 与操作知识更新原文档，保留对象 ID；new 文档挂入 book。任务及当前验证摘要仅在 plan/tasks，详细输出默认 tmp/tao，不自动建立审查报告或提交。实现集成后统一执行必要验证，计划记录实际范围、结果和限制；任务完成不是交付认证。
