# 开发动作

动作由 agent 执行，不登记流程状态。共同授权与输出规则见 [流程操作](workflow.md)，文档写法见 [文档规程](documents.md)。

## new

从业务目标、现有材料与代码澄清范围和验收；自行调查可查事实。依次创建或更新 spec、design、plan：规格写可观察承诺及场景；设计说明边界、接口、不变量、失败和重要取舍；计划引用依据并列可验证任务。任务默认内联，确有规模或并行编辑需要时由 tasks_doc 唯一关联一份附件，不维护两套任务。稳定 ID 由 `tao id new <TYPE> --count <N>` 提供；`tao new --slug <slug>` 仅生成计划骨架，不生成规格设计，不登记事项。CHG 由计划定义；计划前只需 spec/design。按已有授权连续推进，不要求逐篇批准。下一步：推荐 review doc；需求或方案仍不清晰则 refine。

## review doc

对照目标审查 spec/design/plan 的范围、可验收性、设计成本、任务覆盖和真实依赖，检查 ID、引用和导航。结构检查不证明内容正确。按风险选择独立审查，事实核实和处置方法见 [审查规程](review.md)。发现与长日志默认临时；只把有效长期决定同步回权威文档，计划保存当前摘要。下一步：修正缺陷用 refine，已就绪则 implement。

## implement

读取选定计划及唯一任务集，核对实际代码、已有修改和任务依赖，在授权内完成工作。依赖独立且文件边界清楚时可并行，由集成者统一验证。任务勾选反映实际实现进度；verify 说明检查方法，evidence 可选，不用证据文件作为完成勾选的形式门槛。运行项目实际需要且已获准的检查；未运行、失败及未覆盖范围如实记录。计划 verification 覆盖更新当前结果，不追加逐次执行历史。下一步：推荐 review code；需求或设计改变则 refine。

## review code

对照有效需求和设计检查实现、调用方、测试、失败路径、安全及不必要复杂度；核实问题再修复，按影响复核。说明实际审查者、范围及未验证内容，独立审查不可用不得冒充已执行。审查结论不由任务计数推断，不导入回执、不注册轮次。下一步：修复并针对性复核，或报告完成范围并由用户选择后续事项、提交/发布（需相应授权）或显式 handoff；没有 finish。

## refine

明确本次变化，更新同一权威规格、设计、计划及受影响任务，保持原对象 ID。推翻关键假设时暂停依赖工作并解决决定，不重新走形式审批。下一步：按影响推荐 review doc、implement 或 review code。

## status

只读 `tao status [CHG|DOC|计划相对路径]`，未指定目标列出项目计划及尚无计划的规格/设计。汇总未完成任务、计划验证摘要和建议，不执行检查、不写配置或状态。planning/pending/in_progress/implementation_complete 均为推断进度，不是已审查或已交付。审查无记录为 unknown。下一步：选择一个计划 continue，或对规划材料 refine/new。

## continue

从用户指定目标或 status 候选读取 plan/tasks、相关 spec/design 和实际文件；临时交接若存在仅辅助理解，不能覆盖当前事实。根据剩余任务和当前摘要恢复工作，不登记、不迁移、不恢复状态数据库。下一步：推荐实际需要的 refine、review doc、implement 或 review code，并在授权内推进。

## handoff

仅显式执行。编写普通 Markdown，包含目标、权威文件、当前实际结果、关键决定、限制和下一步，调用 `tao handoff [CHG|DOC|计划相对路径] --from <项目相对 Markdown>`。省略目标仅在唯一计划时可用。保存到配置的 temporary/handoffs/<CHG-or-DOC>.md，覆盖同一事项的摘要；不生成 DOC/EVD、不改计划、不入 book。下一步：新会话 continue；没有交接也可直接继续。
