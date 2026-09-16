---
schema: tao.project.user-guide/v0.1
id: DOC_20260916_6N9TWCTX0K6XV2A7
title: 客户端兼容性与验收边界
locale: zh-Hans
status: draft
created: "2026-09-16"
---

# 客户端兼容性与验收边界

<!-- tao:section scope -->
## 分层判定

共享文本只使用 Agent Skills 的 name、description 与文件资源；Markdown 相对路径按所在文件解析。客户端适配保留自己的格式、变量和权限机制，不能用一列“兼容”覆盖所有能力。接入路径及官方来源在 [用户接入指南](../user/clients.md)，本页记录工程判定和本次验证范围（2026-09-16）。

<!-- tao:section prerequisites -->
## 原生验收条件

需要实际 CLI、已配置认证和可验证的项目或调用隔离。先证明项目内发现及项目外缺席，再执行加载、资源读取和检查。测试不安装全局插件，不修改个人配置，不替用户登录。CLI 缺失记“未运行”，不以静态文档检索代替通过。

<!-- tao:section steps -->
## 当前矩阵

| 客户端 | Skill／资源文档依据 | 本机原生状态 | tao 安装管理 | 平台扩展 |
|---|---|---|---|---|
| Claude Code 2.1.270 | 原生 skills、插件根变量 | 已有隔离安装／hook 验收；本次模型调用被服务端 403 阻断 | 已实现 | Claude commands、Markdown reviewer、hook |
| Codex 0.154.0 | 原生 skills、显式资源路径 | 本次项目内 skill／TOML 角色发现与委派通过，项目外均缺席 | 已实现 | hook；可选 TOML reviewer |
| Cursor | SKILL.md、配套文件、项目目录 | 未运行：无 CLI | 未实现 | 不复制 Claude 原生包装作为支持承诺 |
| Oh My Pi | SKILL.md；skill URI 只接受归一化的根内资源路径 | 未运行：无 CLI | 未实现 | 使用本机能力，单独验收 |
| Crush | SKILL.md、配套文件、可配置目录 | 未运行：无 CLI | 未实现 | 同上 |
| Kiro | SKILL.md、自定义 agent 的 skill 资源配置 | 未运行：无 CLI | 未实现 | 同上 |
| Qwen Code | SKILL.md、原生发现及扩展命名空间 | 未运行：无 CLI | 未实现 | 同上 |
| Kimi Code | SKILL.md、项目 skills | 未运行：无 CLI | 未实现 | 同上 |
| OpenCode | SKILL.md、资源工具和权限配置 | 未运行：无 CLI | 未实现 | 同上 |
| Qoder | 官方 Skills 页面检索；正文抓取不可用 | 未运行：无 CLI | 未实现 | 同上 |
| CodeBuddy | SKILL.md、配套资源、原生占位符 | 未运行：无 CLI | 未实现 | 同上 |

本次 Codex 0.154.0 原生探针实际委派 tao_reviewer 一次，读取共享审查规程并复现样例缺陷；原始输出通过 codex-exec-jsonl 解析，模型和供应商保持 unknown。项目外会话未发现 skill 或角色。Claude Code 2.1.270 复用已有认证时收到 `403 Request not allowed`，本次加载后的行为未验收；个人配置摘要保持不变，未重新登录。

本次 PATH 探测仅发现 codex 和 claude。其他客户端有文档依据的接入候选，尚无原生运行保证。Python 的独立 skill 回归覆盖共同脚本边界，不能证明各客户端一定允许执行这些脚本。

### 变量、路径与组件边界

| 内容 | 规则与理由 |
|---|---|
| 共享 skill Markdown | 不使用 CLAUDE_PLUGIN_ROOT 或 PLUGIN_ROOT；保持正常文件相对链接 |
| Claude commands／reviewer | 保留官方展开的 `${CLAUDE_PLUGIN_ROOT}`，包装仅定位共享规程并传递请求 |
| hook JSON／shell | 保留客户端支持的根变量；安装器绑定解释器和脚本绝对路径，不能替换为依赖 cwd 的相对路径 |
| 维护文档中的变量 | 用于解释真实行为的变量名保留；它们不是共享 skill 的运行依赖 |
| `../scripts/tao.py` | 在 references 下正确指向同一 skill 的 scripts；不机械删除 `..` |
| URI 工具 | 先按包含文件解析链接并归一化，再转换成该客户端的资源标识；URI-only 不等于本地可执行 |

Codex 0.154.0 源码的 Claude command 迁移是受限转换，不是原生 command 发现：含 `$ARGUMENTS` 等动态参数的命令会跳过。当前 tao 的 11 个 command 均有该参数；codex-legacy 包也不分发 Claude agents／commands。原生角色是另一接口，不能由目录同名推导兼容。[Codex 迁移说明](https://developers.openai.com/plugins/guides/submit-claude-plugin)

### 回归与安装扩展决策

独立 skill 回归需复制完整 skill 到含空格路径，不携带外层 manifest；从另一 cwd 使用显式 --project，验证未准备诊断、显式离线 setup、局部检查和资源目录未写入。CLI 来源适配需验证真实事件及拒绝反例。当前执行记录见 [兼容性计划](../plans/2026-09/20260916-client-portability.md)。

本次不扩展 `install --client`：九个新增 CLI 不在本机，无法核验注册、信任、升级、卸载与项目外缺席。后续针对确有需求且可隔离验证的客户端逐个实现；共享 skill 接入不受此阻塞。模型／供应商未出现在原始来源中时记 unknown，原生 reviewer 角色名也不证明模型多样性。

<!-- tao:section troubleshooting -->
## 结果解释

记录版本、操作系统、发现范围、实际运行与缺失能力。已有原生验收见 [运行环境计划](../plans/2026-09/20260914-portable-runtime.md)。文档支持、静态解析、独立 Python 回归及原生模型调用分开记录；任何一项局部通过都不代表跨版本或全平台交付就绪。
