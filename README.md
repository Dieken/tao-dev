# tao-dev · 协作开发之道

让 AI 与人围绕可验收的结果协作开发：明确需求，选择简单方案，小步实现，用实际检查支撑交付，并留下能接手的知识。

tao-dev 是给 coding agent 用的一套**开发协议**——agent skill、共享文档模板和确定性 CLI。它把「需求 → 设计 → 计划 → 任务 → 检查结果」连成带稳定 ID 的可追踪链路，并且只在实际跑过检查后才让 agent 声称完成。

## 核心能力

- **控制复杂度**：区分用户目标与实现建议，比较收益、代价及更简单的替代方案；按风险安排独立审查。
- **需求到交付可追踪**：用稳定 ID 关联需求、设计、计划、任务和验证记录，改名或移动时保持引用。
- **检查结果有依据**：接入项目已有测试与静态检查，识别证据过期、按条件复用结果，并汇总任务和必需审查。局部检查通过只代表其覆盖范围。
- **文档可直接使用**：提供中英文模板、格式与关系校验、Sphinx HTML 书籍和稳定链接；项目沿用自己的语言与目录。
- **会话可恢复**：保存目标、决定、实际状态、证据和下一步，接手时核对当前文件与检查结果。

## 一次开发长什么样

安装后在目标项目启动 Claude Code 或 Codex 会话。以下每个单元格都是**一条完整消息**，按阶段逐条发送。示例是用 tao-dev 为 tao-dev 自身增加文档持续预览功能；该功能尚未实现，仅用于演示流程：

| 时机 | Claude Code 输入 | Codex 输入 |
|---|---|---|
| 可选的项目接入 | `/tao-setup` | `$tao-dev setup` |
| 提出业务需求 | `/tao-new 我想在本机预览 tao-dev 的文档，修改后自动更新，停止后不留后台进程。` | `$tao-dev new 我想在本机预览 tao-dev 的文档，修改后自动更新，停止后不留后台进程。` |
| 查看 spec 后推进 | `spec 符合预期，同意开始编写 design。` | 同左 |
| 查看 design 后推进 | `design 符合预期，同意开始编写 plan 和 tasks。` | 同左 |
| 查看计划后审查 | `/tao-review` | `$tao-dev review` |
| 审查完成，开始实现 | `/tao-implement` | `$tao-dev implement` |
| 实现完成后审查 | `/tao-review` | `$tao-dev review` |
| 构建 Sphinx HTML book | `/tao-docs` | `$tao-dev docs` |
| 选择收尾操作 | `/tao-finish` | `$tao-dev finish` |

new 会先调查和澄清，再请你确认是否允许创建 worktree 和编写 spec。agent 自动处理文件名、路径和文档语言，逐阶段提供可点击的产物与下一步选择；实现获准后尽量自主完成代码、测试与必要检查。review 会让你确认范围和串行／并行方式，默认审查本功能从分支起点以来的累计修改，明确区分测试结果与审查结论。finish 会列出合入、推送、清理等选择，按你的实际授权执行。

随时可用的还有：`status` 只读查看阶段与阻断，`continue` 核对实际状态后继续（无需事先 handoff），`refine` 修订 spec／design／plan，`debug` 调查缺陷，`handoff` 保存交接摘要。动作已表达操作意图，无需再附一句同义要求；加载后也可直接用自然语言提出请求。完整的澄清、修改、审查选择、中断恢复及收尾示例见 [使用指南](docs/user/workflow.md)。

## 安装

需要 **Python 3.11–3.14（含 pip、venv）、Git**，以及已安装并登录的 Claude Code 或 Codex CLI。在目标项目目录执行一条命令（换成 `--client claude` 即安装到 Claude Code）：

```sh
curl -fsSL https://raw.githubusercontent.com/Dieken/tao-dev/main/install.sh | sh -s -- --client codex --scope project
```

<details>
<summary>Windows PowerShell</summary>

```powershell
& ([scriptblock]::Create((Invoke-RestMethod https://raw.githubusercontent.com/Dieken/tao-dev/main/install.ps1))) -Client codex -Scope project
```

hook 直接使用安装器选定的 Python，不要求 Git for Windows 提供 `sh`。原生 Windows 完整验收尚未完成，也可在 WSL 中按 Linux 方式使用。

</details>

安装器会取得 tao-dev、准备全部 Python 依赖（含 HTML 出版）、配置插件与 hook，最后自动执行 doctor；无需设置 PATH 或 TAO 环境变量。结束时输出版本、生效范围、`tao` 启动器位置和写入的文件。启动器默认在 `~/.local/bin/tao`（Windows 为 `%USERPROFILE%\.local\bin\tao.cmd`）；安装器不修改 PATH，若该目录不在 PATH 中，直接用摘要里的完整路径。

- `--scope user` 当前用户的所有项目；`--scope project` 指定项目、配置可与团队共享；`--scope local` 仅 Claude，当前项目且仅自己使用。Codex 的 `repo`／`local` 均归一为 `project`。
- **重复执行同一条安装命令即可升级**，匹配的依赖环境会复用，未重新指定来源时沿用原来源。
- 从本地工作目录安装（包含未提交修改）用 `--source .`，安装到别的项目再加 `--project /path/to/project`：

  ```sh
  python3 plugins/tao-dev/skills/tao-dev/scripts/tao.py install \
    --client codex --scope project --source .
  ```

  Windows 把 `python3` 换成可用的 Python 命令，如 `py -3`。

- 卸载用 `tao uninstall --client codex`：列出各份安装的范围与文件，确认后删除；`--list` 只查看。共享配置只清理对应项目，其他安装仍在使用的缓存保留。

`tao install` 完成安装、配置和升级；底层的 `tao setup` 只维护 tao 自身的运行环境，正常使用无需执行，与上表中接入业务项目检查工具的 **setup 动作**不是一回事。离线安装、marketplace 来源、目录归属等完整说明见 [安装管理说明](docs/engineering/installation.md)。

其他支持 Agent Skills 的客户端可以接入完整的**独立 skill**，读取相同规程、模板并调用 Python CLI；不要求 Claude／Codex。目录选择、运行准备及能力边界见 [跨客户端接入指南](docs/user/clients.md)。

## 支持状态

核心文档操作、配置驱动的验证与证据复用、独立审查记录导入、本地 HTML 出版已有实现。审查记录导入核对来源和输入一致性；CLI 本身不调度模型。

| 范围 | 当前依据与限制 |
|---|---|
| macOS 客户端 | Codex CLI 0.154.0、Claude Code 2.1.270 的安装、升级、回滚和卸载已在隔离环境验证；其他场景见验收记录 |
| Codex 原生 hook | 安装器使用兼容 manifest，并检查 skill、hook 与信任状态 |
| 其他 coding agent | 独立 skill 接入指南覆盖九种客户端；本机缺少对应 CLI，尚未原生验收，见 [兼容矩阵](docs/engineering/client-compatibility.md) |
| 其他平台与版本 | 原生 Windows 验收未完成；Python 运行环境的测试矩阵不等于客户端兼容矩阵 |
| 发布就绪 | 当前源码的完整独立审查仍待完成；已有结果不构成所有平台、版本和场景的支持承诺 |

具体受检版本、环境、结果和剩余工作以 [运行环境验收记录](docs/plans/2026-09/20260914-portable-runtime.md) 为准。HTML 构建不包含外部站点部署，当前未实现 PDF 出版。

## 参与开发

开发 tao-dev 需要 **uv 和 Python 3.11–3.14**。进入本仓库后：

```sh
uv sync --no-config --locked --extra publication
uv run --no-config --locked --extra publication python tests/acceptance/runtime.py --download
uv run --no-config --locked --extra publication python -m pytest
```

第二步显式下载测试所需 wheel；准备后普通回归离线运行，不调用模型。环境隔离、文档校验、手册构建、依赖导出和打包命令见 [开发指南](docs/engineering/development.md)。

本仓库通过 [AGENTS.md](AGENTS.md) 使用自身的 skill；运行材料在 `plugins/tao-dev/`，仅供维护的资料在 `docs/`。

## 许可

[Apache License 2.0](LICENSE)。使用、修改和再分发请保留版权声明与许可证文本。

## 深入阅读

- [使用指南](docs/user/workflow.md)：完整功能开发周期、审查与会话恢复。
- [跨客户端接入指南](docs/user/clients.md)：在 Claude／Codex 之外的 agent 中使用。
- [项目手册](docs/index.md)：产品需求、工程设计、长期决定与计划记录。
- [skill 入口](plugins/tao-dev/skills/tao-dev/SKILL.md)：agent 实际读取的规程总入口。
