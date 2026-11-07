---
schema: tao.project.workflow/v0.1
id: DOC_20261106_RNS5FG152G60HSM6
title: 改进 workflow 状态的持久依据、跨目录恢复、多事项切换及正式收尾
locale: zh-Hans
status: draft
created: '2026-11-05'
change: CHG_20261105_YJ2MG6FEGJ4GMXA8
slug: workflow-recovery
record_revision: 10
lifecycle: cancelled
phase: implement
plan_path: docs/plans/2026-11/20261105-workflow-recovery.md
artifacts:
  spec:
  - DOC_20261105_27RJ5NTQG9BNBJHX
  design:
  - DOC_20261105_0H6V7T4BYCRJW79H
  plan:
  - DOC_20261105_VN5X9G1X9DN0QJWR
approvals:
  spec:
    digest: 0977ff6f29596f41674c7348b5e07745e5c8289577723a9d5231798edfea8c4e
  design:
    digest: d3b119ce77f6c67056a382c0bf8fa3108d9e6651bd69ecfddcc236f164c46503
    algorithm: doc-v1
  plan:
    digest: 242f1d97dc1c712c63a4a3ce44f201098dc3706b0e07d7bd4a7441cf1cc9757c
    algorithm: doc-v1
baseline:
  branch: tao/workflow-recovery
  base_commit: 186ae92c674ef4e4c604556c01682f2dac51f2d8
  base_branch: main
review_control:
  docs:
    batch: f22c6d534dc74be29453470b8afbc10a
    phase: plan
    used: 2
    limit: 2
    decision: 已批准2轮文档审查；额度已用尽。
    limits: null
    in_flight: null
    local_digest: fe8cf3f478fcbc560c4f5c0e2b7d194b8ad26eccd7552e8e8af98b8aaf401cb5
  code:
    batch: 95e30131f4c74e048d31b2900dd1f5e6
    phase: implement
    used: 6
    limit: 6
    decision: 用户要求继续补齐本机验收并忽略Windows；在既有5轮基础上追加1轮独立实现审查，覆盖当前累计改动及调用方，单次20分钟，无CLI费用阈值，保留历史尝试。
    limits:
      timeout_seconds: 1200
      cost_limit_usd: null
    in_flight:
      id: 697a05bc48f1448caa7b2397c70a70fd
      round: 6
    local_digest: 5f2e8dfae3a8f75f86b615dfdb8908c56e9d7e4f59ecf9c80d4242b07d88cf5e
closure:
  evidence:
  - 已完成 workflow 状态恢复并验证本地状态文件可读。
  unfinished:
  - 维护回归、独立实现审查和交付缺口核对未完成。
  - diagnostics-locale、python-lint、python-tests 检查证据已过期。
  - 独立实现审查记录缺失。
  result: cancelled
  decision: 用户决定结束当前 workflow；未完成的维护回归、独立实现审查和交付缺口保留为未完成事项。
  recorded_at: '2026-11-07T11:44:39.371898+08:00'
provenance: {}
last_operation_id: 26942650f0174210bbb339d470b4f90e
---

# 改进 workflow 状态的持久依据、跨目录恢复、多事项切换及正式收尾

<!-- tao:section overview -->
## 概述

cancelled · implement
