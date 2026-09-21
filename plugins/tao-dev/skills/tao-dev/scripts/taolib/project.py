"""Project-scoped configuration and filesystem operations."""

import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import tempfile
import tomllib
from contextlib import contextmanager
from tao_messages import valid_locale, Message


class ConfigurationError(ValueError):
    pass


class ConflictError(ValueError):
    pass


def relative_pattern(value):
    """A project-relative path or glob: no drive, no root, no traversal.

    Both flavours judge it, so one configuration is valid or invalid
    everywhere. A single flavour disagrees with the other about what is
    absolute: "/etc/hosts" carries no drive letter, so Windows reads it as
    relative and hands it to glob, which raises instead of reporting a
    configuration error, and "C:/Windows" reads as an ordinary relative name
    on POSIX.
    """
    if not isinstance(value, str) or not value:
        return False
    for flavour in (PurePosixPath, PureWindowsPath):
        path = flavour(value)
        if path.drive or path.root or '..' in path.parts:
            return False
    return True


def contained(root, relative):
    path = root / relative
    try:
        path.resolve().relative_to(root.resolve())
    except (ValueError, RuntimeError) as exc:
        raise ConfigurationError(Message('Path escapes the project: {arg0}', relative)) from exc
    return path


class Project:
    def __init__(self, explicit=None, *, config=None):
        if explicit is None:
            cwd = Path.cwd()
            explicit = next((p for p in [cwd, *cwd.parents] if (p / ".tao/config.toml").is_file() or (p / ".tao/workflows").is_dir()), None)
            if explicit is None:
                raise ConfigurationError("Specify --project or provide project-local .tao/config.toml.")
        self.root = Path(explicit).resolve()
        if not self.root.is_dir():
            raise ConfigurationError("Project root must exist.")
        config_path = contained(self.root, ".tao/config.toml")
        self.config = config if config is not None else (tomllib.loads(config_path.read_text(encoding="utf-8")) if config_path.is_file() else {})
        if self.config and self.config.get("version") != 1:
            raise ConfigurationError("Unsupported configuration version; expected 1.")
        if self.config.keys() - {"version", "locale", "ui", "documents", "paths", "hooks", "verification"}:
            raise ConfigurationError("Unknown configuration keys.")
        ui = self.config.get('ui', {})
        if not isinstance(ui, dict) or ui.keys() - {'locale'} or ('locale' in ui and not valid_locale(ui['locale'])):
            raise ConfigurationError('ui.locale must be a language tag; no other ui keys are supported.')
        self.diagnostic_locale = ui.get('locale')
        documents = self.config.get("documents", {})
        paths = self.config.get("paths", {})
        if not isinstance(documents, dict) or documents.keys() - {"include", "exclude", "book_root", "section_redirects"}:
            raise ConfigurationError("Invalid documents configuration.")
        if not isinstance(paths, dict) or paths.keys() - {"plans", "retired", "temporary"}:
            raise ConfigurationError("Invalid paths configuration.")
        self.includes = documents.get("include", ["docs/**/*.md"])
        self.excludes = documents.get("exclude", [])
        self.section_redirects = documents.get('section_redirects', {})
        if not isinstance(self.section_redirects, dict) or any(not isinstance(key, str) or not isinstance(value, str)
                                                             for key, value in self.section_redirects.items()):
            raise ConfigurationError('documents.section_redirects must map section references to section references.')
        for patterns in (self.includes, self.excludes):
            if not isinstance(patterns, list) or any(not relative_pattern(p) for p in patterns):
                raise ConfigurationError("Document patterns must be project-relative string arrays.")
        self.paths = {"plans": "docs/plans", "retired": "docs/retired", "temporary": "tmp/tao"} | paths
        for value in self.paths.values():
            if not isinstance(value, str) or not value or Path(value).is_absolute():
                raise ConfigurationError("Configured paths must be nonempty project-relative strings.")
            contained(self.root, value)
        self.book_root = documents.get("book_root")
        if self.book_root is not None:
            if not isinstance(self.book_root, str) or not self.book_root or Path(self.book_root).is_absolute():
                raise ConfigurationError("documents.book_root must be a relative path.")
            self.book_root = contained(self.root, self.book_root).resolve().relative_to(self.root).as_posix()
        self.locale = self.config.get("locale")
        if self.locale is not None and not isinstance(self.locale, str):
            raise ConfigurationError("locale must be a language tag string.")
        hooks = self.config.get("hooks", {})
        if not isinstance(hooks, dict) or hooks.keys() - {"docs_enabled", "timeout_seconds"}:
            raise ConfigurationError("Invalid hooks configuration.")
        if type(hooks.get("docs_enabled", True)) is not bool or type(hooks.get("timeout_seconds", 5)) is not int:
            raise ConfigurationError("hooks requires a boolean docs_enabled and integer timeout_seconds.")
        self.hook_enabled = hooks.get("docs_enabled", True)
        self.hook_timeout = hooks.get("timeout_seconds", 5)
        if not 1 <= self.hook_timeout <= 30:
            raise ConfigurationError("Hook timeout must be between 1 and 30 seconds.")

    def sources(self):
        selected = set()
        excluded = {path for pattern in self.excludes for path in self.root.glob(pattern)}
        for pattern in self.includes:
            for path in self.root.glob(pattern):
                if path.is_file() and path not in excluded:
                    selected.add(path)
        return sorted(selected)

    def output(self, key, suffix=""):
        return contained(self.root, Path(self.paths[key]) / suffix)


def create_file(root, path, text):
    """Publish a complete file exclusively; never overwrite a concurrent writer."""
    contained(root, path)
    if path.exists() or path.is_symlink():
        raise ConflictError(Message('File already exists: {arg0}', path.relative_to(root)))
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".tao-new-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError as exc:
            raise ConflictError(Message('Concurrent file creation: {arg0}', path.relative_to(root))) from exc
    finally:
        Path(temporary).unlink(missing_ok=True)


@contextmanager
def mutation_lock(project):
    path = project.output("temporary", "cache/mutation.lock")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.mkdir()
    except FileExistsError as exc:
        raise ConflictError("Another mutation owns the lock; inspect an interrupted operation before removing its stale lock.") from exc
    try:
        yield
    finally:
        path.rmdir()


def replace_file(root, path, text, expected):
    contained(root, path)
    if path.read_bytes() != expected:
        raise ConflictError("The destination changed during preparation; reload it before retrying.")
    descriptor, temporary = tempfile.mkstemp(prefix=".tao-update-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)
