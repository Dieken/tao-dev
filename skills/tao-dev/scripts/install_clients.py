"""Native project skill locations; no client process or configuration changes.

Discovery contracts:
https://code.claude.com/docs/en/skills
https://developers.openai.com/codex/skills
https://cursor.com/docs/skills.md
https://kiro.dev/docs/skills/
"""

from pathlib import Path


PROJECT_SKILLS = {
    'claude': '.claude/skills/tao-dev',
    'codex': '.agents/skills/tao-dev',
    'cursor': '.cursor/skills/tao-dev',
    'kiro': '.kiro/skills/tao-dev',
}


def destination(project, client):
    """Return the documented native project path, never a global fallback."""
    if client not in PROJECT_SKILLS:
        raise ValueError(f'Unsupported client: {client}. Choose {", ".join(PROJECT_SKILLS)}.')
    return Path(project) / PROJECT_SKILLS[client]
