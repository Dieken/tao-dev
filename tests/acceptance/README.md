# 实际客户端试验

这些试验会调用已配置的模型，须在已获准使用客户端与费用的环境中显式运行；普通 pytest 不启动它们。使用开发环境的 Python 调用 clients.py，workspace 选择不继承开发仓库指导文件的独立临时目录。脚本不设置认证、不安装客户端、不注册市场、不修改全局配置。

先按 README 准备开发环境并显式运行 runtime.py --download，取得与发布清单匹配的 wheel。clients.py 在试验 workspace 内显式准备独立核心环境；所有后续命令和 hook 共用这个 TAO_RUNTIME_DIR，既不要求客户端安装 uv，也不向用户数据目录准备环境。

```sh
python tests/acceptance/clients.py --client claude --case inside --workspace /tmp/tao-cli-experiment
python tests/acceptance/clients.py --client claude --case outside --workspace /tmp/tao-cli-experiment
python tests/acceptance/clients.py --client claude --case write --workspace /tmp/tao-cli-experiment
python tests/acceptance/clients.py --client claude --case review --workspace /tmp/tao-cli-experiment
python tests/acceptance/clients.py --client codex --case inside --workspace /tmp/tao-cli-experiment
python tests/acceptance/clients.py --client codex --case outside --workspace /tmp/tao-cli-experiment
python tests/acceptance/clients.py --client codex --case review --workspace /tmp/tao-cli-experiment
python tests/acceptance/clients.py --client codex --case recover --workspace /tmp/tao-cli-experiment
```

Claude 使用调用级 --plugin-dir。Codex 的项目内 .agents/skills/ 路径已做过实际试验，但 0.154.0 会自动把试验目录写入全局 projects 信任配置，调用级 trust override 也未阻止；脚本因此对这个已知版本返回 blocked，不再执行模型试验。先修复或确认客户端的隔离机制再解除此限制，不能改用全局注册绕过。原生 skill 结果也不能代替完整插件、命令或 hook 验收。未验证能够满足无全局安装约束的 Codex 插件加载路径前，不运行 marketplace add 或 plugin add。

inside 核对实际发现、引用定位、doctor/status；outside 不带加载参数、不使用工具，只查询初始可用能力。write 故意创建无效文档，禁止模型手工运行 hook，以便检查原生 PostToolUse 反馈。review 在相同小型导出样例上独立寻找违反“不得覆盖”的行为；Claude 用具名 reviewer 作为当前会话角色，不冒充子代理调度。两份初审输入互不包含对方结论。

原始事件、错误流、运行时间及全局配置文件散列比较存于本仓库 tmp/tao/client-acceptance/，不纳入 VCS。退出 0 只表示进程正常且监测文件未变；验收结论还必须检查初始化组件清单、实际工具调用、输出、模型标识和供应商依据。文件变化可能来自客户端自动维护或并行操作，必须调查，不能自动恢复。监测清单不构成对全部用户目录的完整审计。

模型返回的 token 使用量、CLI 按标价报告的费用和真实账单费用分别记录。未知项保留未知；不要以两个 CLI 的名称断言两个供应商。每例默认 180 秒，到期终止该试验进程组。试验材料仅包含自带合成样例和本插件运行资源，不传入维护仓库或其他项目资料。

recover 创建新的隔离项目，用实际 CLI 生成计划、执行失败基线并保存 handoff，然后启动没有旧会话历史的客户端。模型只能修改导出实现及已有计划；验收者另行检查 ID 保持、回归通过和修改范围。quality.py 用 Coverage.py 的 subprocess 支持执行维护测试并汇总报告，不调用模型；所有覆盖率数据位于 tmp/tao/coverage/。

scopes.py 专门验证 Claude 的 user、project、local 安装范围。每次传入新的 --workspace 和 --scope；脚本将 CLAUDE_CONFIG_DIR、XDG_CONFIG_HOME、GIT_CONFIG_GLOBAL 与运行目录限定在 workspace，再调用真实市场和插件安装命令。这里的 user 仅属于隔离客户端配置，不修改个人安装。加 --probe 读取项目内外初始化事件；scope_loading_verified 表示加载边界正确，model_execution_verified 单独表示模型执行成功。隔离配置没有认证时，加载成功不能代替命令或 hook 的模型行为验收。项目外应无项目级插件；user 范围则在隔离配置的两个目录中都可见。

运行环境测试验证 Python 隔离启动，覆盖率只能统计实际接受 Coverage.py 注入的进程。发布环境不安装开发用 coverage，也不为提高数字关闭 Python 隔离模式；报告中的未观测行不能解释为行为测试未执行。

独立代码审查的维护入口为 [review_claude.py](../../scripts/review_claude.py)。它读取 `tao review <CHG-ID> --format json` 的请求及显式 Git tree／文件集合，先检查输入请求与工作区、固定树一致，再在独立临时目录调用既有 Claude 认证。默认禁用模型工具与自定义组件，限时 240 秒、CLI 预算 2 美元；不加载 tao-dev、不安装或注册插件。只在请求出站已有授权时执行；这不是消费项目必须安装的工具。调用形态为 `.venv/bin/python scripts/review_claude.py --request tmp/tao/review-request.json --tree <固定树> --files <项目相对文件列表>`。

脚本保留实际模型事件和运行摘要；只有调用完成、结论绑定一致且监测的个人配置未变时才生成待导入记录。监测变化、超时或未完成不能作为隔离验收通过；不要猜测原配置后回滚。真实客户端审查不进入普通 pytest，完整 verify 也不自动启动模型。
