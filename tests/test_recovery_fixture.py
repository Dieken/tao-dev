"""The native recovery probe must prepare current, valid document templates."""
import subprocess

from acceptance import clients, recovery
from taolib.documents import validate


def test_recovery_fixture_produces_valid_plan_and_handoff(tmp_path):
    plugin = clients.prepare(tmp_path, 'claude')
    report = recovery.prepare(tmp_path, plugin)
    assert (tmp_path / report['plan']).is_file()
    assert (tmp_path / report['handoff']).is_file()
    plan_text = (tmp_path / report['plan']).read_text(encoding='utf-8')
    assert '  - evidence: [Verification](#DOC_' in plan_text
    assert '--verification)' in plan_text
    result = validate(tmp_path, list((tmp_path / 'docs').rglob('*.md')))
    assert result.valid, result.to_dict()



def test_recovery_fixture_supports_git_repository_without_head(tmp_path):
    subprocess.run(['git', 'init', '--quiet', str(tmp_path)], check=True)
    plugin = clients.prepare(tmp_path, 'claude')
    report = recovery.prepare(tmp_path, plugin)
    assert (tmp_path / report['plan']).is_file()
    assert (tmp_path / report['handoff']).is_file()
