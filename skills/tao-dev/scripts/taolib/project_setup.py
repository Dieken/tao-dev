"""Read-only document settings and explicit, validated project configuration."""
import tomllib

from .project import (Project, ConfigurationError, ConflictError, contained,
                      create_file, replace_file, mutation_lock, file_digest)


def inspect(project):
    config_path = contained(project.root, '.tao/config.toml')
    return {'project': str(project.root), 'locale': project.locale,
            'diagnostic_locale': project.diagnostic_locale,
            'documents': {'include': project.includes, 'exclude': project.excludes,
                          'book_root': project.book_root, 'section_redirects': project.section_redirects},
            'paths': project.paths,
            'managed_sources': [path.relative_to(project.root).as_posix() for path in project.sources()],
            'config_digest': file_digest(config_path) if config_path.is_file() else None}


def configure(project, source, expected=None):
    draft = contained(project.root, source)
    content = draft.read_text(encoding='utf-8')
    parsed = tomllib.loads(content)
    if parsed.get('version') != 1:
        raise ConfigurationError('Project configuration requires version = 1.')
    Project(project.root, config=parsed)
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
            'written': ['.tao/config.toml']}
