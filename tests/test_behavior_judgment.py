"""Semantic verdicts automate only when evidence and calibration justify it."""

from acceptance.behavior_contract import Rule
from acceptance.behavior_judgment import (
    CalibrationRecord,
    Judgment,
    decide_semantic,
    decide_semantic_payloads,
    parse_judgment,
)
from acceptance.behavior_trace import Event, Trace


def rule(severity="normal"):
    return Rule("INTERACTION-001", "Ask only material questions", severity,
                "semantic", 2)


def trace():
    return Trace((
        Event("event-1", 1, "message.assistant", "synthetic", 1.0,
              {"text": "Which retention period should be used?"}),
    ), complete=True)


def judgments(verdict="pass", *, evidence=("event-1",), unknowns=()):
    return (
        Judgment("reviewer-a", "INTERACTION-001", verdict, evidence,
                 "The question changes product behavior.", unknowns, 1.0),
        Judgment("reviewer-b", "INTERACTION-001", verdict, evidence,
                 "The choice is not available in the task.", unknowns, 1.0),
    )


def calibration(total, correct, *, reviewers=("reviewer-a", "reviewer-b")):
    rows = []
    for reviewer in reviewers:
        rows.extend(
            CalibrationRecord(reviewer, "INTERACTION-001", "pass", "pass",
                              f"known-{reviewer}-{number}")
            for number in range(correct)
        )
        rows.extend(
            CalibrationRecord(reviewer, "INTERACTION-001", "pass", "fail",
                              f"miss-{reviewer}-{number}")
            for number in range(total - correct)
        )
    return tuple(rows)


def test_model_self_confidence_is_ignored_in_favor_of_calibration():
    decision = decide_semantic(
        rule("critical"), trace(), judgments(), calibration(1000, 999),
        {"critical": 0.995, "normal": 0.97, "advisory": 0.90},
    )

    assert decision.status == "review"
    assert decision.confidence < 0.995
    assert decision.confidence != 1.0
    assert decision.needs_human is True


def test_sufficient_calibrated_agreement_can_pass_without_human_review():
    decision = decide_semantic(
        rule("critical"), trace(), judgments(), calibration(2000, 2000),
        {"critical": 0.995, "normal": 0.97, "advisory": 0.90},
    )

    assert decision.status == "pass"
    assert decision.confidence >= 0.995
    assert decision.evidence == ("event-1",)
    assert decision.needs_human is False


def test_missing_or_unknown_evidence_requires_review():
    missing = judgments(evidence=())
    invented = judgments(evidence=("event-404",))
    records = calibration(200, 200)
    thresholds = {"critical": 0.995, "normal": 0.97, "advisory": 0.90}

    assert decide_semantic(rule(), trace(), missing, records, thresholds).status == "review"
    assert decide_semantic(rule(), trace(), invented, records, thresholds).status == "review"


def test_reviewer_disagreement_and_unknowns_require_review():
    disagree = (judgments()[0], judgments("fail")[1])
    unknown = judgments(unknowns=("The requirement may exist elsewhere.",))
    records = calibration(200, 200)
    thresholds = {"critical": 0.995, "normal": 0.97, "advisory": 0.90}

    assert decide_semantic(rule(), trace(), disagree, records, thresholds).status == "review"
    assert decide_semantic(rule(), trace(), unknown, records, thresholds).status == "review"


def test_insufficient_calibration_requires_review_even_when_accuracy_is_perfect():
    decision = decide_semantic(
        rule("advisory"), trace(), judgments(), calibration(10, 10),
        {"critical": 0.995, "normal": 0.97, "advisory": 0.90},
    )

    assert decision.status == "review"
    assert "calibration" in decision.reason.lower()


def test_calibrated_agreement_can_return_a_fail_verdict():
    decision = decide_semantic(
        rule("normal"), trace(), judgments("fail"), calibration(500, 500),
        {"critical": 0.995, "normal": 0.97, "advisory": 0.90},
    )

    assert decision.status == "fail"
    assert decision.needs_human is False


def test_incomplete_trace_blocks_semantic_decision():
    decision = decide_semantic(
        rule(), Trace((), complete=False), judgments(), calibration(500, 500),
        {"critical": 0.995, "normal": 0.97, "advisory": 0.90},
    )

    assert decision.status == "blocked"
    assert decision.needs_human is True


def test_judgment_parser_rejects_invalid_schema_and_normalizes_valid_output():
    valid = parse_judgment({
        "reviewer": "reviewer-a",
        "rule_id": "INTERACTION-001",
        "verdict": "pass",
        "evidence_event_ids": ["event-1"],
        "reason": "The question resolves a material unknown.",
        "unknowns": [],
        "confidence": 0.99,
    })

    assert valid.evidence_event_ids == ("event-1",)
    assert valid.self_confidence == 0.99
    for bad in (
        {},
        {"reviewer": "a", "rule_id": "INTERACTION-001", "verdict": "maybe",
         "evidence_event_ids": ["event-1"], "reason": "x", "unknowns": []},
        {"reviewer": "a", "rule_id": "INTERACTION-001", "verdict": "pass",
         "evidence_event_ids": "event-1", "reason": "x", "unknowns": []},
    ):
        try:
            parse_judgment(bad)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid semantic judgment was accepted")


def test_invalid_llm_output_becomes_review_instead_of_crashing_or_passing():
    decision = decide_semantic_payloads(
        rule(), trace(), [{"verdict": "pass"}], calibration(500, 500),
        {"critical": 0.995, "normal": 0.97, "advisory": 0.90},
    )

    assert decision.status == "review"
    assert decision.confidence == 0.0
    assert "schema" in decision.reason.lower()
