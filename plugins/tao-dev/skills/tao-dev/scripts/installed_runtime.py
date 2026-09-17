"""Standard-library installation receipts and read-only runtime selection.

Receipts describe owned storage; they never grant authority to remove arbitrary
paths. Native configuration and cache deletion remain the installer's concern.
"""

import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path

CLIENTS = {"claude": "CLAUDE_CONFIG_DIR", "codex": "CODEX_HOME"}
SCOPES = {"user": 0, "project": 1, "local": 2}


def client_home(client):
    if client not in CLIENTS:
        raise ValueError("Unknown installation client.")
    path = Path(os.environ.get(CLIENTS[client]) or Path.home() / ("." + client))
    if not path.is_absolute():
        raise ValueError("Client configuration directory must be absolute.")
    return path.resolve()


def shared_root():
    """Storage every client shares, so removing one client keeps the CLI.

    An explicit directory keeps experiments and tests off the real one.
    """
    explicit = os.environ.get("TAO_CLI_DIR")
    if explicit:
        path = Path(explicit)
        if not path.is_absolute():
            raise ValueError("Shared CLI directory must be absolute.")
        return path.resolve()
    if sys.platform == "win32":
        parent = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData/Local")
    elif sys.platform == "darwin":
        parent = Path.home() / "Library/Application Support"
    else:
        parent = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local/share")
    if not parent.is_absolute():
        raise ValueError("User data directory must be absolute.")
    return _unlinked(parent / "tao-dev", parent)


def cli_root():
    root = shared_root()
    return _unlinked(root / "cli", root)


def legacy_cli_roots():
    """Earlier releases kept the shared CLI under one client's own home."""
    roots = []
    for client in CLIENTS:
        try:
            home = client_home(client)
            roots.append(_unlinked(home / "tao-dev/cli", home))
        except (OSError, ValueError, RuntimeError):
            continue
    return roots


def _unlinked(path, boundary):
    """Reject symlinks in owned path components beneath a trusted boundary."""
    if not path.is_relative_to(boundary):
        raise ValueError("Installation path escapes its owner.")
    for candidate in (path, *path.parents):
        if candidate == boundary:
            break
        if candidate.is_symlink():
            raise ValueError("Installation paths must not use symbolic links.")
    return path


def registry_root(client):
    home = client_home(client)
    return _unlinked(home / "tao-dev/installations", home)


def _project(scope, project):
    if scope not in SCOPES:
        raise ValueError("Unknown installation scope.")
    if scope == "user":
        return None
    if project is None:
        raise ValueError("Project and local installations require a project.")
    path = Path(project).resolve()
    if path == Path(path.anchor) or path == Path.home().resolve():
        raise ValueError("Installation project must not be a filesystem or home root.")
    return path


def install_id(client, scope, project):
    if client not in CLIENTS:
        raise ValueError("Unknown installation client.")
    project = _project(scope, project)
    identity = json.dumps([client, scope, str(project) if project else None])
    return f"{client}-{scope}-{hashlib.sha256(identity.encode()).hexdigest()[:16]}"


def managed_root(client, scope, project):
    identifier = install_id(client, scope, project)
    project = _project(scope, project)
    if project is None:
        home = client_home(client)
        return _unlinked(home / "tao-dev/managed" / identifier, home)
    return _unlinked(project / ".local/tao-dev" / client / scope, project)


def record_path(client, identifier):
    if not isinstance(identifier, str) or not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,127}", identifier):
        raise ValueError("Invalid installation identifier.")
    root = registry_root(client)
    return _unlinked(root / (identifier + ".json"), client_home(client))


def _absolute(value):
    if not isinstance(value, str) or not value or not Path(value).is_absolute():
        raise ValueError("Installation paths must be absolute.")
    path = Path(value)
    if ".." in path.parts or path == Path(path.anchor):
        raise ValueError("Unsafe installation path.")
    return path


def _validate(record, client=None):
    if not isinstance(record, dict) or type(record.get("schema")) is not int or record["schema"] != 1:
        raise ValueError("Unsupported installation receipt.")
    if client is not None and record.get("client") != client:
        raise ValueError("Installation receipt belongs to another client.")
    client, scope, project = record["client"], record["scope"], record["project"]
    if scope == "user":
        if project is not None:
            raise ValueError("User installation must not bind a project.")
    else:
        project_path = _absolute(project)
        if project_path != project_path.resolve():
            raise ValueError("Installation project must be canonical.")
    if record["id"] != install_id(client, scope, project):
        raise ValueError("Installation identifier does not match its scope.")
    owned = _absolute(record["managed_root"])
    if owned != managed_root(client, scope, project):
        raise ValueError("Installation managed root does not match its owner.")
    runtime = _absolute(record["runtime_dir"])
    _unlinked(runtime, owned)
    if runtime == owned or not runtime.resolve().is_relative_to(owned.resolve()):
        raise ValueError("Installation runtime must be inside its managed root.")
    plugin, base = _absolute(record["plugin_path"]), _absolute(record["plugin_base"])
    if base.resolve() not in (plugin.resolve(), plugin.resolve().parent):
        raise ValueError("Plugin cache base must identify this plugin or its version parent.")
    # A cache base identifies one plugin, never an entire project/home tree.
    boundaries = [Path.home().resolve(), client_home(client), owned]
    if project is not None:
        boundaries.append(Path(project))
    if any(boundary.is_relative_to(base.resolve()) for boundary in boundaries):
        raise ValueError("Plugin cache base is too broad.")
    _absolute(record["python"])
    if "cli_path" in record:
        # A receipt written before the CLI moved out of a client home stays
        # readable; reinstalling is what repoints it.
        allowed = [client_home(client) / "tao-dev/cli"]
        try:
            allowed.append(cli_root())
        except (OSError, ValueError, RuntimeError):
            pass
        if _absolute(record["cli_path"]) not in allowed:
            raise ValueError("CLI binding must point to the shared tao CLI.")
    if record["status"] not in ("ready", "preparing"):
        raise ValueError("Invalid installation status.")
    if not all(isinstance(record[key], str) and record[key] for key in ("plugin_id", "version")):
        raise ValueError("Installation plugin identity and version are required.")
    if not isinstance(record["source"], dict) or not isinstance(record["files"], list) or not all(
            isinstance(path, str) for path in record["files"]):
        raise ValueError("Invalid installation source or file inventory.")
    return record


def records(client):
    """Read valid receipts without creating directories or following links."""
    try:
        root = registry_root(client)
        paths = sorted(root.glob("*.json"))
    except (OSError, ValueError, RuntimeError):
        return []
    result = []
    for path in paths:
        try:
            if path.is_symlink() or not path.is_file():
                continue
            record = _validate(json.loads(path.read_text(encoding="utf-8")), client)
            if path != record_path(client, record["id"]):
                continue
            result.append(record)
        except (OSError, ValueError, KeyError, TypeError, RuntimeError):
            continue
    return result


def save_record(record):
    """Validate and atomically replace a receipt, preserving extra fields."""
    try:
        _validate(record)
        path = record_path(record["client"], record["id"])
    except (KeyError, TypeError) as exc:
        raise ValueError("Incomplete installation receipt.") from exc
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".write-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(record, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return path


def shared_cli(scripts):
    """Recognize the managed CLI copy without depending on a receipt."""
    scripts = Path(scripts).resolve()
    roots = legacy_cli_roots()
    try:
        roots.append(cli_root())
    except (OSError, ValueError, RuntimeError):
        pass
    return any(scripts.is_relative_to(root) for root in roots)


def binding(scripts, cwd=None):
    """Choose the deepest eligible project, then local/project/user scope."""
    scripts = Path(scripts).resolve()
    cwd = Path(cwd).resolve() if cwd is not None else Path.cwd().resolve()
    shared = shared_cli(scripts)
    candidates = []
    for client in CLIENTS:
        for record in records(client):
            if record["status"] != "ready":
                continue
            if not shared and not any(scripts.is_relative_to(Path(record[key]).resolve())
                                      for key in ("plugin_path", "plugin_base")):
                continue
            project = Path(record["project"]) if record["project"] else None
            if project is not None and not cwd.is_relative_to(project):
                continue
            candidates.append((len(project.parts) if project else 0,
                               SCOPES[record["scope"]], record["id"], record))
    return max(candidates, key=lambda item: item[:3])[-1] if candidates else None
