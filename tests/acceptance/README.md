# 实际客户端试验

这些试验包含会调用已配置模型的真实会话。`tests/test_native_sessions.py` 对 Cursor 与 Kiro 使用统一 readiness：CLI 不存在或只读登录检查失败时自动跳过，否则普通 pytest 会自动运行一次受限、可计费的真实写入和 hook 触发；本地与 CI 规则相同。其他长流程仍通过下列命令显式运行。所有 workspace 都选择不继承开发仓库指导文件的独立临时目录；脚本不安装客户端、不重新登录、不修改个人配置。

无需登录的原生安装、scope、升级和卸载探针只要求相应 CLI 存在，缺失时跳过。GitHub CI 自动安装 Claude Code、Codex、Cursor 与 Kiro CLI，但不配置凭据，因此运行安装探针并跳过真实会话。所有模型子进程都有按场景设置的硬超时；Cursor/Kiro hook 探针为 45 秒，超时后终止进程组并保存摘要。

先按 [开发指南](../../docs/engineering/development.md) 准备开发环境并显式运行 runtime.py --download，取得与发布清单匹配的 wheel。clients.py 在试验 workspace 内显式准备独立核心环境；所有后续命令和 hook 共用这个 TAO_RUNTIME_DIR，既不要求客户端安装 uv，也不向用户数据目录准备环境。

```sh
.venv/bin/python tests/acceptance/clients.py --client claude --case recover --claude-scope project --reuse-claude-auth --disable-hooks --workspace /tmp/tao-claude-recover
.venv/bin/python tests/acceptance/clients.py --client claude --case plan --claude-scope local --reuse-claude-auth --workspace /tmp/tao-claude-plan
.venv/bin/python tests/acceptance/clients.py --client claude --case routing --claude-scope local --reuse-claude-auth --workspace /tmp/tao-claude-routing
.venv/bin/python tests/acceptance/lifecycle.py --client claude --claude-scope user --workspace /tmp/tao-claude-lifecycle
.venv/bin/python tests/acceptance/clients.py --client codex --case write --isolated-codex --reuse-codex-auth --codex-legacy --trust-test-hook --workspace /tmp/tao-codex-write
.venv/bin/python tests/acceptance/clients.py --client codex --case recover --isolated-codex --reuse-codex-auth --codex-legacy --trust-test-hook --disable-hooks --workspace /tmp/tao-codex-recover
.venv/bin/python tests/acceptance/clients.py --client codex --case routing --isolated-codex --reuse-codex-auth --codex-legacy --workspace /tmp/tao-codex-routing
.venv/bin/python tests/acceptance/lifecycle.py --codex-legacy --workspace /tmp/tao-codex-lifecycle
PYTHONPATH=tests .venv/bin/python -m acceptance.behavior_live --client claude --workspace /tmp/tao-claude-behavior
PYTHONPATH=tests .venv/bin/python -m acceptance.behavior_live --client codex --workspace /tmp/tao-codex-behavior
```

模型试验必须明确选择独立客户端状态；省略隔离参数时，两端均在启动客户端前返回 blocked，不回退个人配置模式。Codex 选择 --isolated-codex：每个案例使用新的独立 workspace，CODEX_HOME、XDG_CONFIG_HOME、Git 配置位置和安装缓存均留在该工作区；仅试验项目启用插件，客户端默认禁用。安装后用原生 app-server 查询技能边界，项目外空列表之外仍须模型对照。0.154.0 的调用级 trust override 不能阻止其持久化项目信任，不能把它当作配置隔离。

--reuse-codex-auth 明确允许短时复用现有文件式 ChatGPT 认证；仅复制有效期能够覆盖本例的访问令牌、ID token 和账户标识，不复制刷新令牌。副本限制为 0600，调用结束删除并从事件日志中删去任何匹配的令牌值；过期、其他认证方式或自定义 provider/profile 返回未执行，不自动刷新。临时模型配置沿用个人已选模型及供应商路由，禁用远端插件目录、apps、网络搜索和代理委派。报告中的配置模型名不冒充服务端独立确认；Codex token 事件也不提供真实账单。该维护适配目前针对 POSIX，不能用它声称原生 Windows 验收通过。

0.154.0 对公共包只发现 skill，不发现 hook。--codex-legacy 使用 [打包器](../../scripts/package_plugin.py) 从相同运行源生成明确的兼容副本；省略该选项可保留公共包反例。--trust-test-hook 先检查原生 hook 清单恰好只有项目内的已知 handler，核对安装脚本与资源字节，再将该 handler 的精确哈希信任写入临时配置，并重新查询确认；不使用信任绕过参数。--disable-hooks 用于真实客户端禁用后的显式验证案例。

lifecycle.py 不调用模型，实际安装、禁用、重新启用、更新试验副本的版本及描述、卸载，再以新的原生查询验证变化。兼容包同时验证 hook 禁用／移除和定义变更后的信任失效；只改变包版本不会使相同定义的信任失效，信任哈希不是包代码的完整性证明。它不修改源版本或个人安装；更新重新产生默认启用项时必须恢复临时客户端的默认禁用，避免项目外可见。该检查证明加载生命周期，不能替代模型任务和原生 hook 行为。

Claude 选择 --claude-scope user|project|local 和 --reuse-claude-auth，在全新的 CLAUDE_CONFIG_DIR 中通过原生市场与安装命令配置该范围。既有 macOS Keychain 或文件认证中的访问令牌只进入子进程环境；不携带刷新令牌，不重新登录，过期及自定义供应商路由明确拒绝。模型沿用已选模型，允许工具限制在 Read、Glob、Grep、Skill、Bash、Write、Edit，每例 CLI 预算上限 2 美元。前后比较既有凭据与监测文件，不自动回滚变化。这里的 user 作用于试验配置的所有目录，project／local 只作用于安装项目；不改变个人日常安装。[认证管理](https://code.claude.com/docs/en/authentication)、[环境变量](https://code.claude.com/docs/en/env-vars)

inside 核对实际发现、引用定位、doctor/status；outside 不使用工具，只查询初始可用能力，同时核对初始化清单。Claude user 范围在同一试验配置的项目外也应可见，project／local 则不可见。write 故意创建无效文档，禁止模型手工运行 hook，以便检查原生 PostToolUse 反馈。review 在相同小型导出样例上独立寻找违反“不得覆盖”的行为；Claude 用具名 reviewer 作为当前会话角色，不冒充子代理调度。两份初审输入互不包含对方结论。

plan 在明确授权的非 Git 微型维护样例中通过主 skill 创建计划，再调用 handoff；此例使用简化路径，不代表完整功能开发的阶段推进验收。产出完整计划及相同 CHG 的交接，校验实际文档，保留未实现任务。该微型场景的 Claude 调用明确使用低推理强度与简短文档指导，避免把大篇幅写作混入加载验收；不是对默认推理强度的耗时保证。verify 使用真实失败基线，通过 review 动作只运行确定性验证，预期如实报告失败而不修复代码或勾选任务。Claude 要核对真实 Skill 工具调用，不能仅凭命令出现在初始化列表就算验收。lifecycle.py 的 --client claude 与 --claude-scope 组合检查原生启停、版本更新及卸载；这些不调用模型的检查仍不能替代流程行为。

routing 用一个不改变需求、设计或文档的 Python 语法修正检查渐进读取。agent 必须启用 tao-dev，并且只读取 [`references/engineering.md`](../../plugins/tao-dev/skills/tao-dev/references/engineering.md) 与 [`references/workflow.md`](../../plugins/tao-dev/skills/tao-dev/references/workflow.md)，不应进入工具、运行环境、配置化验证、文档格式、出版、本地化、术语、证据保存或模板分支。报告只从实际 Read、Bash 或 Codex command 工具输入提取路径，不采信模型自己的说明；目录级资源扫描单独标为失败，因为这种日志不能准确证明读入边界。探针还独立编译结果，检查未创建 docs 文件且 requirements.txt 与 .tao/config.toml 未变。它验证当前客户端的一次可观察行为，不证明所有任务指令都会采用相同读取路径，也不能充当修改前后的因果基线。

behavior_live.py 执行契约中的真实双轮交互场景，不接受其他 coding agent。专用测试项目只说明导出保留策略尚未决定，不在任务指令或文件中泄漏 30 天及失败处理答案。首轮必须提出会影响产品行为的关键问题，且不得写入文件；脚本仅在该可观察条件命中时发送固定用户回复。第二轮必须以客户端报告的同一 session ID 接续，回答后不得重复提问。两轮事件、逐轮文件哈希差异、客户端版本、可观察模型、token 用量、CLI 估算费用及未知真实账单分别保存；任何缺失 session、换 session、超时、条件不匹配或遥测缺失均为 blocked。普通 pytest 只用伪执行器验证执行流程，不启动模型。

原始事件、错误流、运行时间及个人配置文件散列比较存于本仓库 tmp/tao/client-acceptance/，不纳入 VCS。监测涵盖 Codex 配置、认证及 hook，Claude 设置与市场元数据，以及个人 Git 配置；报告只给出变化文件名，不输出秘密。退出 0 只表示进程正常且监测文件未变；验收结论还必须检查初始化组件清单、实际工具调用、输出、模型标识和供应商依据。文件变化可能来自客户端自动维护或并行操作，必须调查，不能自动恢复。监测清单不构成对全部用户目录的完整审计。

模型返回的 token 使用量、CLI 按标价报告的费用和真实账单费用分别记录。未知项保留 unknown；不要以两个 CLI 的名称断言两个供应商。Cursor/Kiro 自动 hook 会话硬上限 45 秒；`clients.py` 与 `behavior_live.py` 的真实会话默认且最多 60 秒。到期终止完整进程树并调查原因。试验材料仅包含自带合成样例和本插件运行资源，不传入维护仓库或其他项目资料。

recover 创建新的隔离项目，用实际 CLI 生成计划、执行失败基线并保存 handoff，然后启动没有旧会话历史的客户端。模型只能修改导出实现及已有计划；验收者另行检查 ID 保持、回归通过和修改范围。quality.py 用 Coverage.py 的 subprocess 支持执行维护测试并汇总报告，不调用模型；所有覆盖率数据位于 tmp/tao/coverage/。

scopes.py 专门验证 Claude 的 user、project、local 安装范围。每次传入新的 --workspace 和 --scope；脚本将 CLAUDE_CONFIG_DIR、XDG_CONFIG_HOME、GIT_CONFIG_GLOBAL 与运行目录限定在 workspace，再调用真实市场和插件安装命令。这里的 user 仅属于隔离客户端配置，不修改个人安装。加 --probe 读取项目内外初始化事件；scope_loading_verified 表示加载边界正确，model_execution_verified 单独表示模型执行成功。隔离配置没有认证时，加载成功不能代替命令或 hook 的模型行为验收。项目外应无项目级插件；user 范围则在隔离配置的两个目录中都可见。

运行环境测试验证 Python 隔离启动，覆盖率只能统计实际接受 Coverage.py 注入的进程。发布环境不安装开发用 coverage，也不为提高数字关闭 Python 隔离模式；报告中的未观测行不能解释为行为测试未执行。

独立代码审查的维护入口为 [review_claude.py](../../scripts/review_claude.py)。它读取 `tao review <CHG-ID> --format json` 的请求及显式 Git tree／文件集合，先检查输入请求与工作区、固定树一致，再在独立临时目录与客户端配置中调用既有 Claude 访问令牌。必须显式传 --reuse-claude-auth；复用上述认证适配，不携带刷新令牌、写认证文件或回退个人状态。默认禁用模型工具与自定义组件，限时 240 秒、CLI 预算 2 美元；不加载 tao-dev、不安装或注册插件。超时或异常时终止子进程组并清理令牌环境，日志脱敏；凭据或监测配置变化时不生成可导入记录，不猜测回滚个人文件。只有在已获准把固定 Git tree 和所列文件发送给模型时才执行；使用方项目不需要安装这项维护工具。调用形态为 `.venv/bin/python scripts/review_claude.py --reuse-claude-auth --request tmp/tao/review-request.json --tree <固定树> --files <项目相对文件列表>`。

脚本保留实际模型事件和运行摘要；只有调用完成、结论绑定一致且监测的个人配置未变时才生成待导入记录。监测变化、超时或未完成不能作为隔离验收通过；不要猜测原配置后回滚。真实客户端审查不进入普通 pytest，完整 verify 也不自动启动模型。

章节重定向回归通过 Python 开发依赖 mini-racer 内嵌的 V8 引擎，实际执行生成的解析页脚本，检查旧片段、编码片段和默认入口；另在 PATH 为空时验证不需要外部 Node.js。该依赖由 uv sync 安装，仅用于本项目测试，不进入插件核心或出版运行环境。浏览器脚本仍是 JavaScript；用 Python 模拟跳转结果不能代替实际脚本执行。

维护审查目录限制为 0700；两端模型事件和错误日志均以排他创建、0600 权限打开，防护从写入前开始，结束后的脱敏只作为补充。凭据前置条件失败时 clients.py 保存 blocked 摘要并返回 2。审查执行器在公布 review.json 前复用正式记录校验；拒绝的草稿、额外字段或缺少最终 result 的会话不能手工整理成有效审查。


## 自动原生测试

```sh
.venv/bin/python -m pytest tests/test_install_clients.py -k native -q
.venv/bin/python -m pytest tests/test_native_sessions.py -q
```

第一条只要求对应 CLI 已安装，不检查登录；第二条要求 CLI 已安装且只读登录检查通过。Cursor 探针使用官方项目 `.cursor/hooks.json` 入口和 `agent -p --force`，Kiro 探针使用 V3 TUI 的受限伪终端；Kiro 2.24.0 的 `--no-interactive` 路径实测未执行 standalone hook，不能用它替代 TUI 验收。两端都在临时客户端 home 和临时 Git 项目中安装同一受检 hook，以原生写入后的 `tmp/tao/cache/hook.json` 作为直接触发证据，不依赖模型自述。
