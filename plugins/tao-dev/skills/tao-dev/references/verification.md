# 项目检查、度量与证据复用

配置或执行行为检查、解释当前证据和预算时读取本文。操作入口见 [工具规程](tools.md)，人工判断与独立审查见 [审查规程](review.md)。工具只汇总已配置的确定性条件，不替代语义评审，也不是实际账单。

## 一次接入现有工具

工具探测与选择按 [项目接入](project-setup.md)；本文说明 .tao/config.toml 中的验证策略。

```toml
[verification]
inputs = ["src/**/*", "tests/**/*", "pyproject.toml", "requirements.txt"]
budget_seconds = 300
reuse_seconds = 3600
require_logs = false
required_reviews = []
environment = []
usage_reports = []

[[verification.checks]]
id = "tests"
argv = ["python", "-m", "pytest"]
timeout_seconds = 120
```

示例需按实际项目修改，不是强制采用 Python 的约定。所有 checks 均为必需检查，按声明顺序串行执行；需要环境激活时显式指向已准备的解释器。argv 不经过隐式 shell；确需 shell 时必须显式配置已授权命令。范围不明时执行全部配置检查，不让用户每次选择等级。缺配置、空输入集合、未知键或缺工具返回未完成。

单项检查可用同名的 `inputs` 声明自己的输入范围，省略即沿用全局范围：

```toml
[[verification.checks]]
id = "task-graph"
argv = ["python3", "tools/check_task_graph.py"]
inputs = ["tools/check_task_graph.py", "docs/plans/**/*.md", "docs/product/*.md"]
timeout_seconds = 60
```

它只收窄这一项的重跑判定，不改变整份回执的过期判定：任一全局输入变化仍使整份回执过期，下次调用仍须重新执行一次，但声明范围内无变化且上次通过的检查沿用上次结果，不重跑。形状与全局 `inputs` 相同；其匹配到的文件集合必须是全局 `inputs` 匹配集合的子集，匹配到范围外的文件或匹配不到任何文件都按配置错误拒绝。

子集约束挡的是声明越界，挡不住声明不全：某项检查的 `inputs` 若窄于它的真实依赖，它会静默停止重跑而整体仍报通过。工具无法发现隐含依赖，声明的完整性由项目承担；只在确知该检查读什么时才声明，长检查与文档类检查混在同一策略里是典型场景。作为补偿，策略、工具与环境指纹的变化仍使全部检查失效，不设逐项例外。

inputs 是调用方声明的完整行为输入范围，包含相关配置、测试数据、依赖锁文件及未跟踪文件；不能只列这次修改的文件。工具纳入自身代码、项目配置、解释器、检查程序、Python 包版本及平台；PATH、LANG、LC_ALL 与 environment 指定变量参与指纹，值不写入报告。非 Python 依赖、外部服务和数据集须由项目用受控版本文件及显式变量接入；无法固定它们时，不应复用相关结果。工具无法发现所有隐含依赖。

## 实际运行与预算

每项结果包含实际 argv、退出码、耗时和日志位置。CLI 的 duration_seconds 是本次实际耗时；复用检查回执中的检查耗时属于原执行，不能算成本次重新执行。单项 timeout_seconds 与总 budget_seconds 共同约束检查进程；超时终止该进程组，预算耗尽后的检查记为 not_run，不能用跳过换通过。文件枚举和输入识别也有开销，当前不提供硬实时的整个 CLI 截止保证。

可在 check 中声明工具产生的度量报告：

```toml
metrics = {format = "coverage-json", path = "tmp/tao/coverage/coverage.json"}
```

当前支持 `coverage-json` 与 `ruff-json` 两种格式。报告必须位于配置的 temporary 目录；执行前删除该项旧报告，缺失或无效报告不能算通过。阈值由原生命令执行，例如已有的 coverage fail-under，tao 不另造“综合质量分”。未设阈值的覆盖率是观察值，不是质量承诺；测试数量、覆盖率和无 lint 错误都不能证明需求满足。其他工具仍可按退出码接入。

usage_reports 可指向 Claude stream-json 或 Codex JSONL 事件文件，统计已完成事件的用量；缺文件、未完成、无法解析或累计值有歧义时保持未知。

可配置 max_model_tokens 与 max_estimated_usd，在启动检查前检查指定报告的预算；计量未知时返回未完成，已超预算时返回失败。费用只使用 CLI 明确报告的估算，不猜价格；billed_usd 始终未知，真实账单需另接供应商计费来源。这是对指定报告的启动前检查点，不是账户总费用，也不能中止正在运行的模型或限制其未来消费。

## 复用与过期

原始输出及 latest.json 位于默认 tmp/tao/verification/，均不纳入 VCS。检查回执保存输入指纹及执行摘要；Git 修订与 clean／dirty 为补充信息，持久输入引用按 [证据保存](evidence-retention.md) 记录。

复用必须同时满足：输入、策略、工具与环境一致；检查集合完整且全部通过；未超过 reuse_seconds；策略要求的日志仍在。逐项复用另按每项检查自己的范围与执行时刻判定：沿用的行保留原执行时刻、原耗时与原日志位置，报告标出该行为沿用，其耗时不计入本次执行；reuse_seconds 按该行自己的执行时刻计算，整份回执刷新记录时刻不使未重新执行的检查显示为新鲜，任一行超时即便输入未变也使当前证据为 expired 并在下次调用重新执行该行。回执格式版本随字段变化递增，无法按当前版本解读的回执按无效处理并重新执行全部检查。源码变化、新增纳入范围的文件、同一修订下的未提交修改、配置变化均会使结果过期。提交未改变受检内容时不因修订号改变而无意义重跑，原始检查回执的修订引用仍保留。检查前后输入不同标为 stale；完整验证另外检查管理文档是否在运行中变化。检查结果只说明这些观察时点，不保证工作区之后无人修改，也无法发现先改后还原的并发输入；需要更强保证时在不可变快照或受控 CI 中运行。

status 只读比较当前证据。require_logs=true 时缺日志阻止复用，否则结构化结果仍可满足材料条件。缓存损坏或清空后须重跑，不能从文字结论补造通过缓存。

保存位置、历史结果和记录粒度统一按 [证据保存](evidence-retention.md)；修改计划正文是否需重验取决于实际受检输入。

## 完整交付判定

`tao verify` 检查 docs、code、evidence，自动选择唯一开发事项；多个候选时由 agent 根据当前上下文传 CHG ID。目标任务及其依赖必须完成，当前证据可复用，配置要求不得缺失，才返回 complete／checks-satisfied。`--only` 始终 partial／not-evaluated，dry-run 不执行、不生成证据。

required_reviews 声明不能省略的独立审查条件；按 [审查记录](review-receipts.md) 取得输入绑定、导入实际结果。完整验证逐项报告 satisfied、changes-requested、missing、invalid、stale、expired 或 materials-missing；只有全部 satisfied 才满足审查门槛。不能用报告存在、角色名称或任意 passed 字段满足它，也不能为了通过清空已要求的审查。发布、合入和用户风险接受仍由已有授权和实际判断决定。
