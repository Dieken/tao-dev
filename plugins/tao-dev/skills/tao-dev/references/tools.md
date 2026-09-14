# 确定性工具与项目配置

通过已信任的 Python 环境调用本 skill 的 [scripts/tao.py](../scripts/tao.py)。Python 需要 3.11 或以上版本及 [运行依赖](../scripts/requirements.txt)。遵守已有依赖安装授权，不自动全局安装。下文 `tao` 只是该脚本入口的简写，不从 PATH 猜测同名程序。

先运行 `tao --project <目录> doctor --format json`。支持的操作以返回的 capabilities 为准；当前包含 doctor、id.new、show、new、status、verify.docs。尚不包含行为检查、证据复用、交接、退役写入、出版及 hook；这些操作不应被假装执行。

| 操作 | 已实现行为 |
|---|---|
| `tao verify --only docs` | 检查纳入范围的共享格式、ID、关系、任务、退役索引及导航；0 表示本子集通过，coverage 始终 partial，readiness 为 not-evaluated |
| `tao verify` | 需要完整检查能力；当前缺少 code 和 evidence，返回 2 与 blocked，不将它们默认为不适用 |
| `tao verify --only docs --dry-run` | 只显示选择方案，不执行检查，不生成通过证据 |
| `tao id new REQ` | 用本地日期及安全随机源生成 ID；读取现有定义和退役记录查重，不写编号台账 |
| `tao show <ID>` | 显示定义、引用和源位置；站点未构建时 url 为空 |
| `tao new --slug <slug> --locale en` | 排他创建本地日期的变更骨架；同名计划或附件存在时报错，不覆盖。agent 必须继续填写目标、范围和可确定内容，清除占位符 |
| `tao status [CHG-ID]` | 读取任务与文档诊断；不运行行为检查，不改任务勾选，证据复用状态为未评估 |

通用 `--project` 与 `--format text|json` 可以放在操作前后。没有可靠影响基线时，changed 范围回退到 all 并说明原因。未提供历史基线时，源校验结果 deletion_checked 为 false；不能声称已检测所有历史删除。错误元数据、重复定义或越界路径会阻止分配新 ID，避免基于不完整索引生成文件。

## 一次配置，日常复用

显式 --project 指定根目录；否则从当前目录向上寻找最近的 `.tao/config.toml`。不写全局配置。无配置时，显式项目根内默认管理 docs/ 下的 Markdown；没有匹配文件时验证报未完成，不能以空检查通过。README、运行 prompt 与模板有自己的格式，不因 Markdown 扩展名自动纳入。

```toml
version = 1
locale = "en"

[documents]
include = ["docs/**/*.md"]
exclude = []
# 有实际导航文件时才配置：
# book_root = "docs/index.md"

[paths]
changes = "docs/changes"
retired = "docs/retired"
temporary = "tmp/tao"
```

配置只描述工具行为。路径和文件模式限定在项目内，解析符号链接后不得越界；未知键或配置版本报错。语言先取显式 --locale，再取配置，再取已有管理文档的唯一 locale；无法确定时报告缺口，由 agent 依据项目约定解决，不取聊天语言或机器时区作为文档语言。

配置中的目录仅在实际写入时创建。源文件校验器也可单独调用，见 [诊断规程](document-diagnostics.md)；它与 CLI 共用同一实现，不是另一套文档格式。原始输出默认留在临时目录或 CI，简短结果按 [保存规则](document-layout.md) 记录。
