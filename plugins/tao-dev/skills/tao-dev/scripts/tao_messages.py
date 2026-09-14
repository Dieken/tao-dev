"""Standard-library diagnostic rendering shared by bootstrap and core.

English templates stay beside their call sites. Translate whole templates,
never reverse-match interpolated error strings or translate external output.
"""

from functools import lru_cache
import json
from pathlib import Path
import re


class Message(str):
    def __new__(cls, template, *values):
        parameters = {f'arg{i}': str(value) for i, value in enumerate(values)}
        value = super().__new__(cls, template.format_map(parameters))
        value.template = template
        value.parameters = parameters
        value.values = values
        return value

    def __reduce__(self):
        return type(self), (self.template, *self.values)


@lru_cache(maxsize=1)
def translations():
    path = Path(__file__).resolve().parent.parent / 'assets/locales/diagnostics.zh-Hans.json'
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def diagnostic(message, locale=None, suggestion=None):
    if isinstance(message, Exception):
        message = message.args[0] if len(message.args) == 1 else str(message)
    requested = locale or 'en'
    template = getattr(message, 'template', str(message))
    parameters = getattr(message, 'parameters', {})
    rendered, actual = str(message), 'en'
    translated = translations().get(template) if requested == 'zh-Hans' else None
    if isinstance(translated, str):
        try:
            display_parameters = dict(parameters)
            for index, value in enumerate(getattr(message, 'values', ())):
                if isinstance(value, (Message, Exception)):
                    display_parameters[f'arg{index}'] = diagnostic(value, requested)['message']
            rendered, actual = translated.format_map(display_parameters), 'zh-Hans'
        except (KeyError, ValueError):
            pass
    result = dict(message=rendered, message_locale=actual, requested_locale=requested,
                  locale_fallback=actual != requested, parameters=parameters)
    if suggestion is not None:
        translated_suggestion = translations().get(suggestion) if actual == 'zh-Hans' else None
        result['suggestion'] = translated_suggestion or suggestion
        result['suggestion_locale'] = 'zh-Hans' if translated_suggestion else 'en'
    return result


def option(argv, name):
    value = None
    for index, item in enumerate(argv):
        if item == '--':
            break
        if item.startswith(name + '='):
            value = item.split('=', 1)[1]
        elif item == name and index + 1 < len(argv):
            value = argv[index + 1]
    return value


def valid_locale(value):
    return isinstance(value, str) and re.fullmatch(r'[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*', value) is not None


def configured_locale(argv=()):
    """Best-effort display preference, including before core dependencies exist.

    Invalid configuration is diagnosed by its owner; selecting a display
    language must not mask that error or read a symlink outside project scope.
    """
    explicit = option(argv, '--diagnostic-locale')
    if explicit is not None:
        return explicit
    try:
        import tomllib
        supplied = option(argv, '--project')
        cwd = Path.cwd()
        root = Path(supplied).resolve() if supplied else next(
            (p for p in (cwd, *cwd.parents) if (p / '.tao/config.toml').is_file()), None)
        if root is None:
            return None
        path = root / '.tao/config.toml'
        if not path.resolve().is_relative_to(root.resolve()):
            return None
        config = tomllib.loads(path.read_text(encoding='utf-8'))
        ui = config.get('ui', {})
        value = ui.get('locale') if isinstance(ui, dict) else None
        return value if valid_locale(value) else None
    except (OSError, ValueError, RuntimeError, ImportError):
        return None
