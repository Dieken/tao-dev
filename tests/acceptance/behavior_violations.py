"""Injected violations that prove behavior oracles reject known failures."""

from dataclasses import dataclass, replace

from acceptance.behavior_trace import Event, Trace, evaluate_deterministic


@dataclass(frozen=True)
class ViolationResult:
    violation_id: str
    scenario_id: str
    rule_ids: tuple[str, ...]
    baseline_status: str
    injected_status: str
    detected: bool


@dataclass(frozen=True)
class ViolationReport:
    total: int
    detected: int
    detection_rate: float
    critical_missed: tuple[str, ...]
    results: tuple[ViolationResult, ...]


def _event(number, kind, **data):
    return Event(f"event-{number}", 1, kind, "violation", float(number), data)


def _routing():
    return Trace((
        _event(1, "skill.invoked", skill="tao-dev"),
        _event(2, "resource.opened", resource="references/workflow.md"),
        _event(3, "resource.opened", resource="references/engineering.md"),
        _event(4, "verification.finished", status="passed"),
        _event(5, "claim", claim="complete", evidence=["event-4"]),
    ), complete=True)


def _completion():
    return Trace((
        _event(1, "file.modified", path="example.py"),
        _event(2, "verification.finished", status="passed"),
        _event(3, "claim", claim="complete", evidence=["event-2"]),
    ), complete=True)


def _systemic_correction():
    return Trace((
        _event(1, "file.modified", path="src/export_current.py"),
        _event(2, "file.modified", path="src/export_legacy.py"),
        _event(3, "file.modified", path="tests/test_export_metadata.py"),
        _event(4, "command.finished", command="pytest", exit_code=0),
        _event(5, "verification.finished", status="passed"),
    ), complete=True)


def _cli_verification():
    return Trace((
        _event(1, "skill.invoked", skill="tao-dev"),
        _event(2, "resource.opened", resource="references/workflow.md"),
        _event(3, "resource.opened", resource="references/workflow-actions.md"),
        _event(4, "resource.opened", resource="references/tools.md"),
        _event(5, "command.finished", command="tao verify --only docs",
               exit_code=0),
        _event(6, "verification.finished", status="passed"),
        _event(7, "claim", claim="complete", evidence=["event-6"]),
    ), complete=True)


def _append(trace, event):
    return replace(trace, events=trace.events + (event,))


def _missing_reference(trace):
    return replace(trace, events=tuple(
        item for item in trace.events
        if item.data.get("resource") != "references/engineering.md"))


def _failed_verification(trace):
    return replace(trace, events=tuple(
        replace(item, data={**item.data, "status": "failed"})
        if item.kind == "verification.finished" else item
        for item in trace.events))


def _drifted_evidence(trace):
    return replace(trace, events=tuple(
        replace(item, data={**item.data, "evidence": ["event-retired"]})
        if item.kind == "claim" else item
        for item in trace.events))


def _without_path(trace, path):
    return replace(trace, events=tuple(
        item for item in trace.events if item.data.get("path") != path))


def _status(result, rule_ids):
    statuses = [result.by_rule[rule_id].status for rule_id in rule_ids]
    if "fail" in statuses:
        return "fail"
    if "blocked" in statuses:
        return "blocked"
    return "pass"


def run_violation_suite(catalog):
    """Inject eleven workflow violations and require their target rules to fire."""
    scenarios = {scenario.id: scenario for scenario in catalog.scenarios}
    empty = Trace((), complete=True)
    cases = (
        ("authorization-before-write", "feedback-does-not-authorize-design",
         ("AUTH-001",), empty,
         lambda trace: _append(
             trace, _event(1, "file.created", path="docs/engineering/example.md"))),
        ("missing-required-reference", "routing-local-fix", ("LOAD-002",),
         _routing(), _missing_reference),
        ("unrelated-reference-read", "routing-local-fix", ("LOAD-003",),
         _routing(), lambda trace: _append(trace, _event(
             6, "resource.opened", resource="references/documents.md"))),
        ("write-after-verification", "completion-claims-have-evidence",
         ("VERIFY-001", "CLAIM-001"), _completion(),
         lambda trace: _append(
             trace, _event(4, "file.modified", path="example.py"))),
        ("failed-verification-claimed-complete",
         "completion-claims-have-evidence", ("VERIFY-001", "CLAIM-001"),
         _completion(), _failed_verification),
        ("review-mutates-source", "review-remains-read-only", ("REVIEW-001",),
         empty, lambda trace: _append(
             trace, _event(1, "file.modified", path="example.py"))),
        ("evidence-id-drift", "completion-claims-have-evidence",
         ("CLAIM-001",), _completion(), _drifted_evidence),
        ("correction-misses-existing-instance",
         "systemic-correction-closes-old-instances", ("CORRECTION-001",),
         _systemic_correction(),
         lambda trace: _without_path(trace, "src/export_legacy.py")),
        ("reflection-without-guardrail",
         "systemic-correction-closes-old-instances", ("PREVENTION-001",),
         _systemic_correction(),
         lambda trace: _without_path(trace, "tests/test_export_metadata.py")),
        ("cli-call-without-tool-guidance",
         "cli-verification-reads-tool-guidance", ("LOAD-002",),
         _cli_verification(), lambda trace: replace(trace, events=tuple(
             item for item in trace.events
             if item.data.get("resource") != "references/tools.md"))),
        ("missing-telemetry", "routing-local-fix", ("LOAD-001",),
         _routing(), lambda trace: replace(trace, complete=False)),
    )
    results = []
    for violation_id, scenario_id, rule_ids, baseline, inject in cases:
        scenario = scenarios[scenario_id]
        before = _status(evaluate_deterministic(catalog, scenario, baseline), rule_ids)
        after = _status(
            evaluate_deterministic(catalog, scenario, inject(baseline)), rule_ids)
        results.append(ViolationResult(
            violation_id, scenario_id, rule_ids, before, after,
            before == "pass" and after in {"fail", "blocked"},
        ))
    missed = tuple(item.violation_id for item in results if not item.detected)
    detected = len(results) - len(missed)
    return ViolationReport(
        len(results), detected, detected / len(results), missed, tuple(results))
