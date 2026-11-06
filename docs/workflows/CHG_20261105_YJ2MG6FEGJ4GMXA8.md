---
schema: tao.project.workflow/v0.1
id: DOC_20261106_RNS5FG152G60HSM6
title: 改进 workflow 状态的持久依据、跨目录恢复、多事项切换及正式收尾
locale: zh-Hans
status: draft
created: '2026-11-05'
change: CHG_20261105_YJ2MG6FEGJ4GMXA8
slug: workflow-recovery
summary: 改进 workflow 状态的持久依据、跨目录恢复、多事项切换及正式收尾
record_revision: 7
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
    decision: 用户选择 3，批准规格并进入设计
  design:
    digest: d003bb8ac7e1a43ff4a56f5a7a4186aeda72740794a16d7c3e1d47b91bc1c244
    decision: 用户批准修订设计与计划并开始实现
  plan:
    digest: 242f1d97dc1c712c63a4a3ce44f201098dc3706b0e07d7bd4a7441cf1cc9757c
    algorithm: doc-v1
    decision: 实施期自评：与6348e1b版本逐行比较，计划契约仅待确认事项一行改为引用当前验证结果，需求、方案、任务范围、依赖和verify均未变化；既有正式文档审查历史保留，本次运行状态细化不新增正式文档审查，既有完整实现复核历史保留；新预算差异复核失败，当前必需回执为stale，不声称通过。
baseline:
  branch: tao/workflow-recovery
  base_commit: 186ae92c674ef4e4c604556c01682f2dac51f2d8
  base_branch: main
review_batches:
  docs:
    id: f22c6d534dc74be29453470b8afbc10a
    phase: plan
    decision: 用户选择正式文档审查；范围为本事项 spec/design/plan 累计文档改动，一名独立上下文审查者，默认最多两轮，保存报告
    started_at: '2026-11-05T15:10:31.020935+00:00'
    max_rounds: 2
    runs:
    - id: 9fd6096b9f6845998a93c1a54fc354b8
      round: 1
      started_at: '2026-11-05T15:10:31.020935+00:00'
      outcome: changes-requested
      mode: serial
      reviewers: 1
      decision: 用户选择正式文档审查；范围为本事项 spec/design/plan 累计文档改动，一名独立上下文审查者，默认最多两轮，保存报告
      request:
        schema: tao.review-scope/v0.1
        change: CHG_20261105_YJ2MG6FEGJ4GMXA8
        scope: feature
        kind: docs
        base_commit: 186ae92c674ef4e4c604556c01682f2dac51f2d8
        target_commit: 2cd1cdeb2e31723d7e3d16a29c6bd79437c38a5a
        input_digest: 092f34ee82bf1e3e069fe150bc348e715585acbd5d4bd0a9254456834304cbff
        selection_digest: 3f7f8289cbfece13c995f4cca10a106c39f1be7f9a2747e06764f2274fa717bf
      inputs: current
      reports:
      - path: docs/plans/2026-11/20261105-workflow-recovery/reviews/20261105-recovery-contract/01-contract-reviewer.md
        digest: 7ccc4089c463255c8b2e0ae6f8cec22e0cc85aa983dc545788701459cdfed6e7
        validated: true
      ended_at: '2026-11-05T15:15:54.049688+00:00'
      summary_digest: 482130c42faea02142ceb44eb44dc47c005dded381d39fe269c803e8eac43067
      recovered_context: true
      compacted: true
    - id: 64241fcf4d1c4419b651acefd63e6686
      round: 2
      started_at: '2026-11-05T15:26:36.272729+00:00'
      outcome: passed
      mode: serial
      reviewers: 1
      decision: 用户同意修订 A/B 后定向复核；沿用本批剩余第二轮，不扩大调用上限
      request:
        schema: tao.review-scope/v0.1
        change: CHG_20261105_YJ2MG6FEGJ4GMXA8
        scope: feature
        kind: docs
        base_commit: 186ae92c674ef4e4c604556c01682f2dac51f2d8
        target_commit: 79a249381f0c1b0da9b0319099bd8dd769c5b6c8
        input_digest: bd22cc05a386af5ae2ba15cc8d6b46891eb539069d2d1b835677a60d0fae73aa
        selection_digest: f36f9c9b961a12085ac477ce9936887a89ff13ba4f492a0d9b4d794dec5a70d2
      inputs: current
      reports:
      - path: docs/plans/2026-11/20261105-workflow-recovery/reviews/20261105-recovery-contract/02-followup-reviewer.md
        digest: eec109c4d2144edf74c07b0c68ad9b135f23b81cffb18b2700242a318a0088eb
        validated: true
      ended_at: '2026-11-05T15:28:39.374972+00:00'
      summary_digest: b6cdc8e4b91e3f01aab613a0ce35889b58e4aa48387135e265bd4c6b621455fa
      recovered_context: true
      compacted: true
    round_decisions: []
  code:
    id: 95e30131f4c74e048d31b2900dd1f5e6
    phase: implement
    decision: 用户批准recover/plan预算2至4美元的小范围变更；按默认两轮保存本次定向复核，第一轮追记登记失败后误启动并中止的调用，不作为有效审查；第二轮只审本次差异，实际调用上限1美元300秒。
    started_at: '2026-11-06T03:01:42.403373+00:00'
    max_rounds: 5
    runs:
    - id: 4d684f2299294b688c39afb4ee0c1500
      round: 1
      started_at: '2026-11-06T03:01:42.403373+00:00'
      outcome: failed
      mode: serial
      reviewers: 1
      decision: 用户批准recover/plan预算2至4美元的小范围变更；按默认两轮保存本次定向复核，第一轮追记登记失败后误启动并中止的调用，不作为有效审查；第二轮只审本次差异，实际调用上限1美元300秒。
      request:
        schema: tao.review-scope/v0.1
        change: CHG_20261105_YJ2MG6FEGJ4GMXA8
        scope: feature
        kind: code
        base_commit: 186ae92c674ef4e4c604556c01682f2dac51f2d8
        target_commit: 42e94faf61eed082975a3f8a6090cb739161f84a
        input_digest: cec3db56023fa375f5e5671b5293750ed116c299d84180bb443fb4835dd72c96
        selection_digest: 5ab034089afeae461ad7bd8cb72c19a057200a43f016a7aa6ef2a7b71aeae1f8
      inputs: current
      reports: []
      ended_at: '2026-11-06T03:01:47.919496+00:00'
      summary_digest: ac3dc30b88ca8f92e01edcde4b6c1c8abe5a9b49ebd14cbf4aba1bad0f847848
      recovered_context: true
      compacted: true
    - id: 3970eb30b62547c38633e2fe21411737
      round: 2
      started_at: '2026-11-06T03:01:49.345351+00:00'
      outcome: failed
      mode: serial
      reviewers: 1
      decision: 登记成功后执行剩余一轮当前固定输入的预算差异复核；同批不重置轮次，不扩大费用与超时。
      request:
        schema: tao.review-scope/v0.1
        change: CHG_20261105_YJ2MG6FEGJ4GMXA8
        scope: feature
        kind: code
        base_commit: 186ae92c674ef4e4c604556c01682f2dac51f2d8
        target_commit: 42e94faf61eed082975a3f8a6090cb739161f84a
        input_digest: cec3db56023fa375f5e5671b5293750ed116c299d84180bb443fb4835dd72c96
        selection_digest: 0d36f7e2eaef79d0c2e5545c62ad94ee40c2c6fa80d8fb8879efe17004140f16
      inputs: current
      reports: []
      ended_at: '2026-11-06T03:07:33.391798+00:00'
      summary_digest: 4d87ad6e02973dfca775c4364df8c46d2b73d47700d1556c46a3b563982d5dc4
      recovered_context: true
      compacted: true
    - id: b01d88858ad144aa98808fcc6dc82a5f
      round: 3
      started_at: '2026-11-06T03:53:34.706261+00:00'
      outcome: failed
      mode: serial
      reviewers: 1
      decision: 用户继续解决授权内发现了新的取消缺陷及其回归：外层终止后模型组继续运行、双轮重复计时。当前范围扩至这些修复、低强度小型探针和预算差异；按新证据显式增加一轮至3，不重置前两次失败，不自动新建批次。只一次工具禁用的独立CLI审查，预算阈值仍1美元、超时仍300秒。
      request:
        schema: tao.review-scope/v0.1
        change: CHG_20261105_YJ2MG6FEGJ4GMXA8
        scope: feature
        kind: code
        base_commit: 6348e1b75ead1139df51638a2b5eb695d376bf4d
        target_commit: d8ec53f0e38e689f0e900ddecb9fec29bde83a2d
        input_digest: e0990b046cf260339cecb34888af0a0821c33e79c16c3549bbb01ba26f02e883
        selection_digest: 510740550fd4a4c7db93945f7af9cee05424c77247158d2f6b19fd7fd7f89630
      inputs: current
      reports: []
      ended_at: '2026-11-06T03:58:38.634611+00:00'
      summary_digest: c9ff4ad28a175706fb8674eca711182bcfd64b9c06ef029f3fb825da67186448
      recovered_context: true
      compacted: true
    - id: 7046c8c8091e47748cfcfa4c270de59a
      round: 4
      started_at: '2026-11-06T09:08:07.721764+00:00'
      outcome: passed
      mode: serial
      reviewers: 1
      decision: 用户要求继续完成任务，后明确先完成本机可做部分，恢复先前保留的额外独立复核：不设CLI费用阈值，超时20分钟。保留前三次失败，原批次上限显式增至4，不重置历史；范围含当前预算入口、取消清理、必需绑定与正式记录修复及其调用方。只读、禁用工具与委派；Windows保持未覆盖。
      request:
        schema: tao.review-scope/v0.1
        change: CHG_20261105_YJ2MG6FEGJ4GMXA8
        scope: feature
        kind: code
        base_commit: 6348e1b75ead1139df51638a2b5eb695d376bf4d
        target_commit: 4b87c3005641951ab96124ea962bf21dc8bdfa1a
        input_digest: a7bdb83aa8038d982a7e23bd39cc89323bf9d6ec95d71e0b591bf61717198e23
        selection_digest: b047efb169b392db9933299570ae82c59ddf3502396235edc6f27f80b28d8e89
      inputs: current
      reports:
      - path: tmp/tao/finish-local-review-report.md
        digest: ff996e1e796f6d224fd5fb0c918c358623eb0d6968ff51300be7a7db7ae8eda9
        validated: false
      ended_at: '2026-11-06T09:11:11.282864+00:00'
      summary_digest: 63e2a87a1add89dcb66d0cdb5f5dd75666a69c47c47e777f24d7a27dc77a7499
      recovered_context: true
      compacted: true
    - id: 73ae52a9b84746f9a00683206fe8411b
      round: 5
      started_at: '2026-11-06T09:26:01.186291+00:00'
      outcome: passed
      mode: serial
      reviewers: 1
      decision: 按用户完成本机范围的授权，对第4次实际独立报告的REC-01修复做一次定向复核。真实新发现及已执行修复构成新增证据，原批次上限显式从4增至5，仅追加这次跟进，不重置任何失败或通过。继续使用已批准的无CLI费用阈值、1200秒超时，禁用工具与委派；Windows保持未覆盖。
      request:
        schema: tao.review-scope/v0.1
        change: CHG_20261105_YJ2MG6FEGJ4GMXA8
        scope: feature
        kind: code
        base_commit: 6348e1b75ead1139df51638a2b5eb695d376bf4d
        target_commit: fc5f4287eba12c09ecbb50d0e4c7b5cf70f2111b
        input_digest: 35943e54cd204d2f47dd8b79027019a96f27e6a45dd668873bb540fd5b56876f
        selection_digest: 7f097edc54115f41151e8ed4cc09713b868aab12950e92387d08d8c00088ec39
      inputs: current
      reports:
      - path: tmp/tao/finish-followup-review-report.md
        digest: 7fbbd94df8c05f9a352bb4bc6df01f6635ca61e9d34ff6ec4445f54fd09e35d3
        validated: false
      ended_at: '2026-11-06T09:26:56.039859+00:00'
      summary_digest: 58cf0b06258df245b9f5fae96af5b009c400c9b702bac0f82ec8fbe579fdc046
      recovered_context: true
      compacted: true
    round_decisions:
    - before: 2
      after: 3
      decision: 用户继续解决授权内发现了新的取消缺陷及其回归：外层终止后模型组继续运行、双轮重复计时。当前范围扩至这些修复、低强度小型探针和预算差异；按新证据显式增加一轮至3，不重置前两次失败，不自动新建批次。只一次工具禁用的独立CLI审查，预算阈值仍1美元、超时仍300秒。
    - before: 3
      after: 4
      decision: 用户要求继续完成任务，后明确先完成本机可做部分，恢复先前保留的额外独立复核：不设CLI费用阈值，超时20分钟。保留前三次失败，原批次上限显式增至4，不重置历史；范围含当前预算入口、取消清理、必需绑定与正式记录修复及其调用方。只读、禁用工具与委派；Windows保持未覆盖。
    - before: 4
      after: 5
      decision: 按用户完成本机范围的授权，对第4次实际独立报告的REC-01修复做一次定向复核。真实新发现及已执行修复构成新增证据，原批次上限显式从4增至5，仅追加这次跟进，不重置任何失败或通过。继续使用已批准的无CLI费用阈值、1200秒超时，禁用工具与委派；Windows保持未覆盖。
    history:
    - id: 43c92391fdf44cfd9459f66c3da87b7a
      phase: implement
      decision: 按已批准实施计划进行独立实现审查；一名独立上下文审查者，最多两轮，范围为事项累计实现与上下游文档测试
      started_at: '2026-11-05T15:56:24.791602+00:00'
      max_rounds: 3
      runs:
      - id: ad9a3fa16fd74a229fb6847f5a272a25
        round: 1
        started_at: '2026-11-05T15:56:24.791602+00:00'
        outcome: changes-requested
        mode: serial
        reviewers: 1
        decision: 按已批准实施计划进行独立实现审查；一名独立上下文审查者，最多两轮，范围为事项累计实现与上下游文档测试
        request:
          schema: tao.review-scope/v0.1
          change: CHG_20261105_YJ2MG6FEGJ4GMXA8
          scope: feature
          kind: code
          base_commit: 186ae92c674ef4e4c604556c01682f2dac51f2d8
          target_commit: 381130f1447c0b66d8d2f4046ab84ef015139ca3
          input_digest: 7efd25ccfa38c223591ed3839cff4ed92c9a4590cd45bee942211927c7553183
          selection_digest: 37d92b434c9e0b827a483fba007029f41394abc0234848ee534f62a47ca7419b
        inputs: current
        reports:
        - path: docs/plans/2026-11/20261105-workflow-recovery/reviews/20261105-implementation/01-implementation-reviewer.md
          digest: a389b402a0e2f8d7a118c1b52cff05aebde143d4dcbe4d14800fb93db3f530b1
          validated: true
        ended_at: '2026-11-05T16:04:59.961028+00:00'
        summary_digest: c45e71b5655785c2059734c8f494431614a4119ddd649790dd9c5fe7c3255dce
        recovered_context: true
        compacted: true
      - id: c4c3fd1e2ae4495bb6dbd7bc4ebc3fad
        round: 2
        started_at: '2026-11-05T16:13:15.468533+00:00'
        outcome: changes-requested
        mode: serial
        reviewers: 1
        decision: 按已有实现授权修复 I1-I4 后定向复核；本批第二轮，不扩大轮次
        request:
          schema: tao.review-scope/v0.1
          change: CHG_20261105_YJ2MG6FEGJ4GMXA8
          scope: feature
          kind: code
          base_commit: 186ae92c674ef4e4c604556c01682f2dac51f2d8
          target_commit: 381130f1447c0b66d8d2f4046ab84ef015139ca3
          input_digest: 1ae14a8f7e36b942469bf349e52a657e2aa5a15e124f9e7d49c9ea79cf546120
          selection_digest: aa46e1eab12bf10c085438c3e05e0955dfa383f86bd1f8cf886929292acb9236
        inputs: current
        reports:
        - path: docs/plans/2026-11/20261105-workflow-recovery/reviews/20261105-implementation/02-followup-reviewer.md
          digest: 8661533950e4fe2a8cada00a08b89054a9db4da95e52dbe86f1ceb79d83f9379
          validated: true
        ended_at: '2026-11-05T16:19:02.137127+00:00'
        summary_digest: bbca4efc0d16993753c3a772bca6be3b6c38d6c3bf4148570c0230f5174ea26e
        recovered_context: true
        compacted: true
      - id: 55e433f56e284bbb91bcc8f1b5734bb7
        round: 3
        started_at: '2026-11-05T17:20:04.261467+00:00'
        outcome: passed
        mode: serial
        reviewers: 1
        decision: 用户批准额外一轮定向复核最终 I4 校验修复，不启动原生客户端实验
        request:
          schema: tao.review-scope/v0.1
          change: CHG_20261105_YJ2MG6FEGJ4GMXA8
          scope: feature
          kind: code
          base_commit: 186ae92c674ef4e4c604556c01682f2dac51f2d8
          target_commit: cdcabdcc6747929c626d8b820b6504611ad6f3f7
          input_digest: 7d0ed12a63cb45fb1b72b2eab618a5a0539e42dda0ec460f1b40681b7b16d3da
          selection_digest: 8b8521e04b579b116a6997e20d7d6b85c88e39691d70a449a29b5c0e1b5b62af
        inputs: current
        reports:
        - path: docs/plans/2026-11/20261105-workflow-recovery/reviews/20261105-implementation/04-validation-reviewer.md
          digest: 829ba547373e3688358f29c518a1da5f6ed9c45251a7be7d8b5f5e8782154b6c
          validated: true
        ended_at: '2026-11-05T17:23:43.785846+00:00'
        summary_digest: d41541e276936d34798b283bc59be4ceaeb1e09b99a8b244657b76640f07c106
        recovered_context: true
        compacted: true
      round_decisions:
      - before: 2
        after: 3
        decision: 用户批准额外一轮定向复核最终 I4 校验修复，不启动原生客户端实验
    - id: 961cc46f597c410ea057406269c841b5
      phase: implement
      decision: 用户要求继续解决剩余验收和必需机器回执；只读独立实现审查，串行一人，本批最多一轮，调用上限2美元及600秒
      started_at: '2026-11-05T18:38:11.591709+00:00'
      max_rounds: 2
      runs:
      - id: d8cf1fab67144fb797123a520c8110e4
        round: 1
        started_at: '2026-11-05T18:38:11.591709+00:00'
        outcome: changes-requested
        mode: serial
        reviewers: 1
        decision: 用户要求继续解决剩余验收和必需机器回执；只读独立实现审查，串行一人，本批最多一轮，调用上限2美元及600秒
        request:
          schema: tao.review-scope/v0.1
          change: CHG_20261105_YJ2MG6FEGJ4GMXA8
          scope: feature
          kind: code
          base_commit: 186ae92c674ef4e4c604556c01682f2dac51f2d8
          target_commit: d7dc517d3ff03ea4e0946bd01a542ea5a372e58f
          input_digest: a9b076740dcc0dfe66e1fbec87d645e1c5bd2760ad28b4f7ea37624aaf815983
          selection_digest: f6180dfbe19e7dd4c2088ed182295c6bb9c43d4a6e20d15f21bfb0338822dcd2
        inputs: current
        reports:
        - path: tmp/tao/required-review-report.md
          digest: 74e670e5141f057cb5add65ec431ec6d782e7dca6bc2ac2ebf572b37404b665a
          validated: false
        ended_at: '2026-11-05T18:47:18.727732+00:00'
        summary_digest: 1ab1e600a90ef6cd5305e69d892dc3b5a9dd89327ad09a4bab474d7d3fefb3d0
        recovered_context: true
        compacted: true
      - id: 3292367f7c0142b1b2380b1f9137243d
        round: 2
        started_at: '2026-11-05T19:34:30.604114+00:00'
        outcome: passed
        mode: serial
        reviewers: 1
        decision: 本批新增了 Kiro workspace 原始提示及调用级信任适配证据，范围扩展后将上限调整为默认初审加一次定向复核；仅复核 DIAG-01/SEL-01/FIN-01/FIN-02
          和 Kiro 新适配，串行一人，最后一轮，上限2美元及600秒
        request:
          schema: tao.review-scope/v0.1
          change: CHG_20261105_YJ2MG6FEGJ4GMXA8
          scope: feature
          kind: code
          base_commit: 186ae92c674ef4e4c604556c01682f2dac51f2d8
          target_commit: 6348e1b75ead1139df51638a2b5eb695d376bf4d
          input_digest: ae45d38924b5e851413adc9844e81b090fe1965904f88bf2a2fd9876e6831a5d
          selection_digest: 0b4f0a544b03be1c6ff1a43a49c60dcd2de8a8d6b5ecb717dadaba15177b556e
        inputs: current
        reports:
        - path: tmp/tao/required-review-followup.md
          digest: 9a87570976dea5e038e093620eddde7a42cae5b4d9fdb7437a264338987082d5
          validated: false
        ended_at: '2026-11-05T19:50:03.959335+00:00'
        summary_digest: 31c416e16a0aa1a56bb2a37cc643a09f640442c7e0e3b39a2794bc9533ff4a06
        recovered_context: true
        compacted: true
      round_decisions:
      - before: 1
        after: 2
        decision: 本批新增了 Kiro workspace 原始提示及调用级信任适配证据，范围扩展后将上限调整为默认初审加一次定向复核；仅复核 DIAG-01/SEL-01/FIN-01/FIN-02
          和 Kiro 新适配，串行一人，最后一轮，上限2美元及600秒
closure: null
provenance:
  kind: legacy
  source_digest: a6194833ec4cb5cc2043cfa2d07f760e0581a494212a31a4a9d3b408a8dff92f
  source_revision: 44
  unknown_fields: []
  review_budget_unknown: []
  lifecycle_decision: 用户明确要求继续完成全部任务并收尾；已核对迁移前后批准、审查历史、基准和产物未改变，保留原JSON，确认本事项仍在进行。
last_operation_id: a2c2d4ffcc154d9da448267a05cbbe59
---

# 改进 workflow 状态的持久依据、跨目录恢复、多事项切换及正式收尾

<!-- tao:section overview -->
## Overview

改进 workflow 状态的持久依据、跨目录恢复、多事项切换及正式收尾

<!-- tao:section decisions -->
## Decisions

Structured metadata records decisions and their bindings.

<!-- tao:section closure -->
## Closure

The lifecycle and closure metadata are authoritative.
