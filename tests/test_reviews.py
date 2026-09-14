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
    path = root / "docs/changes/2026-09/20260914-export.md"
    path.write_text(path.read_text().replace("- [ ]", "- [x]"))
    config = root / ".tao/config.toml"
    config.write_text(config.read_text().replace("[verification]", '[verification]\nrequired_reviews = ["independent"]'))
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
                          json.dumps({"type": "result", "subtype": "success", "is_error": False, "session_id": "review-context", "structured_output": conclusion}) + "\n")
    else:
        source.write_text(json.dumps(conclusion))
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
    path.write_text(json.dumps(value))
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
        (tmp_path / "check.py").write_text("print(99)")
    elif mutation == "self":
        value["reviewer"]["context"] = value["author"]["context"]
    elif mutation == "unknown":
        value["requirement"] = "unconfigured"
    elif mutation == "flag":
        value["passed"] = True
    elif mutation == "timestamp":
        value["recorded_at"] = "2099-01-01T00:00:00Z"
    elif mutation == "tampered-source":
        (tmp_path / value["source"]["path"]).write_text("forged")
    elif mutation == "unknown-provider-claim":
        value["reviewer"]["provider"] = "Anthropic"
    else:
        path = tmp_path / value["source"]["path"]
        events = [json.loads(line) for line in path.read_text().splitlines()]
        if mutation == "incomplete-model":
            events[-1]["is_error"] = True
        else:
            events[-1]["structured_output"]["summary"] = "Different result"
        path.write_text("\n".join(json.dumps(event) for event in events))
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
    source.write_text(json.dumps({key: value[key] for key in ("binding", "summary", "findings", "limitations")}))
    value["source"]["sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
    assert submit(tmp_path, value)[0] == 0
    code, result = report(tmp_path, "verify", CHG)
    assert code == 1, result
    assert result["outputs"]["reviews"][0]["state"] == "changes-requested"
    (tmp_path / "check.py").write_text("print(99)")
    assert report(tmp_path, "status", CHG)[1]["outputs"]["reviews"][0]["state"] == "stale"


def test_review_receipt_corruption_fails_closed(tmp_path):
    setup_review(tmp_path)
    value = attestation(tmp_path)
    assert submit(tmp_path, value)[0] == 0
    path = next((tmp_path / "tmp/tao/reviews").rglob("*.json"))
    path.write_text('{"status":"passed"}')
    assert report(tmp_path, "verify", CHG)[0] == 2


def test_review_import_preserves_receipt_changed_during_preparation(tmp_path, monkeypatch):
    setup_review(tmp_path)
    value = attestation(tmp_path)
    assert submit(tmp_path, value)[0] == 0
    receipt = next((tmp_path / 'tmp/tao/reviews').rglob('*.json'))
    source = tmp_path / 'tmp/tao/reimport.json'
    source.write_text(json.dumps(value))
    project = Project(tmp_path)
    confirm_source = reviews.confirm_source

    def concurrent_change(current_project, current_value):
        confirm_source(current_project, current_value)
        receipt.write_text('concurrent receipt')

    monkeypatch.setattr(reviews, 'confirm_source', concurrent_change)
    with pytest.raises(ConflictError):
        reviews.import_review(project, policy(project), CHG, source.relative_to(tmp_path))
    assert receipt.read_text() == 'concurrent receipt'


def test_old_source_cannot_be_rewrapped_with_a_new_input_binding(tmp_path):
    setup_review(tmp_path)
    value = attestation(tmp_path, model=True)
    (tmp_path / 'check.py').write_text('print("different input")')
    value['binding'] = report(tmp_path, 'review', CHG)[1]['outputs']['request']['binding']
    code, result = submit(tmp_path, value)
    assert code == 2, result
    assert 'does not match' in result['diagnostics'][0]['message']


def test_required_review_materials_and_expiry_are_reported(tmp_path):
    setup_review(tmp_path)
    config = tmp_path / '.tao/config.toml'
    config.write_text(config.read_text().replace('[verification]', '[verification]\nrequire_logs = true'))
    value = attestation(tmp_path)
    assert submit(tmp_path, value)[0] == 0
    (tmp_path / value['source']['path']).unlink()
    row = report(tmp_path, 'status', CHG)[1]['outputs']['reviews'][0]
    assert row['state'] == 'materials-missing'
    receipt = tmp_path / row['receipt']
    value['recorded_at'] = '2020-01-01T00:00:00Z'
    receipt.write_text(json.dumps(value))
    assert report(tmp_path, 'status', CHG)[1]['outputs']['reviews'][0]['state'] == 'expired'


def test_model_provider_is_taken_from_observed_usage_when_init_omits_it(tmp_path):
    setup_review(tmp_path)
    value = attestation(tmp_path, model=True)
    path = tmp_path / value['source']['path']
    events = [json.loads(line) for line in path.read_text().splitlines()]
    events[-1]['modelUsage'] = {'observed-model': {'provider': 'firstParty'}}
    path.write_text('\n'.join(json.dumps(event) for event in events))
    value['source']['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    value['reviewer']['provider'] = 'firstParty'
    code, result = submit(tmp_path, value)
    assert code == 0, result
