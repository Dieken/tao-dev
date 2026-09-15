"""The native recovery probe must prepare current, valid document templates."""
from acceptance import clients, recovery
from taolib.documents import validate


def test_recovery_fixture_produces_valid_plan_and_handoff(tmp_path):
    plugin = clients.prepare(tmp_path, 'claude')
    report = recovery.prepare(tmp_path, plugin)
    assert (tmp_path / report['plan']).is_file()
    assert (tmp_path / report['handoff']).is_file()
    result = validate(tmp_path, list((tmp_path / 'docs').rglob('*.md')))
    assert result.valid, result.to_dict()
