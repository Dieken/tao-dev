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
        p.write_text('fixture')
    (tmp_path / '.tao').mkdir()
    (tmp_path / '.tao/config.toml').write_text('version = 1\n[documents]\ninclude = ["**/*.md"]\nexclude = '
                                             + json.dumps([exclude]) + '\n')
    assert {p.relative_to(tmp_path).as_posix() for p in Project(tmp_path).sources()} == names - removed
