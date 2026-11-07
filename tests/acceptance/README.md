# 项目 skill 验收

安装与发现分开验收，不把文件部署成功说成模型行为通过。以下命令从仓库根目录执行，所有试验项目与客户端状态均位于自动清理的临时目录。

## 项目安装生命周期

```sh
python3 tests/acceptance/project_skills.py --client claude
python3 tests/acceptance/project_skills.py --client codex
python3 tests/acceptance/project_skills.py --client cursor
python3 tests/acceptance/project_skills.py --client kiro
```

脚本仅依赖 Python 标准库，直接调用 `skills/tao-dev/scripts/tao.py`。检查安装、重复升级、查看、卸载；比较源 skill、安装文件、隔离用户目录和未选中的项目，确认用户文档及相邻用户 skill 保留。不安装客户端，不读取或复制认证，不修改个人配置。实际路径分别为 `.claude/skills/tao-dev`、`.agents/skills/tao-dev`、`.cursor/skills/tao-dev`、`.kiro/skills/tao-dev`。

```sh
uv run --no-config --locked --extra publication pytest -q tests/test_acceptance_project_skills.py tests/test_native_clients.py
```

回归还检查拒绝覆盖非归属目录，以及拒绝升级／卸载已被用户修改的托管文件。更细的安装回滚与路径保护由安装器单元测试覆盖。每个安装 CLI 子进程限时 30 秒。

## 真实原生发现（不调用模型）

```sh
python3 tests/acceptance/project_skills.py --client codex --native
```

要求 PATH 上已有支持 `app-server` 和 `skills/list` 的 Codex CLI；无需登录。检查器只发送 `initialize`、`initialized` 和 `skills/list`，不创建会话或发送模型轮次。HOME、CODEX_HOME、XDG 及临时目录均隔离，子进程环境不继承认证或个人客户端设置。安装后必须在所选项目发现恰好一个启用的 `tao-dev`，且路径匹配安装的 SKILL.md；相邻项目不得发现它，卸载后也不得发现它。

每次发现请求总限时 20 秒，退出时终止并回收检查进程。独立命令要求已有 Codex CLI。pytest 默认跳过真实发现；仅显式设置 `TAO_NATIVE_ACCEPTANCE=1` 时运行，CLI 缺失仍报告 skip。协议错误、扫描错误或不完整结果不会算作通过。协议单元测试的模拟服务只验证检查器，并不替代真实客户端发现测试。

当前没有 Claude、Cursor、Kiro 的原生发现验收，也没有任何计费模型测试。文件生命周期通过不能证明这些客户端已加载 skill；Codex 原生发现通过也不能证明模型会遵循 skill、完成任务或正确审查。

## Python 覆盖率

```sh
uv run --no-config --locked --extra publication python tests/acceptance/quality.py
```

`quality.py` 只运行 pytest 与 coverage，输出到 `tmp/tao/coverage/`；不准备托管运行时、不下载客户端、不调用模型。默认测试不启动原生客户端；显式发现验收结果取决于本机实际版本，本说明不宣称已经执行通过。
