# 文档编写与校验规程

创建、修改、审查 tao 管理文档时，读取本文涉及的规则段及当前 profile 模板；同一任务确实修改多类文档时才读取多个模板。普通代码、测试或配置修改没有文档同步职责时不读取本文。文档格式由同包的 [格式注册表](../assets/document-profiles.json) 和模板提供。

按任务读取：[正文写法](document-content.md) 处理 REQ／UC／ADR、设计内容与任务；[文档组织](document-layout.md) 处理位置与拆分；[退役规程](retirement.md) 处理正式删除；[证据保存](evidence-retention.md) 处理记录与报告；[本地化](localization.md) 处理翻译；[tao 术语](glossary.md) 处理项目受控术语；[出版规程](publication.md) 处理书籍导航、构建和稳定链接。只读取当前任务涉及的小节和模板。

## 选择范围与职责

新建的 tao 管理文档使用注册表中的 profile，不让用户设计 schema。已有项目可映射文档目录、选择显示语言，并在项目开发约定中明确拆分阈值；不能仅为通过检查改写 ID、字段或引用语法。用户明确要求不同格式时尊重该约定，并将该部分标为未按 tao 格式校验，不能宣称等价通过。

接入时明确管理范围：纳入范围的文档必须有受支持的 schema，缺少或未知 schema 报错；未接入的历史文档列为范围外，不悄悄计入覆盖率。按本次修改需要逐步接入，普通 README、外部资料与客户端 manifest 不因使用 Markdown 就自动纳入。配置和适配由 agent 复用已有约定，确有冲突才交由用户决定。

格式注册表权威定义 profile 名称、元数据字段、章节顺序、条目字段和模板位置；本文解释内容要求、引用与完成语义。模板是这些规则的写作起点，不能反过来修改规则以适配模板。

## 文档选择与目录

目录与命名统一见 [文档组织](document-layout.md)。按内容选择 `tao.project.<类型>/v0.1` 及对应模板：

| 内容 | 类型与模板 |
|---|---|
| 阅读目录 | [navigation](../assets/templates/navigation.md) |
| 能力规格 | [spec](../assets/templates/spec.md) |
| 实施计划 | [plan](../assets/templates/plan.md) |
| 系统／模块设计 | [design](../assets/templates/design.md) |
| 任务附件 | [tasks](../assets/templates/tasks.md) |
| 长期决定 | [decision](../assets/templates/decision.md) |
| 用户操作 | [user-guide](../assets/templates/user-guide.md) |
| 运维操作 | [runbook](../assets/templates/runbook.md) |
| 项目术语 | [glossary](../assets/templates/glossary.md) |
| 独立检查摘要 | [evidence](../assets/templates/evidence.md) |
| 恢复摘要 | [handoff](../assets/templates/handoff.md) |

设计通过 `spec_docs` 引用规格 DOC；计划通过 `spec_docs`、`design_docs` 引用适用规格和设计，通过 `tasks_doc` 引用任务附件 DOC。`spec_docs`、`design_docs` 一旦提供，须为非空、无重复的 YAML ID 数组。任务附件必须通过 `change` 引用同一 CHG，专属设计可关联该 CHG，共享设计不必声明专属开发事项。计划生成前的 CHG 由 [工作流状态](workflow-state.md) 提供。正文引用使用 `{need}` 和必要职责说明，不能保留第二份正文。关系只维护正向字段，反向链接由工具生成。按本次事项沿直接关系读取相关文档和章节，不沿反向链接加载整张文档图。草稿可暂缺依据；design/plan 阶段批准前必须关联已批准的上游产物并覆盖本次范围。当前 tasks_doc 指向一份完整任务集合，不通过普通正文引用暗中扩展为多份任务附件；扩展该关系须先定义并验证格式。计划及其任务附件合起来至少有一个 TASK。

## 元数据、结构与语言

既有文档保持 locale 和语言，明确翻译请求才转换或派生。新文档先取用户对产物明确指定的语言，再取项目约定；无法确定时询问一次，不从聊天语言或本 skill 的中文推导。模板显示文字按该语言选择，机器键保持不变；多语言派生见 [本地化](localization.md)。

文档以 YAML frontmatter 开始；必需字段、可选字段、枚举值及拒绝条件以注册表的 `base_metadata` 与 `structure` 为准。元数据中的字符串须非空白。`id` 是文档自身的 DOC ID。status 的 accepted 来自实际评审决定，不能由格式通过自动设置，也不代表文中所有条目均已接受。

日期采用带引号的 `YYYY-MM-DD` 本地日历日期，updated 不能早于 created；精确记录取带偏移量的时间戳，格式由注册表定义。created 不因编辑变化，updated 只在语义修改时更新；已有日期不因环境变化重算。导入文档无法确认创建日期时，记录首次纳入管理的日期并说明依据，不猜原始日期。不要把这些元数据加入 SKILL.md、agent 或 manifest，它们遵循自身格式。

每个二级标题紧邻前置稳定键，顺序与 profile 的 sections 完全一致：

```markdown
<!-- tao:section scope -->
## 目标与边界
```

键不依赖标题翻译或序号。二级章节不能增删或改序，细节放在三级及以下且不跳级。必需章节确实不适用时写一句具体依据，不留空或复制模板提示；规格的术语章节优先链接项目术语表，不重复定义。

plan profile 的 `change` 定义一个 CHG ID，生成计划前由 [工作流状态](workflow-state.md) 提供该标识；evidence profile 的 `evidence` 定义一个 EVD ID。其他 profile 的 `change` 仅引用 CHG；附件引用字段只引用 DOC，不创建新对象。不提供 `{chg}`、`{evd}` 条目块，也不从正文里出现 ID 推断定义。

模板的 heading.* 和 label.* 从 [简体中文资源](../assets/locales/zh-Hans.json) 或 [英文资源](../assets/locales/en.json) 取显示文字，其余变量填实际内容、已有引用或工具生成的 ID；元数据按合法 YAML 转义。扩展为多项时每个新对象独立分配 ID，不复制示例值；翻译既有对象则保留 ID。计划骨架可由 new 生成，其余由 agent 或人工填写；生成后仍需检查是否是真实内容。

## 标识符与引用

新 ID 使用 `tao id new <类型>` 分配，已有对象保留 ID，不手工编造。类型与完整格式由注册表定义，含义见 [tao 术语](glossary.md) 的 ID 类型表；分配日不要求与导入文档的 created 相同。

正文正式引用用 `{need}` 后接反引号包围的完整 ID；代码注释也使用完整 ID。不要把标题序号、文件内的“需求 2.1”或属性编号作为跨文档引用。需要独立引用的验收承诺拆成 REQ；可复用的验证场景或性质使用 UC，不另增局部 Property ID。

标题或文件移动保持 ID；拆成新对象或更改类型时分配新 ID 并保留关系。删除正式对象使用 [退役规程](retirement.md)。

同一版本的正式索引只允许一个定义；示例、档案和测试夹具不注册当前定义，多版本出版分别建索引。退役记录纳入 VCS 并参与查重，无法恢复历史基线时不能宣称查出了所有历史删除。外部项目的正式引用需显式导入索引，无可用索引时报告 unresolved。

文件导航用项目内相对 Markdown 链接，解析含符号链接的路径后不得越出项目；不使用本机绝对地址或 file://。外部资料使用项目可访问的稳定链接，引用范围遵循项目保密约定。发布时条目与章节使用稳定锚点及书籍解析入口，精确规则见 [出版规程](publication.md)。未实际构建并检查链接时，不要宣称移动后的 URL 已可用。

## 检查与修正

填写当前模板、替换全部变量并分配新 ID 后，运行 `tao verify --only docs`。普通局部文档维护检查受影响内容；已接入完整交付流程的事项按 [流程操作](workflow.md) 执行交付检查。

独立 [源校验器](../scripts/validate_documents.py) 也接受 `--project <根目录>`、项目相对 Markdown 路径，以及可选 `--format json`、`--book-root <导航文件>`、`--diagnostic-locale <语言>`；使用已准备的核心环境。

| 结果 | 如何处理 |
|---|---|
| 结构、ID 或关系 error | 按定位修正；重复 ID、缺失验收、引用目标变化需语义判断 |
| 内容 warning | 结合语境复查，词语命中不自动判定需求无效 |
| 工具／配置故障 | 报告未完成，先解决运行条件 |

退出码 0 表示无 error（可含 warning），1 表示文档 error，2 表示工具或配置故障。按 rule_id、位置与 suggestion 定位，不匹配本地化消息文字；诊断提供实际 message_locale，未翻译消息回退英文。

未提供历史基线时 deletion_checked 为 false；未指定书根不代表已检查全书可达性。自动格式修正限于不改变语义的内容并展示差异；例外记录理由、范围、责任人与复查条件，不用全局忽略隐藏错误。
