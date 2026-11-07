"""Packaging must not overwrite user data or follow source symlinks."""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('package_skill', ROOT / 'scripts/package_skill.py')
package = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(package)


def test_existing_output_is_preserved(tmp_path):
    output = tmp_path / 'existing'
    output.mkdir()
    user_file = output / 'notes.md'
    user_file.write_text('do not erase', encoding='utf-8')
    with pytest.raises(ValueError, match='must be new'):
        package.build(output)
    assert user_file.read_text(encoding='utf-8') == 'do not erase'
    assert list(output.iterdir()) == [user_file]


def test_source_subdirectory_is_rejected_without_mutation(tmp_path, monkeypatch):
    source = tmp_path / 'source'
    source.mkdir()
    monkeypatch.setattr(package, 'SOURCE', source)
    with pytest.raises(ValueError, match='outside'):
        package.build(source / 'output')
    assert not (source / 'output').exists()


def test_symlink_source_cannot_leak_external_files(tmp_path, monkeypatch):
    source = tmp_path / 'source'
    source.mkdir()
    (source / 'SKILL.md').write_text('skill', encoding='utf-8')
    private = tmp_path / 'private'
    private.write_text('secret', encoding='utf-8')
    try:
        (source / 'secret').symlink_to(private)
    except OSError:
        pytest.skip('Symlinks are unavailable')
    monkeypatch.setattr(package, 'SOURCE', source)
    with pytest.raises(ValueError, match='symbolic links'):
        package.build(tmp_path / 'output')
    assert not (tmp_path / 'output').exists()
    assert private.read_text(encoding='utf-8') == 'secret'
