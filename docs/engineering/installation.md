---
schema: tao.project.design/v0.1
id: DOC_20260915_P8J10N4KDFYZY2EN
title: 插件安装与卸载管理
locale: zh-Hans
status: draft
created: "2026-09-15"
updated: "2026-09-18"
spec_docs: ["DOC_20260914_E1B61A3F8V1TYAZB"]
---

# 插件安装与卸载管理

<!-- tao:section overview -->
## 目标与范围

提供一次调用即可安装完整插件、核心与出版依赖、配置客户端并运行 doctor 的安装入口。重复 install 刷新来源并升级；uninstall 按客户端发现安装，先展示文件与范围，再让用户选择删除。用户只需准备受支持的 Python、pip、Git 和目标客户端，不要求设置 TAO 环境变量。源码与插件分发共用同一安装实现；首次远程引导器只取得源码并转交 tao install。

install 是用户安装与升级的唯一完整入口。setup 一次准备相互隔离的核心与出版环境，但不负责客户端注册、scope、hook 绑定或最终 doctor 验收。install 在自己的事务流程中调用 setup，用户不需要另行执行。

<!-- tao:section architecture -->
## 组件与数据流

标准库安装模块在运行环境准备之前处理 install/uninstall。客户端适配模块使用原生命令管理 marketplace 与插件，并通过 Codex app-server 的配置写入 API 保留无关 TOML 配置。安装记录模块保存客户端、scope、项目、来源、版本、插件缓存路径、解释器与运行目录。运行入口按当前插件路径与工作目录选择记录，显式 TAO 覆盖仍兼容，但正常使用无需设置。

安装顺序为参数与边界检查、取得来源、准备两套锁定依赖、原生安装与范围配置、将 hook 绑定到已验证的 Python 和插件脚本绝对路径、记录运行绑定、原生加载与 doctor 检查、打印汇总。共享 tao CLI 保存在客户端配置目录的 tao-dev/cli/，命令包装默认写入 ~/.local/bin/；可用 --bin-dir 指定目录，安装报告提供绝对路径，不修改用户的 shell 配置。准备失败不宣称成功；重试复用完整运行环境。升级复用安装标识和运行根；原生缓存由客户端管理。更新前保留原有源码、所有已知旧插件缓存与所选原生配置项，doctor 通过后才原子更新共享命令；失败时恢复配置和缓存，恢复不完整则将记录标记为 preparing 并说明。卸载先修改所选范围的激活配置，再判断是否仍被其他安装引用，最后删除确定归属的 tao-dev 目录；共享配置仅移除本次管理的键。

本地内容摘要作为插件版本的 +local 构建标识，保证同版本工作目录修改也触发缓存更新。


### 运行绑定与 hook 实现

共享 CLI 根据项目从两端记录选择安装，先转交原生插件入口；未准备或无效记录不参与正常绑定。基础解释器取 TAO_PYTHON、匹配记录或启动解释器。运行根依次取 TAO_RUNTIME_DIR、记录 runtime_dir、CLAUDE_PLUGIN_DATA、平台用户数据目录；平台默认位置为 macOS 的 ~/Library/Application Support/tao-dev、Linux 的 ${XDG_DATA_HOME:-~/.local/share}/tao-dev、Windows 的本地应用数据目录。user 工具数据在客户端目录的 tao-dev/managed/<安装 ID>/，共享 CLI 位于 tao-dev/cli/。

静态 hook 使用 python3 -I -B 调用 hook.py，Claude 使用插件根和独立 args，Codex 使用插件根与带引号的命令字符串；安装器固定已验证解释器和脚本的绝对路径。事件从 stdin 输入，普通 hook 只选核心环境，不调用 setup。外层 handler 超时为 35 秒；短检查缓存绑定源、运行代码、契约、配置与依赖版本，仅保留合并指纹和有限诊断。

安装屏蔽可重定向写入的 pip 配置（target、prefix、user 等），只沿用调用者配置的包来源（index-url、extra-index-url、trusted-host、代理与证书），锁定哈希仍决定接受哪个 wheel；下载缓存沿用 pip 默认用户缓存，失败重试复用已取得的 wheel。启动时检查实际包版本和必要导入。项目匹配和卸载归属回归须覆盖共享 CLI、嵌套项目、无效记录和并发准备。

<!-- tao:section contracts -->
## 接口与使用

`tao install --client claude|codex|cursor|kiro --scope user|project|local` 默认使用 GitHub marketplace。`--source <插件目录、仓库目录或 Git URL>` 直接使用明确来源，生成仅本机使用的目录清单，不访问在线 marketplace。`--marketplace <目录或 GitHub 来源>` 显式选择 marketplace；与 --source 互斥。`--project <目录>` 默认当前目录；`--wheelhouse <目录>` 仅使用离线锁定 wheel；`--timeout <秒数>` 为每次依赖准备设定总时限，默认 300，0 取消上限。依赖准备逐包在 stderr 报告名称、版本、来源 URL、大小与实测速度，stdout 仍只有报告文档。文本默认输出路径、版本、范围、写入文件与使用指南；--format json 提供同一信息。

`tao upgrade --client <客户端> [--id <标识> | --all]` 就地更新已记录的安装：从记录取回作用域、项目与来源，没有记录时报错而不新建；`--id` 与 `--all` 互斥。不带 `--all` 时只在服务于 `--project`（默认当前目录）的记录中选择；`--all` 按稳定 ID 顺序升级该 client 的全部 tao 受管 user/project 记录，不包含 native-only 安装，每项独立回滚，部分失败继续处理并返回退出码 2。工作树位于主检出之内，接受上层目录就会在工作树里更新主检出的那份安装，并按成功报告，因此不按上层目录匹配，与运行数据定位的最深匹配不同；跨项目单项升级显式给出 `--project` 或 `--id`。它接受 `--ref`、`--wheelhouse` 和 `--timeout`，不接受 `--scope` 和来源参数。`tao install` 重复执行同一 client、scope 和 project 同样是升级，但 `--scope` 默认 user，漏写就会新建另一份安装。

`tao list --client <客户端>` 只读列出安装及其路径标注，不提供删除。受管行分别显示 `recorded_version` 和 `native_version`；Codex/Cursor project cache 按 SemVer 选择版本，不按目录 mtime。Codex project 配置和 Cursor project settings 不保存实际 cache path/version，因此客户端 cache 漂移时两个版本可能不同；native-only 行没有 `recorded_version`。`--format json` 返回相同的双版本字段。

Claude 使用原生 user/project/local。Codex、Cursor 与 Kiro 只有 user 和 repo/project 两级；repo 与 local 参数均归一化为 project，不创建第三种范围。Cursor user 写入 `~/.cursor/plugins/local/tao-dev`，project 写入项目 `.cursor/settings.json`；安装后需 Reload Window。Kiro 写入 `${KIRO_HOME:-~/.kiro}` 或项目 `.kiro` 下的 skill 与 V3 standalone hook；项目内容是本机 activation，不用于团队共享。Kiro V2 不支持，安装器不修改 `chat.agentEngine`。多个范围可共享原生缓存，移除一个范围不能卸载仍被另一范围使用的缓存。

<!-- tao:section invariants -->
## 不变量与边界

只删除明确属于本安装且通过路径检查的资源；符号链接不能将递归删除引向项目或用户数据。完全归属 tao-dev 的目录在报告中只列目录，不展开内部文件。保留用户已有配置、其他插件、其他安装及未知文件。安装记录分别置于客户端配置目录的 tao-dev/installations/，项目运行资料置于项目 .local/tao-dev/；这些本机路径不作为团队共享业务配置。共享 CLI 副本置于客户端中立的平台数据目录 tao-dev/cli/（可用 TAO_CLI_DIR 覆盖），因此删除某个客户端的配置目录不会使其它客户端的 tao 命令失效。升级以整目录改名替换该副本，而发起升级的进程通常正从该目录中运行，内容未变的 launcher 不重写；维护回归在三个平台上覆盖这次自我替换。

CLI 试验遵循 AGENTS.md：使用独立 CODEX_HOME、CLAUDE_CONFIG_DIR 与 Git 配置，禁止修改个人客户端或认证。必须检查项目内加载及项目外缺席。用户显式 install 包含所选插件及其已核对 hook 的配置授权；不隐式为任意外部 hook 批量写信任。

### 运行定位与数据目录

独立 skill 的入口根据脚本自身位置读取 runtime.json 和依赖清单，不依赖外层插件 manifest。运行数据按 TAO_RUNTIME_DIR、匹配安装记录、CLAUDE_PLUGIN_DATA、平台 tao-dev 数据目录的优先级选择。安装记录位于客户端配置目录的 tao-dev/installations/；配置目录由 CODEX_HOME／CLAUDE_CONFIG_DIR 指定，默认为 ~/.codex／~/.claude。

跨项目显式传 --project；嵌套项目选择最深匹配安装，项目安装优先于 user，Claude 同项目 local 优先于 project。项目安装工具数据位于 `.local/tao-dev/<客户端>/<作用域>/`。运行数据与安装日志不作为项目交付证据，不纳入 VCS；目录和匹配规则由安装实现维护，消费者按安装摘要和 doctor 定位。

<!-- tao:section errors -->
## 失败与恢复

缺少客户端或 Python 模块、离线依赖不足、无效来源、配置冲突或 doctor 失败均以非零退出并列出实际已写资源。运行环境故障按稳定规则号报告：`TAO-RUNTIME-001` 配置或解释器、`TAO-RUNTIME-002` 未准备、`TAO-RUNTIME-003` 损坏、`TAO-RUNTIME-004` 准备锁繁忙、`TAO-RUNTIME-005` 准备失败；规则号稳定，措辞可以改善，运行参考只要求按诊断消息和日志定位。安装与更新失败不能删除已有有效安装。卸载发现无法证明归属的资源时保留并说明；共享缓存仍有引用时保留。已有手工安装通过客户端元数据发现，只清理原生归属，不猜测环境变量曾指向的依赖目录。项目删除或原生插件已被手工卸载时，仍能清理已记录的剩余资源；缺少项目目录不能成为保留失效记录的理由。

<!-- tao:section verification -->
## 验证策略

单元与集成测试覆盖安装范围、重复安装、离线依赖、无环境变量运行、路径归属、非交互拒绝删除、共享安装保留和外部原生安装发现。原生探针在独立目录检查 Claude/Codex 安装、scope、升级与卸载；doctor 检查核心与出版环境 ready。CI 在 Linux、macOS 与 Windows 的托管 runner 上执行同一批探针，不调用模型也不使用凭据；真实客户端会话与 PowerShell 安装器仍按未执行记录。完整项目检查与独立审查结果在本节记录实际范围，不用单元测试替代客户端验收。

### 已记录的验收范围

以下是对应版本的历史执行，不表示当前代码自动通过同样检查。执行方法与限定客户端结果见[运行环境计划](../plans/2026-09/20260914-portable-runtime.md)。

| 受检范围 | 实际结果与限制 |
|---|---|
| 0.2.0安装器，macOS，Codex0.154.0/Claude2.1.270 | 31项客户端专项检查通过，覆盖原生安装、重复更新、共享范围、版本回退、缺项目及缺原生注册后的清理；未以此宣称公开发布 |
| macOS本地全量复验 | 312项pytest通过、0跳过，含当时5项原生探针；Codex project和Claude user/project/local生命周期通过启停、升级及移除。未调用模型或修改个人客户端认证 |
| 提交dd567c6，GitHub Actions run 35229860576 | Linux/macOS/Windows的15项原生安装探针通过；Windows的CPython3.11–3.14四格回归各435项通过。Claude2.1.274、Codex0.154.0；无凭据，不覆盖真实模型会话或PowerShell安装器 |

独立安装审查确认的升级回滚、共享CLI与失效清理缺陷已有修复回归。跨平台回归覆盖路径身份而非路径拼写、hook命令的路径语义和UTF-8隔离子进程；代码与测试维护这些约束，验证摘要不复述返工过程。

0.2.2在macOS/Python3.12、对应锁定wheel上的空间观测为core约14MiB、publication约105MiB，只是该环境的容量依据，不是通用上限。Ruff、依赖导出、受管理文档与HTML及两种包检查按当时范围通过；原始输出在忽略临时存储，不保证长期还原。原生Windows模型行为与当前输入的有效独立审查不能由这些安装探针推导。

### 离线 wheel 准备

在与目标机器具有相同系统、CPU 架构和 Python 次版本的联网机器上，进入同一版本的源码目录执行：

```sh
python3 -m pip download --only-binary=:all: --require-hashes --dest wheelhouse -r plugins/tao-dev/skills/tao-dev/scripts/requirements.txt
python3 -m pip download --only-binary=:all: --require-hashes --dest wheelhouse -r plugins/tao-dev/skills/tao-dev/scripts/requirements-publication.txt
```

将源码和 wheelhouse 复制到目标机器，运行：

```sh
python3 plugins/tao-dev/skills/tao-dev/scripts/tao.py install \
  --client codex --scope project --source . --wheelhouse ./wheelhouse
```

这一步不访问在线 marketplace 或 Python 包索引；客户端、Python、Git 和 shell 必须已安装。模型服务的网络需求不由插件安装器改变。
