---
schema: tao.project.workflow/v0.1
id: DOC_20261106_RNS5FG152G60HSM6
title: 改进 workflow 状态的持久依据、跨目录恢复、多事项切换及正式收尾
locale: zh-Hans
status: draft
created: '2026-11-05'
change: CHG_20261105_YJ2MG6FEGJ4GMXA8
slug: workflow-recovery
record_revision: 8
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
    used: 5
    limit: 5
    decision: 已批准上限5轮，每次20分钟，无CLI费用阈值；扩大范围或追加轮次需另行授权。
    limits:
      timeout_seconds: 1200
      cost_limit_usd: null
    in_flight: null
    local_digest: cf92765ade042af9a66fd99bf25f1d9d19fd1fdd0b33723e8a8c8629946f44e1
closure: null
provenance: {}
last_operation_id: bf1ee088a5504913b7b59c7f2e2babb0
---

# 改进 workflow 状态的持久依据、跨目录恢复、多事项切换及正式收尾

<!-- tao:section overview -->
## 概述

active · implement
