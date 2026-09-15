# 文档编写与校验规程

创建、修改、审查 tao 管理文档时，读取本文涉及的规则段及当前 profile 模板；同一任务确实修改多类文档时才读取多个模板。普通代码、测试或配置修改没有文档同步职责时不读取本文。文档格式由同包的 [格式注册表](../assets/document-profiles.json) 和模板提供。

按本次工作定向读取补充规程：需要选择位置、拆分文件或组织书籍导航时读 [文档组织](document-layout.md)；决定验证结论、报告或临时产物的保存方式时读 [证据与产物保存](evidence-retention.md)；生成不同语言版本或翻译时读 [本地化](localization.md)；实际检查或修正文档时读 [诊断](document-diagnostics.md)；构建、发布或分享书籍链接时读 [出版](publication.md)；遇到不清楚的概念或前缀时查 [术语表](glossary.md)。编写或审查正式 REQ／UC／ADR 时读 [公共依据与写法](document-standards.md)。不满足触发条件就停止，不沿引用递归加载其他规程或未使用的模板。

## 受控术语

只提升跨文档易混淆或反复误用的词，局部术语留在所属规格或设计。项目 glossary 的 terms 节用 `{term} 首选名称` 围栏，正文为定义；可选 `:english:`、`:code:`、`:scope:` 和 `:avoid:`（JSON 字符串数组）。不新增 TERM ID；定义只维护一处，其他位置链接。校验器检查条目结构、同范围重名与自相矛盾的禁用名称；语义误用由审查判断，不全文禁止“身份”等多义词或误报反例。

## 选择范围与职责

新建的 tao 管理文档使用注册表中的 profile，不让用户设计 schema。已有项目可映射文档目录、选择显示语言，并在项目开发约定中明确拆分阈值；不能仅为通过检查改写 ID、字段或引用语法。用户明确要求不同格式时尊重该约定，并将该部分标为未按 tao 格式校验，不能宣称等价通过。

接入时明确管理范围：纳入范围的文档必须有受支持的 schema，缺少或未知 schema 报错；未接入的历史文档列为范围外，不悄悄计入覆盖率。按本次修改需要逐步接入，普通 README、外部资料与客户端 manifest 不因使用 Markdown 就自动纳入。配置和适配由 agent 复用已有约定，确有冲突才交由用户决定。

格式注册表权威定义 profile 名称、元数据字段、章节顺序、条目字段和模板位置；本文解释内容要求、引用与完成语义。模板是这些规则的写作起点，不能反过来修改规则以适配模板。注册表是机器可读的格式目录，**不是完整 JSON Schema 或 Markdown 校验器**。实际检查范围与结果解释见 [诊断规程](document-diagnostics.md)。

## 文档选择与目录

下表为默认位置，目录可映射，profile 和字段含义不随目录改变。每次只创建实际需要的文件。

| 内容与默认位置 | profile | 模板 |
|---|---|---|
| 书／篇／多页章入口 `<group>/index.md` | `tao.project.navigation/v0.1` | [navigation](../assets/templates/navigation.md) |
| 能力规格 `docs/product/<capability>.md` | `tao.project.spec/v0.1` | [spec](../assets/templates/spec.md) |
| 一次交付计划 `docs/plans/<yyyy-mm>/<yyyymmdd>-<slug>.md` | `tao.project.plan/v0.1` | [plan](../assets/templates/plan.md) |
| 系统／模块设计 `docs/engineering/<module>.md`，或计划的设计附件 | `tao.project.design/v0.1` | [design](../assets/templates/design.md) |
| 计划的任务附件 `<plan-stem>/tasks.md` | `tao.project.tasks/v0.1` | [tasks](../assets/templates/tasks.md) |
| 长期决定 `docs/engineering/decisions/<slug>.md` | `tao.project.decision/v0.1` | [decision](../assets/templates/decision.md) |
| 用户操作 `docs/user/<operation>.md` | `tao.project.user-guide/v0.1` | [user-guide](../assets/templates/user-guide.md) |
| 运维操作 `docs/operations/<operation>.md` | `tao.project.runbook/v0.1` | [runbook](../assets/templates/runbook.md) |
| 项目术语 `docs/glossary.md` | `tao.project.glossary/v0.1` | [glossary](../assets/templates/glossary.md) |
| 按需独立检查摘要 `<plan-stem>/evidence/<slug>.md` | `tao.project.evidence/v0.1` | [evidence](../assets/templates/evidence.md) |
| 恢复摘要 `<plan-stem>/handoff.md` | `tao.project.handoff/v0.1` | [handoff](../assets/templates/handoff.md) |

没有关联开发工作的检查放在 `docs/evidence/`；交接关联已有计划或计划生成前的工作流，使用预留计划位置。规格定义承诺，计划引用这些定义并说明本次差异。内容归属、文件命名及拆分阈值的权威规则见 [文档组织](document-layout.md)；目录、章节含义与注册表保持一致。

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

完整 ID 格式由注册表的 id.pattern 定义：`类型_YYYYMMDD_16位随机串`，例如 `REQ_20260914_7M2K9X4C6P8R3T5V`。类型有 DOC、REQ、UC、ADR、TASK、CHG、EVD。日期是首次分配日，随机串使用 `0123456789ABCDEFGHJKMNPQRSTVWXYZ`，将安全随机源独立生成的 10 字节按大端编码为 16 位，保留前导零。完整 ID 分配后固定，不强制分配日与导入文档的 created 相同。

校验真实日历日期、完整 ID 唯一性和引用类型。随机串每位均可使用完整字符集，不套用 ULID 首位限制。生成时检查当前索引和退役记录，完整碰撞则重新生成，每次调用总共最多 3 个候选，仍失败时报错。不得凭模型猜写、用时间或流水号代替随机部分。

正文正式引用用 `{need}` 后接反引号包围的完整 ID；代码注释也使用完整 ID。不要把标题序号、文件内的“需求 2.1”或属性编号作为跨文档引用。需要独立引用的验收承诺拆成 REQ；可复用的验证场景或性质使用 UC，不另增局部 Property ID。

标题或文件移动保持 ID；拆分成新对象、更改对象类型时分配新 ID 并保留关系。正式退役保留原定义及 retired 状态，或移除正文并在 `docs/retired/<yyyymmdd>.jsonl` 留一条最小记录。日期取实际退役的本地日期，而非 ID 的创建日期。记录包含 id、retired_on、非空 reason、replaced_by（同类型 ID 数组，无替代者时为 []）；精确字段见注册表的 retirement_records。两处不重复定义，替代链无环。文档退役同时处理其拥有的条目，避免遗留悬空引用；临时未索引草稿可直接删除。

退役文件采用 UTF-8，每行一个完整 JSON 对象；不使用 Markdown frontmatter，不允许重复键、未知字段或空白记录。文件名去掉扩展名后必须与 retired_on 去掉连字符一致，日期需日历合法。同一 ID 在全部日期文件中只能出现一次；修正已有记录在原处修改，不以追加第二行表示新事件。它是按日期分组的当前退役索引，不是依赖行序重放的事件日志。

新增退役时读取全部退役文件及当前源文档，检查重复、同类型替代目标及关系环；替代目标必须可解析且不能是自身。同日并发或分支合并后按 ID 检查，不能只拼接文本或用最后一行覆盖矛盾记录。JSONL 不作为 Markdown 章节挂入 toctree，但参与全局 ID 索引、查重、引用诊断及退役说明页生成；不能因它不在正文导航中而漏检。

`tao retire <ID> --reason <说明>` 默认只读预览；在已有退役授权内，agent 查看受影响对象与诊断，再用 --apply 写入，不要求用户重复批准已授权动作。--replaced-by 可重复指定同类型替代对象，不自动改写消费者引用。退役 DOC、CHG 或 EVD 时需移除整份拥有文档，并为其全部正式定义留记录；预览必须列全这些 ID，不能只移除必需元数据后留下无效文件。REQ、UC、ADR 和 TASK 则移除完整条目，保留相邻正文与标识符。

写入前校验最终文档集合、导航、文件链接及退役关系；删除后必需章节为空、规格没有需求、计划没有任务或留下坏文件链接时拒绝写入，由 agent 先完成必要的文档调整。已有相同记录可重试，不追加重复行；原因或替代关系不同则报冲突，不悄悄改写历史退役。使用配置的 retired 目录，文件日期取实际退役的本地日期，恢复中断操作时保留原记录日期。

退役中断后先检查源文档与退役记录，再用相同参数重试。中间状态可能报告重复定义；不要隐藏诊断、改写不一致记录或自动删除锁。

retired 表示条目已退出当前有效集合；deprecation 表示不建议继续使用，但不一定已经移除。功能弃用及迁移安排写在相关规格和使用说明中，不因此自动删除条目或生成退役记录。

同一版本的正式索引只允许一个定义；示例、档案和测试夹具不注册当前定义，多版本出版分别建索引。退役记录纳入 VCS 并参与查重，无法恢复历史基线时不能宣称查出了所有历史删除。外部项目的正式引用需显式导入索引，无可用索引时报告 unresolved。

文件导航用项目内相对 Markdown 链接，解析含符号链接的路径后不得越出项目；不使用本机绝对地址或 file://。外部资料使用项目可访问的稳定链接，引用范围遵循项目保密约定。发布时条目与章节使用稳定锚点及书籍解析入口，精确规则见 [出版规程](publication.md)。未实际构建并检查链接时，不要宣称移动后的 URL 已可用。

## 需求、用例与决策

编写或审查这些条目前，读取 [公共依据与写法](document-standards.md)：行为需求默认采用 EARS，场景沿用 Given／When／Then，决策沿用 ADR。该规程定义模板变量的内容职责、中英文表达及标准与自定义规则的边界。

正式条目是文档顶层的三反引号 MyST 风格块，仅支持 req、uc、adr。读取 [REQ 片段](../assets/templates/req-block.md)、[UC 片段](../assets/templates/uc-block.md) 或 [ADR 片段](../assets/templates/adr-block.md) 获取精确写法。围栏内先列选项，空一行再写正文；不得嵌套到列表、引用或其他正式条目中。展示示例时使用四反引号外层围栏，不把示例注册为对象。

共同选项为必需的 id、status，以及可选 links、supersedes；UC 还必须提供 verifies。关系值为逗号分隔的完整 ID，不允许空成员或重复成员；verifies 只指向 REQ，supersedes 只指向同类型。status 使用 proposed、accepted、retired、superseded。superseded 对象应能通过另一条目的 supersedes 找到替代者。

正文用 `<!-- tao:field key -->` 标明字段，后接一个非空 Markdown 段落；字段顺序与注册表一致。字段以结构键标识，显示文字可本地化；显示结构另按条目规则检查。未规定标签样式的条目可调整加粗和标点。字段键仅在正文顶层生效，代码和引用中的同名文本不生效。字段需要多项独立承诺时拆条目，不用嵌套列表暗中引入局部编号体系。

- **REQ：** 正文用 EARS 表达一个可独立验收的行为承诺；acceptance 补充验证输入、方法和判据或引用 UC，不重复正文或新增承诺；source 记录依据与必要动机。非行为约束可用更明确的公式、表格或约束表达，保留可判定性；用户故事不能替代系统承诺。
- **UC：** given 定义前置条件、输入域与约束，when 定义事件或操作序列，then 定义预期结果。表达性质时写清“对任意满足条件的输入”及可判定谓词，例如往返恒等、拒绝操作后状态恢复、增量与基线等价；通过 verifies 关联需求。测试数量和随机试验通过不是形式化证明。
- **ADR：** context 说明问题、约束与实际备选；decision 说明选择及理由；consequences 写代价、限制及后续责任。临时设计选择可留在计划，长期约束使用单独决定文档。

ADR 三个字段都必须以“加粗的纯文本标签＋冒号＋非空说明”开始，注册表以 `field_label_style: strong` 声明这一显示约束。中文模板使用“背景与备选／选择／代价”，英文使用“Context and alternatives／Decision／Consequences”。允许翻译标签，冒号可为半角或全角、位于加粗范围内或紧随其后，例如 `**选择：** 采用独立环境。` 或 `**Decision**: Use an isolated environment.`。标签不能省略，也不能只有标签而没有说明；行内代码不能冒充加粗标签，HTML 注释不能充当说明。这是 tao-dev 的阅读格式约束，不把特定中文词语用作机器键。内容是否充分比较备选、解释选择和评估影响仍须语义审查。

每个规格至少一个 REQ；有用例或性质时使用 UC。REQ 仅定义在 requirements，UC 在 cases 或 invariants（用户明确选择合并文档时可在 plan.design），ADR 在 decisions、design 或 architecture；类型位置也由注册表校验。同一条件在需求、设计、任务间通过 ID 引用，不抄写多份验收标准。

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

evidence 可选，但勾选完成时必需，为指向验证记录的单个 Markdown 链接，默认指向本计划的 verification 章节，也可指向独立 evidence 摘要或实际报告；不要求另建文件或 EVD。章节链接使用出版规程定义的稳定锚点。链接存在不自动代表完成，checkbox 也不代表已合并或发布。依赖图、执行批次、反向引用和覆盖表由字段生成，不另手工维护 JSON waves 或重复状态。

plan 模板的 VERIFICATION 先填写检查办法，执行后在同一章节的 `<!-- tao:results -->` 与 `<!-- /tao:results -->` 之间补充受检输入、时间、命令与环境、结果、范围及保存情况；不用另一份文档重复这些内容。独立 evidence 模板仅在 [保存规则](evidence-retention.md) 要求拆分时使用，其中 reports 字段可写“原始输出未长期保存”及原因，无需伪造报告链接。

evidence 文档 frontmatter 的 result 记录本次结果，coverage 记录本次覆盖；两者不能代替完整交付验证。recorded_at 是实际记录时刻，不能用提交时刻冒充执行时刻。正文 inputs 的 fingerprint 字段记录受检输入引用，优先使用固定 VCS 版本、范围及版本一致性结论；有未提交输入时按 [保存规则](evidence-retention.md) 补充，environment 记录必要环境；checks 记录命令或人工观察步骤、预期、实际观察与报告入口；findings 说明限制；retention 说明保存位置与期限。各字段键见注册表。无法还原输入或取得报告时如实说明限制，不虚构哈希、版本对应关系或 passed。

报告目录、持久保存、VCS 归属与受检输入的排除边界统一见 [证据与产物保存](evidence-retention.md)。日志未保存或过期不自动否定历史结果；当前复用须满足输入一致性、摘要充分性和项目要求的材料保存条件。

## 使用模板与检查

1. 从已有目标确定文档职责与管理范围，选择注册表中的 profile 和模板，复用已有权威文件。
2. 按项目语言替换显示标签与内容，用实际工具分配新 ID；现有对象只引用，所有模板变量须消除。
3. 按源文定义建立索引，再解析引用与依赖；检查必需章节、字段、日期、重复 ID、未知 schema 和未决项。引用存在只证明可解析，不证明设计满足需求。
4. 修改文档后执行 `tao verify --only docs`，交付前按流程执行完整验证。另按项目工具检查行为，注明各自范围。
