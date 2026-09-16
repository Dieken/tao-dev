# 工具入口与操作索引

已有安装使用摘要中已验证的 tao 启动器；独立 skill 使用可用的受支持 Python 调用本 skill 的 [scripts/tao.py](../scripts/tao.py)。从当前已加载 skill 的实际位置定位脚本，以 `--project` 指定业务项目；资源 URI 按客户端提供的读取方式访问。只有 URI 且客户端未提供本地脚本或执行入口时，CLI 能力不可用，仍可读取规程。下文 tao 表示该入口，不从 PATH 猜同名程序。环境未准备或不可用时读 [运行环境](runtime.md)。

首次调用运行 `tao --project <目录> doctor --format json`，按 capabilities 使用可用操作；入口、项目配置和环境未变时复用结果，失败或变化后重查。通用 `--project`、`--format text|json`、`--diagnostic-locale <语言>` 可放在操作前后。

| 操作 | 已实现行为 |
|---|---|
| `tao verify --only docs` | 检查纳入范围的共享格式、ID、关系、任务、退役索引及导航；结果为 partial／not-evaluated |
| `tao verify` | 汇总文档、已配置项目检查、当前证据、目标任务及必需审查；缺策略／工具／有效审查记录时返回 2 与 blocked |
| `tao verify --only code` | 按项目既有检查策略实际运行或复用有效结果，返回 partial；`--only evidence` 只检查当前证据 |
| `tao verify --only docs --dry-run` | 只显示选择方案，不执行检查，不生成通过证据 |
| `tao id new REQ` | 用本地日期及安全随机源生成 ID；读取现有定义和退役记录查重，不写编号台账 |
| `tao retire <ID> --reason <说明> [--replaced-by <ID>] [--apply]` | 默认只读预览移除对象、引用影响及退役后的校验；--apply 才保存退役记录并移除正文。替代参数可重复，必须同类型且可解析；完整规则见 [退役规程](retirement.md) |
| `tao show <ID>` | 显示定义、引用和源位置；站点未构建时 url 为空 |
| `tao new --slug <slug> --locale en` | 排他创建本地日期的变更骨架；同名计划或附件存在时报错，不覆盖。后续由 agent 按流程规程填写草稿 |
| `tao handoff [CHG-ID] --from <文件>` | 校验 agent 写好的、change 元数据与目标 CHG 一致的 handoff 文档，保存到计划附件或计划前的预留位置；更新保留 DOC ID，附只读状态观察；接续方式见工作流状态接口 |
| `tao review <CHG-ID> [--from <文件>]` | 无 --from 时只读返回审查输入绑定；有 --from 时校验并导入实际审查记录，不启动模型；格式及信任边界见 [审查记录](review-receipts.md) |
| `tao docs build` | 按 book_root 构建本地 HTML，检查固定入口；依赖、输出及边界见 [出版规程](publication.md) |
| `tao status [CHG-ID]` | 读取任务与文档诊断；不运行行为检查，不改任务勾选，有项目检查策略时比较证据是否可复用；没有策略时为未评估 |

项目探测与配置见 [项目接入](project-setup.md)，阶段与检查点命令见 [工作流状态](workflow-state.md)，检查策略与结果见 [验证规程](verification.md)。

配置缺失时，显式项目根默认管理 docs/ 下的 Markdown；空范围不算通过。changed 无可靠影响基线时回退 all 并报告；无历史删除基线时 deletion_checked=false。文档错误可能阻止 ID 分配，先修复索引范围内的错误。

hook 仅在已有项目配置时做短文档反馈；终端改动可能不触发，仍需显式检查。它不准备依赖、不运行项目测试或模型，也不替代阶段批准与交付验证。检查记录注明实际触发情况；开关与预算见项目接入。
