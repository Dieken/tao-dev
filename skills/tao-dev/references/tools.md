# 工具入口

用当前已加载技能的实际路径调用 `python <skill>/scripts/tao.py`，下文 `tao` 表示该入口。仓库源码入口为 `skills/tao-dev/scripts/tao.py`。用显式参数 `--project <root>` 限定项目，不依赖同名全局程序。资源 URI 若没有本地执行入口，只能读取规程。依赖准备与客户端发现路径见 [运行环境](runtime.md)。

| 命令 | 用途 |
|---|---|
| `tao doctor` | 只读诊断可用能力 |
| `tao show <ID>` | 定位已定义对象 |
| `tao id new <TYPE> --count <N>` | 批量生成唯一 ID；JSON 使用 `outputs.ids` |
| `tao new --slug <slug> [--locale en\|zh-Hans]` | 仅创建持久计划骨架，不创建规格或设计 |
| `tao status [CHG\|DOC\|计划相对路径]` | 只读计划任务计数、待完成项与源文件位置；省略目标列全部计划及规划材料 |
| `tao verify` | 校验受管理文档；不运行项目测试、不认证交付 |
| `tao docs build` | 构建配置书根的本地 HTML |
| `tao project inspect` | 只读文档配置、项目路径与配置摘要 |
| `tao project configure --from <TOML> [--expect <digest>]` | 显式应用项目配置 |
| `tao retire <ID> --reason <说明> [--apply]` | 预览或显式执行正式对象退役 |

## 查询与进度

日常机器可读查询使用 `--format json`。`status`／`show` 遇到无关草稿错误仍返回可用结果，并标为 `partial`、`outputs.documents_valid=false`；完整校验用 `verify`。所选任务集合缺失、关联错误或结构损坏时，进度为 `unavailable`、计数为 `null`。任务全部勾选时的 `tasks_complete` 不代表已验证、已审查或已交付，结果须从 [计划原文](planning.md#结果保存) 核对。

`status` 返回计数、待办和源文件位置，不复制已完成任务或验证正文；查询不运行检查。`new`／`status` 不提供下一执行动作，计划骨架不授权执行。ID 分配避开未完成草稿和退役记录中的已有 ID，不要求整本书先通过校验。

定位定义用 `show`；需要完整结构索引时，使用 `python <skill>/scripts/validate_documents.py --project <root> --format json <文档相对路径...>`。

## 文档校验

`tao verify` 只读校验受管理文档的基本元数据、必要语义结构、唯一 ID、关系及无环可达导航，返回有效性、计数、删除检查覆盖与诊断。它不执行项目测试、代码静态检查或构建，也不证明内容正确、来源真实、实现完成或交付通过；内容判断见 [语义审查](review.md)，结果保存见 [持久计划](planning.md#结果保存)。

## 可选项目配置

项目配置不是 `status`、ID 分配或计划骨架生成的前置条件；这些操作不创建配置或扫描其他项目。

1. `tao project inspect` 只读文档配置、项目路径和 `config_digest`。
2. 核对受管理文档范围、书根、语言及项目内输出路径，在项目临时目录写 TOML 草稿，保留无关配置。
3. 用 `tao project configure --from <项目相对草稿>` 写入；已有配置使用 `inspect` 返回的 `config_digest` 配合 `--expect` 检测冲突。
4. 忽略临时产物，用 `tao verify` 校验受管理文档；需要出版时另行调用 `tao docs build`。

`.tao/config.toml` 只管理文档、语言、出版及项目内路径；`verification` 配置表不受支持，会明确拒绝。测试、代码静态检查、类型检查、构建及其超时、缓存和报告由项目的 `justfile`、`Makefile`、`package.json` 或 CI 管理，tao 不发现、调度、缓存这些命令或安装业务依赖。
