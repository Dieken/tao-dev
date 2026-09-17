"""Standard-library bootstrap; never install from a normal command or hook."""

import argparse
import ast
import hashlib
import json
import os
import queue
import re
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

from installed_runtime import binding, shared_cli
from tao_messages import Message, configured_locale, diagnostic

SCRIPTS = Path(__file__).resolve().parent
IMPORTS = {"core": ["markdown_it", "yaml"],
           "publication": ["markdown_it", "yaml", "sphinx", "myst_parser", "sphinx_book_theme"]}
# Package sources, never install locations: these decide where a wheel is
# fetched from, and the locked hashes still decide whether it is accepted.
SOURCE_KEYS = ("index-url", "extra-index-url", "trusted-host", "proxy", "cert",
               "client-cert", "retries", "timeout")
REPEATED_KEYS = ("extra-index-url", "trusted-host")
UNITS = {"bytes": 1, "kB": 1000, "MB": 1000 ** 2, "GB": 1000 ** 3}
TIMED_OUT = ('Preparation exceeded its time limit; inspect {arg0}. '
             'Raise or remove the limit with --timeout <seconds>.')
TIMED_OUT_UNMIRRORED = ('Preparation exceeded its time limit; inspect {arg0}. '
                        'Raise or remove the limit with --timeout <seconds>, or configure a nearer '
                        'package index, for example pip config set global.index-url <url>.')
TRANSFER = re.compile(r"\s*(Downloading|Using cached) (\S+)(?: \(([^()]*)\))?\s*")


class RuntimeFailure(ValueError):
    def __init__(self, message, rule="TAO-RUNTIME-001", state="unavailable"):
        super().__init__(message)
        self.rule = rule
        self.state = state


def isolated(python, *options):
    """Run a child interpreter without inherited configuration.

    Isolated mode also ignores PYTHONUTF8, so a child that prints a Chinese
    path (pip echoes the inventory it reads) would encode its own output with
    the legacy Windows code page and fail. The command line restores UTF-8.
    """
    return [str(python), "-I", "-X", "utf8", *options]


def environment():
    # Do not let inherited pip configuration redirect writes out of our venv.
    result = {key: value for key, value in os.environ.items()
              if not key.startswith("PIP_") and key not in ("PYTHONPATH", "PYTHONHOME")}
    result.update(PIP_CONFIG_FILE=os.devnull, PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1")
    return result


def package_source(python):
    """Keep the caller's package source without inheriting where it installs.

    A personal pip configuration can redirect writes into a business
    environment through target, prefix or user, so preparation still runs
    against an empty configuration. An index only says where a wheel comes
    from and every wheel is still matched against the locked hashes, so a
    caller behind a blocked or slow default index keeps their own mirror
    instead of losing the ability to install at all.
    """
    values = {}
    # pip config list reports only the variables once any PIP_ variable is
    # set, so the files are read without them and the variables are read here.
    probe = {key: value for key, value in os.environ.items()
             if not key.startswith("PIP_") or key == "PIP_CONFIG_FILE"}
    try:
        completed = subprocess.run(isolated(python, "-m", "pip", "config", "list"),
                                   capture_output=True, text=True, encoding="utf-8", errors="replace",
                                   timeout=30, env=probe | {"PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1"})
        listed = completed.stdout if completed.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        listed = ""
    # A command section overrides the global one, as it does for pip itself.
    for section in ("global", "install"):
        for line in listed.splitlines():
            name, separator, value = line.partition("=")
            scope, _, key = name.strip().rpartition(".")
            if separator and scope == section and key in SOURCE_KEYS:
                try:
                    values[key] = ast.literal_eval(value.strip())
                except (ValueError, SyntaxError):
                    continue
    values.update({key: os.environ["PIP_" + key.upper().replace("-", "_")] for key in SOURCE_KEYS
                   if "PIP_" + key.upper().replace("-", "_") in os.environ})
    options = []
    for key, value in values.items():
        if not isinstance(value, str):
            continue
        for item in (value.split() if key in REPEATED_KEYS else [value.strip()]):
            if item and item.isprintable():
                options += ["--" + key, item]
    return options


def readable(size):
    if size >= 1000 ** 2:
        return f"{size / 1000 ** 2:.1f} MB"
    if size >= 1000:
        return f"{size / 1000:.1f} kB"
    return f"{size:.0f} bytes"


def measured(text):
    match = re.fullmatch(r"\s*([0-9.]+) (bytes|kB|MB|GB)\s*", text or "")
    return float(match.group(1)) * UNITS[match.group(2)] if match else None


def named(target):
    """Report the distribution, not the index path it happens to live under."""
    filename = target.rsplit("/", 1)[-1].split("?", 1)[0]
    parts = filename.split("-")
    return f"{parts[0]} {parts[1]}" if filename.endswith(".whl") and len(parts) > 2 else filename


class Progress:
    """Name every package, where it came from and how fast it arrived.

    pip publishes no machine-readable progress, so its own output is the only
    source: a transfer starts on its Downloading line and has finished by the
    time pip prints anything else.
    """

    def __init__(self, mode, stream=None):
        self.mode = mode
        self.stream = stream
        self.started = False
        self.pending = None
        self.total = 0.0
        self.seconds = 0.0

    def line(self, text):
        match = TRANSFER.fullmatch(text.rstrip("\r\n"))
        if self.pending and (match or text.strip()):
            self.settle()
        if match and match.group(1) == "Downloading":
            self.pending = (match.group(2), measured(match.group(3)), time.monotonic())
        elif match:
            self.report(f"{named(match.group(2))}  {match.group(3) or 'unknown size'}  cached  {match.group(2)}")

    def settle(self):
        target, size, started = self.pending
        self.pending = None
        seconds = max(time.monotonic() - started, 0.001)
        self.seconds += seconds
        self.total += size or 0.0
        rate = f"{readable(size / seconds)}/s" if size else "rate unknown"
        self.report(f"{named(target)}  {readable(size) if size else 'unknown size'}  "
                    f"{seconds:.1f}s  {rate}  {target}")

    def summary(self):
        if self.pending:
            self.settle()
        if self.total:
            self.report(f"downloaded {readable(self.total)} in {self.seconds:.1f}s")

    def report(self, text):
        if self.stream is None:
            return
        if not self.started:
            print(f"Preparing the {self.mode} runtime.", file=self.stream, flush=True)
            self.started = True
        print("  " + text, file=self.stream, flush=True)


def remaining(deadline):
    return None if deadline is None else max(0.0, deadline - time.monotonic())


def observed(argv, log, progress, deadline):
    """Run one preparation step, recording and reporting its output as it arrives.

    A single deadline covers the whole preparation: a per-process limit turns
    a slow but healthy download into a failure and cannot express the budget
    the caller actually has. The reader thread keeps that bound portable to
    Windows, where a pipe cannot be polled.
    """
    process = subprocess.Popen(argv, env=environment(), stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True, encoding="utf-8", errors="replace")
    lines = queue.Queue()

    def read():
        try:
            for line in process.stdout:
                lines.put(line)
        finally:
            lines.put(None)

    threading.Thread(target=read, daemon=True).start()
    try:
        while True:
            try:
                line = lines.get(timeout=remaining(deadline))
            except queue.Empty:
                raise subprocess.TimeoutExpired(argv[0], 0) from None
            if line is None:
                return process.wait(timeout=30)
            log.write(line)
            progress.line(line)
    finally:
        process.kill()
        process.wait()
        process.stdout.close()


def data_root(installed=None):
    explicit = (os.environ.get("TAO_RUNTIME_DIR")
                or (installed["runtime_dir"] if installed else None)
                or os.environ.get("CLAUDE_PLUGIN_DATA"))
    if explicit:
        path = Path(explicit)
        if not path.is_absolute():
            raise RuntimeFailure("Runtime data directory must be absolute.")
        return path.resolve()
    if sys.platform == "win32":
        parent = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
    elif sys.platform == "darwin":
        parent = Path.home() / "Library/Application Support"
    else:
        parent = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
    if not parent.is_absolute():
        raise RuntimeFailure("User data directory must be absolute.")
    return parent / "tao-dev"


def inspect_python(python):
    code = ("import json,os,platform,sys; print(json.dumps(dict("
            "version=list(sys.version_info[:3]), implementation=sys.implementation.name,"
            "platform=sys.platform, machine=platform.machine(),"
            "executable=os.path.realpath(sys.executable))))")
    try:
        completed = subprocess.run(isolated(python, "-c", code),
                                   capture_output=True, text=True, encoding="utf-8", timeout=10, env=environment())
        if completed.returncode:
            # Keep the interpreter's own reason: without it a broken or
            # unusable Python is indistinguishable from an absent one.
            detail = (completed.stderr or completed.stdout).strip().splitlines()
            raise ValueError(Message('Interpreter probe failed: {arg0}',
                                     detail[-1] if detail else f'exit {completed.returncode}'))
        info = json.loads(completed.stdout)
        policy = json.loads((SCRIPTS / "runtime.json").read_text(encoding="utf-8"))
        if not policy["python_min"] <= info["version"][:2] < policy["python_max"]:
            raise ValueError(Message('Supported Python versions: {arg0} to below {arg1}', policy['python_min'], policy['python_max']))
        return info
    except (OSError, ValueError, KeyError, subprocess.TimeoutExpired) as exc:
        raise RuntimeFailure(Message('Python is unavailable or unsupported: {arg0}', exc)) from exc


def context(mode, project=None):
    installed = binding(SCRIPTS, project)
    python = os.environ.get("TAO_PYTHON") or (installed["python"] if installed else None) or sys.executable
    info = inspect_python(python)
    inventory = SCRIPTS / ("requirements-publication.txt" if mode == "publication" else "requirements.txt")
    digest = hashlib.sha256(inventory.read_bytes()).hexdigest()
    key = hashlib.sha256(json.dumps([info, mode, digest], sort_keys=True).encode()).hexdigest()[:32]
    root = data_root(installed)
    return {"mode": mode, "base_python": str(python), "base": info,
            "inventory": str(inventory), "digest": digest,
            "key": key, "root": root, "slot": root / "runtimes" / key}


def python_in(directory):
    return directory / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def probe(python, mode):
    code = ("import importlib,importlib.metadata as m,json,sys; "
            f"[importlib.import_module(n) for n in {IMPORTS[mode]!r}]; "
            "print(json.dumps({'prefix':sys.prefix,'packages':"
            "sorted((d.metadata['Name'].lower(),d.version) for d in m.distributions())}))")
    completed = subprocess.run(isolated(python, "-c", code), env=environment(),
                               capture_output=True, text=True, encoding="utf-8", timeout=10)
    if completed.returncode:
        raise RuntimeFailure("Runtime imports failed; run tao env prepare for a new environment.",
                             "TAO-RUNTIME-003", "broken")
    return json.loads(completed.stdout)


def selected(ctx):
    pointer = ctx["slot"] / "active.json"
    if not pointer.exists():
        return None
    try:
        name = json.loads(pointer.read_text(encoding="utf-8"))["generation"]
        if not isinstance(name, str) or not re.fullmatch(r"env-[a-z0-9_]+", name):
            raise ValueError("Invalid runtime generation")
        directory = ctx["slot"] / name
        if directory.is_symlink() or not directory.resolve().is_relative_to(ctx["root"].resolve()):
            raise ValueError("Runtime generation escapes data directory")
        ready = json.loads((directory / "ready.json").read_text(encoding="utf-8"))
        actual = probe(python_in(directory), ctx["mode"])
        if ready["key"] != ctx["key"] or ready["probe"] != actual or Path(actual["prefix"]).resolve() != directory.resolve():
            raise ValueError("Runtime environment changed since preparation")
        return directory
    except (OSError, ValueError, KeyError, subprocess.TimeoutExpired) as exc:
        raise RuntimeFailure(Message('Prepared environment is invalid: {arg0}', exc), "TAO-RUNTIME-003", "broken") from exc


def description(ctx, directory=None, state="missing"):
    return {"state": "ready" if directory else state, "mode": ctx["mode"],
            "data_directory": str(ctx["root"]), "dependency_digest": ctx["digest"],
            "base_python": ctx["base_python"],
            "python": str(python_in(directory)) if directory else None}


def atomic_json(path, value):
    descriptor, temporary = tempfile.mkstemp(prefix=".write-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def prepare(ctx, wheelhouse=None, deadline=None, stream=None):
    if wheelhouse is not None and not wheelhouse.is_dir():
        raise RuntimeFailure("Offline wheelhouse must be an existing directory.")
    slot = ctx["slot"]
    if not slot.resolve().is_relative_to(ctx["root"].resolve()):
        raise RuntimeFailure("Runtime slot escapes data directory.")
    slot.mkdir(parents=True, exist_ok=True)
    lock = slot / "prepare.lock"
    waiting = time.monotonic() + 120 if deadline is None else min(time.monotonic() + 120, deadline)
    while True:
        try:
            lock.mkdir()
            break
        except FileExistsError:
            if time.monotonic() >= waiting:
                raise RuntimeFailure("Another preparation owns the lock; retry after it finishes. Inspect interrupted operations before removing a stale lock.", "TAO-RUNTIME-004", "busy")
            time.sleep(0.1)
    try:
        try:
            directory = selected(ctx)
        except RuntimeFailure:
            directory = None
        if directory:
            return directory
        # A venv contains absolute paths. Create it at its permanent location.
        directory = Path(tempfile.mkdtemp(prefix="env-", dir=slot))
        log = directory / "prepare.log"
        progress = Progress(ctx["mode"], stream)

        def step(argv, timed_out=TIMED_OUT):
            try:
                code = observed(argv, output, progress, deadline)
            except subprocess.TimeoutExpired as exc:
                raise RuntimeFailure(Message(timed_out, log), "TAO-RUNTIME-005") from exc
            if code:
                raise RuntimeFailure(Message('Preparation failed; inspect {arg0}. Python must include venv and ensurepip; dependency installation must match the locked inventory.', log), "TAO-RUNTIME-005")

        with log.open("w", encoding="utf-8", newline="\n") as output:
            step(isolated(ctx["base_python"], "-m", "venv", str(directory)))
            # Unbuffered output turns pip's own lines into live progress.
            pip = isolated(python_in(directory), "-u", "-m", "pip")
            install = pip + ["install", "--disable-pip-version-check", "--no-input", "--require-hashes",
                             "--only-binary=:all:", "-r", ctx["inventory"]]
            source = ["--no-index", "--find-links", str(wheelhouse.resolve())] if wheelhouse \
                else package_source(python_in(directory))
            step(install + source,
                 TIMED_OUT if wheelhouse or "--index-url" in source else TIMED_OUT_UNMIRRORED)
            step(pip + ["check"])
        progress.summary()
        actual = probe(python_in(directory), ctx["mode"])
        atomic_json(directory / "ready.json", {"key": ctx["key"], "probe": actual})
        atomic_json(slot / "active.json", {"generation": directory.name})
        return directory
    finally:
        lock.rmdir()


def emit(command, outputs, error=None, json_output=True, locale=None):
    try:
        version = json.loads((SCRIPTS / "runtime.json").read_text(encoding="utf-8"))["version"]
    except (OSError, ValueError, KeyError):
        version = "unknown"
    result = {"tool": "tao-dev", "protocol_version": "0.1", "command": command,
              "tool_version": version,
              "status": "not_run" if error else "passed", "outputs": outputs,
              "diagnostics": [] if error is None else [{"rule_id": error.rule, "severity": "error",
                                                       **diagnostic(error, locale)}]}
    if command == "doctor":
        result["capabilities"] = ["doctor", "env.prepare", "install", "uninstall"]
    if command == "verify":
        result.update(coverage="unknown", readiness="blocked")
    if json_output:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"tao {command}: {result['status']}")
        print(result['diagnostics'][0]['message'] if error else json.dumps(outputs, ensure_ascii=False, indent=2))
    return 2 if error else 0


def operation(argv):
    # Global options can precede the command; their values are not commands.
    index = 0
    while index < len(argv):
        if argv[index] in ("--project", "--format", "--diagnostic-locale"):
            index += 2
        elif argv[index].startswith(("--project=", "--format=", "--diagnostic-locale=")):
            index += 1
        else:
            return argv[index], index
    return "unknown", len(argv)


def utf8_streams():
    """Reports carry Chinese titles, paths and diagnostics, and JSON output keeps
    them unescaped. A Windows console or pipe defaults to a legacy code page and
    raises while printing them, so own the encoding instead of depending on the
    caller's environment."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")


def main(argv=None, entry="tao.py"):
    utf8_streams()
    argv = list(sys.argv[1:] if argv is None else argv)
    command, position = operation(argv)
    if entry == "tao.py" and command in ("install", "uninstall"):
        from installation import main as installation_main
        return installation_main([command, *argv[:position], *argv[position + 1:]])
    if entry == "validate_documents.py":
        command = "validate"
    mode = "publication" if command == "docs" or (command == "doctor" and "--publication" in argv) else "core"
    ctx = None
    json_output = any(value == "--format=json" or argv[index:index + 2] == ["--format", "json"]
                      for index, value in enumerate(argv))
    try:
        project = None
        for index, value in enumerate(argv):
            if value == "--project" and index + 1 < len(argv):
                project = argv[index + 1]
            elif value.startswith("--project="):
                project = value.split("=", 1)[1]
        if shared_cli(SCRIPTS):
            installed = binding(SCRIPTS, project)
            if installed is None:
                raise RuntimeFailure("No installation matches this project. Run tao install to prepare one.")
            native_scripts = Path(installed["plugin_path"]) / "skills/tao-dev/scripts"
            native_entry = native_scripts / entry
            if shared_cli(native_scripts) or not native_entry.is_file():
                raise RuntimeFailure("Installed plugin cache is unavailable. Run tao install to restore it.")
            python = os.environ.get("TAO_PYTHON") or installed["python"]
            return subprocess.run([python, "-I", "-B", str(native_entry), *argv],
                                  env=environment(), check=False).returncode
        ctx = context(mode, project)
        if command == "env":
            parser = argparse.ArgumentParser(prog="tao env")
            parser.add_argument("operation", choices=("prepare",))
            parser.add_argument("--project", type=Path)
            parser.add_argument("--wheelhouse", type=Path)
            parser.add_argument("--timeout", type=float, default=300,
                                help="Seconds allowed for the whole preparation; 0 removes the limit.")
            parser.add_argument("--format", choices=("text", "json"), default="text")
            parser.add_argument("--diagnostic-locale")
            args = parser.parse_args(argv[position + 1:])
            if args.timeout < 0:
                parser.error("--timeout must not be negative.")
            # One budget for the whole command; progress belongs on stderr so
            # that --format json stays a single machine-readable document.
            deadline = time.monotonic() + args.timeout if args.timeout else None
            directory = prepare(ctx, args.wheelhouse, deadline, sys.stderr)
            runtime = description(ctx, directory)
            ctx = context("publication", project)
            publication = prepare(ctx, args.wheelhouse, deadline, sys.stderr)
            runtime["publication"] = description(ctx, publication)
            return emit(command, {"runtime": runtime}, json_output=json_output)
        directory = selected(ctx)
        if directory is None:
            raise RuntimeFailure(Message('The {arg0} runtime is not prepared. Run tao env prepare; ordinary commands do not install dependencies.', mode), "TAO-RUNTIME-002", "missing")
        if Path(sys.prefix).resolve() != directory.resolve():
            child_env = environment() | {"TAO_PYTHON": ctx["base_python"]}
            return subprocess.run([str(python_in(directory)), "-I", "-B", str(SCRIPTS / entry), *argv], env=child_env).returncode
        sys.dont_write_bytecode = True
        if entry == "validate_documents.py":
            from taolib.validator_cli import main as validate_main
            return validate_main(argv)
        from taolib.cli import main as cli_main
        runtime_context = description(ctx, directory)
        if command == "doctor" and mode == "core":
            publication = context("publication", project)
            try:
                prepared = selected(publication)
                runtime_context["publication"] = description(publication, prepared, state="ready" if prepared else "missing")
            except RuntimeFailure as exc:
                runtime_context["publication"] = description(publication, state=exc.state)
        return cli_main([a for a in argv if a != "--publication"], runtime_context=runtime_context)
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        error = exc if isinstance(exc, RuntimeFailure) else RuntimeFailure(str(exc))
        outputs = {"runtime": description(ctx, state=error.state)} if ctx else {}
        return emit(command, outputs, error, json_output, configured_locale(argv))


def hook_main():
    """Check project activation before inspecting or creating any tool data."""
    utf8_streams()
    started = time.monotonic()
    try:
        payload = json.loads(sys.stdin.read(1_000_001))
        if not isinstance(payload, dict):
            raise ValueError("Expected a hook event object.")
        project = next((p for p in [Path.cwd(), *Path.cwd().parents]
                        if (p / ".tao/config.toml").is_file()), None)
        if payload.get("hook_event_name") != "PostToolUse" or project is None:
            print("{}")
            return 0
        import tomllib
        config_path = project / ".tao/config.toml"
        if not config_path.resolve().is_relative_to(project.resolve()):
            raise ValueError("Project configuration escapes its root.")
        config = tomllib.loads(config_path.read_text(encoding="utf-8"))
        hooks = config.get("hooks", {})
        if not isinstance(hooks, dict):
            raise ValueError("Invalid hooks configuration.")
        if hooks.get("docs_enabled", True) is False:
            print("{}")
            return 0
        budget = hooks.get("timeout_seconds", 5)
        if type(budget) is not int or not 1 <= budget <= 30:
            raise ValueError("Invalid hook time budget.")
        ctx = context("core")
        directory = selected(ctx)
        if directory is None:
            raise RuntimeFailure("Core runtime missing; run tao env prepare explicitly.", "TAO-RUNTIME-002")
        if Path(sys.prefix).resolve() == directory.resolve():
            from taolib.hook import run
            response = run(payload)
        else:
            child_env = environment() | {"TAO_PYTHON": ctx["base_python"]}
            remaining = budget - (time.monotonic() - started)
            if remaining <= 0:
                raise ValueError("Hook time budget exceeded during runtime inspection.")
            completed = subprocess.run([str(python_in(directory)), "-I", "-B", str(SCRIPTS / "hook.py")],
                                       env=child_env, input=json.dumps(payload), capture_output=True,
                                       text=True, encoding="utf-8", timeout=remaining)
            if completed.returncode:
                raise ValueError("Hook process could not complete.")
            response = json.loads(completed.stdout)
    except (OSError, ValueError, ImportError, subprocess.TimeoutExpired) as exc:
        response = {"hookSpecificOutput": {"hookEventName": "PostToolUse",
                    "additionalContext": 'tao docs not_run: ' + diagnostic(exc, configured_locale())['message']}}
    print(json.dumps(response, ensure_ascii=False))
    return 0
