"""Language selection changes display text, never validation meaning or scope."""

import json
import subprocess
import sys

from taolib.documents import ASSETS, validate
from test_cli import project, run


def broken(root):
    project(root)
    path = root / 'docs/spec.md'
    path.write_text(path.read_text(encoding='utf-8').replace(':verifies: REQ_', ':verifies: DOC_'), encoding='utf-8')
    return path


def test_document_locale_and_explicit_override_preserve_machine_diagnostics(tmp_path):
    broken(tmp_path)
    zh = validate(tmp_path, ['docs/spec.md']).to_dict()['diagnostics']
    en = validate(tmp_path, ['docs/spec.md'], diagnostic_locale='en').to_dict()['diagnostics']
    assert zh and len(zh) == len(en)
    for left, right in zip(zh, en):
        assert left['message_locale'] == 'zh-Hans'
        assert right['message_locale'] == 'en'
        assert left['message'] != right['message']
        assert left['suggestion'] != right['suggestion']
        for key in ('rule_id', 'severity', 'path', 'line', 'column', 'parameters'):
            assert left[key] == right[key]


def test_cli_ui_locale_and_explicit_option_are_independent_of_document_locale(tmp_path):
    path = broken(tmp_path)
    before = path.read_bytes()
    (tmp_path / '.tao').mkdir()
    (tmp_path / '.tao/config.toml').write_text('version = 1\nlocale = "zh-Hans"\n[ui]\nlocale = "en"\n', encoding='utf-8')
    en = run(tmp_path, 'verify')
    zh = run(tmp_path, '--diagnostic-locale', 'zh-Hans', 'verify')
    assert en.returncode == zh.returncode == 1
    for result, language in ((en, 'en'), (zh, 'zh-Hans')):
        report = json.loads(result.stdout)
        assert report['diagnostics'][0]['message_locale'] == language
        assert 'diagnostics' not in report['outputs']['documents']
    assert before == path.read_bytes()


def test_cli_errors_use_requested_language_and_unknown_locale_reports_fallback(tmp_path):
    zh = json.loads(run(tmp_path, 'verify', '--diagnostic-locale=zh-Hans').stdout)
    fr = json.loads(run(tmp_path, 'verify', '--diagnostic-locale=fr').stdout)
    assert zh['diagnostics'][0]['message_locale'] == 'zh-Hans'
    item = fr['diagnostics'][0]
    assert item['message_locale'] == 'en' and item['locale_fallback'] is True
    assert item['requested_locale'] == 'fr'


def test_standalone_validator_accepts_diagnostic_language(tmp_path):
    broken(tmp_path)
    result = subprocess.run([sys.executable, str(ASSETS.parent / 'scripts/validate_documents.py'),
                             '--project', str(tmp_path), '--format', 'json',
                             '--diagnostic-locale', 'en', 'docs/spec.md'], capture_output=True, text=True, encoding='utf-8')
    assert result.returncode == 1, result.stderr
    assert json.loads(result.stdout)['diagnostics'][0]['message_locale'] == 'en'


def test_missing_message_translation_is_honest_and_preserves_external_details():
    from tao_messages import Message, diagnostic
    item = diagnostic(Message('External failure: {arg0}', 'raw ENGLISH detail'), 'zh-Hans')
    assert item['message_locale'] == 'en' and item['locale_fallback'] is True
    assert item['parameters'] == {'arg0': 'raw ENGLISH detail'}
    assert item['message'] == 'External failure: raw ENGLISH detail'


def test_localization_has_no_process_global_language_state(tmp_path):
    broken(tmp_path)
    def run_one(locale):
        return validate(tmp_path, ['docs/spec.md'], diagnostic_locale=locale).diagnostics[0].message_locale
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor() as pool:
        assert list(pool.map(run_one, ['en', 'zh-Hans'] * 5)) == ['en', 'zh-Hans'] * 5


