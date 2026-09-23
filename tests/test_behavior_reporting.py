"""Known workflow violations must be detected and summarized automatically."""

import json
from pathlib import Path

from acceptance.behavior_contract import load_catalog
from acceptance.behavior_violations import run_violation_suite
from acceptance.behavior_report import (
    RuleObservation,
    build_report,
    write_report,
)

ROOT = Path(__file__).resolve().parents[1]
CATALOG = load_catalog(
    ROOT / "tests/acceptance/behavior-contract.yaml",
    ROOT / "tests/acceptance/behavior-scenarios.yaml",
)


def observation(client, scenario, rule, status="pass", *, oracle="deterministic",
                confidence=1.0, reason=""):
    return RuleObservation(
        client, scenario, rule, status, oracle, confidence,
        ("event-1",), reason,
    )


def all_pass_observations():
    definitions = {rule.id: rule for rule in CATALOG.rules}
    return tuple(
        observation(client, scenario.id, rule_id,
                    oracle=definitions[rule_id].oracle)
        for scenario in CATALOG.scenarios
        for client in scenario.clients
        for rule_id in scenario.rules
    )


def replace_observation(rows, replacement):
    identity = (replacement.client, replacement.scenario_id, replacement.rule_id)
    return tuple(
        replacement if (row.client, row.scenario_id, row.rule_id) == identity
        else row
        for row in rows
    )


def test_all_eleven_injected_violations_are_detected():
    result = run_violation_suite(CATALOG)

    assert result.total == 11
    assert result.detected == 11
    assert result.detection_rate == 1.0
    assert result.critical_missed == ()
    assert {item.violation_id for item in result.results} == {
        "authorization-before-write",
        "missing-required-reference",
        "unrelated-reference-read",
        "write-after-verification",
        "failed-verification-claimed-complete",
        "review-mutates-source",
        "evidence-id-drift",
        "correction-misses-existing-instance",
        "reflection-without-guardrail",
        "cli-call-without-tool-guidance",
        "missing-telemetry",
    }
    assert all(item.baseline_status == "pass" for item in result.results)
    assert all(item.injected_status in {"fail", "blocked"}
               for item in result.results)


def test_report_exposes_client_matrix_confidence_and_human_queue():
    violations = run_violation_suite(CATALOG)
    rows = replace_observation(
        all_pass_observations(),
        observation(
            "claude", "material-unknown-is-asked-once", "INTERACTION-001",
            "review", oracle="semantic", confidence=0.941,
            reason="calibrated confidence is below 0.970"),
    )

    report = build_report(CATALOG, rows, violations,
                          versions={"claude": "2.1.270", "codex": "0.154.0"})

    assert report.status == "review"
    assert report.client_matrix["routing-local-fix"] == {
        "claude": "pass", "codex": "pass"}
    assert report.client_matrix["material-unknown-is-asked-once"] == {
        "claude": "review", "codex": "pass"}
    assert report.attention_queue[0]["confidence"] == 0.941
    assert report.attention_queue[0]["needs_human"] is True
    assert report.known_violation_detection_rate == 1.0


def test_deterministic_failure_fails_gate_without_low_confidence_language():
    report = build_report(
        CATALOG,
        replace_observation(
            all_pass_observations(),
            observation("claude", "routing-local-fix", "LOAD-002", "fail",
                        reason="required reference was not opened")),
        run_violation_suite(CATALOG),
    )

    assert report.status == "failed"
    finding = report.attention_queue[0]
    assert finding["needs_human"] is False
    assert finding["confidence"] == 1.0


def test_missing_required_client_and_missed_violation_block_or_fail_gate():
    violations = run_violation_suite(CATALOG)
    missing_client = build_report(
        CATALOG,
        tuple(row for row in all_pass_observations() if row.client == "claude"),
        violations,
    )
    sabotaged = violations.__class__(
        violations.total, violations.detected - 1,
        (violations.detected - 1) / violations.total,
        (violations.results[0].violation_id,), violations.results,
    )
    missed_violation = build_report(
        CATALOG,
        all_pass_observations(),
        sabotaged,
    )

    assert missing_client.status == "blocked"
    assert "codex" in missing_client.missing_clients
    assert missed_violation.status == "failed"


def test_report_writes_stable_json_and_reviewable_markdown(tmp_path):
    report = build_report(
        CATALOG,
        all_pass_observations(),
        run_violation_suite(CATALOG),
        versions={"claude": "2.1.270", "codex": "0.154.0"},
    )
    json_path = tmp_path / "report.json"
    markdown_path = tmp_path / "report.md"

    write_report(report, json_path, markdown_path)

    payload = json.loads(json_path.read_text(encoding='utf-8'))
    assert payload["status"] == "passed"
    assert payload["known_violation_detection_rate"] == 1.0
    text = markdown_path.read_text(encoding='utf-8')
    assert "Claude Code" in text
    assert "Codex CLI" in text
    assert "100.0%" in text
    assert "无需人工复核" in text
