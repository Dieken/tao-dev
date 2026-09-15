# 插件运行环境

准备或诊断本插件的 Python 环境时读取本文。运行不依赖 uv；使用者提供 Python 3.11–3.14，准备时还须具备 venv 和 ensurepip。不要向系统 Python、业务项目的虚拟环境或插件源码目录安装依赖。

## 位置与作用域

客户端决定插件启用范围。Claude Code 的 user 表示当前用户各项目可用，project 表示项目共享配置，local 表示项目个人配置；这些 scope 不决定虚拟环境位置。源码由客户端提供的插件根定位，不查找 PATH 中同名 tao。插件目录按只读处理。

运行环境根按以下顺序选择：显式 TAO_RUNTIME_DIR、Claude 提供的 CLAUDE_PLUGIN_DATA、平台用户数据目录中的 tao-dev。TAO_RUNTIME_DIR 必须为绝对路径，可用于离线预置、CI 与完全局部的实验；不改变客户端 scope。Codex 未提供已验证的数据目录变量时使用平台用户目录：macOS 为 ~/Library/Application Support/tao-dev，Linux 为 ${XDG_DATA_HOME:-~/.local/share}/tao-dev，Windows 为本地应用数据目录中的 tao-dev。路径变量不写入项目共享配置。

项目配置仍在 .tao/config.toml，规格和计划在 docs/，项目报告在配置的 temporary 目录。运行环境和安装日志属于工具数据，不作为项目验证证据，也不纳入 VCS。不同项目可复用匹配的依赖，不共享项目输入或检查结果。

## 准备与执行

下文 tao 指本插件 scripts/tao.py 的受信任入口，不要求全局注册命令。先用选定 Python 调用该入口；TAO_PYTHON 可明确选择基础解释器，必须是单个可执行路径，不含参数。未指定时使用启动入口的解释器；显式指定无效时不回退。只把它用来创建独立环境，不向它安装包。

POSIX shell 可执行 `sh <插件根>/skills/tao-dev/scripts/tao-launch.sh cli <参数>`；PowerShell 入口为同目录的 tao-launch.ps1。路径含空格时整体引用。启动器依次探测 python3、python、py -3；显式 TAO_PYTHON 优先且不会被替换。validate 入口转发独立文档校验器，hook 入口供客户端事件调用。Python 入口和启动器采用同一套运行环境规则，启动器不负责安装客户端或注册命令。

| 操作 | 实际行为 |
|---|---|
| tao doctor | 只读诊断核心环境，并发现独立出版环境；依赖缺失也输出诊断，不要求先有项目 |
| tao doctor --publication | 只读诊断出版环境 |
| tao setup | 准备核心环境；已匹配且完整时复用 |
| tao setup --publication | 准备核心与出版的完整环境 |
| setup 附加 --wheelhouse <目录> | 仅从明确提供的本地 wheel 目录安装，不访问索引 |
| 其他命令 | 使用所需的已准备环境；docs build 选择出版环境，其余选择核心 |

依赖准备须在已有安装授权内执行；目标与授权明确时由 agent 选择核心或出版，无需反复询问类型。普通执行不联网、不隐式运行 setup。网络准备使用 PyPI；企业离线分发可提供与清单哈希匹配的 wheel。安装过程屏蔽可能将写入重定向的 pip 配置，环境缺少合适包时说明原因，不改为源码构建或未锁定安装。

不支持的 Python、缺少 venv／ensurepip、依赖或网络缺失均报告 not_run，不能自动安装系统软件。TAO-RUNTIME-001 表示配置或解释器问题，002 表示未准备，003 表示环境损坏，004 表示准备锁繁忙，005 表示准备失败；错误信息给出下一步及可用日志位置。完整 verify 在运行前失败时保持 blocked。

hook 在项目未配置时直接无操作，不创建工具数据；项目已配置但 Python 或核心环境不可用时，返回未执行的提示，不阻止原始编辑，也不把缺失检查报告为通过。hook 不调用 setup。客户端 hook 需要可用的启动器；仅有 Python 或 PowerShell 入口不保证客户端会触发它。

## 更新和故障

依赖、Python 或平台改变后，重新运行 doctor，并在已有授权内执行 setup。完整且匹配的环境可复用；准备失败时保留已有可用环境。

运行前检查环境实际包版本和必要导入，损坏时要求显式 setup 准备新代次。安装失败保留日志和已有完整环境；不自动清理旧代次、破解锁或删除共享数据。中断后先确认无活跃准备者，再处理本插件拥有的锁或未完成目录。
