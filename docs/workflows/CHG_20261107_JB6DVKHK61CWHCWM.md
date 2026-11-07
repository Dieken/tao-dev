---
schema: tao.project.workflow/v0.1
id: DOC_20261107_GKD84E61X845ZC0E
title: 修正 native 版本发现并支持批量升级
locale: zh-Hans
status: draft
created: '2026-11-07'
change: CHG_20261107_JB6DVKHK61CWHCWM
slug: native-version-and-batch-upgrade
record_revision: 10
lifecycle: active
phase: implement
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
review_control:
  code:
    batch: 402b8ee2fdb94186989266b743011923
    phase: implement
    used: 2
    limit: 2
    decision: 用户通过 /tao-dev review 发起实现审查；审查当前累计代码、测试和调用方，重点检查 SemVer discovery、recorded/native
      输出和 --all 批量回滚。
    limits:
      timeout_seconds: 1200
      cost_limit_usd: null
    in_flight: null
    local_digest: f3521b4cdbaa597ffb621bb037e566090f3387564cd66f4c4ce5babebb1c8f2e
closure: null
provenance: {}
last_operation_id: 96c88bba50e44053bd26f7e54ef40dc0
---

# 修正 native 版本发现并支持批量升级

<!-- tao:section overview -->
## 概述

active · implement
