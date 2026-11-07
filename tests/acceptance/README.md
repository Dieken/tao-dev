# 项目技能验收

文件复制与客户端发现分别验收，不把文件部署成功当作模型行为验证通过。以下命令从仓库根目录执行，所有试验项目与客户端状态均位于自动清理的临时目录。

## 项目完整复制

```sh
python3 tests/acceptance/project_skills.py --client claude
python3 tests/acceptance/project_skills.py --client codex
python3 tests/acceptance/project_skills.py --client cursor
python3 tests/acceptance/project_skills.py --client kiro
```

脚本仅依赖 Python 标准库，将 `skills/tao-dev/` 完整复制到新项目目录并比较内容（排除字节码缓存），随后移除副本。检查源技能、隔离用户目录和未选中的项目，确认用户文档及相邻的用户技能均保留。脚本不安装客户端，不读取或复制认证，不修改个人配置。Claude 使用 `.claude/skills/tao-dev`，Codex / Cursor 使用 `.agents/skills/tao-dev`，Kiro 使用 `.kiro/skills/tao-dev`。输出的 `copy` 与 `native_discovery` 分别记录文件复制与客户端原生发现结果。

```sh
uv run --no-config --locked --extra publication pytest -q tests/test_acceptance_project_skills.py tests/test_native_clients.py
```

回归测试覆盖副本缺失、内容损坏、额外文件及隔离环境被修改的检测。复制后辅助命令能否独立运行，由独立运行测试（standalone）覆盖。

## 客户端原生发现（不调用模型）

```sh
python3 tests/acceptance/project_skills.py --client codex --native
```

要求 `PATH` 上已有支持 `app-server` 和 `skills/list` 的 Codex 命令行工具，无需登录。检查器只发送 `initialize`、`initialized` 和 `skills/list`，不创建会话或向模型发送请求。`HOME`、`CODEX_HOME`、XDG 目录及临时目录均隔离，子进程环境不继承认证或个人客户端设置。复制后，所选项目必须恰好发现一个启用的 `tao-dev`，且路径匹配副本的 `SKILL.md`；相邻项目不得发现它，移除后也不得发现它。

每次发现请求总限时 20 秒，退出时终止并回收检查进程。独立命令要求已有 Codex 命令行工具。pytest 默认跳过真实发现；仅显式设置 `TAO_NATIVE_ACCEPTANCE=1` 时运行，缺少命令行工具时仍报告跳过（skip）。协议错误、扫描错误或不完整结果不算通过。协议单元测试的模拟服务只验证检查器，不能替代真实客户端发现测试。

当前没有 Claude、Cursor、Kiro 的原生发现验收，也没有任何计费模型测试。文件复制通过不能证明这些客户端已加载技能；Codex 原生发现通过也不能证明模型会遵循技能指令、完成任务或正确审查。

## Python 覆盖率

```sh
uv run --no-config --locked --extra publication python tests/acceptance/quality.py
```

`quality.py` 只运行 pytest 与 coverage，输出到 `tmp/tao/coverage/`；不准备托管运行环境、不下载客户端、不调用模型。默认测试不启动原生客户端；显式发现验收结果取决于本机实际版本，本说明不宣称已经执行通过。
