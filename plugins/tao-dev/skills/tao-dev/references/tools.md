# 确定性工具与项目配置

优先使用安装摘要中已验证的 tao 启动器绝对路径；也可使用本 skill 的 [scripts/tao.py](../scripts/tao.py) 与安装时选定的 Python。首次准备或环境不可用时读取 [运行环境规程](runtime.md)：标准库入口提供 setup 和 doctor，运行不依赖 uv，普通命令只使用已准备的独立环境。遵守已有依赖安装授权，不自动全局安装。下文 `tao` 简写这个已定位入口，不要求用户配置 PATH 或 TAO 环境变量。

本会话首次调用时运行 `tao --project <目录> doctor --format json`；入口、项目配置或运行环境未变时复用结果，发生变化或运行失败再检查。支持的操作以返回的 capabilities 为准；完整安装包含文档与出版能力；新增加的 project.inspect、project.configure、workflow 接口分别用于项目接入和协调状态。配置项目检查策略后包含 verify.code 与 verify.evidence。行为检查、度量、预算与证据复用按 [验证规程](verification.md) 配置和解释。

| 操作 | 已实现行为 |
|---|---|
| `tao verify --only docs` | 检查纳入范围的共享格式、ID、关系、任务、退役索引及导航；结果为 partial／not-evaluated |
| `tao verify` | 汇总文档、已配置项目检查、当前证据、目标任务及必需审查；缺策略／工具／有效审查记录时返回 2 与 blocked |
| `tao verify --only code` | 按项目既有检查策略实际运行或复用有效结果，返回 partial；`--only evidence` 只检查当前证据 |
| `tao verify --only docs --dry-run` | 只显示选择方案，不执行检查，不生成通过证据 |
| `tao id new REQ` | 用本地日期及安全随机源生成 ID；读取现有定义和退役记录查重，不写编号台账 |
| `tao retire <ID> --reason <说明> [--replaced-by <ID>] [--apply]` | 默认只读预览移除对象、引用影响及退役后的校验；--apply 才保存退役记录并移除正文。替代参数可重复，必须同类型且可解析；完整规则见 [文档规程](documents.md) |
| `tao show <ID>` | 显示定义、引用和源位置；站点未构建时 url 为空 |
| `tao new --slug <slug> --locale en` | 排他创建本地日期的变更骨架；同名计划或附件存在时报错，不覆盖。后续由 agent 按流程规程填写草稿 |
| `tao handoff [CHG-ID] --from <文件>` | 校验 agent 写好的、change 元数据与目标 CHG 一致的 handoff 文档，保存到计划附件或计划前的预留位置；更新保留 DOC ID，附只读状态观察；接续方式见工作流状态接口 |
| `tao review <CHG-ID> [--from <文件>]` | 无 --from 时只读返回审查输入绑定；有 --from 时校验并导入实际审查记录，不启动模型；格式及信任边界见 [审查记录](review-receipts.md) |
| `tao docs build` | 按 book_root 构建本地 HTML，检查固定入口；依赖、输出及边界见 [出版规程](publication.md) |
| `tao status [CHG-ID]` | 读取任务与文档诊断；不运行行为检查，不改任务勾选，有项目检查策略时比较证据是否可复用；没有策略时为未评估 |

通用 `--project`、`--format text|json` 与 `--diagnostic-locale <语言>` 可以放在操作前后。诊断默认语言及回退见 [本地化规程](localization.md)，不改变生成文档的语言。没有可靠影响基线时，changed 范围回退到 all 并说明原因。未提供历史基线时，源校验结果 deletion_checked 为 false；不能声称已检测所有历史删除。错误元数据、重复定义或越界路径会阻止分配新 ID，避免基于不完整索引生成文件。

工作流阶段、版本批准与 worktree 绑定使用 [工作流状态接口](workflow-state.md)；`tao workflow status` 为只读，写操作要求显式动作和检查点版本。

项目接入使用 [setup 规程](project-setup.md)：`tao project inspect` 只读探测；`tao project configure --from <file>` 应用已确认配置。

## 一次配置，日常复用

显式 --project 指定根目录；否则从当前目录向上寻找最近的 `.tao/config.toml`。不写全局配置。无配置时，显式项目根内默认管理 docs/ 下的 Markdown；没有匹配文件时验证报未完成，不能以空检查通过。README、运行 prompt 与模板有自己的格式，不因 Markdown 扩展名自动纳入。

```toml
version = 1
locale = "en"

[ui]
locale = "en"

[documents]
include = ["docs/**/*.md"]
exclude = []
# 有实际导航文件时才配置：
# book_root = "docs/index.md"

[paths]
plans = "docs/plans"
retired = "docs/retired"
temporary = "tmp/tao"
```

跨文档章节的旧入口按 [出版规程](publication.md) 配置 documents.section_redirects；值必须指向当前章节，普通文档校验及退役操作同时核对这些关系。

documents.include 与 documents.exclude 均按项目根目录使用 Python Path.glob 的文件模式展开，再从包含集合减去排除集合。`*` 不跨目录，`**` 匹配任意层级（含零层）；例如 `*.md` 只匹配根目录文件，`vendor/**/*.md` 排除 vendor 下各层 Markdown。排除模式不按路径尾部匹配；需要排除整棵 Markdown 子树时使用 `目录/**/*.md`。

配置只描述工具行为。路径和文件模式限定在项目内，解析符号链接后不得越界；未知键或配置版本报错。新文档语言先取显式 --locale，再取顶层 locale 配置，再取已有管理文档的唯一 locale；无法确定时报告缺口，由 agent 依据项目约定解决，不取聊天语言或机器时区作为文档语言。可省略 ui.locale，让文档诊断按各自源文档语言显示。

配置中的目录仅在实际写入时创建。源文件校验器也可单独调用，见 [诊断规程](documents.md)；它与 CLI 共用同一实现，不是另一套文档格式。原始输出默认留在临时目录或 CI，简短结果按 [保存规则](evidence-retention.md) 记录。

## 客户端入口与短检查

Claude 的动作命令与 reviewer 角色引用共享规程；完整动作列表只在 [流程操作](workflow.md) 维护。Codex 使用 tao-dev skill 入口和相同操作意图，不能把 Claude 的命令或角色发现当作 Codex 原生支持。跨供应商审查以实际模型与来源为准。

两端 PostToolUse 配置直接调用同一个 [hook 脚本](../scripts/hook.py)，再选择与 CLI 相同的已准备核心环境。静态 marketplace 配置从 PATH 查找 python3；tao install 将其改为已验证的解释器与脚本绝对路径。依赖缺失时报告 not_run，不自动创建 venv 或安装 package。脚本仅在当前项目已有 .tao/config.toml 时运行，只做 docs 子集反馈，不运行项目命令或模型。可配置：

```toml
[hooks]
docs_enabled = true
timeout_seconds = 5
```

默认预算 5 秒，允许 1–30 秒，外层客户端 handler 超时为 35 秒。相同源文件、运行代码、契约、配置及依赖版本只复用短反馈；改动后重新检查。缓存仅保存合并输入指纹和有限诊断，位于 tmp/tao/cache/，不是持久输入清单或交付证据。超时、依赖缺失、锁冲突和格式错误如实提示；不阻止已发生的写入，也不声称完整验证通过。进程中断遗留锁时先确认没有运行中的写入，再清理临时锁。

hook 只覆盖其匹配的文件工具；由终端命令产生的修改仍依靠 skill 显式验证。禁用 hook 后显式 CLI 仍可用。检查记录须说明 hook 是否实际触发。
