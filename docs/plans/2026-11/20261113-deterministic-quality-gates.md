---
schema: tao.project.plan/v0.1
id: "DOC_20261113_RM0DWJJP6AND1RQ6"
title: "确定性质量门禁改进"
locale: "zh-Hans"
status: draft
change: "CHG_20261113_YBXS796DYVNWYQWG"
spec_docs: ["DOC_20260914_4C7N0XHQSP7CY69P"]
design_docs: ["DOC_20260914_0VF190409FQCN197"]
---

# 确定性质量门禁改进

<!-- tao:section scope -->
## 目标与边界

让 tao-dev 自身的 PR 门禁执行受管理文档校验，并用显式历史 ID 基线发现未经退役的删除；为文档诊断提供可选 SARIF 交换格式，为项目 CI 生成临时证据索引。保留现有 JSON 协议和 Markdown 文档模型，不引入外部需求管理工具，不让 tao 发现、调度或认证使用方项目检查。

<!-- tao:section references -->
## 规格引用

依据 {need}`REQ_20260914_42AXMZ2KH2RAZ8M3` 的确定性诊断、{need}`REQ_20260914_5Y6CWDE3MFMKJXSB` 的稳定 ID、{need}`REQ_20260914_0J68SDKV86ENKER2` 的当前证据边界，以及 {need}`REQ_20260914_95193C19C90NRXV4` 的项目级普通命令约束。CLI 结构沿用 [确定性文档与计划 CLI](../../engineering/cli-design.md)，结果保存沿用技能包的持久计划规程。

<!-- tao:section design -->
## 设计

`tao verify --baseline <项目相对 JSON>` 显式读取版本化 ID 清单；未提供基线时继续报告 `deletion_checked: false`，不猜测 Git 分支或出版目录。仓库 CI 从 PR 目标提交的独立检出目录生成清单，再验证当前文档。基线生成器属于本项目开发脚本，不进入技能分发包。

`tao verify --format sarif` 把同一批诊断映射为 SARIF 2.1.0；原生 JSON 继续承载文档计数和删除检查状态，SARIF 的 run properties 保留这些 tao 结果。其他命令拒绝 SARIF，避免把查询结果伪装成静态分析报告。

仓库 CI 在 `tmp/tao/evidence.json` 记录提交、运行环境、统一检查状态和已有附件路径。它只索引项目检查产物，不成为受管理文档，也不改变 tao CLI 的执行职责。

<!-- tao:section tasks -->
## 任务

- [x] `TASK_20261113_DP25XJYVJ3WW4H94` 接入显式文档 ID 基线和 PR 文档门禁
  - relates: ["REQ_20260914_42AXMZ2KH2RAZ8M3", "REQ_20260914_5Y6CWDE3MFMKJXSB"]
  - verify: 用有效、缺失和畸形基线运行 CLI，并检查 PR 工作流同时执行当前文档校验与目标提交删除校验
- [x] `TASK_20261113_R6F8E95EN2XFBJD0` 增加文档诊断的可选 SARIF 2.1.0 输出
  - relates: ["REQ_20260914_42AXMZ2KH2RAZ8M3"]
  - depends_on: ["TASK_20261113_DP25XJYVJ3WW4H94"]
  - verify: 对通过、文档错误和 CLI 输入错误运行 SARIF 输出，检查 schema、规则、位置、状态与退出码
- [ ] `TASK_20261113_Y8KHRD9WJQ04JZ7W` 为 tao-dev CI 生成临时证据索引
  - relates: ["REQ_20260914_0J68SDKV86ENKER2"]
  - depends_on: ["TASK_20261113_DP25XJYVJ3WW4H94"]
  - verify: 对成功和失败状态生成 evidence.json，检查提交、环境、状态和实际存在的附件路径
- [ ] `TASK_20261113_XH5CBJ7689PFKCHF` 更新公开规程并验证完整变更
  - relates: ["REQ_20260914_95193C19C90NRXV4"]
  - depends_on: ["TASK_20261113_DP25XJYVJ3WW4H94", "TASK_20261113_R6F8E95EN2XFBJD0", "TASK_20261113_Y8KHRD9WJQ04JZ7W"]
  - verify: 运行 just check、文档 HTML 构建和源文档校验，记录实际范围、未覆盖项与限制

<!-- tao:section verification -->
## 验证

2026-11-13，提交 `534b2e0`：实现 `verify --baseline` 的版本化 JSON 输入及基线摘要，新增仓库基线导出脚本，并让 `just check` 执行 `docs-verify`；PR 工作流另行检出目标提交并执行删除检查。当前 112 个定义的 HEAD 基线验证通过；增加一个未退役 REQ 的基线以退出码 1 和 `TAO-ID-003` 失败；非法 ID 基线以退出码 2 和 `TAO-CLI-001` 拒绝。`just check` 通过（322 项通过、1 项原生客户端发现按显式条件跳过、分支覆盖率 87%），CI YAML 可由 PyYAML 解析。尚未在 GitHub 托管运行器执行工作流，远端 required-check 配置未知。

2026-11-13，当前工作树：`verify --format sarif` 对无诊断、文档错误和 CLI 输入错误分别产生 SARIF 2.1.0；退出码为 0、1、2，且 invocation 分别标明检查已执行或未执行。非 `verify` 命令使用 SARIF 以退出码 2 拒绝。人工解析生成文件，核对了 schema 版本、规则号、级别、位置、原生输出和执行状态；`just check` 通过（322 项通过、1 项原生客户端发现按显式条件跳过、分支覆盖率 85%）。未使用外部 SARIF schema 校验器。

<!-- tao:section questions -->
## 待确认事项

无。远端 required checks 和分支保护不由仓库文件配置，本计划只保证工作流定义包含相应检查。
