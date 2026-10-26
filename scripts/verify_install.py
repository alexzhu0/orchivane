#!/usr/bin/env python3
"""Deterministic first-minute check for an installed skills/orchivane directory.

Usage:
    python scripts/verify_install.py                 # repository root, or the skill directory itself
    python scripts/verify_install.py PATH            # skill directory, or a package root with skills/orchivane
    python verify_install.py ~/.agents/skills/orchivane

Checks (pure standard library, read-only):
    required files        SKILL.md, agents/openai.yaml and every routed reference exist
    frontmatter           SKILL.md carries a --- delimited block matching the supported
                          YAML subset: root keys are name/description/license/metadata with
                          at most one occurrence each; metadata must be a bare block whose
                          only key is version (spaces-only, consistent indent); scalars are
                          non-empty plain (no `: `, no `:\t` and no trailing `:`, and no null
                          spellings for required fields), single-line double-quoted (full
                          escape rules) or single-quoted ('' doubling); comments start at a
                          space/tab followed by # outside quotes; a leading BOM is allowed.
                          This is a structural check of a restricted subset, not a YAML
                          parser: unsupported forms get a named FAIL.
    relative links        every local Markdown link inside the skill exists and stays inside it
    private path leaks    no personal paths, private chat/session links or credential-looking
                          tokens in the skill files, including the maintained agents/openai.yaml
Prints one PASS/FAIL line per check and a final PASS/FAIL summary; exits 0 or 1.
Unreadable or non-UTF-8 files produce a named FAIL, never a traceback.
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


def _read_text(path):
    try:
        return path.read_text(encoding='utf-8')
    except (OSError, UnicodeError):
        return None


def _quoted_scalar(value):
    """Validate a single-line quoted scalar's escape rules.

    Double-quoted bodies may contain the YAML escapes in '0abtnvfre "\\/N_LP'
    and \\x/\\u/\\U followed by 2/4/8 hex digits; \\u/\\U code points beyond
    0x10FFFF are malformed. Any other escape or a bare quote inside is
    malformed. Single-quoted bodies escape a quote by doubling it and keep
    backslashes as literal text.
    """
    quote = value[0]
    if len(value) < 2 or value[-1] != quote:
        return False
    body = value[1:-1]
    index = 0
    while index < len(body):
        char = body[index]
        if quote == '"' and char == '\\':
            if index + 1 >= len(body):
                return False  # trailing lone backslash
            esc = body[index + 1]
            if esc in 'xuU':
                width = {'x': 2, 'u': 4, 'U': 8}[esc]
                part = body[index + 2:index + 2 + width]
                if len(part) != width or any(digit not in '0123456789abcdefABCDEF'
                                             for digit in part):
                    return False
                if esc in 'uU' and int(part, 16) > 0x10FFFF:
                    return False  # code point beyond the Unicode range
                index += 2 + width
            elif esc in '0abtnvfre "\\/N_LP':
                index += 2
            else:
                return False
            continue
        if char == quote:
            if quote == "'" and index + 1 < len(body) and body[index + 1] == "'":
                index += 2
                continue
            return False  # bare quote inside the scalar
        index += 1
    return True


# Frontmatter subset v1.0 (see the module docstring).
ROOT_KEYS = ('name', 'description', 'license', 'metadata')
METADATA_KEYS = ('version',)
REQUIRED_SCALAR_FIELDS = ('name', 'description', 'version')
NULL_SPELLINGS = ('~', 'null', 'Null', 'NULL')
PLAIN_FORBIDDEN_FIRST = '-?:,[]{}#&*!|>\'"%@`'
_KEY_LINE = re.compile(r'^([A-Za-z0-9_-]+):(?: (.*)|)$')


def _split_comment(value):
    """Split a line value into (scalar part, comment tail).

    The mode is fixed by the first non-whitespace character: a quote starts
    a quoted scalar and the matching closing quote ends it; anything else is
    a plain scalar in which quotes are ordinary content. A comment starts at
    a space/tab followed by '#', but only outside the quoted portion.
    """
    head = len(value) - len(value.lstrip(' \t'))
    mode = (value[head] if head < len(value) and value[head] in ('"', "'")
            else None)
    if mode is None:
        match = re.search(r'[ \t]#', value)
        return (value[:match.start()], value[match.start()]) if match else (value, '')
    end = None
    index = head + 1
    while index < len(value):
        char = value[index]
        if mode == '"' and char == '\\':
            index += 2
            continue
        if char == mode:
            if mode == "'" and index + 1 < len(value) and value[index + 1] == "'":
                index += 2
                continue
            end = index
            break
        index += 1
    if end is None:
        return value, ''  # unclosed: _quoted_scalar reports it
    tail = value[end + 1:]
    comment = re.search(r'[ \t]#', tail)
    prefix = tail[:comment.start()] if comment else tail
    if prefix.strip():
        return value, ''  # text after the closing quote: _quoted_scalar reports it
    return value[:end + 1], (tail[comment.start():] if comment else '')


def _scalar_problem(field, value):
    """Return a problem string for an invalid scalar, or None."""
    if value is None or not value.strip():
        return f'{field} must be a nonempty scalar'
    scalar, _ = _split_comment(value)
    scalar = scalar.strip()
    if not scalar:
        return f'{field} must be a nonempty scalar'
    if any((ord(char) < 0x20 and char != '\t') or 0x7f <= ord(char) <= 0x9f
           for char in scalar):
        return f'{field} value contains a control character'
    if scalar[0] in ('"', "'"):
        if len(scalar) <= 2 or not _quoted_scalar(scalar):
            return f'{field} value is a malformed quoted scalar'
        return None
    if scalar[0] in PLAIN_FORBIDDEN_FIRST:
        return f'{field} value is not a plain scalar'
    if re.search(r':[ \t]', scalar) or scalar.endswith(':'):
        return f'{field} value contains a colon that must be quoted'
    if field in REQUIRED_SCALAR_FIELDS and scalar in NULL_SPELLINGS:
        return f'{field} value must not be a null spelling'
    return None


def frontmatter(skill_dir):
    problems = []
    path = skill_dir / 'SKILL.md'
    if not path.is_file():
        return problems  # reported by the required-files check
    try:
        text = path.read_text(encoding='utf-8-sig')  # a leading BOM is allowed
    except (OSError, UnicodeError):
        return ['SKILL.md cannot be read as UTF-8']
    opening = re.match(r'\A---[ \t]*\r?\n', text)
    if not opening:
        return ['missing or unterminated YAML frontmatter (--- ... ---)']
    rest = text[opening.end():]
    closing = re.search(r'(?m)^---[ \t]*\r?$', rest)
    if not closing:
        return ['missing or unterminated YAML frontmatter (--- ... ---)']
    body = rest[:closing.start()]
    seen_root = set()
    in_metadata = False
    metadata_indent = None
    version_seen = False
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue  # blank or full-line comment: never counts as a key
        if not line[:1].isspace():
            in_metadata = False
            match = _KEY_LINE.match(line)
            if not match:
                problems.append(f'unsupported root line: {stripped!r}')
                continue
            key, raw = match.group(1), match.group(2)
            if key not in ROOT_KEYS:
                problems.append(f'unknown root key: {key}')
                continue
            if key in seen_root:
                problems.append(f'duplicate root key: {key}')
                continue
            seen_root.add(key)
            if key == 'metadata':
                if raw is not None:
                    problems.append('metadata must be a bare block mapping (no inline value)')
                    continue
                in_metadata = True
                metadata_indent = None
            else:
                problem = _scalar_problem(key, raw)
                if problem:
                    problems.append(problem)
            continue
        if not in_metadata:
            problems.append(f'unsupported indented line outside the metadata block: {stripped!r}')
            continue
        if line.startswith('\t'):
            problems.append('tab indentation is not supported in the metadata block')
            continue
        indent = len(line) - len(line.lstrip(' '))
        if metadata_indent is None:
            metadata_indent = indent
        elif indent != metadata_indent:
            problems.append('inconsistent indentation in the metadata block')
            continue
        match = _KEY_LINE.match(line.lstrip(' '))
        if not match or match.group(1) not in METADATA_KEYS:
            problems.append(f'unsupported key in metadata block: {stripped!r}')
            continue
        raw = match.group(2)
        if version_seen:
            problems.append('duplicate version in metadata block')
            continue
        version_seen = True
        problem = _scalar_problem('version', raw)
        if problem:
            problems.append(problem)
    if 'name' not in seen_root:
        problems.append('frontmatter must declare name:')
    if 'description' not in seen_root:
        problems.append('frontmatter must declare description:')
    if 'metadata' not in seen_root:
        problems.append('frontmatter must contain a metadata: block')
    elif not version_seen:
        problems.append('metadata must declare a valid version: value')
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
        text = _read_text(path)
        if text is None:
            problems.append(f'{path.name}: cannot be read as UTF-8')
            continue
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
    # agents/openai.yaml is a required, maintained configuration file; it is
    # not Markdown (so it is absent from text_files()), but it still joins
    # the disclosure scan.
    files = text_files(skill_dir) + [skill_dir / 'agents/openai.yaml']
    for path in files:
        if not path.is_file():
            continue
        text = _read_text(path)
        if text is None:
            problems.append(f'{path.name}: cannot be read as UTF-8')
            continue
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
