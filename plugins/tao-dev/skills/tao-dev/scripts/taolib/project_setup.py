"""Read-only tool discovery and explicit, validated project configuration."""
import json
import os
from pathlib import Path
import re
import shutil
import tomllib

from .project import Project, ConfigurationError, ConflictError, contained, create_file, replace_file, mutation_lock
from .verification import policy, file_digest

EXCLUDED = {'.git', '.hg', '.svn', '.worktrees', '.venv', 'venv', 'node_modules', 'vendor', 'target', 'build', 'dist', '__pycache__', '.tao', 'tmp'}
MANIFESTS = {'pyproject.toml', 'requirements.txt', 'package.json', 'Cargo.toml', 'go.mod', 'Makefile'}


def inspect(project):
    stacks, candidates, warnings, sources = [], [], [], []
    scanned = 0

    def candidate(name, argv, source):
        executable = argv[0]
        located = str(contained(project.root, executable)) if '/' in executable or '\\' in executable else shutil.which(executable)
        candidates.append({'id': name, 'argv': argv, 'source': source, 'execution': 'not_run',
                           'executable_available': bool(located and Path(located).is_file()),
                           'tool_installed': 'unknown'})

    for directory, children, files in os.walk(project.root, followlinks=False):
        children[:] = sorted(d for d in children if d not in EXCLUDED and not (Path(directory)/d).is_symlink())
        scanned += 1
        if scanned > 1000:
            warnings.append('Directory scan limited to 1000 entries; inspect remaining modules explicitly.')
            break
        parent = Path(directory)
        relative = parent.relative_to(project.root).as_posix()
        prefix = '' if relative == '.' else relative+'/'
        for name in sorted(MANIFESTS & set(files)):
            path = contained(project.root, prefix+name)
            if path.is_symlink():
                warnings.append(f'Skipped symlink manifest: {prefix+name}')
                continue
            if path.stat().st_size > 1024*1024:
                warnings.append(f'Skipped manifest over 1 MiB: {prefix+name}')
                continue
            sources.append(prefix+name)
            try:
                source = path.read_text(encoding='utf-8')
                if name in ('pyproject.toml', 'requirements.txt'):
                    data = tomllib.loads(source) if name.endswith('.toml') else {}
                    stacks.append({'language': 'python', 'root': relative, 'manifest': prefix+name})
                    python = next((prefix+p for p in ('.venv/bin/python', '.venv/Scripts/python.exe') if (parent/p).is_file()), None)
                    # A missing project interpreter is reported, not substituted
                    # with tao's own runtime or a globally installed test tool.
                    argv = [python or prefix+('.venv/Scripts/python.exe' if os.name == 'nt' else '.venv/bin/python'), '-m']
                    tools = data.get('tool', {})
                    for tool, args in [('pytest', []), ('ruff', ['check', '.']), ('mypy', ['.'])]:
                        if relative == '.' and (tool in tools or re.search(r'\b'+tool+r'\b', source)):
                            candidate('python-'+tool, argv+[tool]+args, prefix+name)
                elif name == 'package.json':
                    data = json.loads(source)
                    stacks.append({'language': 'javascript', 'root': relative, 'manifest': prefix+name})
                    manager = 'pnpm' if (parent/'pnpm-lock.yaml').exists() else 'yarn' if (parent/'yarn.lock').exists() else 'npm'
                    for script in data.get('scripts', {}):
                        if script in ('test', 'lint', 'typecheck', 'check', 'build'):
                            location = [] if relative == '.' else ['--dir' if manager == 'pnpm' else '--cwd' if manager == 'yarn' else '--prefix', relative]
                            candidate(script, [manager]+location+['run', script], prefix+name)
                elif name == 'Cargo.toml':
                    tomllib.loads(source)
                    stacks.append({'language': 'rust', 'root': relative, 'manifest': prefix+name})
                    candidate('rust-tests', ['cargo', 'test', '--manifest-path', prefix+name], prefix+name)
                elif name == 'go.mod':
                    stacks.append({'language': 'go', 'root': relative, 'manifest': prefix+name})
                    candidate('go-tests', ['go', '-C', relative, 'test', './...'], prefix+name)
                else:
                    for target in ('test', 'check', 'lint'):
                        if re.search(r'^'+target+r'\s*:', source, re.M):
                            candidate('make-'+target, ['make', '-C', relative, target], prefix+name)
            except (ValueError, UnicodeError, TypeError, AttributeError) as exc:
                warnings.append(f'Cannot interpret {prefix+name}: {type(exc).__name__}; inspect it manually.')
    config_path = project.root / '.tao/config.toml'
    configured = policy(project)
    ci = sorted(p.relative_to(project.root).as_posix() for p in (project.root/'.github/workflows').glob('*') if p.is_file())
    if (project.root/'.gitlab-ci.yml').is_file():
        ci.append('.gitlab-ci.yml')
    return {'project': str(project.root), 'stacks': stacks, 'candidates': candidates,
            'configured_checks': configured['checks'] if configured else [],
            'config_digest': file_digest(config_path) if config_path.is_file() else None, 'ci_files': ci, 'manifests': sources,
            'warnings': warnings, 'coverage': 'partial' if warnings else 'supported manifests',
            'instruction': 'Read manifests and CI before selecting commands. Candidates were not executed; do not infer installed packages from executable availability.'}


def configure(project, source, expected=None):
    draft = contained(project.root, source)
    content = draft.read_text(encoding='utf-8')
    parsed = tomllib.loads(content)
    if parsed.get('version') != 1:
        raise ConfigurationError('Project configuration requires version = 1.')
    candidate = Project(project.root, config=parsed)
    policy(candidate)
    destination = contained(project.root, '.tao/config.toml')
    before = destination.read_bytes() if destination.exists() else None
    if before is not None and tomllib.loads(before.decode('utf-8')) == parsed:
        return {'state': 'unchanged', 'path': '.tao/config.toml', 'config_digest': file_digest(destination), 'written': []}
    if before is not None and (not expected or file_digest(destination) != expected):
        raise ConflictError('Inspect the existing configuration and supply its current digest before replacing it.')
    if before is None and expected:
        raise ConflictError('The expected configuration no longer exists.')
    with mutation_lock(project):
        if before is None:
            create_file(project.root, destination, content)
        else:
            replace_file(project.root, destination, content, before)
    return {'state': 'configured', 'path': '.tao/config.toml', 'config_digest': file_digest(destination),
            'written': ['.tao/config.toml'], 'checks_executed': False}
