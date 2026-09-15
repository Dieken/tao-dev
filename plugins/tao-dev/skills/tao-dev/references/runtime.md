# 插件运行环境

准备依赖、安装更新或诊断运行环境时读取。使用者提供 Python 3.11–3.14、venv 和 ensurepip；运行不依赖 uv。插件目录只读，依赖安装到独立环境，不进入系统 Python、业务 venv 或插件源码目录。

## 安装与执行

| 操作 | 用途 |
|---|---|
| `tao install --client claude\|codex --scope <作用域>` | 安装／更新完整插件，准备核心与出版环境，配置客户端并检查 doctor |
| install 的 `--source <目录或 Git 来源>` | 使用完整插件或仓库来源；与 --marketplace 互斥 |
| install 的 `--marketplace <目录或 Git 来源>` | 从指定 marketplace 安装 |
| `tao uninstall --client claude\|codex --list` | 只读列出安装与资源 |
| `tao uninstall --client claude\|codex` | 选择并确认所删安装；自动化必须同时提供 --id 与 --yes |
| `tao doctor` / `tao doctor --publication` | 只读诊断核心／出版环境，缺依赖也可运行 |
| `tao setup` | 一次准备两套环境，复用已匹配且完整的环境 |
| install／setup 的 `--wheelhouse <目录>` | 仅从该目录安装依赖；不限制 Git 来源或客户端自身联网 |

显式 install 授权所选作用域的插件及两套依赖准备；setup 在已有依赖准备授权内执行。普通命令和 hook 只使用已准备环境，不隐式安装。依赖锁定安装，失败时不改用源码构建或未锁定包，也不自动安装系统软件。

Claude 的作用域为 user、project、local；Codex 为 user、project，repo/local 参数归一为 project。客户端决定启用范围；切换 cwd 或运行环境目录不能改变安装作用域。

## 定位与覆盖

通过 install 安装后无需 TAO 环境变量。跨项目显式传 `--project`；嵌套项目选择最深匹配安装，项目安装优先于 user，Claude 同项目 local 优先于 project。

诊断或局部实验可显式设置：

- `TAO_PYTHON`：单个基础解释器路径，不含参数；无效时报错，不回退。
- `TAO_RUNTIME_DIR`：绝对运行目录，适用于 CI、离线预置和局部实验，不改变客户端 scope。

无显式覆盖时优先使用匹配安装记录，再使用 CLAUDE_PLUGIN_DATA 或平台 tao-dev 数据目录。安装记录位于客户端配置目录的 tao-dev/installations/；配置目录由 CODEX_HOME／CLAUDE_CONFIG_DIR 指定，默认 ~/.codex／~/.claude。项目安装的工具数据位于 `.local/tao-dev/<客户端>/<作用域>/`，运行数据和安装日志不作为项目证据或纳入 VCS。

## 更新与故障处理

同一客户端与作用域重复 install 可更新并复用安装标识；不指定来源时沿用原来源。依赖、解释器或平台变化后先 doctor，再在已有授权内 install 或 setup。错误 TAO-RUNTIME-001 至 005 分别表示配置／解释器、未准备、损坏、准备锁繁忙、准备失败；按诊断的下一步与日志定位。

缺 Python、venv、依赖或网络时报告 not_run；完整 verify 启动失败保持 blocked。损坏环境用显式 setup 准备新代次；失败保留日志与已有完整环境。中断后先确认无活跃准备者，再处理本插件拥有的锁和未完成目录，不自动删除旧代次或共享数据。

uninstall 按所选安装处理激活与归属明确的资源，保留其他安装仍使用的缓存、未知文件及共享 CLI。取消、无选择或输入结束均不删除；--yes 不表示选择全部安装。
