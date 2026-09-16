"""Evidence-bound semantic judgments with conservative calibration."""

import math
from dataclasses import dataclass

MINIMUM_CALIBRATION_SAMPLES = 30
WILSON_Z = 1.96


@dataclass(frozen=True)
class Judgment:
    reviewer: str
    rule_id: str
    verdict: str
    evidence_event_ids: tuple[str, ...]
    reason: str
    unknowns: tuple[str, ...]
    self_confidence: float | None = None


@dataclass(frozen=True)
class CalibrationRecord:
    reviewer: str
    rule_id: str
    expected: str
    predicted: str
    source: str


@dataclass(frozen=True)
class SemanticDecision:
    rule_id: str
    status: str
    confidence: float
    evidence: tuple[str, ...]
    reason: str
    needs_human: bool
    calibration_samples: int


def _text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be non-empty text")
    return value


def _strings(value, label):
    if not isinstance(value, list) or any(
            not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(f"{label} must be a list of non-empty strings")
    return tuple(value)


def parse_judgment(value):
    """Validate a judge response without trusting its confidence claim."""
    if not isinstance(value, dict):
        raise TypeError("judgment must be a mapping")
    verdict = value.get("verdict")
    if verdict not in {"pass", "fail"}:
        raise ValueError("verdict must be pass or fail")
    confidence = value.get("confidence")
    if confidence is not None and (
            not isinstance(confidence, (int, float))
            or isinstance(confidence, bool)
            or not 0 <= float(confidence) <= 1):
        raise ValueError("confidence must be between zero and one")
    return Judgment(
        _text(value.get("reviewer"), "reviewer"),
        _text(value.get("rule_id"), "rule_id"),
        verdict,
        _strings(value.get("evidence_event_ids"), "evidence_event_ids"),
        _text(value.get("reason"), "reason"),
        _strings(value.get("unknowns"), "unknowns"),
        float(confidence) if confidence is not None else None,
    )


def _wilson_lower(correct, total):
    if total == 0:
        return 0.0
    probability = correct / total
    z_squared = WILSON_Z ** 2
    denominator = 1 + z_squared / total
    center = probability + z_squared / (2 * total)
    margin = WILSON_Z * math.sqrt(
        probability * (1 - probability) / total
        + z_squared / (4 * total ** 2)
    )
    return max(0.0, (center - margin) / denominator)


def _review(rule_id, reason, *, confidence=0.0, evidence=(), samples=0,
            status="review"):
    return SemanticDecision(
        rule_id, status, confidence, tuple(evidence), reason, True, samples)


def _calibration(records, reviewer, rule_id):
    selected = {}
    conflicting = False
    for record in records:
        if record.reviewer != reviewer or record.rule_id != rule_id:
            continue
        previous = selected.get(record.source)
        if previous is not None and previous != record:
            conflicting = True
        selected[record.source] = record
    if conflicting:
        return 0.0, 0
    total = len(selected)
    correct = sum(item.expected == item.predicted for item in selected.values())
    return _wilson_lower(correct, total), total


def decide_semantic(rule, trace, judgments, calibration, thresholds):
    """Aggregate two independent judgments using observed evidence and history."""
    if not trace.complete:
        return _review(rule.id, "trace telemetry is incomplete", status="blocked")
    rows = tuple(judgments)
    if len(rows) < 2 or len({item.reviewer for item in rows}) < 2:
        return _review(rule.id, "two independent reviewers are required")
    if any(item.rule_id != rule.id for item in rows):
        return _review(rule.id, "reviewer returned a different rule id")
    verdicts = {item.verdict for item in rows}
    if len(verdicts) != 1:
        return _review(rule.id, "reviewers disagree")
    if any(item.unknowns for item in rows):
        return _review(rule.id, "reviewer reported unresolved unknowns")

    event_ids = {event.id for event in trace.events}
    if any(not item.evidence_event_ids for item in rows):
        return _review(rule.id, "semantic judgment has no evidence")
    if any(set(item.evidence_event_ids) - event_ids for item in rows):
        return _review(rule.id, "semantic judgment cites unknown evidence")

    scores = [_calibration(calibration, item.reviewer, rule.id) for item in rows]
    confidence = min(score for score, _ in scores)
    samples = min(count for _, count in scores)
    evidence = tuple(dict.fromkeys(
        identity for item in rows for identity in item.evidence_event_ids))
    if samples < MINIMUM_CALIBRATION_SAMPLES:
        return _review(
            rule.id, "insufficient calibration samples", confidence=confidence,
            evidence=evidence, samples=samples)
    threshold = thresholds[rule.severity]
    if confidence < threshold:
        return _review(
            rule.id, f"calibrated confidence is below {threshold:.3f}",
            confidence=confidence, evidence=evidence, samples=samples)

    verdict = next(iter(verdicts))
    return SemanticDecision(
        rule.id, verdict, confidence, evidence,
        "independent evidence-bound reviewers agree", False, samples)


def decide_semantic_payloads(rule, trace, payloads, calibration, thresholds):
    """Turn untrusted LLM payloads into a safe semantic decision."""
    try:
        judgments = tuple(parse_judgment(payload) for payload in payloads)
    except (TypeError, ValueError) as exc:
        return _review(rule.id, f"invalid judgment schema: {exc}")
    return decide_semantic(rule, trace, judgments, calibration, thresholds)
