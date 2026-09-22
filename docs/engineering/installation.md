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

实现步骤：先验证记录与运行绑定，再完成客户端适配及原生隔离探针，然后实现安装、升级、交互卸载与引导器，最后简化 README、运行回归和独立审查。临时命令输出与探针放 tmp/tao/。本地内容摘要作为插件版本的 +local 构建标识，保证同版本工作目录修改也触发缓存更新。


### 运行绑定与 hook 实现

共享 CLI 根据项目从两端记录选择安装，先转交原生插件入口；未准备或无效记录不参与正常绑定。基础解释器取 TAO_PYTHON、匹配记录或启动解释器。运行根依次取 TAO_RUNTIME_DIR、记录 runtime_dir、CLAUDE_PLUGIN_DATA、平台用户数据目录；平台默认位置为 macOS 的 ~/Library/Application Support/tao-dev、Linux 的 ${XDG_DATA_HOME:-~/.local/share}/tao-dev、Windows 的本地应用数据目录。user 工具数据在客户端目录的 tao-dev/managed/<安装 ID>/，共享 CLI 位于 tao-dev/cli/。

静态 hook 使用 python3 -I -B 调用 hook.py，Claude 使用插件根和独立 args，Codex 使用插件根与带引号的命令字符串；安装器固定已验证解释器和脚本的绝对路径。事件从 stdin 输入，普通 hook 只选核心环境，不调用 setup。外层 handler 超时为 35 秒；短检查缓存绑定源、运行代码、契约、配置与依赖版本，仅保留合并指纹和有限诊断。

安装屏蔽可重定向写入的 pip 配置（target、prefix、user 等），只沿用调用者配置的包来源（index-url、extra-index-url、trusted-host、代理与证书），锁定哈希仍决定接受哪个 wheel；下载缓存沿用 pip 默认用户缓存，失败重试复用已取得的 wheel。启动时检查实际包版本和必要导入。项目匹配和卸载归属回归须覆盖共享 CLI、嵌套项目、无效记录和并发准备。

<!-- tao:section contracts -->
## 接口与使用

`tao install --client claude|codex --scope user|project|local` 默认使用 GitHub marketplace。`--source <插件目录、仓库目录或 Git URL>` 直接使用明确来源，生成仅本机使用的目录清单，不访问在线 marketplace。`--marketplace <目录或 GitHub 来源>` 显式选择 marketplace；与 --source 互斥。`--project <目录>` 默认当前目录；`--wheelhouse <目录>` 仅使用离线锁定 wheel；`--timeout <秒数>` 为每次依赖准备设定总时限，默认 300，0 取消上限。依赖准备逐包在 stderr 报告名称、版本、来源 URL、大小与实测速度，stdout 仍只有报告文档。文本默认输出路径、版本、范围、写入文件与使用指南；--format json 提供同一信息。

`tao upgrade --client claude|codex [--id <标识>]` 就地更新已记录的安装：从记录取回作用域、项目与来源，没有记录时报错而不新建；记录多于一份时要求 --id。不带 --id 只在服务于 --project（默认当前目录）的记录中选择：项目路径精确匹配，user 作用域的记录服务所有项目。工作树位于主检出之内，接受上层目录就会在工作树里更新主检出的那份安装，并按成功报告，因此不按上层目录匹配，与运行数据定位的最深匹配不同；跨项目升级显式给出 --project 或 --id。客户端自行安装的原生安装没有来源记录，无法升级，报错给出接管它的 tao install 命令。它接受 --ref、--wheelhouse 和 --timeout，不接受 --scope 和来源参数。`tao install` 重复执行同一 client、scope 和 project 同样是升级，但 --scope 默认 user，漏写就会新建另一份安装。

`tao list --client claude|codex` 只读列出安装及其路径标注，不提供删除。`tao uninstall --client claude|codex` 列出已管理及可发现的原生安装并交互选择；--list 只读列出。确认前的清单按路径标注 delete、modify、keep 或 client（由客户端自身的插件移除处理），并附含义说明；取消时报告 status 为 cancelled。自动化可用 --id 与 --yes 删除明确的一份，不能以 --yes 隐式删除全部。未选择或输入结束不删除。

Claude 使用原生 user/project/local。Codex 只有 user 和 repo/project 两级；repo 与 local 参数均归一化为 project，不创建第三种范围。多个范围可共享原生缓存，移除一个范围不能卸载仍被另一范围使用的缓存。

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

### 本次验证结果

2026-09-15，在 macOS 上使用 Codex CLI 0.154.0、Claude Code 2.1.270 验证 0.2.0 安装器。31 项客户端专项检查通过，包括实际原生安装、重复更新、共享范围保留、v2 回退至 v1 后的原生加载，以及项目删除和原生注册已移除后的清理。完整本地来源探针确认两个客户端的核心与出版环境 ready、无 TAO 变量 doctor、重复安装复用和按 ID 卸载。GitHub 引导脚本通过隔离 Git URL 重写指向本地裸仓库验证，覆盖远程来源流程；这不代表当前变更已经发布到公共仓库。

独立审查提出的升级回滚、跨客户端共享 CLI 与失效安装清理问题均已修复，8 项收尾回归通过；本次审查范围仅限安装改动。安装探针报告位于忽略的 tmp/tao/，未调用模型、未修改个人客户端或认证。原生 Windows 仍未验收。

最终全量 pytest：302 项通过，5 项原生探针按默认策略跳过；这些原生探针已在上述 31 项独立运行中通过。项目配置的 Python 静态检查、依赖导出同步检查及 shell 语法检查通过。30 份受管理开发文档的格式、跨文档引用与书籍导航验证通过；未检查历史删除基线，也不据此声明全产品交付就绪。

0.2.1 将两端 hook 改为直接执行 hook.py：静态 marketplace 配置使用 PATH 中的 python3，完整安装将其替换为已验证的解释器与插件脚本绝对路径，并删除 POSIX／PowerShell 启动包装。最终 305 项回归通过，5 项原生探针按默认策略跳过；另行启用的两项双客户端原生范围测试通过。隔离的 Codex project 与 Claude local 完整安装均准备核心及出版 venv 并通过 doctor；Codex 从 0.2.0 重复安装到 0.2.1 后复用两套环境，最终 hook 信任通过。依赖导出、Ruff 错误规则、受管理文档、HTML 书籍与两种插件包检查通过；原生 Windows 仍未执行。

0.2.2 将 setup 收敛为一次准备核心与出版两套隔离环境，删除 --publication 参数；install 只调用一次完整 setup。macOS、Python 3.12 下使用当前锁定 wheel 实测 core venv 占用约 14 MiB，publication venv 约 105 MiB。并发准备会等待同一环境完成后复用；出版准备失败仍保留已经验证的核心环境。

完整复验启用 5 项默认关闭的原生客户端探针后，312 项 pytest 全部通过、无跳过。Codex project 与 Claude local 的本地源码安装均完成首次安装、重复安装复用、无 TAO 变量 doctor、绝对 hook 绑定、按 ID 卸载及空列表确认；Claude user／project／local 和 Codex 的原生生命周期均完成禁用、启用、0.2.2 至 0.2.3 更新与移除。复验中修正 Claude 生命周期脚本仍读取已删除根 plugin.json 的过时路径。依赖导出、Ruff 错误规则、30 份受管理文档、HTML 书籍及 public／Codex 兼容包检查通过。测试未调用模型、未修改个人客户端或认证；原生 Windows 仍未执行。

2026-09-17，GitHub Actions run 35229860576（提交 `dd567c6`）首次在 windows-latest 上跑通全部安装相关检查。三个平台安装当前 Claude Code 2.1.274 与 codex-cli 0.154.0 后，15 项原生探针全部通过，覆盖原生安装、scope 选择、重复安装、失败升级回滚与移除；Windows 上另有 CPython 3.11–3.14 的四格回归各 435 项通过。通过前修复了三处 Windows 专有缺陷：hook 信任按路径而非字节比较命令、marketplace 源按文件系统身份而非拼写识别、隔离子进程以 `-X utf8` 运行以免 pip 用旧代码页编码中文路径。探针不调用模型、不使用客户端凭据，也不覆盖 PowerShell 安装器与真实客户端会话。

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
