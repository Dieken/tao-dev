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

受检实现树为 `224d104db374484f9e739b869535ba239a749bed`；平台为 macOS，Python 3.12.13。配置检查执行 139 项测试全部通过，Ruff 错误检查通过；清单与锁文件导出一致。测试包含真实离线环境准备、无 uv／空 PATH、只读插件、并发和失败恢复、独立校验器、出版副本，以及缺依赖诊断协议。实际总检查用时 261.3 秒；测试上限为 330 秒，总预算为 360 秒，避免真实 venv 测试被原 150 秒上限截断。

Coverage.py 观察值为 54.91%，覆盖范围包含启动脚本；隔离 Python 子进程不安装 coverage，也不为提高数字关闭隔离，因此该数值不是全部执行路径的完整观测。实际 Sphinx 构建通过，78 个稳定标识符的出版链接检查通过。

| 客户端范围 | 实际结果 |
|---|---|
| Claude Code 2.1.268 user／project／local | 三种原生安装均使用独立配置目录，初始化事件验证了项目内外加载边界，监测的个人配置未变；隔离配置无认证，模型执行未通过 |
| Claude 调用级插件 | 既有认证下，实际发现并调用 status 操作，doctor 正确区分核心可用／出版未准备；原生 Write 触发文档错误反馈，项目外不发现 tao-dev；三例监测的个人配置未变 |
| Codex CLI 0.154.0 | 既有版本会持久化全局项目信任；隔离守卫返回 blocked，未启动新的模型实验或注册插件 |
| 原生 Windows | 未实际验收；PowerShell 入口存在不代表客户端 hook 已兼容 |

Claude 三个完成的调用级案例返回模型 claude-opus-5、供应方 firstParty，CLI 标价合计 0.475711 美元；真实账单未知，不含未完成审查。两次独立只读审查基于固定实现快照，分别在 180 秒与 120 秒内未返回结论，不能算通过。首次审查期间，客户端自动刷新了既有官方市场的元数据时间戳；未发现 tao-dev 被全局注册，但该次监测不能声明完全无变化。后一次使用禁用自定义组件的安全模式，监测文件未变；不自动回滚无法还原的既有元数据，不再追加审查调用。

上述固定树验收的代码检查通过；当时总体为 not_run／readiness=blocked，原因包括最后一项验收未完成和必需审查缺失。审查记录接入已实现，后续执行与当前隔离限制见 [交付记录](20260914-bootstrap.md#DOC_20260914_8MPMXBCGKMRS74T4--verification)。最后一项任务继续保持未勾选，不以局部结果降低门槛。原始报告、模型事件及临时运行目录不纳入 VCS；本节只保存摘要。

同一受检提交 `b59329d` 的补充平台验收如下。每组执行 test_runtime.py、test_cli.py、test_hooks.py、test_diagnostics_locale.py，覆盖真实离线准备、无 uv、只读发布副本、失败恢复、出版、CLI 与短检查及本地化；不是原生客户端模型行为验收。

| 环境 | 实测结果 |
|---|---|
| macOS x86_64／CPython 3.11.15 | 49 项通过，192.76 秒；按锁文件使用 Sphinx 9.0.4 |
| macOS x86_64／CPython 3.13.15 | 49 项通过，160.91 秒；解释器及测试依赖仅置于项目临时目录，无全局可执行链接 |
| macOS x86_64／CPython 3.14.7 | 49 项通过，186.69 秒 |
| Linux x86_64 容器／CPython 3.12.14 | 49 项通过，129.22 秒；固定源码副本与官方 Python 镜像，包含无需 uv 的离线准备和出版 |
| Windows | 无真实测试环境，未执行；不以 POSIX 或路径模拟结果替代 |

Python 3.12.13 的维护环境已对同一提交完成全部 198 项回归，结果见 [核心能力验收](20260914-bootstrap.md#DOC_20260914_8MPMXBCGKMRS74T4--verification)。各环境安装发布依赖时校验锁定哈希；测试依赖与基础 Python 分离。Linux 镜像为 `docker.io/library/python@sha256:2fe5997d249a808b8eeea52c58a1dbffbba28754dc11699ef5c029f2d818ce79`；容器已删除，复用的虚拟机恢复停止状态，未安装系统 helper 或修改个人 CLI 配置。此矩阵说明已执行的组合，不宣称所有操作系统与 Python 版本组合均已验证。

<!-- tao:section questions -->
## 未决问题

后续验收需要可保持局部配置的 Codex 运行方式、原生 Windows 环境，以及可保持个人配置不变的独立审查执行方式。Claude 三种 scope 的加载结果不能替代各 scope 下完整流程的模型行为验收。
