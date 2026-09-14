"""Language selection changes display text, never validation meaning or scope."""

import json
import os
import subprocess
import sys

from taolib.documents import ASSETS, validate
from test_cli import project, run


def broken(root):
    project(root)
    path = root / 'docs/spec.md'
    path.write_text(path.read_text().replace('<!-- tao:field acceptance -->', '<!-- tao:field wrong -->'))
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
    (tmp_path / '.tao/config.toml').write_text('version = 1\nlocale = "zh-Hans"\n[ui]\nlocale = "en"\n')
    en = run(tmp_path, 'verify', '--only', 'docs')
    zh = run(tmp_path, '--diagnostic-locale', 'zh-Hans', 'verify', '--only', 'docs')
    assert en.returncode == zh.returncode == 1
    for result, language in ((en, 'en'), (zh, 'zh-Hans')):
        report = json.loads(result.stdout)
        assert report['diagnostics'][0]['message_locale'] == language
        assert report['diagnostics'] == report['outputs']['documents']['diagnostics']
    assert before == path.read_bytes()


def test_cli_errors_use_requested_language_and_unknown_locale_reports_fallback(tmp_path):
    zh = json.loads(run(tmp_path, 'verify', '--only', '', '--diagnostic-locale=zh-Hans').stdout)
    fr = json.loads(run(tmp_path, 'verify', '--only', '', '--diagnostic-locale=fr').stdout)
    assert zh['diagnostics'][0]['message_locale'] == 'zh-Hans'
    item = fr['diagnostics'][0]
    assert item['message_locale'] == 'en' and item['locale_fallback'] is True
    assert item['requested_locale'] == 'fr'


def test_standard_library_bootstrap_localizes_without_preparing_runtime(tmp_path):
    env = os.environ | {'TAO_RUNTIME_DIR': str(tmp_path / 'unprepared')}
    result = subprocess.run([sys.executable, str(ASSETS.parent / 'scripts/tao.py'),
                             '--diagnostic-locale=zh-Hans', 'verify', '--format=json'],
                            capture_output=True, text=True, env=env)
    report = json.loads(result.stdout)
    assert result.returncode == 2 and report['command'] == 'verify'
    assert report['diagnostics'][0]['message_locale'] == 'zh-Hans'
    assert not (tmp_path / 'unprepared').exists()


def test_bootstrap_reports_failure_when_tomllib_is_unavailable(tmp_path):
    entry = ASSETS.parent / 'scripts/tao.py'
    code = '''import runpy, sys
class NoTomllib:
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "tomllib":
            raise ModuleNotFoundError("tomllib unavailable")
sys.meta_path.insert(0, NoTomllib())
sys.argv = [sys.argv[1], "doctor", "--format=json"]
runpy.run_path(sys.argv[0], run_name="__main__")
'''
    env = os.environ | {'TAO_PYTHON': str(tmp_path / 'missing-python')}
    result = subprocess.run([sys.executable, '-I', '-c', code, str(entry)],
                            capture_output=True, text=True, env=env)
    assert result.returncode == 2, result.stderr
    assert json.loads(result.stdout)['diagnostics'][0]['rule_id'] == 'TAO-RUNTIME-001'


def test_standalone_validator_accepts_diagnostic_language(tmp_path):
    broken(tmp_path)
    result = subprocess.run([sys.executable, str(ASSETS.parent / 'scripts/validate_documents.py'),
                             '--project', str(tmp_path), '--format', 'json',
                             '--diagnostic-locale', 'en', 'docs/spec.md'], capture_output=True, text=True)
    assert result.returncode == 1, result.stderr
    assert json.loads(result.stdout)['diagnostics'][0]['message_locale'] == 'en'


def test_missing_message_translation_is_honest_and_preserves_external_details():
    from tao_messages import Message, diagnostic
    item = diagnostic(Message('External failure: {arg0}', 'raw ENGLISH detail'), 'zh-Hans')
    assert item['message_locale'] == 'en' and item['locale_fallback'] is True
    assert item['parameters'] == {'arg0': 'raw ENGLISH detail'}
    assert item['message'] == 'External failure: raw ENGLISH detail'


def test_nested_owned_errors_translate_without_changing_raw_parameters():
    from tao_messages import Message, diagnostic
    error = ValueError(Message('Supported Python versions: {arg0} to below {arg1}', [3, 11], [3, 15]))
    message = Message('Python is unavailable or unsupported: {arg0}', error)
    zh, en = diagnostic(message, 'zh-Hans'), diagnostic(message, 'en')
    assert '支持的 Python 版本' in zh['message']
    assert zh['parameters'] == en['parameters']


def test_localization_has_no_process_global_language_state(tmp_path):
    broken(tmp_path)
    def run_one(locale):
        return validate(tmp_path, ['docs/spec.md'], diagnostic_locale=locale).diagnostics[0].message_locale
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor() as pool:
        assert list(pool.map(run_one, ['en', 'zh-Hans'] * 5)) == ['en', 'zh-Hans'] * 5


def test_catalogue_covers_owned_diagnostics_and_preserves_placeholder_sets():
    import ast
    from string import Formatter
    catalogue = json.loads((ASSETS / 'locales/diagnostics.zh-Hans.json').read_text())
    def fields(text):
        return {name for _, name, _, _ in Formatter().parse(text) if name is not None}
    for source, translated in catalogue.items():
        assert translated and fields(source) == fields(translated), source
    for path in (ASSETS.parent / 'scripts').rglob('*.py'):
        for node in ast.walk(ast.parse(path.read_text())):
            if not isinstance(node, ast.Call):
                continue
            name = node.func.id if isinstance(node.func, ast.Name) else node.func.attr if isinstance(node.func, ast.Attribute) else ''
            index = 3 if name == 'error' and len(node.args) >= 4 else 4 if name == 'Diagnostic' else 0 if name in ('Message', 'ConfigurationError', 'ConflictError', 'RuntimeFailure', 'ValueError', 'display') else None
            if index is None or len(node.args) <= index:
                continue
            argument = node.args[index]
            assert not isinstance(argument, ast.JoinedStr), (path, node.lineno)
            if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
                assert argument.value in catalogue, (path, node.lineno, argument.value)


def test_hook_uses_ui_language_and_invalidates_cached_translations(tmp_path, monkeypatch):
    from taolib.hook import run as hook
    broken(tmp_path)
    (tmp_path / '.tao').mkdir()
    config = tmp_path / '.tao/config.toml'
    config.write_text('version = 1\n[ui]\nlocale = "zh-Hans"\n[hooks]\ntimeout_seconds = 30\n')
    monkeypatch.chdir(tmp_path)
    first = hook({'hook_event_name': 'PostToolUse'})['hookSpecificOutput']['additionalContext']
    assert '仅检查文档' in first and '期望字段' in first
    config.write_text(config.read_text().replace('zh-Hans', 'en'))
    second = hook({'hook_event_name': 'PostToolUse'})['hookSpecificOutput']['additionalContext']
    assert 'docs only' in second and 'Expected fields' in second
