"""Prepare a real failed check and persisted handoff for a fresh CLI session."""

from datetime import date
import json
import re
import subprocess
import sys


def prepare(directory, plugin, env=None):
    entry = plugin / 'skills/tao-dev/scripts/tao.py'
    def tao(*arguments):
        p = subprocess.run([sys.executable, str(entry), '--project', str(directory), '--format', 'json', *arguments], env=env, capture_output=True, text=True)
        if p.returncode:
            raise RuntimeError(p.stdout + p.stderr)
        return json.loads(p.stdout)
    config = directory / '.tao/config.toml'
    config.write_text('version = 1\nlocale = "en"\n[verification]\ninputs = ["example.py", "check.py", "requirements.txt"]\nbudget_seconds = 30\n[[verification.checks]]\nid = "export-regression"\nargv = [' + json.dumps(sys.executable) + ', "check.py"]\ntimeout_seconds = 10\n', encoding='utf-8')
    (directory / 'check.py').write_text('''from pathlib import Path
from tempfile import TemporaryDirectory
from example import export

with TemporaryDirectory(dir="tmp/tao") as folder:
    existing = Path(folder) / "existing"
    existing.write_bytes(b"original\\x00")
    try:
        export(existing, "replacement")
    except FileExistsError:
        pass
    else:
        raise AssertionError("Existing file must be refused")
    assert existing.read_bytes() == b"original\\x00"
    fresh = Path(folder) / "fresh"
    export(fresh, "hello")
    assert fresh.read_text() == "hello"
print("Existing bytes preserved; new file exported.")
''', encoding='utf-8')
    created = tao('new', '--slug', 'protect-export')['outputs']
    path = directory / created['path']
    values = {'TITLE':'Protect existing export files', 'SCOPE':'Refuse existing paths and preserve their exact bytes.',
              'REFERENCES':'See requirements.txt in the project root.', 'DESIGN_REFERENCE':'This focused maintenance fixture uses exclusive creation; a separate feature design is outside this probe.',
              'TASK_TITLE':'Implement and verify refusal of existing targets', 'TASK_VERIFY':'Run the configured export regression and validate documentation.',
              'VERIFICATION':'The initial check fails because export overwrites an existing file.', 'QUESTIONS':'None.'}
    path.write_text(re.sub(r'\{\{([^}]+)\}\}', lambda m: values[m[1]], path.read_text(encoding='utf-8')), encoding='utf-8')
    failure = subprocess.run([sys.executable, str(entry), '--project', str(directory), 'verify', '--only', 'code', '--format', 'json'], env=env, capture_output=True, text=True)
    if failure.returncode != 1:
        raise RuntimeError('Expected a real failing baseline: ' + failure.stdout)
    labels = json.loads((plugin / 'skills/tao-dev/assets/locales/en.json').read_text(encoding='utf-8'))
    values = labels | {'DOC_ID':tao('id','new','DOC')['outputs']['id'], 'TITLE':'Resume export protection',
                       'LOCALE':'en', 'CREATED':date.today().isoformat(),
                       'SCOPE':created['ids']['CHG_ID'],
                       'STATE':'The implementation still overwrites files. The configured regression has failed.',
                       'DECISIONS':'Preserve existing bytes by refusing overwrite. Keep current IDs and the current plan.',
                       'EVIDENCE':'Read tmp/tao/verification/latest.json. It records the executed failing baseline.',
                       'NEXT':'Repair example.py, prove old evidence is stale, run configured checks, and update the existing plan with actual evidence.'}
    draft = directory / 'tmp/tao/handoff-draft.md'
    draft.write_text(re.sub(r'\{\{([^}]+)\}\}', lambda m: values[m[1]], (plugin / 'skills/tao-dev/assets/templates/handoff.md').read_text(encoding='utf-8')), encoding='utf-8')
    draft.write_text(draft.read_text(encoding='utf-8').replace('status: draft\n', 'status: draft\nchange: ' + created['ids']['CHG_ID'] + '\n'), encoding='utf-8')
    saved = tao('handoff', created['ids']['CHG_ID'], '--from', str(draft.relative_to(directory)))
    return {'change': created['ids']['CHG_ID'], 'plan': created['path'], 'handoff': saved['outputs']['path']}
