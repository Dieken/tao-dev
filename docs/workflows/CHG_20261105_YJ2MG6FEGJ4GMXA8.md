---
schema: tao.project.workflow/v0.1
id: DOC_20261106_RNS5FG152G60HSM6
title: 改进 workflow 状态的持久依据、跨目录恢复、多事项切换及正式收尾
locale: zh-Hans
status: draft
created: '2026-11-05'
change: CHG_20261105_YJ2MG6FEGJ4GMXA8
slug: workflow-recovery
record_revision: 9
lifecycle: active
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
    local_digest: d353857458c9f506eb09426ac5100dd700a6d5e619ae2bfac8265c71ea5e42a6
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
    local_digest: 6d146efc94fc7768d78daaeb811101182258ced15b9be8f60c1575a658e6bf75
closure: null
provenance: {}
last_operation_id: 35f74e8d24f44351876f16c0e8340454
---

# 改进 workflow 状态的持久依据、跨目录恢复、多事项切换及正式收尾

<!-- tao:section overview -->
## 概述

active · implement
