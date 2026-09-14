---
schema: tao.plugin-design/v0.2
id: DOC_20260914_7RJ1YVEC0CP478BY
title: 插件打包与运行环境
locale: zh-Hans
status: draft
created: "2026-09-14"
bootstrap: manual
---

# 插件打包与运行环境

本文是 tao-dev 的内部产品设计，定义运行组件的格式、分发边界和验收方法，不属于发布包。需求依据为 {need}`REQ_20260914_BWAY1ZF6HNPM855Y`，总体协议见 [协作开发协议](protocol.md)。目录图展示目标布局；当前已实现两个 manifest、skill 入口、工程规程及流程操作规程，其余组件按需实现，运行验收尚未完成。

<!-- tao:section scope -->
## 一、标准基线与目标环境

以 **Agent Plugins 1.0.0** 作为公共包装基线，skill 内容遵循其引用的 Agent Skills 规范。**Codex CLI 和 Claude Code CLI 均为首批必需验收环境**；不以其中一个通过代替另一个，也不以桌面应用运行代替 CLI 验收。其他客户端暂不承诺兼容。

公共规范规定根 manifest、skills 与可选 MCP 组件；agent、command 和 hook 不属于 1.0.0 的公共组件类型。它们按目标客户端的官方扩展约定实现。目录名称相似不代表触发条件、权限和执行语义相同。[Agent Plugins 规范](https://agent-plugins.org/specification)、[客户端扩展](https://agent-plugins.org/plugin-authors/client-extensions)

标准版本、产品版本和客户端版本分别记录。首次运行验收时固定具体 CLI 版本、操作系统、模型与必要配置；通过这些组合后再声明支持范围。仅检查版本号或读取官方文档不能证明运行兼容。

<!-- tao:section package -->
## 二、源码与发布包

开发资料留在项目根的 `docs/`；运行源码单独放在 `plugins/tao-dev/`。根目录 `AGENTS.md` 管理本项目开发，旁置 `CLAUDE.md` 仅含一行 `@AGENTS.md` 供 Claude 导入；二者均不作为产品 agent 定义或分发内容。按实际组件逐步创建目录，未实现的组件不放空配置或虚假入口。

当前 prompt 实现由 [SKILL.md](../plugins/tao-dev/skills/tao-dev/SKILL.md) 明确加载 [工程规程](../plugins/tao-dev/skills/tao-dev/references/engineering.md)，落实 {need}`REQ_20260914_4CS6P421MGW68PME`。工程条款的权威执行文本维护在该运行参考中，内部文档维护需求、理由和验收，不复制一套同文规则。发布目录离开开发仓库后仍须能完整读取这些指令。

```text
tao-dev/
  AGENTS.md
  README.md
  docs/                              # 内部需求、设计与维护资料
  plugins/
    tao-dev/                         # 插件根，独立复制后可以安装
      plugin.json                    # Agent Plugins 公共 manifest
      skills/
        tao-dev/
          SKILL.md                   # 共享流程入口
          references/                # 运行时需要的规程
          assets/                    # 交付模板及本地化资源
          scripts/                   # 被实际调用的公共检查逻辑
      com.openai/
        hooks/hooks.json             # Codex hook 配置，显式声明路径
      .claude-plugin/
        plugin.json                  # Claude Code 兼容 manifest
      agents/                        # 按需：Claude Code 原生角色入口
      commands/                      # 按需：Claude Code 斜杠命令入口
      hooks/hooks.json               # 按需：Claude Code hook 配置
```

使用方格式同样随包提供：[文档规程](../plugins/tao-dev/skills/tao-dev/references/documents.md) 负责编写规则，assets/document-profiles.json 负责机器可读结构，assets/templates 与 assets/locales 提供模板和显示资源。skill 和未来 CLI 读取同一版本，不从内部 docs 动态加载格式，也不要求使用方另建 schema。当前模板可填写，脚本和平台适配仍按实际能力验收。

公共 manifest 的最小格式如下；示例产品版本不代表已经发布：

```json
{
  "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
  "name": "tao-dev",
  "version": "0.1.0",
  "description": "Evidence-based workflows for human-agent development."
}
```

`$schema` 标识标准版本，`version` 标识产品版本。顶层只使用规范允许的字段，不自行加入 `agents`、`commands` 或 `hooks`。平台信息放在正式支持的扩展或兼容 manifest 中；元数据校验采用固定版本 schema，不在插件加载时从网络取回执行规则。[Manifest 约定](https://agent-plugins.org/plugin-authors/manifest)

Codex 专用 hook 在根 manifest 的 `extensions.com.openai.hooks` 显式指向 `./com.openai/hooks/hooks.json`，避免同时误载 Claude 默认 hook。该字段及目标文件只在实现相应 hook 时加入。新包优先使用公共 manifest；`.codex-plugin/plugin.json` 仅作为有实际版本兼容需求时的回退，不再维护一份重复的默认定义。[OpenAI 插件构建](https://developers.openai.com/plugins/build/plugins)

Claude Code 使用 `.claude-plugin/plugin.json` 及其原生组件目录；兼容 manifest 的名称、版本和描述从公共元数据派生并检查一致性。`agents/`、`commands/`、`hooks/` 位于插件根，不放进 `.claude-plugin/`。这些是 Claude 的兼容布局，不冒充公共规范；不自行假设一个未被客户端实现的扩展命名空间。[Claude 插件参考](https://code.claude.com/docs/en/plugins-reference)

公共版本需要 MCP 时才增加根 `mcp.json`；Claude 兼容配置按其原生格式生成并单独验收。初版不为符合目录示意而引入 MCP 服务。

发布按文件清单取用插件根的实际组件；包含必要的运行引用、脚本、模板及许可证信息，不包含内部 `docs/`、开发指导、研究材料、缓存和验收凭据。包内文件路径和符号链接解析后必须留在插件根；安装目录改变后仍能运行。组件注册、市场发布及用户全局配置的修改是独立操作，不随文档构建自动执行。

<!-- tao:section components -->
## 三、组件职责与平台映射

| 组件 | 公共定义与格式 | Codex CLI | Claude Code CLI |
|---|---|---|---|
| skill | `skills/<name>/SKILL.md`；YAML 元数据＋Markdown 正文；必需字段为 `name`、`description` | 通过原生 skill 发现与显式调用使用 | 通过插件 skill 发现及带插件命名空间的入口使用 |
| agent | 角色的职责、输入、输出和验证规程在共享 skill 资源中维护；不自建公共 agent manifest | 复用角色规程，按原生子代理能力执行；具名 agent 配置须按目标版本另行验证 | 按需用 `agents/*.md` 定义原生子代理，采用官方 frontmatter 和正文格式 |
| 斜杠命令（slash command） | 操作语义由 skill 维护；命令只选择操作和传递参数 | 使用 `/skills` 或 `$` 选择 skill；不假设会加载 Claude 的 `commands/` | 优先使用 skill 提供的命名空间入口；必要时以 `commands/*.md` 提供仅转发操作与参数的斜杠命令包装 |
| hook | 共享可确定的检查逻辑；事件绑定与输入输出由平台适配 | 使用 Codex hook JSON、受支持事件与执行类型 | 使用 Claude hook JSON、受支持事件与执行类型 |

Skill 的名称与目录、元数据字段、文件引用遵循 [Agent Skills](https://agentskills.io/specification)。本项目内部文档的 `tao.*` profile、章节键和研发条目不能直接套到运行 `SKILL.md`、agent 或 command 的 frontmatter；这些文件按各自标准检查。平台专有元数据只在有明确支持的组件中使用。

客户端斜杠命令与终端中的 `tao` CLI 是不同接口。CLI 的能力发现、参数、副作用和退出码集中在 [命令设计](cli-design.md)；运行 skill 的 [流程操作规程](../plugins/tao-dev/skills/tao-dev/references/workflow.md) 定义调用时机，避免把自然语言阶段名当作已经实现的 CLI 子命令。

角色入口复用实际运行材料，不引用内部设计文档；不把同一工作规程复制为 skill、agent 和 command 三份正文。插件根 `agents/` 的子代理定义与某些 skill 内的 `agents/openai.yaml` 界面元数据职责不同，不能互相替代。Codex 对 Claude agent／command 的兼容处理不能等同原生发现；未实现的注册能力应明确报告。[OpenAI 兼容迁移说明](https://developers.openai.com/plugins/guides/submit-claude-plugin)、[Claude 子代理](https://code.claude.com/docs/en/sub-agents)

初版 hook 优先使用确定性的 command handler，并分别验证两端事件载荷、输出、退出状态、超时和信任流程。平台提供的插件根变量由适配层处理：Codex 使用 `PLUGIN_ROOT`，Claude 使用 `CLAUDE_PLUGIN_ROOT`；脚本调用正确处理带空格的安装路径。使用方的文档资产写入 docs/ 或其配置映射位置，派生索引与缓存默认放 artifacts/cache/tao/；.tao/ 仅放配置。客户端自身的数据按其支持的目录管理，不能写入假定可修改的插件缓存。

同名事件不直接推导语义等价，prompt／agent 类型 hook 也不视为两端共有能力。hook 未获信任、被禁用或执行失败时，说明哪些动作未运行，并提供显式检查路径。不能绕过客户端权限，也不能将缺失检查算作通过。[Codex hooks](https://learn.chatgpt.com/docs/hooks)、[Claude hooks](https://code.claude.com/docs/en/hooks)

<!-- tao:section acceptance -->
## 四、双 CLI 验收

验收在隔离的使用方项目及测试配置中进行，使用同一发布版本和等价输入。两端分别记录证据，包含实际加载位置、CLI 版本、模型、系统环境、权限／hook 信任状态、命令、退出状态及观察结果。开发者日常环境已有的插件或配置不得掩盖缺失依赖。

直接使用已配置好的 `claude` 和 `codex` 命令及既有认证，不为试验重新安装或配置客户端。试验 skill 只通过经确认的项目局部或单次调用加载机制启用；进入试验目录本身不代表安装范围已受限。禁止全局安装、注册，以及修改全局插件、skill、marketplace 或 hook 配置；这一限制同时传给受测 agent 和辅助脚本。项目局部配置及清理不得影响其他项目。若所选版本无法提供所需隔离，记录该项受阻，不回退到全局安装。

| 验收项 | 两端都必须满足的结果 |
|---|---|
| 试验隔离 | 试验项目内能加载受测 skill；无加载参数的无关项目不能发现或触发它；试验前后全局启用与注册状态不变 |
| 格式与加载 | 公共 manifest、skill 格式及平台配置分别通过适用校验；实际 CLI 能加载声明的组件；不存在重复注册 |
| 显式操作 | skill／command 进入预期操作，参数和相关上下文正确；不会依赖另一个客户端的特殊语法 |
| 角色执行 | 对已声明的角色，实际执行职责、输入输出与修改边界可检查；使用串行回退时明确标记，不宣称原生子代理已通过 |
| Hook | 受信任时按预期触发；禁用、超时、失败及重复事件有明确结果；不会同时加载两份平台 hook |
| 功能路径 | 同一小变更完成澄清、任务、实现、验证和交接；需求变化与旧证据过期被识别 |
| 审查独立性 | 需要跨供应商的样例记录实际模型与供应商；未知或未执行明确报告；先独立审查再比较理由，不用两个客户端名称冒充模型差异 |
| 可携带性与 i18n | 离开开发仓库、换安装目录、带空格路径均可运行；中英文使用方项目遵循各自语言 |
| 更新与移除 | 更新后使用新版本组件；禁用／移除后不再触发；用户文档和必要状态不被误删 |

公共格式通过、原生加载通过和行为验收通过分别报告。必须能力缺失时该平台不得通过；可选能力只有在发布范围明确未包含时才记为不适用。其他功能存在回退路径，不意味着未通过的 hook 或 agent 可以被标记兼容。

Claude 可使用 `claude plugin validate` 做静态检查；Codex 的检查入口按所选版本的 CLI 能力确定。静态验证均不能代替实际加载和流程运行。没有可执行组件前，只记录设计与检查计划，不给出运行兼容结论。

<!-- tao:section sources -->
## 五、维护依据

以 Agent Plugins 的版本化规范约束公共定义，以两端官方文档及选定 CLI 的实际行为约束适配。客户端升级后，重新运行受影响的验收；超出已测组合的支持范围需有新证据。

- [Agent Plugins 1.0.0](https://agent-plugins.org/specification)、[JSON Schemas](https://agent-plugins.org/schemas)：公共格式与校验依据。
- [Agent Skills](https://agentskills.io/specification)：skill 目录和内容格式。
- [OpenAI 插件构建](https://developers.openai.com/plugins/build/plugins)、[Codex hooks](https://learn.chatgpt.com/docs/hooks)：Codex 扩展与运行语义。
- [Claude 插件参考](https://code.claude.com/docs/en/plugins-reference)、[Claude 子代理](https://code.claude.com/docs/en/sub-agents)、[Claude hooks](https://code.claude.com/docs/en/hooks)：Claude 原生组件格式。
