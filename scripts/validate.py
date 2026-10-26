#!/usr/bin/env python3
"""Offline release checks, not a complete official schema or secret scanner."""
import argparse
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

try:
    import yaml
except ImportError:
    sys.exit('ERROR: PyYAML is required for development checks; install requirements-dev.txt.')

EXCLUDED = {'.git', '.venv', 'venv', '__pycache__', 'dist', 'build',
            'node_modules', '.pytest_cache', '.mypy_cache', '.ruff_cache', '.runtime'}
PRIVATE = {
    'personal absolute path': re.compile(r'(?:/(?:Users|home)/[\w.-]+(?:/|\b)|[A-Za-z]:\\Users\\[\w.-]+)', re.I),
    'private thread link': re.compile(r'codex://' r'threads/[^\s\x22\x27]+'),
    'private session link': re.compile(r'claude://' r'[A-Za-z0-9][^\s\x22\x27\x60()<>]*'),
    'private session id': re.compile(r'\blocal_[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\b'),
    'possible credential': re.compile(r'\b(?:sk-(?:proj-)?[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|AKIA[A-Z0-9]{16})\b'),
}

# Documented bilingual drift allowances between README.md and README.zh-CN.md.
# The checks below fail on ANY difference outside these entries, so resolving
# a drift means editing the READMEs and then shrinking the matching entry.
# All three allowances are empty after the 0.4.1 alignment: zh-CN now has no
# sections beyond the English ones, the previously split install code blocks
# were merged, and the evidence table lists the same records in both copies.
# Re-adding an entry requires documenting here why that asymmetry is legitimate.
BILINGUAL_ZH_ONLY_H2 = set()  # zh-CN-only H2 sections without an English counterpart.
BILINGUAL_ZH_EXTRA_CODE_BLOCKS = 0  # extra fenced code blocks in README.zh-CN.md.
BILINGUAL_ZH_ONLY_LINKS = set()  # relative links that exist only in the Chinese guide.


def heading_sequence(text):
    """Ordered (level, title) pairs for every ATX heading."""
    result = []
    for line in text.splitlines():
        match = re.match(r'^(#{1,6})\s+(.+?)\s*$', line)
        if match:
            result.append((len(match.group(1)), match.group(2).strip()))
    return result


def code_block_count(text):
    fences = re.findall(r'^[ \t]*(?:`{3,}|~{3,})[^\n]*$', text, re.M)
    return len(fences) // 2


def relative_link_paths(text):
    """Same link-extraction shortcut as the file walk below; keep both in sync."""
    prose = re.sub(r'(?ms)^\s*(`{3,}|~{3,})[^\n]*\n.*?^\s*\1\s*$', '', text)
    prose = re.sub(r'`+[^`\n]*`+', '', prose)
    targets = re.findall(r'!?\[[^\]\n]*\]\(\s*(<[^>\n]+>|(?:[^\s()]+|\([^()\n]*\))+)', prose)
    targets += re.findall(r'^\s{0,3}\[[^\]\n]+\]:\s*(<[^>\n]+>|\S+)', prose, re.M)
    result = set()
    for target in targets:
        target = target.strip('<>')
        try:
            url = urlsplit(target)
        except ValueError:
            continue
        if url.scheme or url.netloc or not url.path:
            continue
        result.add(unquote(url.path.split('#', 1)[0]))
    return result


def bilingual_link_key(target):
    """Map a .zh-CN document variant to its English counterpart target."""
    return re.sub(r'\.zh-CN(?=\.\w+$)', '', target)


def validate(root):
    errors = []

    def error(path, message):
        errors.append(f'{path.relative_to(root)}: {message}')

    def inside(path, value, base):
        if not isinstance(value, str) or not value.strip():
            error(path, 'path must be a nonempty string')
            return None
        target = (base / value).resolve()
        if not target.is_relative_to(root):
            error(path, f'path escapes package root: {value}')
            return None
        if not target.exists():
            error(path, f'missing path: {value}')
            return None
        if any(part in EXCLUDED for part in target.relative_to(root).parts):
            error(path, f'path points into excluded files: {value}')
            return None
        return target

    def mapping(path, parser, content=None):
        try:
            value = parser(path.read_text(encoding='utf-8') if content is None else content)
            if not isinstance(value, dict):
                raise ValueError('expected a mapping/object')
            return value
        except (OSError, UnicodeError, ValueError, yaml.YAMLError) as exc:
            error(path, f'invalid or unreadable data ({type(exc).__name__})')
            return {}

    manifests = [root / 'plugin.json', root / '.codex-plugin/plugin.json']
    configs = [mapping(path, json.loads) for path in manifests]
    for key in ('name', 'version'):
        for path, config in zip(manifests, configs):
            if not isinstance(config.get(key), str) or not config[key].strip():
                error(path, f'{key} must be a nonempty string')
        if configs[0].get(key) != configs[1].get(key):
            error(manifests[1], f'{key} differs from root plugin.json')
    skill_roots = [inside(path, config.get('skills', './skills/'), root)
                   for path, config in zip(manifests, configs)]
    if skill_roots[0] != skill_roots[1]:
        error(manifests[1], 'skills path differs from root plugin.json')
    skill_root = skill_roots[0]
    claude_path = root / '.claude-plugin/plugin.json'
    if claude_path.exists():
        claude = mapping(claude_path, json.loads)
        for key in ('name', 'version'):
            if claude.get(key) != configs[0].get(key):
                error(claude_path, f'{key} differs from root plugin.json')
        if inside(claude_path, claude.get('skills', './skills/'), root) != skill_root:
            error(claude_path, 'skills path differs from root plugin.json')
    skills = sorted(skill_root.glob('*/SKILL.md')) if skill_root and skill_root.is_dir() else []
    if not skills:
        error(manifests[0], 'skills path must contain skill directories with SKILL.md')
    for path in skills:
        try:
            text = path.read_text(encoding='utf-8')
        except (OSError, UnicodeError):
            error(path, 'cannot read SKILL.md')
            continue
        match = re.match(r'\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)', text, re.S)
        if not match:
            error(path, 'missing YAML frontmatter')
            continue
        meta = mapping(path, yaml.safe_load, match[1])
        name = meta.get('name')
        if (not isinstance(name, str) or len(name) > 64 or
                not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', name) or name != path.parent.name):
            error(path, 'name must match its directory and use lowercase letters, digits and single hyphens (max 64)')
        description = meta.get('description')
        if (not isinstance(description, str) or not description.strip() or
                len(description) > 1024 or '<' in description or '>' in description):
            error(path, 'description must be nonempty text, at most 1024 characters, without angle brackets')
        metadata = meta.get('metadata', {})
        if not isinstance(metadata, dict):
            error(path, 'metadata must be a mapping')
        elif 'version' in metadata and metadata['version'] != configs[0].get('version'):
            error(path, 'metadata.version differs from plugin version')
        ui_path = path.parent / 'agents/openai.yaml'
        ui = mapping(ui_path, yaml.safe_load).get('interface')
        if not isinstance(ui, dict):
            error(ui_path, 'interface must be a mapping')
            continue
        short = ui.get('short_description')
        if not isinstance(short, str) or not 25 <= len(short) <= 64:
            error(ui_path, 'short_description must be 25–64 characters')
        prompt = ui.get('default_prompt')
        if not isinstance(prompt, str) or not prompt.strip() or f'${path.parent.name}' not in prompt:
            error(ui_path, 'default_prompt must be nonempty and mention $' + path.parent.name)

    for relative in ('marketplace.json', '.agents/plugins/marketplace.json',
                     '.codex-plugin/marketplace.json', '.claude-plugin/marketplace.json'):
        path = root / relative
        if not path.exists():
            continue
        entries = mapping(path, json.loads).get('plugins')
        if not isinstance(entries, list) or not entries:
            error(path, 'plugins must be a nonempty list')
            continue
        for entry in entries:
            source = entry.get('source') if isinstance(entry, dict) else None
            local = source.get('path') if isinstance(source, dict) else source
            target = inside(path, local, root)
            if target and not target.is_dir():
                error(path, 'source path must be a directory')

    # Bilingual README guards, active only when both copies exist.
    en_readme, zh_readme = root / 'README.md', root / 'README.zh-CN.md'
    if en_readme.exists() and zh_readme.exists():
        expected_version = configs[0].get('version')
        for path in (en_readme, zh_readme):
            try:
                text = path.read_text(encoding='utf-8')
            except OSError:
                error(path, 'cannot read README')
                continue
            lines = text.splitlines()
            first = lines[0].lstrip('\ufeff').strip() if lines else ''
            match = re.fullmatch(r'#\s+.*\s+([0-9][^\s]*)', first)
            if not match:
                error(path, 'first line must be a versioned H1 title, e.g. "# Orchivane 0.4.1"')
            elif match.group(1) != expected_version:
                error(path, f'first-line title version {match.group(1)!r} differs from plugin version {expected_version!r}')
        en_text = en_readme.read_text(encoding='utf-8')
        zh_text = zh_readme.read_text(encoding='utf-8')
        # Translated headings cannot be matched by title text, so parity is
        # pinned through the heading LEVEL sequence: after dropping the
        # documented zh-CN-only sections, the level sequences must be equal.
        # That pins section count, nesting depth and level order; a section
        # added, removed, moved across levels or re-leveled in either copy
        # fails here.
        en_levels = [level for level, _ in heading_sequence(en_text)]
        zh_levels = [level for level, title in heading_sequence(zh_text)
                     if not (level == 2 and title in BILINGUAL_ZH_ONLY_H2)]
        if zh_levels != en_levels:
            error(zh_readme, f'section structure drifted: README.md levels {en_levels}, '
                             f'README.zh-CN.md levels {zh_levels} '
                             '(after removing the documented zh-CN-only sections)')
        en_blocks = code_block_count(en_text)
        zh_blocks = code_block_count(zh_text)
        if zh_blocks - en_blocks != BILINGUAL_ZH_EXTRA_CODE_BLOCKS:
            error(zh_readme, f'code block counts drifted: README.md has {en_blocks}, '
                             f'README.zh-CN.md has {zh_blocks}; expected {en_blocks + BILINGUAL_ZH_EXTRA_CODE_BLOCKS}')
        en_links = {bilingual_link_key(target) for target in relative_link_paths(en_text)}
        zh_links = {bilingual_link_key(target) for target in relative_link_paths(zh_text)}
        missing = sorted(en_links - zh_links)
        if missing:
            error(zh_readme, 'README.md links missing from README.zh-CN.md: ' + ', '.join(missing))
        unexpected_links = sorted(zh_links - en_links - BILINGUAL_ZH_ONLY_LINKS)
        if unexpected_links:
            error(zh_readme, 'zh-CN-only links outside the documented whitelist: '
                             + ', '.join(unexpected_links))

    count = 0
    for directory, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = sorted(name for name in dirs if name not in EXCLUDED)
        for name in list(dirs):
            path = Path(directory) / name
            if path.is_symlink():
                inside(path, name, Path(directory))
                dirs.remove(name)
        for name in sorted(files):
            path = Path(directory) / name
            if path.suffix in {'.pyc', '.pyo'} or name == '.DS_Store':
                continue
            if not inside(path, name, Path(directory)):
                continue
            count += 1
            try:
                text = path.read_text(encoding='utf-8')
            except UnicodeError:
                continue  # Binary assets are outside these text-only disclosure checks.
            except OSError:
                error(path, 'cannot read file')
                continue
            for label, pattern in PRIVATE.items():
                for match in pattern.finditer(text):
                    line = text.count('\n', 0, match.start()) + 1
                    error(path, f'line {line}: {label}')
            if path.suffix.lower() != '.md':
                continue
            # shortcut: ordinary Markdown links only; use a parser if HTML/complex syntax is introduced.
            prose = re.sub(r'(?ms)^\s*(`{3,}|~{3,})[^\n]*\n.*?^\s*\1\s*$', '', text)
            prose = re.sub(r'`+[^`\n]*`+', '', prose)
            targets = re.findall(r'!?\[[^\]\n]*\]\(\s*(<[^>\n]+>|(?:[^\s()]+|\([^()\n]*\))+)', prose)
            targets += re.findall(r'^\s{0,3}\[[^\]\n]+\]:\s*(<[^>\n]+>|\S+)', prose, re.M)
            for target in targets:
                target = target.strip('<>')
                try:
                    url = urlsplit(target)
                except ValueError:
                    error(path, f'invalid link: {target}')
                    continue
                if url.scheme or url.netloc or not url.path:
                    continue
                inside(path, unquote(url.path), path.parent)
    return errors, count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', nargs='?', type=Path, default=Path(__file__).resolve().parents[1])
    root = parser.parse_args().root.resolve()
    if not root.is_dir():
        print('ERROR: package root must be an existing directory', file=sys.stderr)
        return 1
    errors, count = validate(root)
    if errors:
        for message in errors:
            print('ERROR: ' + message, file=sys.stderr)
        return 1
    print(f'OK: static package checks passed ({count} files scanned).')
    return 0


if __name__ == '__main__':
    sys.exit(main())
