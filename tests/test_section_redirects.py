"""Old section URLs resolve to validated current chapters, including retired docs."""

import json
import re

import pytest
from py_mini_racer import MiniRacer

from taolib.project import Project, ConfigurationError
from taolib.publication import build
from test_cli import run
from test_documents import DOC
from test_publication import project, Page


OLD_DOC = 'DOC_20260913_0000000000000070'
OLD_SECTION = OLD_DOC + '--old-requirements'
NEW_SECTION = DOC + '--requirements'


def configured(root, target=NEW_SECTION):
    project(root)
    path = root / '.tao/config.toml'
    path.write_text(path.read_text() + f'\n[documents.section_redirects]\n"{OLD_SECTION}" = "{target}"\n')
    retired = root / 'docs/retired'
    retired.mkdir()
    (retired / '20260914.jsonl').write_text(json.dumps({'id': OLD_DOC, 'retired_on': '2026-09-14', 'reason': 'Content moved to the current specification.', 'replaced_by': [DOC]}) + '\n')
    return Project(root)


def resolve(page, fragment):
    scripts = re.findall(r'<script>(.*?)</script>', page, re.S)
    assert scripts, 'Resolver page must contain an executable redirect script.'
    code = ('let redirects=[];let location={hash:' + json.dumps(fragment)
            + ',replace(value){redirects.push(value);}};\n'
            + '\n'.join(scripts) + '\nJSON.stringify(redirects);')
    with MiniRacer() as engine:
        return json.loads(engine.eval(code, timeout_sec=5))


def test_resolver_executes_without_external_node(monkeypatch):
    monkeypatch.setenv('PATH', '')
    assert resolve('<script>location.replace("../docs/current.html#target");</script>', '#old') == ['../docs/current.html#target']


def test_old_retired_section_redirects_and_has_a_readable_fallback(tmp_path):
    config = configured(tmp_path)
    output = build(config)
    root = tmp_path / output['directory']
    page = (root / f'refs/{OLD_DOC}.html').read_text()
    target = '../docs/spec.html#' + NEW_SECTION
    assert resolve(page, '#' + OLD_SECTION) == [target]
    assert resolve(page, '#' + OLD_SECTION.replace('_', '%5F')) == [target]
    assert resolve(page, '#' + OLD_DOC) == []
    link = next(a for a in Page(page).links if a['href'] == target)
    assert '需求' in link['text']
    (tmp_path / 'docs/spec.md').rename(tmp_path / 'docs/current.md')
    nav = tmp_path / 'docs/index.md'
    nav.write_text(nav.read_text().replace('spec.md', 'current.md'))
    build(config)
    page = (root / f'refs/{OLD_DOC}.html').read_text()
    assert resolve(page, '#' + OLD_SECTION) == ['../docs/current.html#' + NEW_SECTION]


@pytest.mark.parametrize('target', [DOC + '--unknown-section', OLD_SECTION, 'REQ_20260914_0000000000000010--scope'])
def test_bad_redirect_cannot_pass_docs_or_replace_the_previous_book(tmp_path, target):
    config = configured(tmp_path)
    output = build(config)
    resolver = tmp_path / output['directory'] / f'refs/{OLD_DOC}.html'
    before = resolver.read_bytes()
    path = tmp_path / '.tao/config.toml'
    path.write_text(path.read_text().replace('= "' + NEW_SECTION + '"', '= "' + target + '"'))
    result = run(tmp_path, 'verify', '--only', 'docs')
    assert result.returncode == 1, result.stdout
    assert json.loads(result.stdout)['diagnostics']
    with pytest.raises(ConfigurationError):
        build(Project(tmp_path))
    assert resolver.read_bytes() == before


def test_redirects_must_point_directly_to_the_final_section(tmp_path):
    configured(tmp_path)
    path = tmp_path / '.tao/config.toml'
    path.write_text(path.read_text() + f'"{NEW_SECTION}" = "{DOC}--scope"\n')
    result = run(tmp_path, 'verify', '--only', 'docs')
    assert result.returncode == 1, result.stdout


def test_retirement_cannot_delete_a_redirect_destination(tmp_path):
    configured(tmp_path)
    config = tmp_path / '.tao/config.toml'
    config.write_text(config.read_text().replace('book_root = \"docs/index.md\"\n', ''))
    (tmp_path / 'docs/index.md').unlink()
    source = tmp_path / 'docs/spec.md'
    before = source.read_bytes()
    result = run(tmp_path, 'retire', DOC, '--reason', 'Remove target.', '--apply')
    assert result.returncode == 1, result.stdout
    assert source.read_bytes() == before


def test_active_document_keeps_default_routes_and_redirects_selected_sections(tmp_path):
    configured(tmp_path)
    config = tmp_path / '.tao/config.toml'
    config.write_text(config.read_text() + f'"{DOC}--terms" = "{NEW_SECTION}"\n')
    output = build(Project(tmp_path))
    page = (tmp_path / output['directory'] / f'refs/{DOC}.html').read_text()
    assert resolve(page, '#' + DOC + '--terms') == ['../docs/spec.html#' + NEW_SECTION]
    assert resolve(page, '#' + DOC + '--scope') == ['../docs/spec.html#' + DOC + '--scope']
    assert resolve(page, '#%ZZ') == ['../docs/spec.html#%ZZ']
