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
record_revision: 2
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
        include: []
        excluded_record_directories:
        - docs/plans/2026-11/20261105-workflow-recovery/reviews/20261105-recovery-contract/
        input_digest: 092f34ee82bf1e3e069fe150bc348e715585acbd5d4bd0a9254456834304cbff
        output_files:
        - docs/plans/2026-11/20261105-workflow-recovery/reviews/20261105-recovery-contract/00-adjudication.md
        - docs/plans/2026-11/20261105-workflow-recovery/reviews/20261105-recovery-contract/01-contract-reviewer.md
      inputs: current
      reports:
      - path: docs/plans/2026-11/20261105-workflow-recovery/reviews/20261105-recovery-contract/01-contract-reviewer.md
        digest: 7ccc4089c463255c8b2e0ae6f8cec22e0cc85aa983dc545788701459cdfed6e7
        validated: true
      summary: 独立文档初审确认两项 P2 阻断：旧 JSON 缺明确迁移应用入口；新记录无法保存旧计划未知生命周期。两项均采用待修订，源文档未改。报告及导航源校验通过，无诊断。
      ended_at: '2026-11-05T15:15:54.049688+00:00'
      evidence_boundary: Scheduling record only. Required independent attestations
        use tao review imports; report existence does not prove correctness or identity.
      recovered_context: true
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
        include: []
        excluded_record_directories:
        - docs/plans/2026-11/20261105-workflow-recovery/reviews/20261105-recovery-contract/
        input_digest: bd22cc05a386af5ae2ba15cc8d6b46891eb539069d2d1b835677a60d0fae73aa
        output_files:
        - docs/plans/2026-11/20261105-workflow-recovery/reviews/20261105-recovery-contract/02-followup-reviewer.md
        - docs/plans/2026-11/20261105-workflow-recovery/reviews/20261105-recovery-contract/03-followup-adjudication.md
      inputs: current
      reports:
      - path: docs/plans/2026-11/20261105-workflow-recovery/reviews/20261105-recovery-contract/02-followup-reviewer.md
        digest: eec109c4d2144edf74c07b0c68ad9b135f23b81cffb18b2700242a318a0088eb
        validated: true
      summary: 第二轮定向复核确认 A/B 已闭合，无残余阻断或已证实回归；适用于修订工作区快照。文档源校验通过，不代表实现验收或阶段批准。
      ended_at: '2026-11-05T15:28:39.374972+00:00'
      evidence_boundary: Scheduling record only. Required independent attestations
        use tao review imports; report existence does not prove correctness or identity.
      recovered_context: true
    round_decisions: []
  code:
    id: 95e30131f4c74e048d31b2900dd1f5e6
    phase: implement
    decision: 用户批准recover/plan预算2至4美元的小范围变更；按默认两轮保存本次定向复核，第一轮追记登记失败后误启动并中止的调用，不作为有效审查；第二轮只审本次差异，实际调用上限1美元300秒。
    started_at: '2026-11-06T03:01:42.403373+00:00'
    max_rounds: 3
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
        include:
        - tests/acceptance/clients.py
        excluded_record_directories: []
        input_digest: cec3db56023fa375f5e5671b5293750ed116c299d84180bb443fb4835dd72c96
      inputs: current
      reports: []
      summary: 'Retrospective failure audit only: dispatch ran after review-begin
        was rejected by the verification mutation lock. It read prior revision 25
        metadata instead of current revision 30 inputs and was interrupted. No valid
        conclusion or receipt. Raw interrupted stream tmp/tao/budget-review-source.jsonl;
        isolation record tmp/tao/budget-review-isolation.json says global_unchanged=true.
        This newly registered snapshot is an audit scheduling reference, not evidence
        that the aborted call reviewed it. Unmanaged raw logs were not document-schema
        validated.'
      ended_at: '2026-11-06T03:01:47.919496+00:00'
      evidence_boundary: Scheduling record only. Required independent attestations
        use tao review imports; report existence does not prove correctness or identity.
      recovered_context: true
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
        include:
        - tests/acceptance/clients.py
        excluded_record_directories:
        - tmp/tao/
        input_digest: cec3db56023fa375f5e5671b5293750ed116c299d84180bb443fb4835dd72c96
        output_files:
        - tmp/tao/budget-final-review-report.md
      inputs: current
      reports: []
      summary: 'Actual registered delta review failed: Claude CLI exit 1, subtype
        error_max_budget_usd, 294258ms, 15 turns, estimated total_cost_usd 1.14164
        against requested max-budget-usd 1. No structured conclusion or valid importable
        receipt. Source tmp/tao/budget-final-review-source.jsonl retained; global
        configuration unchanged per tmp/tao/budget-final-review-isolation.json. Batch
        two attempts exhausted; no automatic retry. Unmanaged raw logs were not document-schema
        validated.'
      ended_at: '2026-11-06T03:07:33.391798+00:00'
      evidence_boundary: Scheduling record only. Required independent attestations
        use tao review imports; report existence does not prove correctness or identity.
      recovered_context: true
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
        include:
        - tests/acceptance/cancellation.py
        - tests/acceptance/behavior_clients.py
        - tests/acceptance/behavior_runner.py
        - tests/acceptance/behavior_live.py
        - tests/acceptance/clients.py
        - tests/acceptance/native_session_hooks.py
        - tests/test_live_acceptance.py
        - tests/test_acceptance_cancellation.py
        - tests/test_behavior_runner.py
        - scripts/review_claude.py
        - tests/acceptance/README.md
        - docs/plans/2026-11/20261105-workflow-recovery.md
        excluded_record_directories:
        - tmp/tao/
        input_digest: e0990b046cf260339cecb34888af0a0821c33e79c16c3549bbb01ba26f02e883
        output_files:
        - tmp/tao/cancellation-review-report.md
      inputs: current
      reports: []
      summary: 'Actual tool-free cancellation/budget delta review did not yield an
        importable receipt. Preserved execution summary: tmp/tao/cancellation-review-execution.json.
        No retry. Raw logs unmanaged and not document-schema validated.'
      ended_at: '2026-11-06T03:58:38.634611+00:00'
      evidence_boundary: Scheduling record only. Required independent attestations
        use tao review imports; report existence does not prove correctness or identity.
      recovered_context: true
    round_decisions:
    - before: 2
      after: 3
      decision: 用户继续解决授权内发现了新的取消缺陷及其回归：外层终止后模型组继续运行、双轮重复计时。当前范围扩至这些修复、低强度小型探针和预算差异；按新证据显式增加一轮至3，不重置前两次失败，不自动新建批次。只一次工具禁用的独立CLI审查，预算阈值仍1美元、超时仍300秒。
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
          include: []
          excluded_record_directories:
          - docs/plans/2026-11/20261105-workflow-recovery/reviews/20261105-implementation/
          input_digest: 7efd25ccfa38c223591ed3839cff4ed92c9a4590cd45bee942211927c7553183
          output_files:
          - docs/plans/2026-11/20261105-workflow-recovery/reviews/20261105-implementation/00-adjudication.md
          - docs/plans/2026-11/20261105-workflow-recovery/reviews/20261105-implementation/01-implementation-reviewer.md
        inputs: current
        reports:
        - path: docs/plans/2026-11/20261105-workflow-recovery/reviews/20261105-implementation/01-implementation-reviewer.md
          digest: a389b402a0e2f8d7a118c1b52cff05aebde143d4dcbe4d14800fb93db3f530b1
          validated: true
        summary: 独立实现初审确认四项阻断 I1-I4：finish 缺当前调度审查核对、未知轮次自动重置、frontmatter 子串分隔、嵌套审查元数据校验不足。全部采用，按已有实现授权修复。
        ended_at: '2026-11-05T16:04:59.961028+00:00'
        evidence_boundary: Scheduling record only. Required independent attestations
          use tao review imports; report existence does not prove correctness or identity.
        recovered_context: true
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
          include: []
          excluded_record_directories:
          - docs/plans/2026-11/20261105-workflow-recovery/reviews/20261105-implementation/
          input_digest: 1ae14a8f7e36b942469bf349e52a657e2aa5a15e124f9e7d49c9ea79cf546120
          output_files:
          - docs/plans/2026-11/20261105-workflow-recovery/reviews/20261105-implementation/02-followup-reviewer.md
          - docs/plans/2026-11/20261105-workflow-recovery/reviews/20261105-implementation/03-followup-adjudication.md
        inputs: current
        reports:
        - path: docs/plans/2026-11/20261105-workflow-recovery/reviews/20261105-implementation/02-followup-reviewer.md
          digest: 8661533950e4fe2a8cada00a08b89054a9db4da95e52dbe86f1ceb79d83f9379
          validated: true
        summary: 代码第二轮复核 I1-I3 闭合，I4 部分闭合：request.base_commit 等必需值缺少类型验证。独立 53 项测试通过，但额外反例仍崩溃。两轮用尽，先保留本轮结论，再补齐校验和回归。
        ended_at: '2026-11-05T16:19:02.137127+00:00'
        evidence_boundary: Scheduling record only. Required independent attestations
          use tao review imports; report existence does not prove correctness or identity.
        recovered_context: true
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
          include: []
          excluded_record_directories:
          - docs/plans/2026-11/20261105-workflow-recovery/reviews/20261105-implementation/
          input_digest: 7d0ed12a63cb45fb1b72b2eab618a5a0539e42dda0ec460f1b40681b7b16d3da
          output_files:
          - docs/plans/2026-11/20261105-workflow-recovery/reviews/20261105-implementation/04-validation-reviewer.md
          - docs/plans/2026-11/20261105-workflow-recovery/reviews/20261105-implementation/05-validation-adjudication.md
        inputs: current
        reports:
        - path: docs/plans/2026-11/20261105-workflow-recovery/reviews/20261105-implementation/04-validation-reviewer.md
          digest: 829ba547373e3688358f29c518a1da5f6ed9c45251a7be7d8b5f5e8782154b6c
          validated: true
        summary: 用户批准的第三轮定向复核；passed，范围仅 I4 最终修复，完整交付及机器证据仍未完成
        ended_at: '2026-11-05T17:23:43.785846+00:00'
        evidence_boundary: Scheduling record only. Required independent attestations
          use tao review imports; report existence does not prove correctness or identity.
        recovered_context: true
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
          include: []
          excluded_record_directories:
          - tmp/tao/
          input_digest: a9b076740dcc0dfe66e1fbec87d645e1c5bd2760ad28b4f7ea37624aaf815983
          output_files:
          - tmp/tao/required-review-report.md
        inputs: current
        reports:
        - path: tmp/tao/required-review-report.md
          digest: 74e670e5141f057cb5add65ec431ec6d782e7dca6bc2ac2ebf572b37404b665a
          validated: false
        summary: 'Reviewed the cumulative base→fixed diff for the workflow-recovery
          change against docs/product/workflow-recovery.md (DOC_20261105_27RJ5NTQG9BNBJHX)
          and docs/engineering/workflow-recovery.md (DOC_20261105_0H6V7T4BYCRJW79H),
          inspecting workflow_records.py, workflow_recovery.py, workflows.py, review_runs.py,
          project.py, cli.py, frontmatter.py, the new profile/template/locales, the
          new and changed tests, and the acceptance-harness changes. Much of the specification
          is implemented faithfully: .tao/workflows JSON stays ignored (.gitignore;
          workflow_records.write refuses out-of-scope and git-ignored targets) while
          start creates a docs/workflows/<CHG>.md formal record before the JSON; recover
          is preview-only without --apply, refuses to overwrite existing or corrupt
          state, re-checks inside the lock, and binds a source digest; recovery reconstructs
          only recorded facts — plan-only recovery yields lifecycle=unknown, empty
          approvals, explicit blockers, unknown review budget requiring an explicit
          new batch, and recovered review runs are never treated as passed; finish
          saves a structured closure (evidence/unfinished/result/decision/recorded_at),
          gates completed on verify plus a current code review plus phase=finish with
          no blockers/operations/stale approvals, requires unfinished disposition
          for cancelled, and is idempotent on retry; the two-file durable-event ordering
          (record first, local projection second) and its failure-injection tests
          match the design; advance at finish now refuses and points to finish. The
          acceptance fix is sound: isolated_codex.py now reuses the installer''s own
          _write_config/_key path (verified present and used by the installer itself
          for trust hashes), and the behavior-scenarios.yaml prompt change pins the
          scheduler decision and grants proceeding, consistent with its AUTH-001/INTERACTION-001
          expectations. Four defects remain: corrupt formal records are misdiagnosed
          as corrupt local state with the wrong path and an inapplicable recovery
          command; cross-worktree selection short-circuits on local candidates, hides
          a live worktree''s state, and its diagnostic can guide the user into creating
          a duplicate parallel state that is then never flagged (the missing() diagnostic
          also omits the design-required candidate_sources); finish on a legacy record-less
          workflow silently writes the closure only to the transient local JSON; and
          finish does not clear lifecycle from provenance.unknown_fields. These findings
          are from static analysis; the test suite and the concurrency, real-worktree,
          and acceptance-client behaviors were not executed in this review, so this
          is not a delivery-readiness claim.'
        ended_at: '2026-11-05T18:47:18.727732+00:00'
        evidence_boundary: Scheduling record only. Required independent attestations
          use tao review imports; report existence does not prove correctness or identity.
        recovered_context: true
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
          include: []
          excluded_record_directories:
          - tmp/tao/
          input_digest: ae45d38924b5e851413adc9844e81b090fe1965904f88bf2a2fd9876e6831a5d
          output_files:
          - tmp/tao/required-review-followup.md
        inputs: current
        reports:
        - path: tmp/tao/required-review-followup.md
          digest: 9a87570976dea5e038e093620eddde7a42cae5b4d9fdb7437a264338987082d5
          validated: false
        summary: 'Follow-up review of the fixes for DIAG-01, SEL-01, FIN-01 and FIN-02
          plus the directly affected behavior, against docs/engineering/workflow-recovery.md
          (DOC_20261105_0H6V7T4BYCRJW79H) and the workflow-recovery product requirements,
          and of the new launch-only Kiro workspace-trust scope in tests/acceptance/native_session_hooks.py.
          All four prior findings are fixed with real evidence: observation now reads
          the formal record first and returns a formal-record-invalid diagnostic that
          names the record file, drops the inapplicable recover command and blocks
          writes/recovery while leaving the local JSON untouched (DIAG-01); locate
          now resolves the single worktree owning the live state across all registered
          worktree roots, recover refuses to create a duplicate state copy, the status
          listing marks duplicates as selection-required, and the shared missing/ambiguity
          diagnostics provide rule_id, candidate_sources across discovered worktrees,
          recovery commands and the conflict reason (SEL-01); finish on a record-less
          workflow now refuses with a migration-required diagnostic pointing at the
          record path and a migrate preview command, and after migrate plus finish
          the closure remains recognizable from the record after the local JSON is
          deleted (FIN-01); workflow_records.build now clears ''lifecycle'' from provenance.unknown_fields
          and records the lifecycle decision whenever a closure is written, matching
          reconcile''s resume behavior (FIN-02). The start slug check no longer treats
          a legacy phase=complete JSON as closed, which is the design''s "unknown
          lifecycle is not finished" rule, covered by a new test rather than a regression.
          The Kiro change adds a launch-only --trust-workspace flag, feature-detected
          via an isolated ''kiro chat --help'' probe and gated by a guard that accepts
          only the isolated acceptance layout (KIRO_HOME under the fresh workspace,
          project outside the repository) and raises otherwise; nothing is persisted
          outside the isolated experiment, the PTY confirmation key was corrected
          to carriage return, and provided offline evidence (native-launch-trust-tests.log:
          7 passed in 64.92 s covering both real native sessions; launch-trust-unit-final.log:
          5 passed, 2 deselected) is consistent with the plan record that the native
          write and hook feedback passed with personal state summaries unchanged.
          I executed the three permitted targeted test files (64 passed, 2 deselected,
          including all 13 new fix-specific tests) with the project Python; I found
          no new blockers or suggestions introduced by these fixes. This is not a
          delivery-readiness claim: the configured full code check still carries two
          Claude budget failures per the change plan, Windows native acceptance remains
          uncovered, and native/model acceptance was not rerun here.'
        ended_at: '2026-11-05T19:50:03.959335+00:00'
        evidence_boundary: Scheduling record only. Required independent attestations
          use tao review imports; report existence does not prove correctness or identity.
        recovered_context: true
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
last_operation_id: a3795b6a3eb245fda7f34e73c5194a85
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
