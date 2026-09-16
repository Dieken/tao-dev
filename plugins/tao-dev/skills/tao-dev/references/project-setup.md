# 项目接入与配置

处理 setup 动作或修改项目配置时读取。用户的 setup 接入业务项目；install 安装插件，底层 `tao setup` 准备 tao 运行环境，见 [运行环境](runtime.md)。项目接入是可选的，用户可直接 new。

## 接入步骤

1. 运行 `tao --project <root> project inspect`，结合 manifest、CI、已有配置与源码核对检查入口。探测不执行候选命令；executable_available 仅表示找到入口。未识别的技术栈和扫描缺口由 agent 补查。
2. 优先采用既有 CI 和项目命令，检查 watch 模式、外部服务与副作用。非空项目提供“接入现有工具”“补充选中工具”“仅查看建议”；空项目待技术栈明确后再接入。已有授权覆盖时直接推进。
3. 在确认范围内使用项目依赖管理器和锁文件准备选中的工具，保留已有门槛；业务工具不装入 tao venv，不自动全局安装或新增 CI 平台。检查命令及参数来自核实过的入口，配置方式见 [验证规程](verification.md)。
4. 在项目临时目录编写最小 TOML 草稿。已有配置先完整读取，保留无关约定；历史文档按需要逐步接入，空项目可暂用 include=[]，但这不构成检查通过。
5. 执行 `tao project configure --from <项目相对草稿路径>`，已有配置加 `--expect <inspect 返回的 config_digest>`。冲突时读取新配置再协调；configure 本身不安装依赖或执行检查。
6. 核对生成目录与 `/.worktrees/` 的忽略规则，保留 `.tao/config.toml`、工作流状态和正式 handoff；运行 `tao doctor` 与获准基线检查，报告写入及结果，已有事项接 `continue` 动作，否则接 `new` 动作。重复 `setup` 动作只检查、补充。

## 配置格式

显式 --project 指定根；否则向上寻找最近的 `.tao/config.toml`。配置限定项目内路径，解析符号链接后也不得越界；未知键或版本报错。目录仅在实际写入时创建。

```toml
version = 1
locale = "en"

[documents]
include = ["docs/**/*.md"]
exclude = []
# 有实际书入口时才配置：
# book_root = "docs/index.md"

[paths]
plans = "docs/plans"
retired = "docs/retired"
temporary = "tmp/tao"

[hooks]
docs_enabled = true
timeout_seconds = 5
```

include、exclude 从项目根按 Python Path.glob 展开，以包含集合减去排除集合；`*` 不跨目录，`**` 含零层或多层。排除整棵子树用 `vendor/**/*.md`，不按路径尾部匹配。普通 README、运行 prompt、模板与 manifest 不因文件后缀自动纳入。

locale 为新文档默认语言，可选 `[ui] locale` 独立设置诊断语言；不设置时按源文档语言诊断。明确的 --locale 优先于项目配置，未配置时 CLI 可采用已有管理文档唯一 locale；仍不明确则由 agent 按 [文档语言规则](documents.md) 解决。章节迁移映射 documents.section_redirects 见 [出版规程](publication.md)。

hook 默认启用，预算默认 5 秒、允许 1–30 秒；禁用不影响显式 CLI。依赖缺失、超时或锁冲突报告未完成，不阻止已发生的编辑。处理遗留锁前确认没有活跃写入者。
