# 插件运行环境

准备或诊断本插件的 Python 环境时读取本文。运行不依赖 uv；使用者提供 Python 3.11–3.14，准备时还须具备 venv 和 ensurepip。不要向系统 Python、业务项目的虚拟环境或插件源码目录安装依赖。

## 位置与作用域

客户端决定插件启用范围。Claude Code 的 user 表示当前用户各项目可用，project 表示项目共享配置，local 表示项目个人配置。Codex 使用 user 与 project；安装参数 repo、local 均归一为 project，不提供额外的个人项目作用域。插件内命令从当前插件根定位源码，插件目录按只读处理。

通过 tao install 安装后无需设置 TAO 环境变量。安装记录保存基础 Python、独立运行目录和原生插件缓存位置；插件入口按当前插件路径及工作目录选择记录。共享 CLI 从两个客户端的记录中按项目选择安装，先转交该安装的原生插件入口，再检查其依赖环境。CLI 的 --project 可明确指定项目；hook 使用当前工作目录。嵌套项目优先选择最深的项目记录，同一项目的 Claude local 优先于 project，项目记录优先于 user。准备未完成或无效的记录不参与正常运行绑定。

运行环境根按以下顺序选择：显式 TAO_RUNTIME_DIR、匹配安装记录中的 runtime_dir、Claude 提供的 CLAUDE_PLUGIN_DATA、平台用户数据目录中的 tao-dev。TAO_RUNTIME_DIR 必须为绝对路径，可用于离线预置、CI 与完全局部的实验；不改变客户端 scope。无安装绑定时的平台位置为：macOS 的 ~/Library/Application Support/tao-dev、Linux 的 ${XDG_DATA_HOME:-~/.local/share}/tao-dev、Windows 的本地应用数据目录中的 tao-dev。路径变量不写入项目共享配置。

安装记录位于客户端配置目录的 tao-dev/installations/。客户端配置目录分别由 CODEX_HOME 或 CLAUDE_CONFIG_DIR 指定，未指定时为 ~/.codex 或 ~/.claude。user 安装的工具数据位于该目录的 tao-dev/managed/<安装 ID>/；项目安装位于项目的 .local/tao-dev/<客户端>/<作用域>/，运行环境放在其中的 runtime/。共享 CLI 位于客户端配置目录的 tao-dev/cli/，由安装器管理；原生插件缓存由客户端管理。

项目配置仍在 .tao/config.toml，规格和计划在 docs/，项目报告在配置的 temporary 目录。运行环境和安装日志属于工具数据，不作为项目验证证据，也不纳入 VCS。不同项目可复用匹配的依赖，不共享项目输入或检查结果。

## 准备与执行

下文 tao 指安装器提供的命令，也可用 Python 直接调用本插件 scripts/tao.py。TAO_PYTHON 可明确选择基础解释器，必须是单个可执行路径，不含参数；未指定时使用匹配安装记录中的解释器，无记录时使用启动入口的解释器。显式指定无效时不回退。基础解释器只用来创建独立环境，不向它安装包。

客户端静态 hook 通过 PATH 中的 `python3 -I -B` 调用 scripts/hook.py：Claude 使用 `${CLAUDE_PLUGIN_ROOT}` 和独立 args，Codex 使用 `${PLUGIN_ROOT}` 和带引号的命令字符串。tao install 会把解释器与脚本占位符固化为已验证的绝对路径，因此安装后的 hook 不依赖 PATH 中仍有同名 Python。脚本接受客户端通过 stdin 传入的事件，并与 CLI 采用相同运行环境规则。

| 操作 | 实际行为 |
|---|---|
| tao install --client claude\|codex --scope <作用域> | 安装或更新完整插件，准备核心与出版环境，写入客户端配置与运行绑定，并检查两套环境的 doctor 结果 |
| install 附加 --source <目录或 Git 来源> | 从完整插件或仓库建立本机专用目录清单，再通过客户端原生机制安装 |
| install 附加 --marketplace <目录或 Git 来源> | 从明确指定的 marketplace 安装；与 --source 互斥 |
| tao uninstall --client claude\|codex --list | 只读列出已管理及可发现的原生安装、范围与资源 |
| tao uninstall --client claude\|codex | 展示清单并让用户选择、确认删除；自动化须同时指定 --id 与 --yes |
| tao doctor | 只读诊断核心环境，并发现独立出版环境；依赖缺失也输出诊断，不要求先有项目 |
| tao doctor --publication | 只读诊断出版环境 |
| tao setup | 准备相互隔离的核心与出版环境；已匹配且完整时分别复用 |
| install 或 setup 附加 --wheelhouse <目录> | 依赖仅从明确提供的本地 wheel 目录安装，不访问包索引；Git 来源与客户端操作仍按来源执行 |
| 其他命令 | 使用所需的已准备环境；docs build 选择出版环境，其余选择核心 |

显式 install 包含完整插件、核心与出版依赖，以及所选客户端范围内配置的安装授权。独立 setup 在已有依赖准备授权内一次准备两套环境，无需让使用者选择类型。普通命令与 hook 不下载依赖、不隐式运行 setup。网络依赖准备使用 PyPI；企业离线分发可提供与清单哈希匹配的 wheel。安装过程屏蔽可能将写入重定向的 pip 配置，环境缺少合适包时说明原因，不改为源码构建或未锁定安装。

不支持的 Python、缺少 venv／ensurepip、依赖或网络缺失均报告 not_run，不能自动安装系统软件。TAO-RUNTIME-001 表示配置或解释器问题，002 表示未准备，003 表示环境损坏，004 表示准备锁繁忙，005 表示准备失败；错误信息给出下一步及可用日志位置。完整 verify 在运行前失败时保持 blocked。

hook 在项目未配置时直接无操作，不创建工具数据；项目已配置但 Python 或核心环境不可用时，返回未执行的提示，不阻止原始编辑，也不把缺失检查报告为通过。hook 不调用 setup。面向使用者的完整安装应使用 tao install，由它准备两套依赖环境、保存运行绑定并写入精确 hook 路径。

## 更新和故障

已管理安装重复运行相同客户端和作用域的 install，会刷新来源并升级，复用安装标识与完整且匹配的环境；不指定新来源时沿用记录中的来源。依赖、Python 或平台改变后重新运行 doctor，并在已有授权内执行 install 或 setup。

运行前检查环境实际包版本和必要导入，损坏时要求显式 setup 准备新代次。安装失败保留日志和已有完整环境；不自动清理旧代次、破解锁或删除共享数据。中断后先确认无活跃准备者，再处理本插件拥有的锁或未完成目录。

uninstall 先处理所选范围的客户端激活，再删除可确认归属的安装资源；其他安装仍引用的原生缓存会保留。未知文件和无法确认归属的手工运行环境保留并说明。共享 CLI 保留，供后续 install/uninstall 使用。未选择安装、取消确认或输入结束均不删除；--yes 不能隐式选择全部安装。
