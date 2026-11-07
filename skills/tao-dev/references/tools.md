# 工具入口

用当前已加载 skill 的实际路径调用 `python <skill>/scripts/tao.py`，下文 tao 表示该入口。仓库源码入口为 skills/tao-dev/scripts/tao.py。显式 `--project <root>` 限定项目；不要猜测 PATH 中的同名全局程序。资源 URI 没有本地执行入口时只能读取规程，不声称 CLI 已运行。

| 命令 | 用途 |
|---|---|
| `tao doctor` | 只读诊断可用能力 |
| `tao show <ID>` | 定位已定义对象 |
| `tao id new <TYPE> --count <N>` | 批量生成唯一 ID；JSON 使用 outputs.ids |
| `tao new --slug <slug> [--locale en\|zh-Hans]` | 仅创建计划骨架，不注册事项 |
| `tao status [CHG\|DOC\|计划相对路径]` | 只读计划进度；省略目标列全部计划及规划材料 |
| `tao handoff [目标] --from <项目相对 Markdown>` | 显式替换一份临时交接；省略目标须只有一个计划 |
| `tao verify [目标] --only docs\|code\|docs,code` | 显式确定性检查，默认 docs,code；不认证交付 |
| `tao docs build` | 构建配置书根的本地 HTML |
| `tao project inspect` | 只读配置与检查候选 |
| `tao project configure --from <TOML> [--expect <digest>]` | 显式应用项目配置 |
| `tao retire <ID> --reason <说明> [--apply]` | 预览或显式执行正式对象退役 |

status/show 遇到无关草稿错误仍返回可用结果，并标为 `partial`、`outputs.documents_valid=false`；完整校验用 verify docs。所选任务集合缺失、错绑或结构损坏时，进度是 `unavailable`、计数为 null，不推断实现完成。handoff 必须使用归属于所选计划的有效唯一 CHG/DOC，不能用草稿别名覆盖其他事项。ID 分配会保留未完成草稿和退役记录中的已有 ID，但不要求整本书先通过校验。

日常机器可读查询使用 `--format json`；verify 和 status 优先加 `--simplified`，避免把完整文档索引或已完成任务反复送入上下文。需要定位具体定义时用 show，不为简单动作重复输出整本书。

new 的 spec/design/plan 编排、review doc/code、implement、refine、continue 是 skill 动作，不是同名 Python 状态机。没有 workflow、review 导入、finish 或 evidence-only gate。检查未运行、审查未知与任务完成须分开报告。项目复制与依赖准备见 [运行环境](runtime.md)，文档规则见 [文档规程](documents.md)。
