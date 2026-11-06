"""Prospective record admission must agree with managed-source discovery."""
from pathlib import Path
import pytest
from taolib.project import Project, ConfigurationError
from taolib import workflows


@pytest.mark.parametrize('pattern',['docs/**/*.md','docs/*/*.md','*.md','**/*.md','docs/**','docs/**/','docs/**/workflows/*.md'])
def test_prospective_file_patterns_agree_with_real_glob(tmp_path,pattern):
    project=Project(tmp_path)
    names=['root.md','docs/root.md','docs/workflows/record.md','docs/eng/workflows/record.md','other/record.md']
    before={name:project.matches_file(Path(name),pattern) for name in names}
    for name in names:
        path=tmp_path/name;path.parent.mkdir(parents=True,exist_ok=True);path.touch()
    selected=set(tmp_path.glob(pattern))
    assert before=={name:tmp_path/name in selected for name in names}


def test_nested_workflow_directory_is_discovered_after_start(tmp_path):
    project=Project(tmp_path,config={'version':1,'paths':{'workflows':'docs/eng/workflows'}})
    state=workflows.start(project,'nested','Nested workflow','en','Synthetic test authorization')
    record=tmp_path/'docs/eng/workflows'/f"{state['change']}.md"
    assert record in project.sources()


def test_recursive_exclusion_rejects_record_before_publication(tmp_path):
    project=Project(tmp_path,config={'version':1,'paths':{'workflows':'docs/eng/workflows'},
                                    'documents':{'include':['docs/eng/workflows/*.md'],'exclude':['docs/**/*.md']}})
    with pytest.raises(ConfigurationError,match='outside managed'):
        workflows.start(project,'excluded','Excluded workflow','en','Synthetic test authorization')
    assert not list(tmp_path.rglob('CHG_*.md'))
    assert not list(tmp_path.rglob('CHG_*.json'))


def test_recursive_pattern_does_not_follow_a_directory_symlink(tmp_path):
    target=tmp_path/'target';target.mkdir();docs=tmp_path/'docs';docs.mkdir()
    link=docs/'linked'
    try:link.symlink_to(target,target_is_directory=True)
    except OSError:pytest.skip('Directory symlink creation unavailable')
    project=Project(tmp_path)
    relative=Path('docs/linked/workflows/record.md')
    assert not project.matches_file(relative,'docs/**/*.md')
    assert project.matches_file(relative,'docs/linked/**/*.md')
