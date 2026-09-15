---
schema: tao.project.design/v0.1
id: DOC_20260914_7RJ1YVEC0CP478BY
title: 插件打包与运行环境
locale: zh-Hans
status: draft
created: '2026-09-14'
updated: "2026-09-15"
---

# 插件打包与运行环境

本文是 tao-dev 的内部产品设计，定义运行组件的格式、分发边界和验收方法，不属于发布包。需求依据为 {need}`REQ_20260914_BWAY1ZF6HNPM855Y`，总体协议见 [协作开发协议](../product/protocol.md)。目录图展示源码布局；当前已提供 Codex 与 Claude 兼容 manifest、公共格式打包、共享 skill、核心 CLI、Claude commands／reviewer，以及两端的短文档 hook 配置；Claude 调用级插件与 hook、两端原生 skill／操作及独立审查已有部分运行结果；完整双端验收尚未完成，见 [实际记录](../plans/2026-09/20260914-bootstrap.md)。

<!-- tao:section overview -->
## 标准基线与目标环境

以 **Agent Plugins 1.0.0** 作为公共包装基线，skill 内容遵循其引用的 Agent Skills 规范。**Codex CLI 和 Claude Code CLI 均为首批必需验收环境**；不以其中一个通过代替另一个，也不以桌面应用运行代替 CLI 验收。其他客户端暂不承诺兼容。

公共规范规定根 manifest、skills 与可选 MCP 组件；agent、command 和 hook 不属于 1.0.0 的公共组件类型。它们按目标客户端的官方扩展约定实现。目录名称相似不代表触发条件、权限和执行语义相同。[Agent Plugins 规范](https://agent-plugins.org/specification)、[客户端扩展](https://agent-plugins.org/plugin-authors/client-extensions)

标准版本、产品版本和客户端版本分别记录。首次运行验收时固定具体 CLI 版本、操作系统、模型与必要配置；通过这些组合后再声明支持范围。仅检查版本号或读取官方文档不能证明运行兼容。

<!-- tao:section architecture -->
## 源码与发布包

开发资料留在项目根的 `docs/`；运行源码单独放在 `plugins/tao-dev/`。根目录 `AGENTS.md` 管理本项目开发，旁置 `CLAUDE.md` 仅含一行 `@AGENTS.md` 供 Claude 导入；二者均不作为产品 agent 定义或分发内容。按实际组件逐步创建目录，未实现的组件不放空配置或虚假入口。

当前 prompt 实现由 [SKILL.md](../../plugins/tao-dev/skills/tao-dev/SKILL.md) 明确加载 [工程规程](../../plugins/tao-dev/skills/tao-dev/references/engineering.md)，落实 {need}`REQ_20260914_4CS6P421MGW68PME`。工程条款的权威执行文本维护在该运行参考中，内部文档维护需求、理由和验收，不复制一套同文规则。发布目录离开开发仓库后仍须能完整读取这些指令。

```text
tao-dev/
  AGENTS.md
  README.md
  docs/                              # 内部需求、设计与维护资料
  plugins/
    tao-dev/                         # 插件根，独立复制后可以安装
      .codex-plugin/
        plugin.json                  # Codex 兼容 manifest；公共格式由打包生成
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

是否分发资源，以消费项目中的实际读取者或运行调用方为准：LLM 按需读取的工程、流程、审查和文档规则放 references/；CLI 加载的格式注册表、模板和显示资源放 assets/；实际执行代码放 scripts/。只有工具读取的资源无需进入 LLM 上下文。本项目的需求、实现理由、研发任务及验收报告留在 docs/；可复用或自举时有用，本身不构成分发理由。混合职责的文档按段落拆分，包内规则不依赖开发仓库。

运行源码仅放入分发所需内容。打包脚本从 plugins/tao-dev/ 复制运行目录，排除 Python 字节码；公共格式复制运行目录（排除 .codex-plugin/），从 Codex manifest 的名称、版本、描述和 hook 路径生成根 plugin.json；Codex 兼容格式仅选 skills/、com.openai/ 和 .codex-plugin/。维护者应检查实际包内容，避免把开发文件放入运行源码目录；当前脚本不是逐文件白名单。

`--marketplace` 在所选格式外增加客户端可读取的本地目录索引，插件位于输出根的 `plugins/tao-dev/`。public 的索引使用 Claude 格式，codex-legacy 使用 Codex 格式，均以相对路径引用完整插件；它不修改客户端配置或注册状态。用户按 README 完成原生安装、运行依赖准备和 hook 检查，单独复制 skill 不能代替完整插件安装。

仓库根的 `.claude-plugin/marketplace.json` 与 `.agents/plugins/marketplace.json` 分别是 Claude Code、Codex 的 GitHub 分发入口，使用稳定的 marketplace 名称 `tao-dev`，相对引用 `./plugins/tao-dev`，不在目录条目里重复版本号。生成的 `tao-dev-local` 目录用于本地安装与开发，两种来源分别注册，迁移时移除旧插件以免重复加载。GitHub marketplace 随默认分支更新，客户端通过插件 manifest 版本识别新版本；固定 Git tag 是可选的快照安装方式，会停止跟随分支。

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

源码的 `.codex-plugin/plugin.json` 显式将 hooks 指向 `./com.openai/hooks/hooks.json`，避免误载 Claude 默认 hook。GitHub 清单直接引用这个兼容源码目录；公共包由打包器将同一路径写入根 manifest 的 `extensions.com.openai.hooks`。运行资源只维护一份，平台格式在打包边界转换。[OpenAI 插件构建](https://developers.openai.com/plugins/build/plugins)

Codex CLI 0.154.0 实测可发现公共包的 skill，却不发现其中的 hook；同一运行代码采用兼容 manifest 后可以发现。因此 GitHub 分发目录不放优先级更高的根 plugin.json；仅追加兼容 manifest，或移除公共 manifest 的 inline extension，均不能让该版本发现 hook。维护入口 `scripts/package_plugin.py --format codex-legacy --output <新目录>` 复制兼容 manifest、skills/ 与 com.openai/。兼容副本不包含优先级更高的根 manifest，也不带 Claude command／agent；Codex 通过 skill 执行相同操作。默认 public 输出保留公共布局。两种输出均不包含开发文档，不安装或注册插件，不覆盖已有目录。

Claude Code 使用 `.claude-plugin/plugin.json` 及其原生组件目录；其 manifest 的名称、版本和描述与 Codex manifest 检查一致；公共格式由打包器派生。`agents/`、`commands/`、`hooks/` 位于插件根，不放进 `.claude-plugin/`。这些是 Claude 的兼容布局，不冒充公共规范；不自行假设一个未被客户端实现的扩展命名空间。[Claude 插件参考](https://code.claude.com/docs/en/plugins-reference)

公共版本需要 MCP 时才增加根 `mcp.json`；Claude 兼容配置按其原生格式生成并单独验收。初版不为符合目录示意而引入 MCP 服务。

发布前核对实际包内容：必要的运行引用、脚本、模板及许可证信息齐全，内部 `docs/`、开发指导、研究材料、缓存和验收凭据已排除。包内文件路径和符号链接解析后必须留在插件根；安装目录改变后仍能运行。组件注册、市场发布及用户全局配置的修改是独立操作，不随文档构建自动执行。

### 独立运行环境的实现

环境键包含依赖清单、Python 实现与版本、基础可执行文件和平台。准备过程有互斥与等待上限，在最终路径创建 venv；检查通过后才原子发布选择记录，不能移动 venv。失败环境没有 ready 标记，不会被正常执行选中，已完成环境不在安装过程中修改。依赖锁定和隔离的取舍见 [运行环境决定](decisions/isolated-runtime.md)。

客户端 manifest 使用 shell 启动器；原生 Windows 的 shell 可用性和 PowerShell 接入需单独验收，不能由 Python 单元测试推导。运行参考只维护使用者所需的准备、诊断和恢复步骤；平台与版本结果在验收记录中维护。

<!-- tao:section contracts -->
## 组件职责与平台映射

| 组件 | 公共定义与格式 | Codex CLI | Claude Code CLI |
|---|---|---|---|
| skill | `skills/<name>/SKILL.md`；YAML 元数据＋Markdown 正文；必需字段为 `name`、`description` | 通过原生 skill 发现与显式调用使用 | 通过插件 skill 发现及带插件命名空间的入口使用 |
| agent | 角色的职责、输入、输出和验证规程在共享 skill 资源中维护；不自建公共 agent manifest | 复用角色规程，按原生子代理能力执行；具名 agent 配置须按目标版本另行验证 | 按需用 `agents/*.md` 定义原生子代理，采用官方 frontmatter 和正文格式 |
| 斜杠命令（slash command） | 操作语义由 skill 维护；命令只选择操作和传递参数 | 使用 `/skills` 或 `$` 选择 skill；不假设会加载 Claude 的 `commands/` | 优先使用 skill 提供的命名空间入口；必要时以 `commands/*.md` 提供仅转发操作与参数的斜杠命令包装 |
| hook | 共享可确定的检查逻辑；事件绑定与输入输出由平台适配 | 使用 Codex hook JSON、受支持事件与执行类型 | 使用 Claude hook JSON、受支持事件与执行类型 |

Skill 的名称与目录、元数据字段、文件引用遵循 [Agent Skills](https://agentskills.io/specification)。本项目内部文档的 `tao.*` profile、章节键和研发条目不能直接套到运行 `SKILL.md`、agent 或 command 的 frontmatter；这些文件按各自标准检查。平台专有元数据只在有明确支持的组件中使用。

客户端斜杠命令与终端中的 `tao` CLI 是不同接口。CLI 的能力发现、参数、副作用和退出码集中在 [命令设计](cli-design.md)；运行 skill 的 [流程操作规程](../../plugins/tao-dev/skills/tao-dev/references/workflow.md) 定义调用时机，避免把自然语言阶段名当作已经实现的 CLI 子命令。

new 包装接收自然语言描述并保留会话上下文，调用共享流程规程，由 agent 整理输入并填写草稿；不能仅转发到终端生成器就宣称完成。CLI 使用显式 --slug，不能把描述当作 slug 或 shell 命令；两层契约见 [CLI 设计](cli-design.md)。

Claude command 与角色的运行引用使用客户端展开的 `${CLAUDE_PLUGIN_ROOT}`，不让模型从使用方目录猜测相对根。角色入口复用实际运行材料，不引用内部设计文档；不把同一工作规程复制为 skill、agent 和 command 三份正文。插件根 `agents/` 的子代理定义与某些 skill 内的 `agents/openai.yaml` 界面元数据职责不同，不能互相替代。Codex 对 Claude agent／command 的兼容处理不能等同原生发现；未实现的注册能力应明确报告。[OpenAI 兼容迁移说明](https://developers.openai.com/plugins/guides/submit-claude-plugin)、[Claude 子代理](https://code.claude.com/docs/en/sub-agents)

初版 hook 使用确定性的 command handler，并分别验证两端事件载荷、输出、退出状态、超时和信任流程。静态配置以 PATH 中的 python3 直接调用 hook.py；Codex 使用 `PLUGIN_ROOT`，Claude 使用 `CLAUDE_PLUGIN_ROOT` 和独立参数。完整安装把解释器与脚本写成绝对路径，正确处理空格且不依赖 shell 启动包装。使用方的文档资产写入 docs/ 或其配置映射位置，派生索引与缓存默认放 tmp/tao/cache/；.tao/ 仅放配置。客户端自身的数据按其支持的目录管理，不能写入假定可修改的插件缓存。

同名事件不直接推导语义等价，prompt／agent 类型 hook 也不视为两端共有能力。hook 未获信任、被禁用或执行失败时，说明哪些动作未运行，并提供显式检查路径。不能绕过客户端权限，也不能将缺失检查算作通过。[Codex hooks](https://learn.chatgpt.com/docs/hooks)、[Claude hooks](https://code.claude.com/docs/en/hooks)

<!-- tao:section invariants -->
## 分发与兼容边界

运行组件不依赖开发文档；平台专用行为分别验收。公共元数据与兼容 manifest 一致；声明的能力必须对应实际实现。

<!-- tao:section errors -->
## 隔离失败与能力缺失

无法在项目或调用范围内隔离时，该项验收受阻；不回退全局安装。组件不可用或执行失败时报告真实缺口，不把串行回退标为原生子代理通过。

<!-- tao:section verification -->
## 双 CLI 验收与维护依据

验收在隔离的使用方项目及测试配置中进行，使用同一发布版本和等价输入。两端分别记录证据，包含实际加载位置、CLI 版本、模型、系统环境、权限／hook 信任状态、命令、退出状态及观察结果。开发者日常环境已有的插件或配置不得掩盖缺失依赖。

直接使用已配置好的 `claude` 和 `codex` 命令及既有认证，不为试验重新安装或配置客户端。试验 skill 只通过经确认的项目局部或单次调用加载机制启用；进入试验目录本身不代表安装范围已受限。禁止全局安装、注册，以及修改全局插件、skill、marketplace 或 hook 配置；这一限制同时传给受测 agent 和辅助脚本。项目局部配置及清理不得影响其他项目。若所选版本无法提供所需隔离，记录该项受阻，不回退到全局安装。

Codex 验收使用独立临时 CODEX_HOME：原生安装缓存留在该目录，客户端默认禁用 tao-dev，仅受信任的试验项目启用。必须同时检查原生 skills/list、hooks/list 和实际模型行为；plugin list 在项目外为空不足以证明技能未进入上下文。已有、未过期的访问凭据可在显式授权的试验中临时复用，副本权限为 0600，不携带刷新令牌，结束后删除；不登录、不刷新、不改个人认证。hook 信任只绑定已核对代码及原生清单中的精确哈希，写入试验配置，不跳过客户端信任检查。源码、环境与真实结果保存规则见 [客户端验收说明](../../tests/acceptance/README.md)。

Claude 验收同样使用独立的 CLAUDE_CONFIG_DIR，通过原生命令分别安装到 user、project、local。访问令牌仅经子进程环境复用，保留既有模型和供应商选择；不携带刷新令牌，不写个人认证，前后核对已有凭据及监测配置。user 范围在同一隔离配置的其他目录可见属于预期；project／local 范围须做项目外不可见对照。模型入口同时检查实际原生组件调用和产物，不能用无认证时的初始化事件替代行为成功。维护适配及验收脚本留在 tests/acceptance/，不进入消费项目的运行包。

| 验收项 | 两端都必须满足的结果 |
|---|---|
| 试验隔离 | 试验项目内能加载受测 skill；个人日常配置未注册试验插件。project／local 项目外不可见；Claude user 在同一隔离配置的其他目录可见是预期，不能误判为个人全局安装 |
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

### 维护依据

以 Agent Plugins 的版本化规范约束公共定义，以两端官方文档及选定 CLI 的实际行为约束适配。客户端升级后，重新运行受影响的验收；超出已测组合的支持范围需有新证据。

- [Agent Plugins 1.0.0](https://agent-plugins.org/specification)、[JSON Schemas](https://agent-plugins.org/schemas)：公共格式与校验依据。
- [Agent Skills](https://agentskills.io/specification)：skill 目录和内容格式。
- [OpenAI 插件构建](https://developers.openai.com/plugins/build/plugins)、[Codex hooks](https://learn.chatgpt.com/docs/hooks)：Codex 扩展与运行语义。
- [Claude 插件参考](https://code.claude.com/docs/en/plugins-reference)、[Claude 子代理](https://code.claude.com/docs/en/sub-agents)、[Claude hooks](https://code.claude.com/docs/en/hooks)：Claude 原生组件格式。
