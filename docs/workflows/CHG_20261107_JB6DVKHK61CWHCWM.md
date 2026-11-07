---
schema: tao.project.workflow/v0.1
id: DOC_20261107_GKD84E61X845ZC0E
title: 修正 native 版本发现并支持批量升级
locale: zh-Hans
status: draft
created: '2026-11-07'
change: CHG_20261107_JB6DVKHK61CWHCWM
slug: native-version-and-batch-upgrade
record_revision: 15
lifecycle: completed
phase: complete
plan_path: docs/plans/2026-11/20261107-native-version-and-batch-upgrade.md
artifacts:
  spec:
  - DOC_20261107_F6HNNP5XE5133SM9
  design:
  - DOC_20261107_AXTBBST6KW3DDGHQ
  plan:
  - DOC_20261107_9H3W3CWYP7KAPE00
approvals:
  spec:
    digest: c5317e10b7ada951226080282ee98240c9bb3384769e1e0c4725d870a990dea9
    algorithm: doc-v1
  design:
    digest: 199e89115c3b9ecefe2c15a2ab5a10e418811bdc0ed21253595ec55e81d3058b
    algorithm: doc-v1
  plan:
    digest: bc6bf0d3c37e947483f76be018904ff8abf0f09aae1472d498791655a18d3d07
    algorithm: doc-v1
baseline:
  branch: tao/native-version-and-batch-upgrade
  base_commit: c2b0baf7dad8c8fdd799baacf783ae1421493892
  base_branch: main
review_control: {}
closure:
  evidence:
  - 完整 tao verify CHG_20261107_JB6DVKHK61CWHCWM 返回 checks-satisfied，需求覆盖 4/4，任务全部完成。
  - 配置代码检查通过：diagnostics-locale、python-tests、python-lint；python-tests 覆盖率 78.6039%。
  - 受管理文档验证通过。
  - 最终独立实现审查 attestation 已通过 tao review 导入并满足 independent-implementation-review。
  - 实现、审查记录和 workflow 状态均已提交到 tao/native-version-and-batch-upgrade。
  unfinished: []
  result: completed
  decision: 实现、完整交付验证和最终独立实现审查均已完成；审查保留的 malformed cache manifest 为非阻断后续维护建议。
  recorded_at: '2026-11-07T14:55:51.861046+08:00'
provenance: {}
last_operation_id: 6ee919a3384b40a9b687f9cc3a08ff9e
---

# 修正 native 版本发现并支持批量升级

<!-- tao:section overview -->
## 概述

completed · complete
