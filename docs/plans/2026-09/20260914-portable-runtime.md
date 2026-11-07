---
schema: tao.project.plan/v0.1
id: DOC_20260914_3541E3H7SN5V7MS5
title: 可独立准备的插件运行环境
locale: zh-Hans
status: draft
created: "2026-09-14"
change: CHG_20260914_3RC5QW89C26B69MA
spec_docs: ["DOC_20260914_E1B61A3F8V1TYAZB"]
design_docs: ["DOC_20260915_P8J10N4KDFYZY2EN", "DOC_20260914_7RJ1YVEC0CP478BY"]
updated: "2026-09-17"
---

# 可独立准备的插件运行环境

<!-- tao:section scope -->
## 目标与边界

落实无需 uv 的插件运行与明确的作用域边界；实施依赖统一、标准库启动与环境准备、两端接入和隔离验收。保留现有文档格式及业务命令，不引入插件安装器、系统 Python 下载器或后台服务。

<!-- tao:section references -->
## 规格依据

{need}`DOC_20260914_E1B61A3F8V1TYAZB`。

<!-- tao:section design -->
## 设计

设计依据：{need}`DOC_20260915_P8J10N4KDFYZY2EN`；{need}`DOC_20260914_7RJ1YVEC0CP478BY`。

开发依赖在 pyproject.toml 唯一定义，uv.lock 锁定；核心及核心加出版两份 requirements 自动导出。开发使用 .venv，发布包无需 uv 或开发目录。

标准库入口在导入 taolib 之前处理 setup、doctor 和执行环境选择。TAO_RUNTIME_DIR 优先于客户端数据目录；Claude 使用 CLAUDE_PLUGIN_DATA，其他适配采用明确的用户数据目录。TAO_PYTHON 选择基础解释器，不向该解释器安装包。正常运行不联网安装。依赖缺失时输出诊断；未配置项目的 hook 保持无操作。

环境按依赖清单、Python 和平台隔离。采用排他准备和有界等待；在最终路径创建独立代次，验证后发布选择记录；失败不切换、不删除已完成环境。管理员安装和操作系统部署不属于本轮范围。

CLI 启动范围不替代客户端插件 scope。两端验收采用隔离的客户端配置目录；Codex 默认禁用插件、仅试验项目启用，以原生发现与模型行为共同检查边界。针对 0.154.0 的 hook 加载差异，生成单独兼容包，保留一份公共元数据与运行源码；未验证的个人配置模式保持阻断。

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

本节保存有固定版本、平台和包格式的历史验收结果；不表示当前版本自动取得同样保证。核心交付和必需审查限制见[交付记录](20260914-bootstrap.md#DOC_20260914_8MPMXBCGKMRS74T4--verification)，执行入口见[客户端验收](../../../tests/acceptance/README.md)。

### 核心与平台

固定实现树224d104db374484f9e739b869535ba239a749bed在macOS/Python3.12.13执行139项回归通过，Ruff、依赖一致性与HTML通过，78个稳定标识符入口有效。实际261.3秒的检查超过原150秒上限，因此当时采用330秒单项、360秒总预算；覆盖率54.91%未完整观测隔离子进程，不表示路径未执行。

同一受检提交b59329d的离线准备、出版、CLI、hook与本地化专项在macOS x86_64的Python3.11.15/3.13.15/3.14.7及Linux容器Python3.12.14分别49项通过；不是原生模型行为验收。Linux固定镜像为docker.io/library/python@sha256:2fe5997d249a808b8eeea52c58a1dbffbba28754dc11699ef5c029f2d818ce79。

提交dd567c6的GitHub Actions run 35229860576补齐三平台CPython3.11–3.14十二格维护回归：

| 环境 | 实测结果 |
|---|---|
| windows-2025-vs2026／CPython 3.11.9、3.12.10、3.13.15、3.14.7 | 四格各 435 项通过、5 项跳过，816–926 秒；修复三处 Windows 专有缺陷后通过：hook 命令按路径而非字节比较、隔离子进程以 `-X utf8` 运行、受记录解释器改为链接解释器主目录 |
| macos-26-arm64／CPython 3.11–3.14 | 四格各 435 项通过、5 项跳过，340–477 秒；首次覆盖 arm64 |
| ubuntu-24.04／CPython 3.11–3.14 | 四格各 435 项通过、5 项跳过，326–417 秒 |

同一run在三平台以无凭据模式执行Claude Code2.1.274与codex-cli0.154.0的15项原生安装探针并通过，覆盖安装、范围、重复更新、回滚和移除。该结果不含模型会话、hook模型反馈或PowerShell安装器，原生Windows客户端行为仍未验收。

### Codex限定版本与包格式

macOS x86_64、Python3.12.13、Codex0.154.0；运行资源与9cd5449相同。配置模型为gpt-6-astra/openai，事件未独立确认服务端模型或费用。公共包与codex-legacy包使用相同skill及契约，各例在独立客户端状态内运行。

| 场景 | 实际观察 |
|---|---|
| 公共包项目内调用 | 原生发现 tao-dev:tao-dev；读取必需规程，使用已准备的环境执行 doctor/status，均退出 0 |
| 公共包审查与恢复 | 独立上下文实际复现覆盖文件；恢复保留计划和 ID，旧证据过期后执行回归并完成验证；分别 51.210 与 109.599 秒 |
| 兼容包原生 hook | 原生 apply_patch 创建无效文档，模型未手工检查；收到 TAO-DOC-001，缓存记录一致 |
| 兼容包禁用 hook 后恢复 | 无 hook 缓存；仅修改实现及原计划，保留 ID 和测试条件；回归退出 0，完整 verify 为 complete／checks-satisfied |
| 项目外对照 | 公共包和兼容包的模型均未使用工具，返回不可用；原生技能及 hook 清单确认项目外无受测组件；兼容包 13.005 秒 |
| 安装生命周期 | 原生安装、禁用、重新启用、更新和卸载后，技能及 hook 发现符合实际版本和作用域；改变 hook 定义后旧信任失效；独立调用，不启动模型 |

公共包未触发hook，不计hook通过；兼容包才提供实测反馈。九例监测配置未变，认证副本无刷新令牌且已清理。恢复样例由宿主核对原脚本、需求、配置与ID未改；退出0本身不构成验收。

### Claude限定版本与作用域

macOS x86_64、Python3.12.13、Claude Code2.1.268、既有模型claude-opus-5；来源字段为canonicalModel/firstParty，不据此另推供应商。核心运行资源与5dc525d相同，四个操作入口的规程读取修正另按6765cef验收。三种scope均使用独立CLAUDE_CONFIG_DIR，只复用访问令牌。

| 场景 | 实际观察 |
|---|---|
| project 的 status 与原生 hook | 实际 Skill 调用 status，doctor/status 退出 0；原生 Write 收到 TAO-DOC-001，模型未手工检查 |
| project 禁用 hook 后恢复 | 150.124 秒；无 hook 缓存，实际识别旧证据，修复覆盖缺陷并完成回归与完整 verify |
| user／local 恢复 | 原生 skill 与 hook 工作，完整 verify 为 complete／checks-satisfied |
| 作用域对照 | project／local 的项目外初始化清单与模型均不可见；user 在同一试验配置的其他目录可见，符合其作用域；三例均未使用工具 |
| 原生 verify | 61.037 秒；真实失败基线得到失败报告及阻断状态，未修复代码或勾选任务，符合验证专用场景 |
| new → handoff | 最终低推理强度案例 133.327 秒完成；实际调用两个原生 Skill 并读取工程规程，计划与交接同一 CHG、两个任务未勾选；宿主复核文档、源文件和插件副本，配置与凭据监测未变 |
| reviewer | 重验 89.325 秒；复现覆盖问题，源文件不变，复现目录在 tmp/tao 且自动清理；最小建议保留默认编码并说明新增异常及类型边界 |
| 三种安装生命周期 | 分别实际安装、禁用、启用、更新到试验版本 0.1.1、卸载；每步原生状态与范围、缓存路径一致；未调用模型 |

保留的失败边界：初次reviewer越出复现目录并建议改变编码，不计完整边界通过；两次默认强度new→handoff超过240秒，不能用低强度案例的完成保证默认时延。一次低强度plan监测到个人.claude.json变化，来源不能确认，该例隔离不通过；入口修正后的status和new→handoff重验观察到必读规程且配置/凭据未变。不得把这些失败改写为通过或猜测回滚个人文件。

未完成调用的费用不能按零计算，CLI估算不等于真实账单；本节不作为账户费用或后续预算依据。

### 最终历史判定与审查限制

| 固定输入 | 维护检查 | 完整交付状态 |
|---|---|---|
| 6765cef | 218项通过，346.05秒；代码检查349.677秒，Ruff/Node.js/HTML通过 | 限定版本macOS双端组合验收完成；未完成任务和必需审查仍阻断 |
| ea41a62 | 229项通过，306.94秒；代码检查310.181秒，Ruff/Node.js/HTML通过 | 覆盖率62.80%受隔离观测限制；完整verify仍not_run/blocked |

固定树1e75ed31c7a7494175561a4afb1968f68fc202f4的十八文件只读Claude审查在240.152秒超时，退出143；草稿有额外rationale_note字段且缺最终result，被拒绝，没有可导入结论。配置/凭据监测未变，费用未知。草稿提出的权限、路径匹配和凭据失败诊断问题已由本地反例修复；这不把草稿转为有效审查，也不证明曾有令牌泄漏。

原始日志、模型事件与快照不纳入VCS，不保证长期可还原。历史结论不因材料清理而撤销，但不复用为当前通过。原生Windows客户端行为与当前输入的有效独立审查仍未完成，保证只覆盖本节明确列出的版本、包格式、平台和合成场景。

<!-- tao:section questions -->
## 待确认事项

无。
