---
schema: tao.project.user-guide/v0.1
id: DOC_20260916_J7HZD61YYQTTYBW0
title: 在不同 coding agent 中接入 tao-dev
locale: zh-Hans
status: draft
created: "2026-09-16"
---

# 在不同 coding agent 中接入 tao-dev

<!-- tao:section scope -->
## 选择接入方式

| 方式 | 获得的能力 | 入口 |
|---|---|---|
| Claude／Codex／Cursor／Kiro 完整插件 | 共享 skill、CLI、模板、对应客户端 hook 与安装管理 | [README](../../README.md) |
| 独立 skill | 同一份规程、模板与 Python CLI；客户端原生扩展另行接入 | 下文 |

共享 skill 不依赖 Claude command、子代理或根目录变量。客户端能读懂 SKILL.md，不代表已验证脚本执行、独立审查、hook 或自动安装；各层的依据见 [兼容矩阵](../engineering/client-compatibility.md)。

<!-- tao:section prerequisites -->
## 准备条件

只读规程需要客户端支持 Agent Skills 及配套资源读取。运行 tao CLI 还需要本地完整 skill、shell 执行能力，以及 Python 3.11–3.14（含 venv、ensurepip）。完整功能开发流程使用 Git；普通文档检查可无 Git。依赖准备需要网络或预先取得的锁定 wheelhouse。

如果客户端只提供资源 URI，先按它的资源接口读取规程；没有本地脚本或客户端执行接口时，只能使用规程，不能宣称 CLI 已可运行。远程会话需在远程环境配置资源与 Python，本机安装不自动同步。

<!-- tao:section steps -->
## 独立 skill 接入

1. 从源码取得整个 `plugins/tao-dev/skills/tao-dev/`，包括 SKILL.md、references、assets、scripts；不要只复制 SKILL.md。
2. 在目标项目按下表选择一个受客户端支持的目录，放入 `tao-dev/`。同一客户端避免重复发现多个副本。目录是官方文档提供的候选入口，九个新增客户端尚未在本机原生验收。
3. 启动新会话，用客户端的 skill 选择入口加载 tao-dev，再表达需求，如“只检查当前 Markdown，保存报告”。加载后动作名与自然语言均可使用，完整阶段示例见 [流程指南](workflow.md)。
4. 需要 CLI 时使用选定 Python 和 skill 实际路径运行 `tao doctor`；若缺依赖，在已有准备授权下显式运行 `tao env prepare`，再运行约定检查。

| 客户端 | 项目内 skill 根目录（放入 tao-dev/） | 官方入口 |
|---|---|---|
| Codex | `.agents/skills/` | [Skills](https://developers.openai.com/codex/skills) |
| Claude Code | `.claude/skills/` | [Skills](https://code.claude.com/docs/en/skills) |
| Cursor | `.cursor/skills/` 或 `.agents/skills/` | [Skills](https://cursor.com/docs/skills) |
| Oh My Pi | `.omp/skills/` 或 `.agents/skills/` | [Skills](https://github.com/can1357/oh-my-pi/blob/main/docs/skills.md) |
| Crush | `.crush/skills/` 或 `.agents/skills/` | [Agent Skills](https://github.com/charmbracelet/crush#agent-skills) |
| Kiro | `tao install --client kiro`（V3）；手工接入仍可用 `.kiro/skills/` | [Skills](https://kiro.dev/docs/skills/) |
| Qwen Code | `.qwen/skills/` | [Skills](https://qwenlm.github.io/qwen-code-docs/en/users/features/skills/) |
| Kimi Code | `.agents/skills/` | [Skills](https://moonshotai.github.io/kimi-code/en/customization/skills) |
| OpenCode | `.opencode/skills/` 或 `.agents/skills/` | [Skills](https://opencode.ai/docs/skills/) |
| Qoder | `.qoder/skills/` | [Skills](https://docs.qoder.com/cli/Skills) |
| CodeBuddy | `.codebuddy/skills/` | [Skills](https://www.codebuddy.ai/docs/cli/skills) |

下面以项目根目录的 `.agents/skills/tao-dev/` 为例，在项目根执行；Python 名称按本机实际替换。agent 从已加载 skill 的位置确定路径，不依赖当前工作目录：

```sh
python3 .agents/skills/tao-dev/scripts/tao.py --project . doctor --format json
python3 .agents/skills/tao-dev/scripts/tao.py --project . env prepare
python3 .agents/skills/tao-dev/scripts/tao.py --project . verify --only docs
```

`env prepare` 会安装 tao 自身依赖；离线时加 `--wheelhouse /absolute/path/to/wheels`。它沿用你为 pip 配置的包来源（如镜像 index-url），但不沿用会改写安装位置的配置；默认 300 秒的总时限可用 `--timeout <秒数>` 调整，0 表示不限。普通检查不隐式安装。检查范围以项目配置为准；独立 skill 不提供 `tao install --client <其他客户端>`。运行环境保持在 skill 目录外，诊断及覆盖方式见 [运行环境](../../plugins/tao-dev/skills/tao-dev/references/runtime.md)。

升级时更新完整 skill，保留项目文档和外部运行数据，再运行 `tao doctor`。删除独立 skill 只取消发现；按归属清理不再使用的运行环境，不能清空共享数据根。完整插件的升级、卸载使用 README 中的安装管理入口。

### 原生入口与独立审查

Claude 插件的 `com.anthropic/agents/`、`com.anthropic/commands/` 是 Claude 原生包装；Codex 的完整插件包通过共享 skill 执行动作。Codex 可选 reviewer 需按下节显式注册。其他客户端使用自身委派能力执行共享审查规程；缺少独立执行能力时只能明确记录自检与未执行范围。

真实审查报告可以保存；机器回执还需来源格式适配和当前输入绑定。支持格式以 [审查记录](../../plugins/tao-dev/skills/tao-dev/references/review-receipts.md) 为准，不能将未支持来源改写为人工审查来绕过完成条件。

### 可选：Codex 原生 reviewer

包内 [tao-reviewer.toml](../../plugins/tao-dev/com.openai/agents/tao-reviewer.toml) 定义 `tao_reviewer`，与 Claude reviewer 复用相同审查和工程规程。它继承主会话的模型选择，采用 read-only sandbox；需要写入的复现由主 agent 在已授权的隔离环境执行。结论返回主 agent 保存，角色本身不重新调度审查。

在需要此入口的项目中：

1. 先接入 tao-dev skill，使父子会话能够发现；主 agent 委派时传递实际 skill 路径及审查材料。
2. 将完整插件中的 `com.openai/agents/tao-reviewer.toml` 复制到项目 `.codex/agents/tao-reviewer.toml`。独立 skill 不包含此平台适配文件，可从上面的源码入口取得。已有同名文件或角色时先检查冲突，不覆盖。
3. 确认项目 `.codex/config.toml` 属于当前受信任的配置层。若尚无该文件，可创建空文件；若原生 agents 被关闭，在该项目现有配置中合并 `[agents]` 的 `enabled = true`，不覆盖已有配置。启动新会话，确认可用角色中有 `tao_reviewer` 后再委派。[Codex 原生子代理文档](https://learn.chatgpt.com/docs/agent-configuration/subagents)

插件安装器只分发此 TOML，不自动复制或注册角色；Codex 不会仅因文件位于插件的 `com.openai/agents/` 就加载它。升级插件后按需更新项目中的角色副本。取消角色时只移除自己添加的文件及专用配置，不删除整个 `.codex/agents/`。普通 `$tao-dev review` 使用共享流程，不要求注册此角色。上述发现与具名委派已在 Codex 0.154.0 的临时受信任项目验证，项目外角色缺席；其他版本仍需核对原生行为。

<!-- tao:section troubleshooting -->
## 排查

| 现象 | 检查 |
|---|---|
| 找不到 skill | 当前会话的发现目录、项目范围、重启要求和重复副本；不要直接改全局配置 |
| `references/` 目录或脚本失踪 | 是否复制了完整目录；Markdown 链接按所在文件解析，不按业务项目根解析 |
| URI 拒绝 `..` | 将文件相对目标归一化为 skill 内资源，再用该客户端 URI 接口访问；不要全局重写 Markdown 链接 |
| Python 或依赖缺失 | 运行 `tao doctor`；无安装授权时继续可用检查并记录 `not_run` |
| 没有 hook／reviewer／斜杠命令 | 这些是原生扩展；独立 skill 的发现不代表安装了它们 |
