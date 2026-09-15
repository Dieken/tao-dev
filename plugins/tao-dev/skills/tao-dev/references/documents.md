# 文档编写与校验规程

创建、修改、审查 tao 管理文档时，读取本文涉及的规则段及当前 profile 模板；同一任务确实修改多类文档时才读取多个模板。普通代码、测试或配置修改没有文档同步职责时不读取本文。文档格式由同包的 [格式注册表](../assets/document-profiles.json) 和模板提供。

按任务读取：[文档组织](document-layout.md) 处理位置与拆分；[条目写法](document-entries.md) 处理 REQ／UC／ADR；[退役](retirement.md) 处理正式删除；[证据保存](evidence-retention.md) 处理记录与报告；[本地化](localization.md) 处理翻译；[出版](publication.md) 处理书籍导航、构建和稳定链接。只读取当前任务涉及的小节和模板。

## 受控术语

只提升跨文档易混淆或反复误用的词，局部术语留在所属规格或设计。项目 glossary 的 terms 节用 `{term} 首选名称` 围栏，正文为定义；可选 `:english:`、`:code:`、`:scope:` 和 `:avoid:`（JSON 字符串数组）。不新增 TERM ID；定义只维护一处，其他位置链接。校验器检查条目结构、同范围重名与自相矛盾的禁用名称；语义误用由审查判断，不全文禁止“身份”等多义词或误报反例。

## 选择范围与职责

新建的 tao 管理文档使用注册表中的 profile，不让用户设计 schema。已有项目可映射文档目录、选择显示语言，并在项目开发约定中明确拆分阈值；不能仅为通过检查改写 ID、字段或引用语法。用户明确要求不同格式时尊重该约定，并将该部分标为未按 tao 格式校验，不能宣称等价通过。

接入时明确管理范围：纳入范围的文档必须有受支持的 schema，缺少或未知 schema 报错；未接入的历史文档列为范围外，不悄悄计入覆盖率。按本次修改需要逐步接入，普通 README、外部资料与客户端 manifest 不因使用 Markdown 就自动纳入。配置和适配由 agent 复用已有约定，确有冲突才交由用户决定。

格式注册表权威定义 profile 名称、元数据字段、章节顺序、条目字段和模板位置；本文解释内容要求、引用与完成语义。模板是这些规则的写作起点，不能反过来修改规则以适配模板。注册表是机器可读的格式目录，**不是完整 JSON Schema 或 Markdown 校验器**。实际检查范围与结果解释见本文“检查与修正”。

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

设计通过 `spec_docs` 引用规格 DOC；计划通过 `spec_docs`、`design_docs`（非空、无重复的 YAML ID 数组）引用适用规格和设计，通过 `tasks_doc` 引用任务附件 DOC。目标类型由注册表校验；任务附件必须通过 `change` 引用同一 CHG，专属设计可关联该 CHG，共享设计不必声明专属开发工作。计划生成前的 CHG 由 [工作流状态](workflow-state.md) 提供。正文引用使用 `{need}` 和必要职责说明，不能保留第二份正文。关系只维护正向字段，反向链接由工具生成。按本次事项沿直接关系读取相关文档和章节，不沿反向链接加载整张文档图。草稿可暂缺依据；design/plan 阶段批准前必须关联已批准的上游产物并覆盖本次范围。当前 tasks_doc 指向一份完整任务集合，不通过普通正文引用暗中扩展为多份任务附件；扩展该关系须先定义并验证格式。计划及其任务附件合起来至少有一个 TASK。

## 元数据、结构与语言

UTF-8 Markdown 以 YAML frontmatter 开始。共同必需字段为 `schema`、`id`、`title`、`locale`、`status`、`created`，可选 `updated`；含义与枚举以注册表为准。字符串非空，拒绝重复键、未知字段、自定义 YAML tag。`id` 是文档自身的 DOC ID；正文恰有一个一级标题，与 title 一致。status 的 accepted 来自实际评审决定，不能由格式通过自动设置，也不代表文中所有条目均已接受。

日期采用带引号的 `YYYY-MM-DD` 本地日历日期，updated 不能早于 created；精确记录使用带数值 UTC 偏移量或 Z 的 RFC 3339 时间戳。created 不因编辑变化，updated 只在语义修改时更新；已有日期不因环境变化重算。导入文档无法确认创建日期时，记录首次纳入管理的日期并说明依据，不猜原始日期。不要把这些元数据加入 SKILL.md、agent 或 manifest，它们遵循自身格式。

每个二级标题紧邻前置稳定键，顺序必须与 profile 的 sections 完全一致：

```markdown
<!-- tao:section scope -->
## 目标与边界
```

章节键与字段键均匹配 `[a-z][a-z0-9-]*`，不依赖标题翻译或序号。二级章节不能增删或改序，细节放在三级及以下且不跳级。必需章节确实不适用时写一句具体依据，不留空或复制模板提示；规格的术语章节优先链接项目术语表，不重复定义。

plan profile 的 `change` 定义一个 CHG ID，生成计划前由工作流状态提供该标识；evidence profile 的 `evidence` 定义一个 EVD ID。其他 profile 的 `change` 仅引用 CHG；附件引用字段只引用 DOC，不创建新对象。不提供 `{chg}`、`{evd}` 条目块，也不从正文里出现 ID 推断定义。

模板中的 `{{TOKEN}}` 是待替换变量。heading.* 和 label.* 从 [简体中文资源](../assets/locales/zh-Hans.json) 或 [英文资源](../assets/locales/en.json) 取显示文字，其余由 agent 填入实际内容、已有引用或工具生成的 ID。替换元数据时使用合法 YAML 字符串转义，不把用户文本直接拼进 YAML。新增语言沿用同一变量键集，只翻译显示文字，不改变结构键、schema、ID 或关系。

模板输出不得残留变量。需求／用例／决策扩展为多项时，每个新对象独立分配 ID，不复制示例值；翻译既有对象则保留 ID。变更骨架可由 new 生成，其余模板由 agent 或人工填写；生成骨架后仍需消除占位符并检查真实内容。

## 标识符与引用

新 ID 使用 `tao id new <类型>` 分配，类型为 DOC、REQ、UC、ADR、TASK、CHG、EVD；已有对象保留 ID，不手工编造。完整格式 `类型_YYYYMMDD_16位随机串` 由注册表定义，分配日不要求与导入文档的 created 相同。

正文正式引用用 `{need}` 后接反引号包围的完整 ID；代码注释也使用完整 ID。不要把标题序号、文件内的“需求 2.1”或属性编号作为跨文档引用。需要独立引用的验收承诺拆成 REQ；可复用的验证场景或性质使用 UC，不另增局部 Property ID。

标题或文件移动保持 ID；拆成新对象或更改类型时分配新 ID 并保留关系。删除正式对象使用 [退役流程](retirement.md)。

同一版本的正式索引只允许一个定义；示例、档案和测试夹具不注册当前定义，多版本出版分别建索引。退役记录纳入 VCS 并参与查重，无法恢复历史基线时不能宣称查出了所有历史删除。外部项目的正式引用需显式导入索引，无可用索引时报告 unresolved。

文件导航用项目内相对 Markdown 链接，解析含符号链接的路径后不得越出项目；不使用本机绝对地址或 file://。外部资料使用项目可访问的稳定链接，引用范围遵循项目保密约定。发布时条目与章节使用稳定锚点及书籍解析入口，精确规则见 [出版规程](publication.md)。未实际构建并检查链接时，不要宣称移动后的 URL 已可用。

## 需求、用例与决策

创建或审查 REQ／UC／ADR 时读取 [条目写法](document-entries.md) 的对应段落和片段模板，语法、字段职责与语义检查在该处统一维护。

## 设计与验证内容

设计文档的固定章节区分边界与架构、接口与数据、不变量、失败处理、验证。完整流程中设计独立维护，plan.design 引用适用设计；具体组织见文档组织。确实无变化的方面可用一句说明，不复制整段代码充当设计。

明确系统边界与数据流、公开接口和调用方、数据约束和所有者、状态转换、失败后的状态与恢复。只记录影响决定的签名、模型、公式或图；详细实现由代码承担。已有基线时说明保持哪些可观察行为，避免把“优化”默认解释为允许语义变化。

verification 说明检查什么、输入与环境、比较基线、执行办法、通过条件及必要报告；正确性性质关联 UC，具体任务关联 REQ／CHG。选择单元、集成、端到端或属性测试依据风险和验证目标，不按固定测试次数或覆盖率一刀切。必要验证不能标成可选；不适用须说明条件依据。

性能与成本承诺需说明工作负载、规模、基线版本、环境、测量办法、重复次数或统计方法、阈值与容差。设计估算与实测数据明确区分；没有实测就保留待验证，不能把公式推导出的预期节省写成已达成收益。

## 任务与证据

正式 TASK 仅位于 tasks 章节，每项为扁平 checkbox 和固定字段；分组可用三级标题，不能再维护一份父任务完成状态：

```markdown
- [ ] `TASK_<YYYYMMDD>_<16位随机串>` 可验证的结果
  - relates: ["REQ_<YYYYMMDD>_<16位随机串>"]
  - depends_on: []
  - verify: 实际检查办法及预期结果。
```

checkbox 只接受 `[ ]` 或 `[x]`。字段行缩进两个空格，按 relates、depends_on、verify、evidence 排序；前三项必需。数组为单行 JSON 字符串数组，不允许重复成员；relates 至少一个 REQ 或 CHG，depends_on 仅引用其他 TASK 且无环。verify 是非空单行文本，任务说明修改范围与可验证结果，不能仅写“完成某模块”。

evidence 在勾选完成时必需，为验证记录的单个 Markdown 链接，通常指向计划 verification 的稳定章节锚点。依赖图、执行批次和反向引用由字段生成，不另维护父任务状态或 JSON waves。

plan 的 VERIFICATION 先写检查办法，执行后在 `<!-- tao:results -->` 与 `<!-- /tao:results -->` 之间补结果，避免执行记录改变计划批准。记录内容、输入引用和独立摘要的使用条件统一见 [证据保存](evidence-retention.md)。

独立 evidence 的 frontmatter result、coverage 表示本次结果与范围，recorded_at 元数据记录实际记录时刻；inputs.fingerprint 填受检输入引用，environment 填环境，checks 填命令／观察、预期、结果与报告入口，findings 填限制，retention 填保存安排。reports 可明确写原始输出未长期保存及原因；字段格式见注册表。

## 检查与修正

填写当前模板、替换全部变量并分配新 ID 后，运行 `tao verify --only docs`。普通局部文档维护以相称的文档检查结束；已接入完整交付流程的事项按 [流程操作](workflow.md) 执行交付检查。

独立 [源校验器](../scripts/validate_documents.py) 也接受 `--project <根目录>`、项目相对 Markdown 路径，以及可选 `--format json`、`--book-root <导航文件>`、`--diagnostic-locale <语言>`；使用已准备的核心环境。

| 结果 | 如何处理 |
|---|---|
| 结构、ID 或关系 error | 按定位修正；重复 ID、缺失验收、引用目标变化需语义判断 |
| 内容 warning | 结合语境复查，词语命中不自动判定需求无效 |
| 工具／配置故障 | 报告未完成，先解决运行条件 |

退出码 0 表示无 error（可含 warning），1 表示文档 error，2 表示工具或配置故障。按 rule_id、位置与 suggestion 定位，不匹配本地化消息文字；诊断提供实际 message_locale，未翻译消息回退英文。

未提供历史基线时 deletion_checked 为 false；未指定书根不代表已检查全书可达性。结构通过不等于语义验收或 HTML 构建通过。自动格式修正限于不改变语义的内容并展示差异；例外记录理由、范围、责任人与复查条件，不用全局忽略隐藏错误。
