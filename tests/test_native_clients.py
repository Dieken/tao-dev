"""Project deployment is separate from actual, non-billable native discovery."""

import os

import pytest

import native_clients
from acceptance import project_skills


def test_native_readiness_only_requires_executable(monkeypatch):
    monkeypatch.setattr(native_clients.shutil, "which", lambda name: "/installed/" + name)
    for client in native_clients.CLI:
        assert native_clients.cli_skip_reason(client) is None


def test_native_readiness_reports_missing_cli(monkeypatch):
    monkeypatch.setattr(native_clients.shutil, "which", lambda name: None)
    for client in native_clients.CLI:
        assert "not installed" in native_clients.cli_skip_reason(client)
    with pytest.raises(pytest.skip.Exception, match="not installed"):
        native_clients.require_cli("codex")


def test_unknown_native_client_is_rejected():
    with pytest.raises(ValueError, match="Unknown native client"):
        native_clients.cli_skip_reason("unknown")


@pytest.mark.skipif(os.environ.get("TAO_NATIVE_ACCEPTANCE") != "1",
                    reason="Native discovery is explicit; set TAO_NATIVE_ACCEPTANCE=1")
def test_codex_discovers_only_copied_project_skill():
    native_clients.require_cli("codex")
    assert project_skills.run("codex", native=True)["native_discovery"] == "passed"
