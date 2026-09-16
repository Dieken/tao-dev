# 审查记录与输入绑定

当项目配置了 required_reviews，或需要保存可供 verify 检查的独立审查结果时读取本文。规程约束判断方法；本接口只核对记录与当前产物的一致性，不证明结论正确、身份真实或授权有效。

## 操作

1. agent 调用 `tao review <CHG-ID> --format json`，取得 request.binding 和必需审查名称。此操作只读，不启动模型、不创建报告，不构成审查完成。
2. 按 [审查规程](review.md) 固定输入，向独立审查者提供适用要求、实际产物、相关调用方和验证依据，以及完整 binding。input_ref 写可还原的固定 VCS 版本或快照及实际审查范围；只有 HEAD 且工作区有修改时不能声称输入已固定。binding 的合并哈希用于检查一致性，不是备份。
3. 保存审查者的实际结构化结论与来源，agent 在项目临时目录编写以下记录，调用 `tao review <CHG-ID> --from <项目相对路径>` 导入。未完成、无来源或无结论不得补写成功记录。无法取得受支持的原始输出时保留真实报告并说明未导入，不改称人工审查；必需证据仍保持未满足。
4. `tao status <CHG-ID>` 只读显示审查时效；完整 `tao verify <CHG-ID>` 汇总各必需审查。输入变化后旧报告不能直接换 binding 再导入，应按影响进行实际复核；原始结论内的 binding 也必须匹配。

## 记录格式

UTF-8 JSON 对象，schema 为 `tao.review/v0.1`。下表列出全部必需字段；拒绝未知字段和重复 JSON 键，不提供 passed 字段。结构校验由 [审查模块](../scripts/taolib/reviews.py) 实现。

| 字段 | 内容 |
|---|---|
| schema | 固定 `tao.review/v0.1` |
| requirement | required_reviews 中的一个唯一名称；小写单词用连字符分隔 |
| binding | request 返回的 source_digest、policy_digest、change 原样保留，不手工重算或替换 |
| input_ref | 非空的固定输入引用及实际审查范围；可还原性仍须实际核实 |
| recorded_at | 带偏移量的 ISO 8601 时间戳，不得晚于当前时间；不是记录导入时间 |
| author | name、context，均为非空字符串；context 是作者会话或人工工作上下文的实际标识 |
| reviewer | kind、name、context、model、provider；kind 为 human 或 model；context 必须不同于作者 |
| source | path、sha256、format；path 为项目内相对路径，sha256 为原始输出的 64 位小写十六进制摘要 |
| summary | 审查结论和检查范围的非空摘要，无问题也是有效结论 |
| findings | 下述发现对象数组，无发现时为 [] |
| limitations | 限制的非空字符串数组，无已知限制时为 []；不得省略实际未覆盖的条件 |

每项发现只包含 id、severity、location、problem、disposition、rationale，均为非空字符串。id 在本次报告中唯一，仅用于处理审查发现，不是项目级正式条目 ID。severity 为 blocker 或 suggestion；disposition 为 open、fixed、rejected、deferred。location 定位文件／行或正式 ID，problem 写触发条件及后果，rationale 写证据与处理理由。

blocker 处于 open 或 deferred 时阻断。fixed 需要针对当前输入的修复验证；rejected 需要说明为何不是必须解决的缺陷。处置属于审查者实际输出，导入者不得在模型结果之外把阻断改为 fixed／rejected。需要追加处置时进行有界复核，或由另一位实际人工审查者明确承担结论，不能悄悄修改原模型报告。

## 来源适配及信任边界

human 的 model／provider 必须为 null，审查者 name 必须不同于作者。source.format 为 human-json；来源文件恰有 binding、summary、findings、limitations 四个字段，内容与记录一致。仅导入实际具名人工结论。

model 当前支持 claude-stream-json；来源需有恰好一个 init 和一个成功 result，两个 session_id 与 reviewer.context 一致。model 必须出现在实际 assistant 或 modelUsage 中，provider 取 init.apiProvider，或匹配实际模型／canonicalModel 的 modelUsage.provider；来源冲突时拒绝，均未提供时只能写 unknown。不能从品牌名推断实际模型，更不能把 CLI 名称当作跨供应商证明。result.structured_output（或可解析为 JSON 的 result.result）必须恰有 binding、summary、findings、limitations，且与记录一致。失败、超时、缺结果或不一致的来源不能导入。其他模型事件格式暂不支持，不得伪装成 Claude 来源。

导入后保存到 `tmp/tao/reviews/<CHG-ID>/<requirement>.json`。保存原则见 [证据规程](evidence-retention.md)；require_logs=true 时来源缺失或摘要不符阻止复用，reuse_seconds 限定时长。输入、策略或目标不符为 stale；缺失、无效、过期和未解决发现分别报告，不自动重审。

本地一致性检查不提供防篡改或身份认证。导入成功只表示记录已接收，即使有阻断发现也会保存；以完整 verify 的结果和实际语义判断决定是否可交付。
