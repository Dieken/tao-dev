"""Document includes and exclusions share root-relative recursive semantics."""

import json

import pytest

from taolib.project import Project


@pytest.mark.parametrize('exclude,removed', [
    ('vendor/**/*.md', {'vendor/a.md', 'vendor/a/b.md', 'vendor/a/b/c.md'}),
    ('*.md', {'root.md'}),
    ('drafts/*.md', {'drafts/a.md'}),
])
def test_exclusions_match_the_same_root_relative_globs_as_includes(tmp_path, exclude, removed):
    names = {'root.md', 'docs/a.md', 'vendor/a.md', 'vendor/a/b.md', 'vendor/a/b/c.md',
             'drafts/a.md', 'docs/drafts/a.md'}
    for name in names:
        p = tmp_path / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text('fixture', encoding='utf-8')
    (tmp_path / '.tao').mkdir()
    (tmp_path / '.tao/config.toml').write_text('version = 1\n[documents]\ninclude = ["**/*.md"]\nexclude = '
                                             + json.dumps([exclude]) + '\n', encoding='utf-8')
    assert {p.relative_to(tmp_path).as_posix() for p in Project(tmp_path).sources()} == names - removed


@pytest.mark.parametrize('pattern', ['/etc/*.md', 'C:/docs/*.md', '..\\outside\\*.md'])
def test_a_rooted_or_traversing_document_pattern_is_refused_on_every_platform(tmp_path, pattern):
    """A pattern whose own flavour reads as rooted is a configuration error,
    not a glob call: the other flavour raises there instead of reporting it."""
    (tmp_path / '.tao').mkdir()
    (tmp_path / '.tao/config.toml').write_text(
        'version = 1\n[documents]\ninclude = ' + json.dumps([pattern]) + '\n', encoding='utf-8')
    with pytest.raises(ValueError, match='project-relative'):
        Project(tmp_path)


def test_reads_use_existing_defaults_without_creating_configuration(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    project = Project()
    assert project.root == tmp_path
    assert project.sources() == []
    assert project.paths == {"plans": "docs/plans", "retired": "docs/retired", "temporary": "tmp/tao"}
    assert list(tmp_path.iterdir()) == []


def test_temporary_handoffs_are_excluded_even_from_broad_document_scope(tmp_path):
    summary = tmp_path / "scratch/handoffs/summary.md"
    summary.parent.mkdir(parents=True)
    summary.write_text("# Disposable context\n", encoding="utf-8")
    document = tmp_path / "docs/spec.md"
    document.parent.mkdir()
    document.write_text("# Indexed document\n", encoding="utf-8")
    project = Project(tmp_path, config={"version": 1, "documents": {"include": ["**/*.md"]},
                                       "paths": {"temporary": "scratch"}})
    assert project.sources() == [document]


@pytest.mark.parametrize("removed", [{"hooks": {}}, {"paths": {"workflows": "docs/workflows"}}])
def test_removed_engine_configuration_is_rejected(tmp_path, removed):
    with pytest.raises(ValueError):
        Project(tmp_path, config={"version": 1, **removed})
