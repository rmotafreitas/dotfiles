#!/usr/bin/env python3
"""Build vscode/ricardo.code-profile from the files in vscode/ for Profiles: Import Profile."""
import json
from pathlib import Path

VSCODE = Path(__file__).resolve().parents[1] / 'vscode'
PROFILE = VSCODE / 'ricardo.code-profile'


def build() -> str:
    # Each resource is itself a JSON-encoded string, matching what VS Code's own export writes.
    snippets = {p.name: p.read_text() for p in sorted((VSCODE / 'snippets').glob('*.json'))}
    extensions = [{'identifier': {'id': line.strip()}}
                  for line in (VSCODE / 'extensions.txt').read_text().splitlines() if line.strip()]
    profile = {
        'name': 'Ricardo',
        'settings': json.dumps({'settings': (VSCODE / 'settings.json').read_text()}),
        'snippets': json.dumps({'snippets': snippets}),
        'extensions': json.dumps(extensions),
    }
    return json.dumps(profile, indent=2) + '\n'


if __name__ == '__main__':
    PROFILE.write_text(build())
    print(f'Wrote {PROFILE}')
