#!/usr/bin/env python3
"""Deterministic first-minute check for an installed skills/orchivane directory.

Usage:
    python scripts/verify_install.py                 # repository root, or the skill directory itself
    python scripts/verify_install.py PATH            # skill directory, or a package root with skills/orchivane
    python verify_install.py ~/.agents/skills/orchivane

Checks (pure standard library, read-only):
    required files        SKILL.md, agents/openai.yaml and every routed reference exist
    frontmatter           SKILL.md carries the --- delimited block with name, description and metadata.version
    relative links        every local Markdown link inside the skill exists and stays inside it
    private path leaks    no personal paths, private chat/session links or credential-looking tokens
Prints one PASS/FAIL line per check and a final PASS/FAIL summary; exits 0 or 1.
"""
import argparse
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

# Keep this list in sync with the routing table in SKILL.md ("Required reference").
REQUIRED_REFERENCES = ('setup', 'adoption', 'dispatch', 'handoff',
                       'health-check', 'codex', 'claude-code')

# Same disclosure patterns as scripts/validate.py; keep both in sync.
PRIVATE = {
    'personal absolute path': re.compile(r'(?:/(?:Users|home)/[\w.-]+(?:/|\b)|[A-Za-z]:\\Users\\[\w.-]+)', re.I),
    'private thread link': re.compile(r'codex://' r'threads/[^\s\x22\x27]+'),
    'private session link': re.compile(r'claude://' r'[A-Za-z0-9][^\s\x22\x27\x60()<>]*'),
    'private session id': re.compile(r'\blocal_[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\b'),
    'possible credential': re.compile(r'\b(?:sk-(?:proj-)?[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|AKIA[A-Z0-9]{16})\b'),
}


def find_skill_dir(candidate):
    candidate = Path(candidate)
    if (candidate / 'SKILL.md').is_file():
        return candidate
    if (candidate / 'skills' / 'orchivane' / 'SKILL.md').is_file():
        return candidate / 'skills' / 'orchivane'
    return candidate  # not a recognized layout; the checks below name what is missing


def text_files(skill_dir):
    files = [skill_dir / 'SKILL.md']
    files += [skill_dir / 'references' / f'{name}.md' for name in REQUIRED_REFERENCES]
    return files


def required_files(skill_dir):
    problems = []
    for name in ('SKILL.md', 'agents/openai.yaml'):
        if not (skill_dir / name).is_file():
            problems.append(f'missing {name}')
    for name in REQUIRED_REFERENCES:
        relative = f'references/{name}.md'
        if not (skill_dir / relative).is_file():
            problems.append(f'missing {relative}')
    return problems


def frontmatter(skill_dir):
    problems = []
    path = skill_dir / 'SKILL.md'
    if not path.is_file():
        return problems  # reported by the required-files check
    try:
        text = path.read_text(encoding='utf-8')
    except (OSError, UnicodeError):
        return ['SKILL.md cannot be read as UTF-8']
    match = re.match(r'\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|$)', text, re.S)
    if not match:
        return ['missing or unterminated YAML frontmatter (--- ... ---)']
    body = match[1]
    if not re.search(r'(?m)^name:\s*\S+', body):
        problems.append('frontmatter must declare a nonempty name:')
    if not re.search(r'(?m)^description:\s*\S+', body):
        problems.append('frontmatter must declare a nonempty description:')
    if not re.search(r'(?m)^metadata:\s*$', body):
        problems.append('frontmatter must contain a metadata: block')
    elif not re.search(r'(?m)^\s+version:\s*\S', body):
        problems.append('metadata must declare version:')
    return problems


def link_targets(text):
    """Same link-extraction shortcut as scripts/validate.py; keep both in sync."""
    prose = re.sub(r'(?ms)^\s*(`{3,}|~{3,})[^\n]*\n.*?^\s*\1\s*$', '', text)
    prose = re.sub(r'`+[^`\n]*`+', '', prose)
    targets = re.findall(r'!?\[[^\]\n]*\]\(\s*(<[^>\n]+>|(?:[^\s()]+|\([^()\n]*\))+)', prose)
    targets += re.findall(r'^\s{0,3}\[[^\]\n]+\]:\s*(<[^>\n]+>|\S+)', prose, re.M)
    return targets


def relative_links(skill_dir):
    problems = []
    skill_root = skill_dir.resolve()
    for path in text_files(skill_dir):
        if not path.is_file():
            continue
        text = path.read_text(encoding='utf-8')
        for target in link_targets(text):
            target = target.strip('<>')
            try:
                url = urlsplit(target)
            except ValueError:
                problems.append(f'{path.name}: invalid link target {target!r}')
                continue
            if url.scheme or url.netloc or not url.path:
                continue  # external links are outside install integrity
            resolved = (path.parent / unquote(url.path.split('#', 1)[0])).resolve()
            if not resolved.exists():
                problems.append(f'{path.name}: missing link target {target!r}')
            elif not resolved.is_relative_to(skill_root):
                problems.append(f'{path.name}: link escapes the skill directory: {target!r}')
    return problems


def private_leaks(skill_dir):
    problems = []
    for path in text_files(skill_dir):
        if not path.is_file():
            continue
        text = path.read_text(encoding='utf-8')
        for label, pattern in PRIVATE.items():
            for match in pattern.finditer(text):
                line = text.count('\n', 0, match.start()) + 1
                problems.append(f'{path.name} line {line}: {label}')
    return problems


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('root', nargs='?', default='.',
                        help='skill directory or package root (default: current directory)')
    skill_dir = find_skill_dir(parser.parse_args().root)
    checks = [('required files', required_files),
              ('SKILL.md frontmatter', frontmatter),
              ('relative link targets', relative_links),
              ('private path leaks', private_leaks)]
    failed = False
    for label, function in checks:
        problems = function(skill_dir)
        if problems:
            failed = True
            print(f'[FAIL] {label}')
            for problem in problems:
                print(f'       - {problem}')
        else:
            print(f'[PASS] {label}')
    if failed:
        print(f'FAIL: {skill_dir} is incomplete or unsafe; fix the issues above.')
        return 1
    print(f'PASS: {skill_dir} looks like a complete orchivane install.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
