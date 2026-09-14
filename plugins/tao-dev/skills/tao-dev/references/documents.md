# 文档编写与校验规程

创建、修改、审查 tao 管理的规格、设计、计划、任务或证据时读取本文，再按需要读取相应模板。**文档格式由 tao-dev 提供；使用方填写内容，CLI 实现同一契约的确定性检查。** 本文、[格式注册表](../assets/document-profiles.json) 与模板随 skill 分发，运行时不依赖开发仓库。

按本次工作定向读取补充规程：确定目录、拆分或保存报告读 [文档组织](document-layout.md)，生成或翻译文档读 [本地化](localization.md)，检查与修正文档读 [诊断](document-diagnostics.md)，出版及分享链接读 [出版](publication.md)，理解概念或前缀时查 [术语表](glossary.md)。这些也是随包的权威规则，无需一次加载全部参考。

## 选择范围与职责

新建的 tao 管理文档使用注册表中的 profile，不让用户设计 schema。已有项目可映射文档目录、选择显示语言和配置拆分阈值；不能仅为通过检查改写 ID、字段或引用语法。用户明确要求不同格式时尊重该约定，并将该部分标为未按 tao 格式校验，不能宣称等价通过。

接入时明确管理范围：纳入范围的文档必须有受支持的 schema，缺少或未知 schema 报错；未接入的历史文档列为范围外，不悄悄计入覆盖率。按本次修改需要逐步接入，普通 README、外部资料与客户端 manifest 不因使用 Markdown 就自动纳入。配置和适配由 agent 复用已有约定，确有冲突才交由用户决定。

格式注册表权威定义 profile 名称、元数据字段、章节顺序、条目字段和模板位置；本文解释内容要求、引用与完成语义。模板是这些规则的写作起点，不能反过来修改规则以适配模板。注册表是机器可读的格式目录，**不是完整 JSON Schema 或 Markdown 校验器**。未来 CLI 读取同包注册表，用 Markdown AST 校验结构、关系与源位置；目前可按本文手工编写和复核，不报告自动校验成功。

## 文档选择与目录

下表为默认位置，目录可映射，profile 和字段含义不随目录改变。每次只创建实际需要的文件。

| 内容与默认位置 | profile | 模板 |
|---|---|---|
| 能力规格 `docs/product/<capability>.md` | `tao.project.spec/v0.1` | [spec](../assets/templates/spec.md) |
| 一次交付计划 `docs/changes/<date>-<seq>-<slug>.md` | `tao.project.change/v0.1` | [change](../assets/templates/change.md) |
| 系统／模块设计 `docs/engineering/<module>.md`，或计划的设计附件 | `tao.project.design/v0.1` | [design](../assets/templates/design.md) |
| 计划的任务附件 `<plan-stem>/tasks.md` | `tao.project.tasks/v0.1` | [tasks](../assets/templates/tasks.md) |
| 长期决定 `docs/engineering/decisions/<slug>.md` | `tao.project.decision/v0.1` | [decision](../assets/templates/decision.md) |
| 用户操作 `docs/user/<operation>.md` | `tao.project.user-guide/v0.1` | [user-guide](../assets/templates/user-guide.md) |
| 运维操作 `docs/operations/<operation>.md` | `tao.project.runbook/v0.1` | [runbook](../assets/templates/runbook.md) |
| 项目术语 `docs/glossary.md` | `tao.project.glossary/v0.1` | [glossary](../assets/templates/glossary.md) |
| 实际检查摘要 `<plan-stem>/evidence/<slug>.md` | `tao.project.evidence/v0.1` | [evidence](../assets/templates/evidence.md) |
| 恢复摘要 `<plan-stem>/handoff.md` | `tao.project.handoff/v0.1` | [handoff](../assets/templates/handoff.md) |

一次检查或交接没有关联变更时，分别放在 `docs/evidence/` 或 `docs/handoffs/`。规格定义承诺，计划引用这些定义并说明本次差异。内容归属、文件命名、拆分阈值及日期序号登记的权威规则见 [文档组织](document-layout.md)；目录、章节含义与注册表保持一致。

拆分时计划通过 `tasks_doc`、`design_doc` 引用附件 DOC；附件通过 `change` 引用计划定义的 CHG。原章节只留对应 `{need}` 引用和职责说明，不能保留第二份正文。当前 tasks_doc 指向一份完整任务集合，不通过普通正文引用暗中扩展为多份任务附件；扩展该关系须先定义并验证格式。计划及其任务附件合起来至少有一个 TASK。

## 元数据、结构与语言

UTF-8 Markdown 以 YAML frontmatter 开始。共同必需字段为 `schema`、`id`、`title`、`locale`、`status`、`created`，可选 `updated`；含义与枚举以注册表为准。字符串非空，拒绝重复键、未知字段、自定义 YAML tag。`id` 是文档自身的 DOC ID；正文恰有一个一级标题，与 title 一致。status 的 accepted 来自实际评审决定，不能由格式通过自动设置，也不代表文中所有条目均已接受。

日期采用带引号的 `YYYY-MM-DD` 本地日历日期，updated 不能早于 created；精确记录使用带数值 UTC 偏移量或 Z 的 RFC 3339 时间戳。created 不因编辑变化，updated 只在语义修改时更新；已有日期不因环境变化重算。导入文档无法确认创建日期时，记录首次纳入管理的日期并说明依据，不猜原始日期。不要把这些元数据加入 SKILL.md、agent 或 manifest，它们遵循自身格式。

每个二级标题紧邻前置稳定键，顺序必须与 profile 的 sections 完全一致：

```markdown
<!-- tao:section scope -->
## 目标与边界
```

章节键与字段键均匹配 `[a-z][a-z0-9-]*`，不依赖标题翻译或序号。二级章节不能增删或改序，细节放在三级及以下且不跳级。必需章节确实不适用时写一句具体依据，不留空或复制模板提示；规格的术语章节优先链接项目术语表，不重复定义。

change profile 的 `change` 定义一个 CHG ID；evidence profile 的 `evidence` 定义一个 EVD ID。其他 profile 的 `change` 仅引用 CHG；附件引用字段只引用 DOC，不创建新对象。不提供 `{chg}`、`{evd}` 条目块，也不从正文里出现 ID 推断定义。

模板中的 `{{TOKEN}}` 是待替换变量。heading.* 和 label.* 从 [简体中文资源](../assets/locales/zh-Hans.json) 或 [英文资源](../assets/locales/en.json) 取显示文字，其余由 agent 填入实际内容、已有引用或工具生成的 ID。替换元数据时使用合法 YAML 字符串转义，不把用户文本直接拼进 YAML。新增语言沿用同一变量键集，只翻译显示文字，不改变结构键、schema、ID 或关系。

模板输出不得残留变量。需求／用例／决策扩展为多项时，每个新对象独立分配 ID，不复制示例值；翻译既有对象则保留 ID。当前模板供 agent 或人工填写，尚无自动模板引擎。

## 标识符与引用

完整 ID 格式由注册表的 id.pattern 定义：`类型_YYYYMMDD_16位随机串`，例如 `REQ_20260914_7M2K9X4C6P8R3T5V`。类型有 DOC、REQ、UC、ADR、TASK、CHG、EVD。日期是首次分配日，随机串使用 `0123456789ABCDEFGHJKMNPQRSTVWXYZ`，将安全随机源独立生成的 10 字节按大端编码为 16 位，保留前导零。这是 tao-dev 的自定义格式，不是标准 ULID；含三字母类型前缀的 ID 为 29 个字符，TASK 为 30 个字符。完整 ID 分配后固定，不强制分配日与导入文档的 created 相同。

校验真实日历日期、完整 ID 唯一性和引用类型。随机串每位均可使用完整字符集，不套用 ULID 首位限制。生成时检查当前索引和退役记录，完整碰撞则重新生成，每次调用总共最多 3 个候选，仍失败时报错。不得凭模型猜写、用时间或流水号代替随机部分。

正文正式引用用 `{need}` 后接反引号包围的完整 ID；代码注释也使用完整 ID。不要把标题序号、文件内的“需求 2.1”或属性编号作为跨文档引用。需要独立引用的验收承诺拆成 REQ；可复用的验证场景或性质使用 UC，不另增局部 Property ID。

标题或文件移动保持 ID；拆分成新对象、更改对象类型时分配新 ID 并保留关系。正式退役保留原定义及状态，或移除正文并在 `.tao/retired.jsonl` 留一条记录：id、retired_on、非空 reason、replaced_by（同类型 ID 数组）。两处不重复定义，替代链无环。文档退役同时处理其拥有的条目，避免遗留悬空引用；临时未索引草稿可直接删除。

同一版本的正式索引只允许一个定义；示例、档案和测试夹具不注册当前定义，多版本出版分别建索引。退役记录纳入 VCS 并参与查重，无法恢复历史基线时不能宣称查出了所有历史删除。外部项目的正式引用需显式导入索引，无可用索引时报告 unresolved。

文件导航用项目内相对 Markdown 链接，解析含符号链接的路径后不得越出项目；不使用本机绝对地址或 file://。外部资料使用项目可访问的稳定链接，引用范围遵循项目保密约定。发布时条目与章节使用稳定锚点及书籍解析入口，精确规则见 [出版规程](publication.md)。出版尚未实现时不要宣称移动后的 URL 已可用。

## 需求、用例与决策

正式条目是文档顶层的三反引号 MyST 风格块，仅支持 req、uc、adr。读取 [REQ 片段](../assets/templates/req-block.md)、[UC 片段](../assets/templates/uc-block.md) 或 [ADR 片段](../assets/templates/adr-block.md) 获取精确写法。围栏内先列选项，空一行再写正文；不得嵌套到列表、引用或其他正式条目中。展示示例时使用四反引号外层围栏，不把示例注册为对象。

共同选项为必需的 id、status，以及可选 links、supersedes；UC 还必须提供 verifies。关系值为逗号分隔的完整 ID，不允许空成员或重复成员；verifies 只指向 REQ，supersedes 只指向同类型。status 使用 proposed、accepted、retired、superseded。superseded 对象应能通过另一条目的 supersedes 找到替代者。

正文用 `<!-- tao:field key -->` 标明字段，后接一个非空 Markdown 段落；字段顺序与注册表一致。显示标签可翻译、改标点或取消加粗，解析只认结构键。字段键仅在正文顶层生效，代码和引用中的同名文本不生效。字段需要多项独立承诺时拆条目，不用嵌套列表暗中引入局部编号体系。

- **REQ：** 一个可独立验收的承诺；交代谁受益、需要什么及原因，用户故事句式可选。acceptance 写清条件／触发、系统主体、可观察结果与验证方式；source 记录需求依据。普通行为、持续状态、异常输入和可选功能按实际涉及情况覆盖。可借鉴 EARS 的条件句式，但不强制中文夹写 WHEN／SHALL，也不靠关键词存在判断需求正确。
- **UC：** given 定义前置条件、输入域与约束，when 定义事件或操作序列，then 定义预期结果。表达性质时写清“对任意满足条件的输入”及可判定谓词，例如往返恒等、拒绝操作后状态恢复、增量与基线等价；通过 verifies 关联需求。测试数量和随机试验通过不是形式化证明。
- **ADR：** context 说明问题、约束与实际备选；decision 说明选择及理由；consequences 写代价、限制及后续责任。临时设计选择可留在计划，长期约束使用单独决定文档。

每个规格至少一个 REQ；有用例或性质时使用 UC。REQ 仅定义在 requirements，UC 在 cases 或 invariants（紧凑计划可在 design），ADR 在 decisions、design 或 architecture；类型位置也由注册表校验。同一条件在需求、设计、任务间通过 ID 引用，不抄写多份验收标准。

## 设计与验证内容

设计文档的固定章节区分边界与架构、接口与数据、不变量、失败处理、验证。紧凑计划在 design 章节简明覆盖受影响的这些方面；确实无变化的方面可以合并一句说明，不能靠复制整段代码充当设计。

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

evidence 可选，但勾选完成时必需，为指向可复查报告的单个 Markdown 链接；有证据不自动代表完成，checkbox 也不代表已合并或发布。原始报告可先直接链接；使用 tao.project.evidence 摘要时，其中列出报告、输入、结果与限制。依赖图、执行批次、反向引用和覆盖表由字段生成，不另手工维护 JSON waves 或重复状态。

evidence 文档 frontmatter 的 result 记录本次结果，coverage 记录本次覆盖；两者不能代替完整交付验证。recorded_at 是实际记录时刻，不能用提交时刻冒充执行时刻。正文 inputs 记录实际输入指纹与环境；checks 记录命令或人工观察步骤、预期、实际观察与报告入口；findings 说明限制；retention 说明保存位置与期限。各字段键见注册表。无法取得指纹或报告时如实说明缺失，不虚构哈希或 passed。

报告目录、持久保存、VCS 归属与输入指纹的排除边界统一见 [文档组织规程](document-layout.md)。报告不可读取、已过期或输入变化时，不能继续把旧证据当作当前通过依据。

## 使用模板与检查

1. 从已有目标确定文档职责与管理范围，选择注册表中的 profile 和模板，复用已有权威文件。
2. 按项目语言替换显示标签与内容，用实际工具分配新 ID；现有对象只引用，所有模板变量须消除。
3. 按源文定义建立索引，再解析引用与依赖；检查必需章节、字段、日期、重复 ID、未知 schema 和未决项。引用存在只证明可解析，不证明设计满足需求。
4. CLI 可用后在修改文档时执行 `tao verify --only docs`，交付前按流程执行完整验证。当前采用实际可用的检查并注明手工或临时校验范围。

CLI 不自行发明另一套格式，也不在执行时让模型猜章节或把每个项目的自然语言约定当成 schema。新增 profile 或结构字段需在 tao-dev 的注册表、规程、模板和验证夹具中一起修改；第三方项目无需重复定义这套格式。
