"""Review gates validate current, traceable attestations, not pass flags."""

import hashlib
import json
from datetime import datetime, timezone

import pytest

from taolib import reviews
from taolib.project import ConflictError, Project
from taolib.verification import policy
from test_verification import configured, report
from test_relationships import CHG


def setup_review(root):
    configured(root)
    path = root / "docs/plans/2026-09/20260914-export.md"
    path.write_text(path.read_text(encoding='utf-8').replace("- [ ]", "- [x]"), encoding='utf-8')
    config = root / ".tao/config.toml"
    config.write_text(config.read_text(encoding='utf-8').replace("[verification]", '[verification]\nrequired_reviews = ["independent"]'), encoding='utf-8')
    return path


def attestation(root, *, model=False):
    code, result = report(root, "review", CHG)
    assert code == 0, result
    binding = result["outputs"]["request"]["binding"]
    source = root / "tmp/tao/review-source.jsonl"
    source.parent.mkdir(parents=True, exist_ok=True)
    conclusion = {"binding": binding, "summary": "Checked overwrite protection and recovery paths.", "findings": [],
                  "limitations": ["Native Windows was not exercised."]}
    if model:
        source.write_text(json.dumps({"type": "system", "subtype": "init", "session_id": "review-context", "model": "observed-model"}) + "\n" +
                          json.dumps({"type": "assistant", "message": {"model": "observed-model"}}) + "\n" +
                          json.dumps({"type": "result", "subtype": "success", "is_error": False, "session_id": "review-context", "structured_output": conclusion}) + "\n", encoding='utf-8')
    else:
        source.write_text(json.dumps(conclusion), encoding='utf-8')
    value = {"schema": "tao.review/v0.1", "requirement": "independent", "binding": binding,
             "input_ref": "fixture snapshot available in this test workspace",
             "recorded_at": datetime.now(timezone.utc).isoformat(),
             "author": {"name": "Author", "context": "author-context"},
             "reviewer": {"kind": "model" if model else "human", "name": "Reviewer", "context": "review-context",
                          "model": "observed-model" if model else None, "provider": "unknown" if model else None},
             "source": {"path": source.relative_to(root).as_posix(), "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                        "format": "claude-stream-json" if model else "human-json"},
             **{key: conclusion[key] for key in ("summary", "findings", "limitations")}}
    return value


def submit(root, value):
    path = root / "tmp/tao/review.json"
    path.write_text(json.dumps(value), encoding='utf-8')
    return report(root, "review", CHG, "--from", str(path.relative_to(root)))


def test_review_request_is_read_only_and_cannot_open_the_gate(tmp_path):
    setup_review(tmp_path)
    code, result = report(tmp_path, "review", CHG)
    assert code == 0, result
    assert "source_digest" in result["outputs"]["request"]["binding"]
    assert not (tmp_path / "tmp").exists()
    assert report(tmp_path, "verify", CHG)[0] == 2


@pytest.mark.parametrize("model", [False, True])
def test_current_attestation_opens_gate_without_reinvoking_reviewer(tmp_path, model):
    setup_review(tmp_path)
    value = attestation(tmp_path, model=model)
    assert submit(tmp_path, value)[0] == 0
    code, result = report(tmp_path, "verify", CHG)
    assert code == 0, result
    assert result["outputs"]["reviews"][0]["state"] == "satisfied"
    assert result["readiness"] == "checks-satisfied"
    (tmp_path / value["source"]["path"]).unlink()
    assert report(tmp_path, "status", CHG)[1]["outputs"]["reviews"][0]["state"] == "satisfied"
    assert report(tmp_path, "verify", CHG)[0] == 0


@pytest.mark.parametrize("mutation", ["stale", "self", "unknown", "flag", "timestamp", "tampered-source", "unknown-provider-claim", "incomplete-model", "different-conclusion"])
def test_invalid_or_unsubstantiated_review_cannot_be_imported(tmp_path, mutation):
    setup_review(tmp_path)
    value = attestation(tmp_path, model=True)
    if mutation == "stale":
        (tmp_path / "check.py").write_text("print(99)", encoding='utf-8')
    elif mutation == "self":
        value["reviewer"]["context"] = value["author"]["context"]
    elif mutation == "unknown":
        value["requirement"] = "unconfigured"
    elif mutation == "flag":
        value["passed"] = True
    elif mutation == "timestamp":
        value["recorded_at"] = "2099-01-01T00:00:00Z"
    elif mutation == "tampered-source":
        (tmp_path / value["source"]["path"]).write_text("forged", encoding='utf-8')
    elif mutation == "unknown-provider-claim":
        value["reviewer"]["provider"] = "Anthropic"
    else:
        path = tmp_path / value["source"]["path"]
        events = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
        if mutation == "incomplete-model":
            events[-1]["is_error"] = True
        else:
            events[-1]["structured_output"]["summary"] = "Different result"
        path.write_text("\n".join(json.dumps(event) for event in events), encoding='utf-8')
        value["source"]["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    assert submit(tmp_path, value)[0] != 0
    assert report(tmp_path, "verify", CHG)[0] != 0


def test_open_blocker_and_source_changes_remain_visible(tmp_path):
    setup_review(tmp_path)
    value = attestation(tmp_path)
    value["findings"] = [{"id": "R1", "severity": "blocker", "location": "check.py:1",
                           "problem": "An invalid input can overwrite output.", "disposition": "open",
                           "rationale": "Reproduce before selecting a correction."}]
    source = tmp_path / value["source"]["path"]
    source.write_text(json.dumps({key: value[key] for key in ("binding", "summary", "findings", "limitations")}), encoding='utf-8')
    value["source"]["sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
    assert submit(tmp_path, value)[0] == 0
    code, result = report(tmp_path, "verify", CHG)
    assert code == 1, result
    assert result["outputs"]["reviews"][0]["state"] == "changes-requested"
    (tmp_path / "check.py").write_text("print(99)", encoding='utf-8')
    assert report(tmp_path, "status", CHG)[1]["outputs"]["reviews"][0]["state"] == "stale"


def test_review_receipt_corruption_fails_closed(tmp_path):
    setup_review(tmp_path)
    value = attestation(tmp_path)
    assert submit(tmp_path, value)[0] == 0
    path = next((tmp_path / "tmp/tao/reviews").rglob("*.json"))
    path.write_text('{"status":"passed"}', encoding='utf-8')
    assert report(tmp_path, "verify", CHG)[0] == 2


def test_review_import_preserves_receipt_changed_during_preparation(tmp_path, monkeypatch):
    setup_review(tmp_path)
    value = attestation(tmp_path)
    assert submit(tmp_path, value)[0] == 0
    receipt = next((tmp_path / 'tmp/tao/reviews').rglob('*.json'))
    source = tmp_path / 'tmp/tao/reimport.json'
    source.write_text(json.dumps(value), encoding='utf-8')
    project = Project(tmp_path)
    confirm_source = reviews.confirm_source

    def concurrent_change(current_project, current_value):
        confirm_source(current_project, current_value)
        receipt.write_text('concurrent receipt', encoding='utf-8')

    monkeypatch.setattr(reviews, 'confirm_source', concurrent_change)
    with pytest.raises(ConflictError):
        reviews.import_review(project, policy(project), CHG, source.relative_to(tmp_path))
    assert receipt.read_text(encoding='utf-8') == 'concurrent receipt'


def test_old_source_cannot_be_rewrapped_with_a_new_input_binding(tmp_path):
    setup_review(tmp_path)
    value = attestation(tmp_path, model=True)
    (tmp_path / 'check.py').write_text('print("different input")', encoding='utf-8')
    value['binding'] = report(tmp_path, 'review', CHG)[1]['outputs']['request']['binding']
    code, result = submit(tmp_path, value)
    assert code == 2, result
    assert 'does not match' in result['diagnostics'][0]['message']


def test_required_review_materials_and_expiry_are_reported(tmp_path):
    setup_review(tmp_path)
    config = tmp_path / '.tao/config.toml'
    config.write_text(config.read_text(encoding='utf-8').replace('[verification]', '[verification]\nrequire_logs = true'), encoding='utf-8')
    value = attestation(tmp_path)
    assert submit(tmp_path, value)[0] == 0
    (tmp_path / value['source']['path']).unlink()
    row = report(tmp_path, 'status', CHG)[1]['outputs']['reviews'][0]
    assert row['state'] == 'materials-missing'
    receipt = tmp_path / row['receipt']
    value['recorded_at'] = '2020-01-01T00:00:00Z'
    receipt.write_text(json.dumps(value), encoding='utf-8')
    assert report(tmp_path, 'status', CHG)[1]['outputs']['reviews'][0]['state'] == 'expired'


def test_model_provider_is_taken_from_observed_usage_when_init_omits_it(tmp_path):
    setup_review(tmp_path)
    value = attestation(tmp_path, model=True)
    path = tmp_path / value['source']['path']
    events = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
    events[-1]['modelUsage'] = {'observed-model': {'provider': 'firstParty'}}
    path.write_text('\n'.join(json.dumps(event) for event in events), encoding='utf-8')
    value['source']['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    value['reviewer']['provider'] = 'firstParty'
    code, result = submit(tmp_path, value)
    assert code == 0, result


def workflow_state(root, runs):
    """A minimal workflow record carrying only what binding() reads."""
    directory = root / ".tao/workflows"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{CHG}.json").write_text(json.dumps({
        "schema": "tao.workflow/v0.1", "change": CHG, "phase": "review", "revision": 1,
        "artifacts": {}, "approvals": {}, "reviews": runs}), encoding='utf-8')


def digest(root):
    project = Project(root)
    return reviews.binding(project, policy(project), CHG)["source_digest"]


def test_reserved_report_outputs_do_not_change_the_reviewed_inputs(tmp_path):
    setup_review(tmp_path)
    reports = tmp_path / "docs/plans/2026-09/20260914-export/reviews/20260914-first"
    reports.mkdir(parents=True)
    history = reports / "01-first-claude.md"
    history.write_text("# earlier round\n", encoding='utf-8')
    workflow_state(tmp_path, {"docs": {"runs": [
        {"request": {"output_files": [history.relative_to(tmp_path).as_posix()]}},
        {"request": {"output_files": ["docs/plans/2026-09/20260914-export/reviews/20260914-first/02-recheck-claude.md"]}},
    ]}})
    other = tmp_path / "docs/plans/2026-09/20260914-export/reviews/20260901-earlier"
    other.mkdir(parents=True)
    elsewhere = other / "01-earlier-claude.md"
    elsewhere.write_text("# another batch\n", encoding='utf-8')
    before = digest(tmp_path)
    current = reports / "02-recheck-claude.md"
    current.write_text("# this round's report\n", encoding='utf-8')
    assert digest(tmp_path) == before, "writing this round's declared output must not move the binding"
    current.write_text("# this round's report, revised\n", encoding='utf-8')
    assert digest(tmp_path) == before
    # The adjudication and the batch navigation page are equally this batch's
    # own records, and completing a round requires both.
    (reports / "00-adjudication.md").write_text("# adjudication\n", encoding='utf-8')
    (reports / "index.md").write_text("# batch\n", encoding='utf-8')
    assert digest(tmp_path) == before
    # An earlier round of the same batch is also this batch's record.
    history.write_text("# earlier round, edited\n", encoding='utf-8')
    assert digest(tmp_path) == before
    # Another batch's report is history; changing it does expire a result.
    elsewhere.write_text("# another batch, edited\n", encoding='utf-8')
    assert digest(tmp_path) != before


def test_binding_excludes_nothing_without_readable_workflow_state(tmp_path):
    setup_review(tmp_path)
    reports = tmp_path / "docs/plans/2026-09/20260914-export/reviews/20260914-first"
    reports.mkdir(parents=True)
    declared = "docs/plans/2026-09/20260914-export/reviews/20260914-first/01-first-claude.md"
    assert reviews.declared_outputs(Project(tmp_path), CHG) == []
    before = digest(tmp_path)
    (tmp_path / declared).write_text("# report\n", encoding='utf-8')
    assert digest(tmp_path) != before, "with no state to declare it, a new report is an ordinary input"
    (tmp_path / f".tao/workflows/{CHG}.json").parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / f".tao/workflows/{CHG}.json").write_text("{not json", encoding='utf-8')
    assert reviews.declared_outputs(Project(tmp_path), CHG) == []
    workflow_state(tmp_path, {"docs": {"runs": [{"request": {"output_files": [declared]}}]}})
    assert digest(tmp_path) == before


def test_excluding_every_input_still_fails_closed(tmp_path):
    """The guard lives where the exclusion is applied; an exclusion that empties
    the scope is a configuration error, not a scope that passes by default."""
    from taolib.verification import snapshot
    setup_review(tmp_path)
    project = Project(tmp_path)
    names = [path.relative_to(tmp_path).as_posix()
             for pattern in policy(project)["inputs"] for path in tmp_path.glob(pattern) if path.is_file()]
    with pytest.raises(ValueError):
        snapshot(project, policy(project), exclude=names + [".tao/config.toml"])


@pytest.mark.parametrize("runs", ['"text"', '["not-a-dict"]', '[{"request": 7}]', '[{"request": {"output_files": 3}}]',
                                  '[{}]', '[]', '{"round": 1}'])
def test_malformed_but_parseable_workflow_state_excludes_nothing(tmp_path, runs):
    setup_review(tmp_path)
    before = digest(tmp_path)
    directory = tmp_path / ".tao/workflows"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{CHG}.json").write_text(
        '{"schema": "tao.workflow/v0.1", "change": "%s", "phase": "review", "revision": 1,'
        ' "artifacts": {}, "approvals": {}, "reviews": {"docs": {"runs": %s}}}' % (CHG, runs), encoding='utf-8')
    assert reviews.declared_outputs(Project(tmp_path), CHG) == []
    assert digest(tmp_path) == before


@pytest.mark.parametrize("change,requirement", [
    ("../../escape", "independent"), ("CHG/../../x", "independent"), ("/etc", "independent"),
    (CHG, "../secret"), (CHG, "Independent"), (CHG, ""), ("", "independent"),
    ("CHG_20260914_lowercase0000000", "independent"),
])
def test_review_record_paths_reject_identities_that_are_not_indexed(tmp_path, change, requirement):
    """Both parts become path segments; containment alone would still allow a
    record to land outside the reviews directory."""
    with pytest.raises(ValueError):
        reviews.path_for(Project(tmp_path), change, requirement)


def test_review_record_path_stays_inside_the_reviews_directory(tmp_path):
    setup_review(tmp_path)
    project = Project(tmp_path)
    path = reviews.path_for(project, CHG, "independent")
    assert path.resolve().parent == (project.output("temporary", f"reviews/{CHG}")).resolve()


@pytest.mark.parametrize("change", ["../../escape", "CHG/../../x", "not-an-id", "CHG_20260914_lowercase0000000"])
def test_status_reports_a_row_state_for_an_identity_it_cannot_locate(tmp_path, change):
    """Locating a record is part of reading it, so a rejected identity is a
    row state; nothing in this module may raise at the caller."""
    setup_review(tmp_path)
    rows = reviews.status(Project(tmp_path), policy(Project(tmp_path)), change)
    assert [row["state"] for row in rows] == ["invalid"]
