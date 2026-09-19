# 审查调度记录

agent 已进入 review 且需要固定范围、保存受检输入或控制调用轮次时读取。审查方式、默认轮次和用户选择统一见 [审查规程](review.md)。本接口保存协调状态，不调用模型、不验证审查者身份；项目必需的独立审查证据仍用 [审查记录](review-receipts.md) 导入。

## 先预览与确认

`tao workflow review-preview <CHG-ID>` 默认选本次 feature/bug fix 的累计修改，按阶段选择 docs 或 code；命令行参数 --scope project 可预览全项目，--include <相对文件或目录> 可重复，--kind docs|code 可明确内容，--base <固定修订> 用于核实并确认新的比较基准。

预览返回完整 base/target commit、selected_files、上下文文件、排除项、总字节数及输入摘要。feature 包含基础提交以来的全部修改、暂存/未暂存修改及未忽略的新文件；基础版本不再是祖先时拒绝猜测，应调查 rebase 等情况并确认新基准。全项目模式不依赖 fork。文档阶段聚焦 Markdown，代码阶段仍对照适用文档；哪些规范已生效由审查者判断，不能把未来草稿当作现有代码的承诺。

确认范围、审查方式、实际可用审查者和预算后，把预览结果保存到项目 temporary 目录。保存的是预览输出中的 `outputs` 对象，不是带 `tool`、`status`、`diagnostics` 的完整命令信封；`review-begin --from` 只认该对象顶层的 `change`。传错形状会被拒绝并指出应改传 `outputs`。保存到受检源目录会改变输入，应重新预览。新批次默认时间预算为 7200 秒（2 小时），可按实际项目和用户决定调整；已有批次继续使用记录中的预算，省略参数不重置。预算从批次首次 review-begin 开始按墙钟时间累计，包含人的复查、讨论、修复及等待；当前调度器不调用模型，不能将这段时间解释为 LLM 实际审查耗时。这是调度窗口，不是供应商账单或远程进程的实时限制器。

本轮将新建的正式报告、裁决或专用导航，在预览时用可重复的 `--output <项目相对 Markdown 文件>` 逐个预留。路径必须尚不存在且不属于跟踪输入，不接受目录或 glob；预览的 output_files 与排除项一起确认。开始前仍须不存在，开始后仅这些文件不参与输入摘要；历史报告、其他新文件、源码和已有导航变更仍使输入过期。发布挂接若需修改已有导航，将该修改纳入受检版本或作为后续文档变更，不把它伪装成本轮新输出。无输出声明的旧记录沿用原绑定。

## 登记后派发

```text
tao workflow review-begin <CHG-ID> --expect <revision> --from <preview.json> --mode serial|parallel --reviewers <数量> --decision <确认内容>
```

开始前重新核对预览，输入变化即拒绝。登记成功后返回工作区与暂存区各自的受检 ZIP 快照、摘要和记录，agent 才派发审查。输入同时绑定工作区内容、文件模式及暂存区 blob/mode；暂存区与工作区不同也必须检查。快照包含受检文件及未修改上下文，删除项由范围与 Git 基准解释；只读检查快照和固定 Git 版本，不让子 agent 修改被审查文件。必要复现使用独立临时目录。

每轮记录 reviewers 个审查者，serial 为一个，parallel 最多三个；各自先独立形成判断，再由主 agent 合并重复发现并核实跨范围问题。多个并行审查者属于同一轮。审查者来源与授权按 [审查规程](review.md) 处理。

已登记为 running 的轮次必须先核对进程和实际结果，不再次派发。失败尝试也占用轮次。每个审查批次保存阶段、确认内容、开始时间和已用轮次；换会话、修复后复核或中断恢复不清零。用户明确发起新的阶段或范围审查时，重新确认并传 `--new-batch`，旧批次完整保留在 review_history，新批次独立计时计轮次；不因失败或预算耗尽自动新建批次。确有新证据、范围扩展或用户新预算时，可显式传 --max-rounds 与 --budget-seconds 调整累计上限，记录决定；不能由 agent 为了继续尝试自行增加。

## 汇总与停止

正式 Markdown 报告与裁决先按 [审查规程](review.md) 整理为受管理的 evidence 文档。review-end 仅核对报告文件及输入绑定，不代替输出的 schema、引用和适用的出版检查；临时原始输出按 [证据保存](evidence-retention.md) 保留，不能因登记成功就声称正式报告完整。

每个完成的审查者保存实际报告，主 agent 逐项裁决发现。用 JSON 写入 outcome（passed、changes-requested 或 failed）、reports（不同报告的项目相对路径数组）和 summary，再调用：

```text
tao workflow review-end <CHG-ID> --expect <revision> --from <result.json>
```

非失败结果必须有对应数量的非空报告；输入改变会记为 stale，超出时间预算记为 budget-exceeded。这些记录不自动满足 required_reviews，也不证明报告结论正确。历史变化或其他输入错误不阻止登记失败，错误原因随记录保留。失败或中断不能补造成功报告；记录实际失败后，由剩余预算决定能否重试。

修复、复核及新增范围按 [审查规程](review.md) 处理；原始快照与报告按 [证据保存](evidence-retention.md) 管理。
