"""Load and validate executable tao-dev behavior contracts."""

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

SUPPORTED_CLIENTS = ("claude", "codex")
SEVERITIES = ("critical", "normal", "advisory")
ORACLES = ("deterministic", "semantic")
RULE_ID = re.compile(r"^[A-Z][A-Z0-9-]*-[0-9]{3}$")
SCENARIO_ID = re.compile(r"^[a-z][a-z0-9-]*$")


class CatalogError(ValueError):
    """A stable, machine-readable catalog validation failure."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class Rule:
    id: str
    title: str
    severity: str
    oracle: str
    required_scenarios: int


@dataclass(frozen=True)
class Scenario:
    id: str
    title: str
    clients: tuple[str, ...]
    fixture: str
    prompt: str
    turns: tuple[dict, ...]
    rules: tuple[str, ...]
    expectations: dict


@dataclass(frozen=True)
class Catalog:
    version: int
    thresholds: dict[str, float]
    rules: tuple[Rule, ...]
    scenarios: tuple[Scenario, ...]


@dataclass(frozen=True)
class CoverageReport:
    status: str
    clients: tuple[str, ...]
    rule_count: int
    scenario_count: int
    uncovered_rules: tuple[str, ...]
    client_gaps: dict[str, tuple[str, ...]]


def _mapping(value, code, label):
    if not isinstance(value, dict):
        raise CatalogError(code, f"{label} must be a mapping")
    return value


def _sequence(value, code, label):
    if not isinstance(value, list):
        raise CatalogError(code, f"{label} must be a list")
    return value


def _text(value, code, label):
    if not isinstance(value, str) or not value.strip():
        raise CatalogError(code, f"{label} must be non-empty text")
    return value


def _read_yaml(path):
    try:
        value = yaml.safe_load(Path(path).read_text(encoding='utf-8'))
    except (OSError, yaml.YAMLError) as exc:
        raise CatalogError("invalid-yaml", f"Cannot read {path}: {exc}") from exc
    return _mapping(value, "invalid-document", str(path))


def _load_rules(document):
    rules = []
    seen = set()
    for number, raw in enumerate(_sequence(document.get("rules"), "invalid-rules", "rules"), 1):
        value = _mapping(raw, "invalid-rule", f"rule {number}")
        identity = _text(value.get("id"), "invalid-rule-id", f"rule {number} id")
        if not RULE_ID.fullmatch(identity):
            raise CatalogError("invalid-rule-id", f"Invalid rule id: {identity}")
        if identity in seen:
            raise CatalogError("duplicate-rule", f"Duplicate rule id: {identity}")
        seen.add(identity)
        severity = value.get("severity")
        oracle = value.get("oracle")
        required = value.get("required_scenarios")
        if severity not in SEVERITIES:
            raise CatalogError("invalid-severity", f"Invalid severity for {identity}")
        if oracle not in ORACLES:
            raise CatalogError("invalid-oracle", f"Invalid oracle for {identity}")
        if not isinstance(required, int) or isinstance(required, bool) or required < 1:
            raise CatalogError("invalid-required-scenarios",
                               f"Invalid required_scenarios for {identity}")
        rules.append(Rule(identity, _text(value.get("title"), "invalid-title",
                                          f"rule {identity} title"),
                          severity, oracle, required))
    if not rules:
        raise CatalogError("invalid-rules", "At least one rule is required")
    return tuple(rules)


def _expectation_strings(expectations):
    for key in ("required_resources", "forbidden_resources"):
        values = expectations.get(key, [])
        if not isinstance(values, list):
            raise CatalogError("invalid-expectations", f"{key} must be a list")
        for value in values:
            yield _text(value, "invalid-expectations", key)


def _load_scenarios(document, rule_ids):
    scenarios = []
    seen = set()
    for number, raw in enumerate(_sequence(document.get("scenarios"),
                                           "invalid-scenarios", "scenarios"), 1):
        value = _mapping(raw, "invalid-scenario", f"scenario {number}")
        identity = _text(value.get("id"), "invalid-scenario-id",
                         f"scenario {number} id")
        if not SCENARIO_ID.fullmatch(identity):
            raise CatalogError("invalid-scenario-id", f"Invalid scenario id: {identity}")
        if identity in seen:
            raise CatalogError("duplicate-scenario", f"Duplicate scenario id: {identity}")
        seen.add(identity)
        clients = tuple(_sequence(value.get("clients"), "invalid-clients",
                                  f"scenario {identity} clients"))
        unsupported = [client for client in clients if client not in SUPPORTED_CLIENTS]
        if unsupported or len(set(clients)) != len(clients) or not clients:
            raise CatalogError("unsupported-client",
                               f"Unsupported or duplicate clients for {identity}: {unsupported}")
        rules = tuple(_sequence(value.get("rules"), "invalid-scenario-rules",
                                f"scenario {identity} rules"))
        unknown = [rule for rule in rules if rule not in rule_ids]
        if unknown:
            raise CatalogError("unknown-rule", f"Unknown rules for {identity}: {unknown}")
        if len(set(rules)) != len(rules) or not rules:
            raise CatalogError("invalid-scenario-rules",
                               f"Scenario {identity} needs unique rules")
        expectations = _mapping(value.get("expectations", {}),
                                "invalid-expectations", identity)
        prompt = _text(value.get("prompt"), "invalid-prompt", f"scenario {identity} prompt")
        leaked = [item for item in _expectation_strings(expectations) if item in prompt]
        if leaked:
            raise CatalogError("prompt-leaks-expectation",
                               f"Scenario {identity} prompt exposes {leaked}")
        turns = tuple(_sequence(value.get("turns", []), "invalid-turns",
                                f"scenario {identity} turns"))
        if any(not isinstance(turn, dict) for turn in turns):
            raise CatalogError("invalid-turns", f"Scenario {identity} has a non-mapping turn")
        scenarios.append(Scenario(
            identity,
            _text(value.get("title"), "invalid-title", f"scenario {identity} title"),
            clients,
            _text(value.get("fixture"), "invalid-fixture", f"scenario {identity} fixture"),
            prompt,
            turns,
            rules,
            expectations,
        ))
    if not scenarios:
        raise CatalogError("invalid-scenarios", "At least one scenario is required")
    return tuple(scenarios)


def load_catalog(contract_path, scenario_path):
    contract = _read_yaml(contract_path)
    scenarios = _read_yaml(scenario_path)
    if contract.get("version") != 1 or scenarios.get("version") != 1:
        raise CatalogError("unsupported-version", "Behavior catalog version must be 1")
    thresholds = _mapping(contract.get("thresholds"), "invalid-thresholds", "thresholds")
    if set(thresholds) != set(SEVERITIES) or any(
            not isinstance(value, (int, float)) or isinstance(value, bool)
            or not 0 < float(value) <= 1 for value in thresholds.values()):
        raise CatalogError("invalid-thresholds", "Thresholds must define three probabilities")
    rules = _load_rules(contract)
    loaded_scenarios = _load_scenarios(scenarios, {rule.id for rule in rules})
    return Catalog(1, {key: float(value) for key, value in thresholds.items()},
                   rules, loaded_scenarios)


def validate_catalog(catalog):
    coverage = {rule.id: 0 for rule in catalog.rules}
    client_coverage = {
        client: {rule.id: 0 for rule in catalog.rules}
        for client in SUPPORTED_CLIENTS
    }
    required = {rule.id: rule.required_scenarios for rule in catalog.rules}
    for scenario in catalog.scenarios:
        for rule in scenario.rules:
            coverage[rule] += 1
            for client in scenario.clients:
                client_coverage[client][rule] += 1
    uncovered = tuple(sorted(rule for rule, count in coverage.items()
                             if count < required[rule]))
    gaps = {
        client: tuple(sorted(rule for rule, count in rows.items()
                             if count < required[rule]))
        for client, rows in client_coverage.items()
    }
    gaps = {client: rules for client, rules in gaps.items() if rules}
    return CoverageReport(
        "passed" if not uncovered and not gaps else "failed",
        SUPPORTED_CLIENTS,
        len(catalog.rules),
        len(catalog.scenarios),
        uncovered,
        gaps,
    )
