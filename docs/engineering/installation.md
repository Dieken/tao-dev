---
schema: tao.project.design/v0.1
id: DOC_20260915_P8J10N4KDFYZY2EN
title: 项目 skill 分发与接入
locale: zh-Hans
status: draft
spec_docs: ["DOC_20260914_E1B61A3F8V1TYAZB"]
---

# 项目 skill 分发与接入

<!-- tao:section overview -->
## 目标与范围

分发完整文档与知识管理 skill，包含持久计划能力而非通用开发编排，接入只发生在明确项目内。手工复制是无安装器依赖的基线，通用 skills 工具是可选便利方式；tao 不实现安装生命周期。用户操作见 [接入指南](../user/clients.md)。

<!-- tao:section architecture -->
## 组件与数据流

`scripts/package_skill.py` 从 canonical `skills/tao-dev/` 产生完整包，排除开发缓存。使用者把包复制到客户端项目发现目录，或委托通用工具处理。CLI 只提供文档、ID、计划与校验等领域功能；包内不维护所有权清单或客户端安装适配。

<!-- tao:section contracts -->
## 接入与依赖

发现目录由客户端约定，不是 Agent Skills 格式或 Agent Plugins 打包标准统一的安装协议。Codex 与 Cursor 可共享 `.agents/skills/tao-dev/`；Claude Code 与 Kiro 使用各自项目目录。只维护一份 skill 内容，不新增 plugin 包装层。

包内保留 SKILL.md、references、assets、scripts。阅读和复制不需要 Python；调用辅助脚本才需要受支持的 Python，文档和出版依赖分别显式准备。通用安装工具不是运行依赖，也不由 tao 包装调用。

<!-- tao:section invariants -->
## 文件与版本责任

手工复制前由使用者确认目标是授权项目内的新目录，避免覆盖改动或经符号链接写出项目。来源和版本交给项目 Git 或所选工具记录；更新先备份，再完整替换，不叠加复制；移除只针对 skill 副本，不删除项目文档、配置或其他 skill。手工复制不提供自动修改检测或回滚，第三方工具的保证以其实现为准。

<!-- tao:section verification -->
## 验证范围

在临时项目和隔离用户目录中验证完整复制、复制后 CLI 与移除，确认源包、项目文档、外部项目和用户配置保持不变。打包完整性继续由源码测试覆盖。真实客户端发现另行选择运行，同时检查项目内可见、项目外缺席及移除后不可见；未运行不能声称兼容，模型行为也不能由文件部署替代。
