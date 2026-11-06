#!/usr/bin/env python3
"""Static development-package integrity checks (not an install or runtime test)."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / 'skills' / 'agent-handoff-manager' / 'SKILL.md'
REQUIRED = [
    'README.md', 'README.en.md', 'WORK_ORDER.md', 'AGENTS.md',
    'INTENTS.md', 'INDENTS.md', 'ARCHITECTURE.md', 'PROJECT_TRACKER.md',
    'docs/INSTALLATION_AND_SHARING.md', 'docs/COPILOT_SETUP.md',
    'docs/MARKETPLACES.md', 'docs/COMPATIBILITY.md',
    '.github/copilot-instructions.md',
    'scripts/check_upstreams.py', 'upstreams.lock.json',
]
PLATFORMS = ('Claude Code', 'Codex', 'OpenCode', 'Antigravity', 'Copilot')

def validate(root=ROOT):
    root = Path(root)
    failures = []
    for rel in REQUIRED:
        if not (root / rel).is_file():
            failures.append(f'missing: {rel}')
    skill = root/'skills'/'agent-handoff-manager'/'SKILL.md'
    if not skill.is_file():
        failures.append('missing: canonical SKILL.md')
    else:
        content = skill.read_text(encoding='utf-8')
        if not content.startswith('---\n'):
            failures.append('SKILL.md missing YAML frontmatter')
        if '\nname: agent-handoff-manager\n' not in content:
            failures.append('skill name differs from canonical directory')
        if '\ndescription:' not in content:
            failures.append('SKILL.md missing description')
        if 'NOT an operational skill' not in content:
            failures.append('development status not explicit')
    if (root/'README.md').exists():
        s=(root/'README.md').read_text(encoding='utf-8')
        for p in PLATFORMS:
            if p.lower() not in s.lower():
                failures.append(f'README missing platform: {p}')
    return failures

if __name__ == '__main__':
    errors = validate()
    if errors:
        for err in errors:
            print('FAIL:',err)
        sys.exit(1)
    print('PASS: distribution scaffold structure, SKILL metadata, five-host descriptions')
    print('NOTE: runtime commands and remote install have NOT been tested.')
