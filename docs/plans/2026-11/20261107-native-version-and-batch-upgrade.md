---
schema: tao.project.plan/v0.1
id: "DOC_20261107_9H3W3CWYP7KAPE00"
title: "Native 版本发现与批量升级实施计划"
locale: "zh-Hans"
status: draft
created: "2026-11-07"
spec_docs: ["DOC_20261107_F6HNNP5XE5133SM9"]
design_docs: ["DOC_20261107_AXTBBST6KW3DDGHQ"]
change: "CHG_20261107_JB6DVKHK61CWHCWM"
---

# Native 版本发现与批量升级实施计划

<!-- tao:section scope -->
## 范围

实现语义版本 native discovery、明确的 recorded/native list 版本字段、默认单项不变的 `upgrade --all` 批量协调、逐项结果与文档同步。批量范围为该 client 的全部 tao 受管记录，包括 user 和 project scope；native-only 安装不自动升级。Codex/Cursor 原生 cache 生命周期和客户端 CLI 不在本次修改范围。

<!-- tao:section references -->
## 参考

- 规格：[Native 版本发现与批量升级](../../product/native-version-and-batch-upgrade.md)
- 设计：[Native 版本发现与批量升级设计](../../engineering/native-version-and-batch-upgrade.md)
- 现有安装实现：`plugins/tao-dev/skills/tao-dev/scripts/installation.py`、`install_clients.py`
- 现有回滚与发现测试：`tests/test_installation.py`、`tests/test_install_clients.py`

<!-- tao:section design -->
## 设计

复用单项 `install()` 事务和现有 native discovery 结构。新增纯标准库 SemVer 排序 helper；Codex project 与 Cursor project 使用该 helper，其他 client 保持原生路径来源。list row 只保存 `recorded_version` 与 `native_version`，text/JSON 使用同一模型。`--all` 与 `--id` 互斥，批量按 installation id 稳定排序，逐项执行并继续处理，失败项独立回滚，部分失败返回退出码 2。

<!-- tao:section tasks -->
## 任务

- [x] `TASK_20261107_SQNN0MVFRZB8GHW8` 实现并测试 SemVer 排序与 Codex/Cursor native discovery 版本选择
  - relates: ["REQ_20261107_A307JYYYWTYPDZMW"]
  - depends_on: []
  - verify: 用隔离 cache fixture 反置 mtime，运行 Codex/Cursor discovery 测试，确认最高有效 SemVer 被选择且无效版本不越过有效版本。
  - evidence: [验证记录](#DOC_20261107_9H3W3CWYP7KAPE00--verification)
- [x] `TASK_20261107_3GXYTFYFA8HGS891` 分离 list 的 recorded/native 版本字段并更新 text/JSON 输出
  - relates: ["REQ_20261107_R3MBRP0VSP65JMKX"]
  - depends_on: ["TASK_20261107_SQNN0MVFRZB8GHW8"]
  - verify: 运行 list 输出测试，确认受管版本不同时两个字段均可见，native-only 行 recorded 字段为空，旧单一 `version` 字段不再输出。
  - evidence: [验证记录](#DOC_20261107_9H3W3CWYP7KAPE00--verification)
- [x] `TASK_20261107_BZM2XJQAG5AG1CEF` 增加 `upgrade --all` 参数、选择器和逐项批量结果
  - relates: ["REQ_20261107_AGB8YQ12FYY6HN9F", "REQ_20261107_J6SWVFTRGDW0T956"]
  - depends_on: []
  - verify: 运行 parser、稳定排序、user/project 混合、id/all 互斥、部分失败继续和退出状态测试。
  - evidence: [验证记录](#DOC_20261107_9H3W3CWYP7KAPE00--verification)
- [x] `TASK_20261107_Z5FBJ763YWYNXYK7` 同步安装设计、CLI 契约和 README 的局限与新接口
  - relates: ["REQ_20261107_A307JYYYWTYPDZMW", "REQ_20261107_R3MBRP0VSP65JMKX", "REQ_20261107_AGB8YQ12FYY6HN9F"]
  - depends_on: ["TASK_20261107_SQNN0MVFRZB8GHW8", "TASK_20261107_3GXYTFYFA8HGS891", "TASK_20261107_BZM2XJQAG5AG1CEF"]
  - verify: 执行受管理文档验证，确认 Codex/Cursor cache 局限、字段语义、`--all` 范围和失败行为与实现一致。
  - evidence: [验证记录](#DOC_20261107_9H3W3CWYP7KAPE00--verification)
- [x] `TASK_20261107_GQQ3ZZ91QRAGWN6M` 执行回归检查并核对需求验收
  - relates: ["REQ_20261107_A307JYYYWTYPDZMW", "REQ_20261107_R3MBRP0VSP65JMKX", "REQ_20261107_AGB8YQ12FYY6HN9F", "REQ_20261107_J6SWVFTRGDW0T956"]
  - depends_on: ["TASK_20261107_Z5FBJ763YWYNXYK7"]
  - verify: 运行受影响 pytest、项目配置的代码检查和 tao docs 验证；逐项记录命令、输入与观察结果，不以静态检查替代用户可观察验收。
  - evidence: [验证记录](#DOC_20261107_9H3W3CWYP7KAPE00--verification)
<!-- tao:section verification -->
## 验证

先运行 `tests/test_install_clients.py` 和 `tests/test_installation.py` 的受影响测试，再运行完整项目测试和配置的 lint。使用 `.venv/bin/python`，不调用裸 `uv`。执行 `tao verify --only docs --project <worktree>` 检查受管理文档。必要时运行隔离 native discovery fixture，不访问个人客户端配置。最终按 REQ/UC 核对 list text/JSON、默认单项 upgrade、`--all` 批量成功/失败和语义版本选择。

<!-- tao:results -->
- 受影响测试：`TAO_TEST_WHEELHOUSE=.../tmp/tao/wheels .venv/bin/python -m pytest -q tests/test_install_clients.py tests/test_installation.py`，108 passed、2 skipped；跳过项为 Windows-only process-tree tests。
- 完整回归：`.venv/bin/python -m pytest -q`，820 passed、6 skipped、2 warnings；4 个模型路线在 preflight 阶段跳过，2 个 Windows-only 测试跳过。
- 配置代码检查：`tao verify --only code --simplified --format json`，diagnostics-locale、python-tests、python-lint 全部 passed；python-tests 覆盖率 78.4006%。
- 文档检查：`tao verify --only docs --simplified --format json`，文档结构、关系和导航 valid，无 diagnostics。
<!-- /tao:results -->
<!-- tao:section questions -->
## 未决问题

无。用户已同意推荐的批量范围、逐项继续和部分失败策略，并明确不保留旧 `version` 字段兼容。
