"""Git-specific workspace operations; ordinary document checks need no VCS."""
import subprocess
from pathlib import Path

from tao_messages import Message

from .project import ConfigurationError, ConflictError, Project, contained, create_file


def run(root, *args, required=True):
    try:
        result = subprocess.run(['git', '-C', str(root), *args], capture_output=True,
                                timeout=30, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        if not required:
            return None
        raise ConfigurationError(Message('Git operation unavailable: {arg0}', str(exc))) from exc
    if result.returncode:
        if not required:
            return None
        raise ConfigurationError(result.stderr.decode(errors='replace').strip())
    return result.stdout.decode('utf-8', errors='surrogateescape').strip()


def context(root):
    top = run(root, 'rev-parse', '--show-toplevel', required=False)
    if not top or Path(top).resolve() != root.resolve():
        return None
    return {'branch': run(root, 'branch', '--show-current'),
            'base_commit': run(root, 'rev-parse', 'HEAD', required=False),
            'base_branch': run(root, 'branch', '--show-current')}


def roots(project):
    """Only discover workspaces registered with this repository, not arbitrary links."""
    found = [project.root]
    if not context(project.root):
        return found
    listing = run(project.root, 'worktree', 'list', '--porcelain', '-z')
    for item in listing.split('\0'):
        if item.startswith('worktree '):
            root = Path(item[9:]).resolve()
            if root.is_dir() and root not in found:
                found.append(root)
    return found


def prepare(project, slug):
    info = context(project.root)
    if info is None:
        raise ConfigurationError('The complete worktree workflow requires a Git repository with an initial commit.')
    git_dir = Path(run(project.root, 'rev-parse', '--absolute-git-dir')).resolve()
    common = Path(run(project.root, 'rev-parse', '--path-format=absolute', '--git-common-dir')).resolve()
    if git_dir != common and not run(project.root, 'rev-parse', '--show-superproject-working-tree'):
        # Existing host-managed worktree: record this baseline, do not nest another.
        return project, info
    if run(project.root, 'status', '--porcelain', '--untracked-files=no'):
        raise ConflictError('Tracked changes exist. Commit or select an existing isolated workspace before creating a worktree.')
    if run(project.root, 'check-ignore', '.worktrees/probe', required=False) is None:
        raise ConfigurationError('Ignore /.worktrees/ in the project before creating a local worktree.')
    target = contained(project.root, Path('.worktrees') / slug)
    if target.exists():
        raise ConflictError('Worktree destination exists; inspect and resume it or choose another slug.')
    branch = 'tao/' + slug
    run(project.root, 'worktree', 'add', '-b', branch, str(target))
    # A local setup configuration may intentionally be untracked.
    source = project.root / '.tao/config.toml'
    destination = target / '.tao/config.toml'
    if source.is_file() and not destination.exists():
        create_file(target, destination, source.read_text(encoding='utf-8'))
    return Project(target), info | {'branch': branch}
