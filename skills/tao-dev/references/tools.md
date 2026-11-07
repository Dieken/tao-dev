# 工具入口

用当前已加载 skill 的实际路径调用 `python <skill>/scripts/tao.py`，下文 tao 表示该入口。仓库源码入口为 skills/tao-dev/scripts/tao.py。显式 `--project <root>` 限定项目；不要猜测 PATH 中的同名全局程序。资源 URI 没有本地执行入口时只能读取规程，不声称 CLI 已运行。

| 命令 | 用途 |
|---|---|
| `tao doctor` | 只读诊断可用能力 |
| `tao show <ID>` | 定位已定义对象 |
| `tao id new <TYPE> --count <N>` | 批量生成唯一 ID；JSON 使用 outputs.ids |
| `tao new --slug <slug> [--locale en\|zh-Hans]` | 仅创建持久计划骨架，不创建规格或设计、不注册流程 |
| `tao status [CHG\|DOC\|计划相对路径]` | 只读计划任务计数、待完成项与源文件位置；省略目标列全部计划及规划材料 |
| `tao verify` | 校验受管理文档；不运行项目测试、不认证交付 |
| `tao docs build` | 构建配置书根的本地 HTML |
| `tao project inspect` | 只读文档配置、项目路径与配置摘要 |
| `tao project configure --from <TOML> [--expect <digest>]` | 显式应用项目配置 |
| `tao retire <ID> --reason <说明> [--apply]` | 预览或显式执行正式对象退役 |

status/show 遇到无关草稿错误仍返回可用结果，并标为 `partial`、`outputs.documents_valid=false`；完整校验用 verify。所选任务集合缺失、错绑或结构损坏时，进度是 `unavailable`、计数为 null，不推断任务完成。任务全部勾选时进度 `tasks_complete` 不代表已验证、已审查或已交付；验证与审查记录从计划原文核对，CLI 不代作结论。ID 分配会保留未完成草稿和退役记录中的已有 ID，但不要求整本书先通过校验。

日常机器可读查询使用 `--format json`。verify 固定返回有效性、计数、删除检查覆盖与诊断；status 固定返回计数、待办和源文件位置，不复制已完成任务或验证正文。临时总结由 agent 按用户问题读取权威文档后完成。需要定位具体定义用 show；明确需要完整结构索引时，使用底层 `python <skill>/scripts/validate_documents.py --project <root> --format json <文档相对路径...>`，不让日常检查默认输出整本书。

new/status 不提供下一执行动作或流程关卡；查询不触发检查，计划骨架不授权执行。文档管理与持久计划规则由 agent 按 [文档规程](documents.md) 和 [持久计划](planning.md) 使用。检查未运行、审查未知与任务完成须分开报告。文档配置见 [可选项目接入](project-setup.md)，项目原生命令与结果限制见 [确定性检查](verification.md)，项目复制与依赖准备见 [运行环境](runtime.md)。临时总结是普通用户请求，不需要专用辅助命令。
