---
schema: tao.project.design/v0.1
id: DOC_20260915_P8J10N4KDFYZY2EN
title: 项目 skill 安装与卸载
locale: zh-Hans
status: draft
created: "2026-09-15"
updated: "2026-09-18"
spec_docs: ["DOC_20260914_E1B61A3F8V1TYAZB"]
---

# 项目 skill 安装与卸载

<!-- tao:section overview -->
## 目标与范围

只向明确项目的原生 skill 目录部署文件。install、upgrade、list、uninstall 不要求文档或出版依赖，不调用客户端插件命令，不修改用户目录和外部项目。用户接口见 [接入指南](../user/clients.md)。

<!-- tao:section architecture -->
## 组件与数据流

tao.py 在可选文档依赖导入前分派安装管理。安装器使用标准库解析本地仓库或完整 skill 来源，按显式 client 映射项目目录，记录管理文件及来源；`.tao-install.json` 位于每份受管 skill 内。四个适配为 claude、codex、cursor、kiro。list 默认只列当前项目四种客户端，不使用全局索引。

<!-- tao:section contracts -->
## 命令

`python skills/tao-dev/scripts/tao.py <install|upgrade|list|uninstall> --project <已存在目录> --client <client>`。list 可省 client；install/upgrade 可提供 --source <仓库或skill>，默认运行中的 skill。支持 --format json。不存在 scope、all、yes 参数。

安装内容为 SKILL.md、references、assets、scripts，不含 hook、native plugin、marketplace 或全局 launcher。读取 skill 不需要 Python；运行安装器需要 Python；文档命令才需要显式准备的解析依赖。

<!-- tao:section invariants -->
## 所有权与事务

拒绝路径逃逸、符号链接、不归属内容与被用户修改的管理文件；不以强制覆盖解决冲突。失败回滚本次管理文件，保留先前安装和无关用户内容。卸载仅移除验证归属的安装，不删除 docs、计划或业务文件；不改变其他 client、项目或用户配置。

<!-- tao:section verification -->
## 验证范围

在临时项目和隔离用户目录中验证安装、重复升级、列表、卸载、修改保护、符号链接与失败回滚。文件部署与真实客户端发现是不同验收；缺 CLI/认证不能声称运行兼容。源包切换不能操作维护者已有全局部署。
