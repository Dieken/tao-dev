# 运行环境与插件安装

准备依赖、安装更新或诊断运行环境时读取。需要 Python 3.11–3.14、venv 和 ensurepip；运行不依赖 uv。skill 目录只读，依赖安装到独立环境，不进入系统 Python、业务 venv 或 skill 源码目录。

## 通用运行环境

独立接入时保留完整 skill 目录，用可用的受支持 Python 调用 [scripts/tao.py](../scripts/tao.py)，不要求 Claude／Codex 或全局 tao 启动器。以下 tao 代表该入口；业务项目通过 `--project` 指定。

| 操作 | 用途 |
|---|---|
| `tao doctor` / `tao doctor --publication` | 只读诊断核心／出版环境，缺依赖也可运行 |
| `tao setup` | 显式准备核心与出版两套环境，复用已匹配且完整的环境 |
| setup 的 `--wheelhouse <目录>` | 仅从本地锁定 wheel 准备依赖 |

setup 需要已有依赖准备授权；单纯检查或审查请求不隐含该授权。普通命令和 hook 只使用已准备环境，不隐式安装。依赖锁定安装，失败时不改用源码构建或未锁定包，也不自动安装系统软件。缺环境时继续可用的项目检查并说明 tao 检查未运行。

默认使用匹配安装记录或平台 tao-dev 数据目录。诊断、CI 或局部实验可显式覆盖：

- `TAO_PYTHON`：单个基础解释器路径，不含参数；无效时报错，不回退。
- `TAO_RUNTIME_DIR`：绝对运行目录，不改变客户端的 skill／插件生效范围。

## Claude／Codex 完整插件

完整插件安装器仅支持以下客户端；其他客户端按其 skill 接入方式加载目录，再准备上述运行环境。

| 操作 | 用途 |
|---|---|
| `tao install --client claude\|codex --scope <作用域>` | 安装／更新完整插件，准备两套环境，配置客户端并检查 doctor |
| install 的 `--source <目录或 Git 来源>` / `--marketplace <目录或 Git 来源>` | 选择完整插件／仓库或 marketplace 来源，两者互斥 |
| install 的 `--wheelhouse <目录>` | 限制 Python 依赖来源，不限制 Git 来源或客户端联网 |
| `tao uninstall --client claude\|codex --list` | 只读列出安装与资源 |
| `tao uninstall --client claude\|codex` | 选择并确认所删安装；自动化必须同时提供 --id 与 --yes |

显式 install 授权所选作用域的插件及两套依赖准备，完成后无需 TAO 变量。Claude 的 scope 为 user、project、local；Codex 为 user、project，repo/local 归一为 project。客户端决定启用范围，切换 cwd 或运行目录不能代替范围隔离。

## 更新与故障处理

同一客户端与作用域重复 install 更新并复用安装标识；未指定来源时沿用原来源。独立 skill 更新整个目录，保留外部运行数据；依赖、解释器或平台变化后先 doctor，再在已有授权内 install 或 setup。

TAO-RUNTIME-001 至 005 分别表示配置／解释器、未准备、损坏、准备锁繁忙、准备失败；按诊断及日志定位。缺 Python、venv、依赖或网络时报告 not_run，完整 verify 启动失败保持 blocked。显式 setup 可准备新代次，失败保留已有完整环境；中断后确认无活跃准备者再处理本次锁和未完成目录，不删除共享数据。

uninstall 只处理所选安装及归属明确的资源，保留其他安装仍使用的缓存、未知文件及共享 CLI。取消、无选择或输入结束均不删除；--yes 不表示全部安装。
