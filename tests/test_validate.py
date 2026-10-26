"""Exercise the CLI against disposable packages, without network or client access."""
import errno
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import unquote, urlsplit

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'validate.py'


def _load_validate():
    """Load scripts/validate.py as a module so fixtures track its whitelist."""
    spec = importlib.util.spec_from_file_location('validate_script', str(SCRIPT))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VALIDATE = _load_validate()

# Independent canaries for the real bilingual READMEs: written as equality
# invariants (EN == ZH) instead of snapshot numbers, so a 0.4.2-style content
# change passes as long as the two copies stay symmetric, and any re-opened
# whitelist in scripts/validate.py cannot hide a real asymmetry from these
# assertions. Update them deliberately only when the invariant itself changes.


def level_sequence(text):
    result = []
    for line in text.splitlines():
        match = re.match(r'^(#{1,6})\s+\S', line)
        if match:
            result.append(len(match.group(1)))
    return result


def fence_count(text):
    return len(re.findall(r'^[ \t]*(?:`{3,}|~{3,})[^\n]*$', text, re.M)) // 2


def readme_links(text):
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
        result.add(re.sub(r'\.zh-CN(?=\.\w+$)', '', unquote(url.path.split('#', 1)[0])))
    return result


class ValidateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'package'
        self.root.mkdir()
        self.write('plugin.json', json.dumps({'name': 'demo', 'version': '1.0.0'}))
        self.write('.codex-plugin/plugin.json', json.dumps({
            'name': 'demo', 'version': '1.0.0', 'skills': './skills/'}))
        self.skill = ('---\nname: demo\ndescription: >-\n  Coordinate a project.\n'
                      'metadata:\n  version: "1.0.0"\n---\n# Demo\n')
        self.write('skills/demo/SKILL.md', self.skill)
        self.write('skills/demo/agents/openai.yaml',
                   'interface:\n  short_description: "Coordinate project work across sessions"\n'
                   '  default_prompt: "Use $demo to coordinate this project."\n')
        self.write('README.md', '[Skill](skills/demo/SKILL.md)\n')

    def write(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')

    def run_check(self, script=SCRIPT, explicit_root=True):
        return subprocess.run([sys.executable, str(script)] +
                              ([str(self.root)] if explicit_root else []),
                              cwd=self.temp.name, capture_output=True, text=True)

    def assert_invalid(self, clue):
        result = self.run_check()
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn(clue, result.stderr)
        self.assertNotIn('Traceback', result.stderr)

    def test_valid_package_from_unrelated_cwd_is_read_only(self):
        before = {p.relative_to(self.root): p.read_bytes()
                  for p in self.root.rglob('*') if p.is_file()}
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(before, {p.relative_to(self.root): p.read_bytes()
                                 for p in self.root.rglob('*') if p.is_file()})

    def test_default_root_is_script_parent(self):
        target = self.root / 'scripts' / 'validate.py'
        target.parent.mkdir()
        shutil.copyfile(SCRIPT, target)
        result = self.run_check(target, explicit_root=False)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_normal_markdown_paths_titles_and_code_examples(self):
        self.write('guide (draft).md', '# Draft')
        self.write('guide(draft).md', '# Draft')
        self.write('README.md', '[Draft](<guide (draft).md>)\n'
                   '[Draft](guide(draft).md "Title")\n'
                   '`[Example](missing.md)`\n'
                   '```markdown\n[Example](missing.md)\n```\n')
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_bad_relative_link(self):
        self.write('README.md', '[Missing](missing.md)')
        self.assert_invalid('missing.md')

    def test_reference_link_and_encoded_escape(self):
        for target in ('missing.md', '%2e%2e/outside.md'):
            with self.subTest(target=target):
                self.write('README.md', '[Read][guide]\n\n[guide]: ' + target)
                self.assert_invalid('README.md')

    def test_existing_path_outside_package_is_rejected(self):
        (self.root.parent / 'outside.md').write_text('outside')
        self.write('README.md', '[Outside](../outside.md)')
        self.assert_invalid('escapes')

    def test_link_through_symlink_outside_package_is_rejected(self):
        (self.root.parent / 'outside.md').write_text('outside')
        (self.root / 'outside.md').symlink_to(self.root.parent / 'outside.md')
        self.write('README.md', '[Outside](outside.md)')
        self.assert_invalid('escapes')

    def test_mismatched_manifest_versions(self):
        self.write('plugin.json', '{"name":"demo", "version":"2.0.0"}')
        self.assert_invalid('version')

    def test_skill_version_and_name(self):
        for old, new, clue in [('"1.0.0"', '"2.0.0"', 'version'),
                               ('name: demo', 'name: other', 'name')]:
            with self.subTest(clue=clue):
                self.write('skills/demo/SKILL.md', self.skill.replace(old, new))
                self.assert_invalid(clue)

    def test_invalid_frontmatter_yaml_and_field_types(self):
        for value in ('[invalid', 'name: [demo]\ndescription: true',
                      'name: demo\ndescription: ""'):
            with self.subTest(value=value):
                self.write('skills/demo/SKILL.md', '---\n' + value + '\n---\n')
                self.assert_invalid('SKILL.md')

    def test_ui_constraints(self):
        for fields in ('short_description: short\n  default_prompt: "Use $demo"',
                       'short_description: "Coordinate project work across sessions"\n'
                       '  default_prompt: "Use the skill"'):
            with self.subTest(fields=fields):
                self.write('skills/demo/agents/openai.yaml', 'interface:\n  ' + fields)
                self.assert_invalid('openai.yaml')

    def test_private_paths_threads_and_obvious_tokens(self):
        examples = ['/Users/' + 'real-person/private', '/home/' + 'real-person/private',
                    'C:\\Users\\' + 'real-person\\private',
                    'codex://' + 'threads/123-private', 'ghp_' + 'a' * 36,
                    'claude://' + 'claude.ai/session/private',
                    'local_' + '12345678-1234-1234-1234-123456789abc',
                    'sk-' + 'a' * 36]
        for value in examples:
            with self.subTest(value=value[:12]):
                self.write('README.md', value)
                self.assert_invalid('README.md')

    def test_bare_claude_scheme_in_prose_is_allowed(self):
        self.write('docs/notes.md', 'Use claude://, then `claude://` links.')
        self.assertEqual(self.run_check().returncode, 0)

    def test_build_and_cache_files_are_excluded(self):
        for directory in ('.git', '.venv', '__pycache__', 'dist', 'node_modules', '.runtime'):
            self.write(directory + '/private.md', '/Users/' + 'real-person/private')
        self.assertEqual(self.run_check().returncode, 0)

    def test_skills_path_must_match_and_remain_inside(self):
        for path in ('./elsewhere', '../skills'):
            with self.subTest(path=path):
                self.write('.codex-plugin/plugin.json', json.dumps({
                    'name': 'demo', 'version': '1.0.0', 'skills': path}))
                self.assert_invalid('skills')

    def test_marketplace_local_source(self):
        name = '.agents/plugins/marketplace.json'
        for path in ('./', '../', './missing'):
            with self.subTest(path=path):
                self.write(name, json.dumps({'plugins': [
                    {'name': 'demo', 'source': {'path': path}}]}))
                result = self.run_check()
                if path == './':
                    self.assertEqual(result.returncode, 0, result.stderr)
                else:
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn('marketplace.json', result.stderr)

    def test_claude_manifest_matches_root(self):
        name = '.claude-plugin/plugin.json'
        self.write(name, json.dumps({'name': 'demo', 'version': '1.0.0'}))
        self.assertEqual(self.run_check().returncode, 0)
        for fields, clue in [({'name': 'demo', 'version': '2.0.0'}, 'version'),
                             ({'name': 'other', 'version': '1.0.0'}, 'name'),
                             ({'name': 'demo', 'version': '1.0.0', 'skills': './elsewhere'}, 'skills')]:
            with self.subTest(clue=clue):
                self.write(name, json.dumps(fields))
                self.assert_invalid(clue)

    def test_claude_marketplace_string_source(self):
        name = '.claude-plugin/marketplace.json'
        for path in ('./', '../', './missing'):
            with self.subTest(path=path):
                self.write(name, json.dumps({'plugins': [{'name': 'demo', 'source': path}]}))
                result = self.run_check()
                if path == './':
                    self.assertEqual(result.returncode, 0, result.stderr)
                else:
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn('marketplace.json', result.stderr)

    def test_malformed_manifest_fails_cleanly(self):
        self.write('plugin.json', '{')
        self.assert_invalid('plugin.json')

    def en_base(self, blocks=1, links=('[Skill](skills/demo/SKILL.md)',)):
        text = '# demo 1.0.0\n\n## One\n\n'
        text += '```sh\necho hi\n```\n' * blocks
        return text + '\n' + '\n'.join(links) + '\n'

    def zh_base(self, en, extra_h2=(), extra_blocks=None, extra_links=()):
        """Chinese copy built from the English one plus only documented drift."""
        if extra_blocks is None:
            extra_blocks = VALIDATE.BILINGUAL_ZH_EXTRA_CODE_BLOCKS
        parts = [en.rstrip('\n')]
        parts += ['## ' + title for title in extra_h2]
        parts += ['```sh\necho extra\n```'] * extra_blocks
        parts += list(extra_links)
        return '\n\n'.join(parts) + '\n'

    def write_bilingual_readmes(self, en=None, zh=None):
        if en is None:
            en = self.en_base()
        if zh is None:
            zh = self.zh_base(en)
        self.write('README.md', en)
        self.write('README.zh-CN.md', zh)

    def test_bilingual_readme_title_version_guard(self):
        self.write_bilingual_readmes()
        self.assertEqual(self.run_check().returncode, 0)
        for bad in ('# demo 2.0.0', '# demo', 'plain line'):
            with self.subTest(bad=bad):
                self.write_bilingual_readmes(
                    zh=bad + '\n' + self.en_base().split('\n', 1)[1])
                self.assert_invalid('README.zh-CN.md')

    def test_bilingual_readme_section_guard(self):
        self.write_bilingual_readmes()
        self.assertEqual(self.run_check().returncode, 0)
        # zh-CN-only section outside the documented whitelist
        self.write_bilingual_readmes(
            zh=self.zh_base(self.en_base(), extra_h2=('Extra',)))
        self.assert_invalid('section structure')
        # section re-leveled in one copy
        self.write_bilingual_readmes(
            zh=self.zh_base(self.en_base()).replace('## One', '### One', 1))
        self.assert_invalid('section structure')
        # every documented whitelisted H2 passes
        for title in sorted(VALIDATE.BILINGUAL_ZH_ONLY_H2):
            with self.subTest(title=title):
                self.write_bilingual_readmes(
                    zh=self.zh_base(self.en_base(), extra_h2=(title,)))
                self.assertEqual(self.run_check().returncode, 0)
        # any other extra H2 stays invalid
        self.write_bilingual_readmes(
            zh=self.zh_base(self.en_base(), extra_h2=('Other',)))
        self.assert_invalid('section structure')

    def test_bilingual_readme_code_block_guard(self):
        allowance = VALIDATE.BILINGUAL_ZH_EXTRA_CODE_BLOCKS
        self.write_bilingual_readmes()
        self.assertEqual(self.run_check().returncode, 0)
        # one block beyond the documented allowance
        self.write_bilingual_readmes(
            zh=self.zh_base(self.en_base(), extra_blocks=allowance + 1))
        self.assert_invalid('code block')
        # English block without a Chinese counterpart
        self.write_bilingual_readmes(
            en=self.en_base(blocks=2),
            zh=self.zh_base(self.en_base(), extra_blocks=allowance))
        self.assert_invalid('code block')

    def test_bilingual_readme_link_guard(self):
        self.write_bilingual_readmes()
        self.assertEqual(self.run_check().returncode, 0)
        # zh-CN-only link outside the documented whitelist
        self.write('docs/zh-only.md', '# Only\n')
        self.write_bilingual_readmes(
            zh=self.zh_base(self.en_base(), extra_links=('[Extra](docs/zh-only.md)',)))
        self.assert_invalid('docs/zh-only.md')
        # English link missing from the Chinese copy
        self.write('docs/en-only.md', '# Only\n')
        self.write_bilingual_readmes(
            en=self.en_base(links=('[Skill](skills/demo/SKILL.md)',
                                   '[Extra](docs/en-only.md)')),
            zh=self.zh_base(self.en_base()))
        self.assert_invalid('docs/en-only.md')
        # .zh-CN suffix variants map to their English counterparts
        self.write('docs/research.md', '# Research\n')
        self.write('docs/research.zh-CN.md', '# Research\n')
        self.write_bilingual_readmes(
            en=self.en_base(links=('[Skill](skills/demo/SKILL.md)',
                                   '[Research](docs/research.md)')),
            zh=self.zh_base(self.en_base(),
                            extra_links=('[Research](docs/research.zh-CN.md)',)))
        self.assertEqual(self.run_check().returncode, 0)
        # every documented whitelisted link passes
        for target in sorted(VALIDATE.BILINGUAL_ZH_ONLY_LINKS):
            self.write(target, '# Whitelisted\n')
            with self.subTest(target=target):
                self.write_bilingual_readmes(
                    zh=self.zh_base(self.en_base(),
                                    extra_links=('[Whitelisted](' + target + ')',)))
                self.assertEqual(self.run_check().returncode, 0)


    def test_real_bilingual_readmes_match_structural_invariants(self):
        root = Path(__file__).resolve().parents[1]
        en = (root / 'README.md').read_text(encoding='utf-8')
        zh = (root / 'README.zh-CN.md').read_text(encoding='utf-8')
        self.assertTrue(level_sequence(en))
        self.assertEqual(level_sequence(en), level_sequence(zh))
        self.assertGreater(fence_count(en), 0)
        self.assertEqual(fence_count(en), fence_count(zh))
        en_links, zh_links = readme_links(en), readme_links(zh)
        self.assertTrue(en_links)
        self.assertEqual(en_links, zh_links)

    def test_real_version_consistent_across_all_sources(self):
        root = Path(__file__).resolve().parents[1]
        sources = {}
        for name in ('plugin.json', '.codex-plugin/plugin.json', '.claude-plugin/plugin.json'):
            sources[name] = json.loads((root / name).read_text(encoding='utf-8'))['version']
        for name in ('README.md', 'README.zh-CN.md'):
            first = (root / name).read_text(encoding='utf-8').splitlines()[0]
            match = re.fullmatch(r'#\s+.*\s+([0-9][^\s]*)', first.lstrip('\ufeff').strip())
            self.assertIsNotNone(match, name)
            sources[name] = match.group(1)
        skill = (root / 'skills/orchivane/SKILL.md').read_text(encoding='utf-8')
        frontmatter = re.match(r'\A---\r?\n(.*?)\r?\n---', skill, re.S).group(1)
        match = re.search(r'(?m)^\s+version:\s*"?([^"\s]+)"?', frontmatter)
        self.assertIsNotNone(match)
        sources['skills/orchivane/SKILL.md'] = match.group(1)
        self.assertEqual(len(set(sources.values())), 1, sources)


if __name__ == '__main__':
    unittest.main()
