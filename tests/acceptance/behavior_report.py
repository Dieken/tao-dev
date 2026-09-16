"""Machine-readable and compact human-facing behavior acceptance reports."""

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from acceptance.behavior_contract import SUPPORTED_CLIENTS


@dataclass(frozen=True)
class RuleObservation:
    client: str
    scenario_id: str
    rule_id: str
    status: str
    oracle: str
    confidence: float
    evidence: tuple[str, ...]
    reason: str


@dataclass(frozen=True)
class BehaviorReport:
    status: str
    versions: dict[str, str]
    missing_clients: tuple[str, ...]
    missing_observations: tuple[str, ...]
    client_matrix: dict[str, dict[str, str]]
    observations: tuple[RuleObservation, ...]
    attention_queue: tuple[dict, ...]
    mutation_detection_rate: float
    mutation_total: int
    mutation_detected: int
    critical_mutations_missed: tuple[str, ...]

    def to_dict(self):
        return {
            "status": self.status,
            "versions": self.versions,
            "missing_clients": list(self.missing_clients),
            "missing_observations": list(self.missing_observations),
            "client_matrix": self.client_matrix,
            "observations": [asdict(item) for item in self.observations],
            "attention_queue": list(self.attention_queue),
            "mutation_detection_rate": self.mutation_detection_rate,
            "mutation_total": self.mutation_total,
            "mutation_detected": self.mutation_detected,
            "critical_mutations_missed": list(self.critical_mutations_missed),
        }


def _scenario_status(rows):
    statuses = {row.status for row in rows}
    for status in ("fail", "blocked", "review", "pass"):
        if status in statuses:
            return status
    return "blocked"


def build_report(catalog, observations, mutations, *, versions=None):
    """Aggregate automated verdicts and isolate the small attention queue."""
    rows = tuple(observations)
    observed_clients = {row.client for row in rows}
    missing_clients = tuple(
        client for client in SUPPORTED_CLIENTS if client not in observed_clients)
    observed = {
        (row.client, row.scenario_id, row.rule_id) for row in rows
    }
    expected = {
        (client, scenario.id, rule_id)
        for scenario in catalog.scenarios
        for client in scenario.clients
        for rule_id in scenario.rules
    }
    missing_observations = tuple(
        "/".join(identity) for identity in sorted(expected - observed))
    grouped = {}
    for row in rows:
        grouped.setdefault((row.scenario_id, row.client), []).append(row)
    matrix = {}
    for (scenario_id, client), values in sorted(grouped.items()):
        matrix.setdefault(scenario_id, {})[client] = _scenario_status(values)

    queue = []
    for row in rows:
        if row.status == "pass":
            continue
        queue.append({
            "client": row.client,
            "scenario_id": row.scenario_id,
            "rule_id": row.rule_id,
            "status": row.status,
            "oracle": row.oracle,
            "confidence": row.confidence,
            "reason": row.reason,
            "evidence": list(row.evidence),
            "needs_human": row.status in {"review", "blocked"},
        })
    for client in missing_clients:
        queue.append({
            "client": client,
            "scenario_id": None,
            "rule_id": None,
            "status": "blocked",
            "oracle": "infrastructure",
            "confidence": 0.0,
            "reason": "required client has no observations",
            "evidence": [],
            "needs_human": True,
        })
    if missing_observations:
        queue.append({
            "client": "catalog",
            "scenario_id": None,
            "rule_id": None,
            "status": "blocked",
            "oracle": "coverage",
            "confidence": 0.0,
            "reason": f"{len(missing_observations)} required observations are missing",
            "evidence": [],
            "needs_human": False,
        })

    statuses = {row.status for row in rows}
    if mutations.critical_missed or "fail" in statuses:
        status = "failed"
    elif missing_clients or missing_observations or "blocked" in statuses:
        status = "blocked"
    elif "review" in statuses:
        status = "review"
    else:
        status = "passed"
    return BehaviorReport(
        status,
        dict(versions or {}),
        missing_clients,
        missing_observations,
        matrix,
        rows,
        tuple(queue),
        mutations.detection_rate,
        mutations.total,
        mutations.detected,
        mutations.critical_missed,
    )


def _markdown(report):
    labels = {"claude": "Claude Code", "codex": "Codex CLI"}
    lines = [
        "# Agent behavior acceptance report",
        "",
        f"Overall status: **{report.status}**",
        "",
        ("Mutation detection: "
         f"{report.mutation_detected}/{report.mutation_total} "
         f"({report.mutation_detection_rate:.1%})"),
        "",
        "## Client versions",
        "",
    ]
    for client in SUPPORTED_CLIENTS:
        lines.append(f"- {labels[client]}: {report.versions.get(client, 'not recorded')}")
    lines.extend(("", "## Scenario matrix", "", "| Scenario | Claude Code | Codex CLI |",
                  "|---|---|---|"))
    for scenario, clients in report.client_matrix.items():
        lines.append(
            f"| {scenario} | {clients.get('claude', 'not run')} | "
            f"{clients.get('codex', 'not run')} |")
    lines.extend(("", "## Attention queue", ""))
    if not report.attention_queue:
        lines.append("无需人工复核。")
    else:
        for item in report.attention_queue:
            lines.append(
                f"- {item['client']} / {item['scenario_id'] or '-'} / "
                f"{item['rule_id'] or '-'}: {item['status']}; "
                f"confidence={item['confidence']:.3f}; {item['reason']}")
    return "\n".join(lines) + "\n"


def write_report(report, json_path, markdown_path):
    Path(json_path).write_text(
        json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n")
    Path(markdown_path).write_text(_markdown(report))
