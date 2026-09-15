# 需求、用例与决策条目

编写或审查 REQ／UC／ADR 时读取对应小节及片段模板。共同元数据、ID 和文档检查见 [文档规程](documents.md)；精确字段与允许位置以 [格式注册表](../assets/document-profiles.json) 为准。

## 共同语法

正式条目使用文档顶层的三反引号 MyST 块，类型为 req、uc、adr；选项后空一行再写正文，不嵌入列表、引用或其他条目。共同选项为 id、status，以及可选 links、supersedes；UC 必须有 verifies。关系值是逗号分隔的完整 ID，不含空项或重复项；verifies 指向 REQ，supersedes 指向同类型。status 使用 proposed、accepted、retired、superseded；superseded 对象须有另一条目的 supersedes 指向它。

字段用 `<!-- tao:field key -->` 标记，顺序遵循注册表，每个字段为非空 Markdown 段落；标记在代码或引用中不生效。多个独立承诺拆成条目，通过 ID 关联，不维护局部编号或复制验收标准。

## REQ：系统承诺

使用 [REQ 片段](../assets/templates/req-block.md)，在 spec.requirements 定义；每份规格至少一个 REQ。正文采用 EARS 条件化表达，每个 REQ 对应可独立接受、修改或失败的一个承诺：

| 条件 | 中文写法 | 英文关键词 |
|---|---|---|
| 始终适用 | 系统应…… | shall |
| 事件触发 | 当……时，系统应…… | When |
| 状态持续 | 在……期间，系统应…… | While |
| 产品包含某功能 | 对于包含……功能的版本，系统应…… | Where |
| 异常发生 | 如果……，则系统应…… | If / then |
| 组合条件 | 按适用条件、状态、触发、响应组织 | 组合上述关键词 |

例如：当用户取消导出时，导出器应停止该次导出。英文正文使用 shall 表示承诺；Where 表示产品包含某功能，While 表示运行状态。只选适用条件，不为填满类型添加需求。

- REQ_BODY：系统主体、条件与可观察响应。验收必要的时间、容量、精度须有单位与测量条件；未知数值留作未决项。
- REQ_ACCEPTANCE：验证输入、观察方法和通过判据，或引用 UC；不重复正文或增加承诺。
- REQ_SOURCE：真实来源与必要动机。

范围、术语和设计理由不套 EARS。公式、状态机或决策表更清楚时引用其权威定义及判定办法；用户故事可解释动机，不能代替系统承诺。

## UC：场景与性质

使用 [UC 片段](../assets/templates/uc-block.md)，位于 cases 或 invariants；用户明确合并文档时也可位于 plan.design。

- UC_GIVEN：初始条件、输入域和约束。
- UC_WHEN：触发动作或操作序列。
- UC_THEN：可观察、可断言的结果；性质说明适用输入范围和谓词。
- verifies：关联被验证的 REQ。

项目已有可执行 Gherkin 场景时引用其位置和关联 ID，不复制步骤。MyST UC 本身不是可执行测试；随机试验通过不等于形式化证明。

## ADR：选择与后果

使用 [ADR 片段](../assets/templates/adr-block.md)，位于 decisions、design 或 architecture。长期决定的抽取条件见 [文档组织](document-layout.md)。

- ADR_CONTEXT：问题、约束和实际备选。
- ADR_DECISION：选择与理由。
- ADR_CONSEQUENCES：收益、代价、限制与后续责任。

每个字段以加粗纯文本标签、冒号和非空说明开始，例如 `**选择：** 采用独立环境。`。标签可翻译，冒号可为半角或全角、位于加粗范围内或紧随其后；结构键保持不变。

## 内容审查

检查条件类型、系统主体、响应可观察性、独立承诺拆分，以及验收是否改变原需求。中文不要求英文关键词；句式匹配不能证明语义正确。当前没有 EARS 语义检查器，结构检查与实际验收分别报告。
