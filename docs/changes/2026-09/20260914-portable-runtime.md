---
schema: tao.project.change/v0.1
id: DOC_20260914_3541E3H7SN5V7MS5
title: 可独立准备的插件运行环境
locale: zh-Hans
status: draft
created: "2026-09-14"
change: CHG_20260914_3RC5QW89C26B69MA
---

# 可独立准备的插件运行环境

<!-- tao:section scope -->
## 目标与边界

落实无需 uv 的插件运行与明确的作用域边界；实施依赖统一、标准库启动与环境准备、两端接入和隔离验收。保留现有文档格式及业务命令，不引入插件安装器、系统 Python 下载器或后台服务。

<!-- tao:section references -->
## 规格引用

需求见 [插件运行环境](../../product/runtime.md)，长期决定为 {need}`ADR_20260914_Z19W6HRG4MWQM97A`。

<!-- tao:section design -->
## 设计

开发依赖在 pyproject.toml 唯一定义，uv.lock 锁定；核心及核心加出版两份 requirements 自动导出。开发使用 .venv，发布包无需 uv 或开发目录。

标准库入口在导入 taolib 之前处理 setup、doctor 和执行环境选择。TAO_RUNTIME_DIR 优先于客户端数据目录；Claude 使用 CLAUDE_PLUGIN_DATA，其他适配采用明确的用户数据目录。TAO_PYTHON 选择基础解释器，不向该解释器安装包。正常运行不联网安装。依赖缺失时输出诊断；未配置项目的 hook 保持无操作。

环境按依赖清单、Python 和平台隔离。采用排他准备和有界等待；在最终路径创建独立代次，验证后发布选择记录；失败不切换、不删除已完成环境。管理员安装和操作系统部署不属于本轮范围。

CLI 启动范围不替代客户端插件 scope。先验证运行核心，再用隔离的客户端配置目录验收真实 Claude scope；无法保证隔离的 Codex 模式保持阻断。

<!-- tao:section tasks -->
## 任务

- [x] `TASK_20260914_FZVY1ESMP2EANWMG` 统一开发依赖与发布清单
  - relates: ["REQ_20260914_W1NDXAS6DMV7D7HH", "CHG_20260914_3RC5QW89C26B69MA"]
  - depends_on: []
  - verify: 锁文件与导出清单一致；现有测试、源码检查及书籍构建通过。
  - evidence: [本计划验证](20260914-portable-runtime.md#DOC_20260914_3541E3H7SN5V7MS5--verification)

- [x] `TASK_20260914_XGJCX0D6XA3PV3SP` 实现独立运行环境与诊断
  - relates: ["REQ_20260914_GH69P66HSM6HDZXF", "CHG_20260914_3RC5QW89C26B69MA"]
  - depends_on: ["TASK_20260914_FZVY1ESMP2EANWMG"]
  - verify: 无 uv、缺依赖、准备失败、并发、版本隔离、只读安装和离线执行的行为测试通过。
  - evidence: [本计划验证](20260914-portable-runtime.md#DOC_20260914_3541E3H7SN5V7MS5--verification)

- [x] `TASK_20260914_YT79BXFY4CDDM2K3` 统一 CLI、skill 与客户端 hook 入口
  - relates: ["REQ_20260914_WAHF2CDHEJFSBGDC", "CHG_20260914_3RC5QW89C26B69MA"]
  - depends_on: ["TASK_20260914_XGJCX0D6XA3PV3SP"]
  - verify: 所有入口共享定位规则；项目外无操作、缺环境不误报成功、核心无需 Sphinx。
  - evidence: [本计划验证](20260914-portable-runtime.md#DOC_20260914_3541E3H7SN5V7MS5--verification)

- [ ] `TASK_20260914_35YA18HM8H3TFVAA` 完成独立包及客户端作用域验收
  - relates: ["REQ_20260914_5PFGD8NJKSAVG2NT", "CHG_20260914_3RC5QW89C26B69MA"]
  - depends_on: ["TASK_20260914_YT79BXFY4CDDM2K3"]
  - verify: 发布副本无需开发仓库；真实客户端各范围执行与反例验收，未支持项如实保留。

<!-- tao:section verification -->
## 验证

基线为 `40666bb`。按各任务的可观察场景先增加反例，再实现并重验；完整 verify 保留既有独立审查凭据要求。实际结果在本节追加简短记录，详细日志仅放 tmp/tao/。

依赖增量：基于 `8d17e36` 后的依赖、导出脚本和 README 差异，在本机 Python 3.12.13 执行锁定环境测试，126 项通过；两份发布清单导出一致，实际 Sphinx 构建通过。原始输出仅保存在临时目录，不代表其它平台已验证。

运行环境增量：在 `37faf4e` 后的启动层与测试差异上执行 9 项真实环境测试，覆盖无 uv、空 PATH、只读插件、失败恢复、并发准备和目录越界；均通过。原有 CLI 与 hook 回归 22 项通过。环境安装使用发布清单匹配的离线 wheel；仅验证本机 macOS / Python 3.12。

入口增量：在 ae3e20f 后的 CLI、启动器、校验器和 hook 差异上执行 32 项回归，全部通过；包括无 Python 时项目外无操作、项目内明确未执行，以及 doctor 发现独立出版环境。Ruff 错误检查通过；PowerShell 文件已提供，但未在 Windows 执行。

<!-- tao:section questions -->
## 未决问题

Podman 当前探测受本机目录写入权限限制，不能据此声称跨操作系统已验收。Codex 既有实验会修改用户信任配置的问题仍需保持隔离边界。

