"""Exercise the CLI against disposable packages, without network or client access."""
import errno
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'validate.py'

# Errnos that mean "symlinks are not possible here" on an otherwise healthy
# platform: filesystems without symlink support (EPERM/EOPNOTSUPP on POSIX)
# and Windows privilege restrictions (winerror 5/1314, which CPython surfaces
# as EACCES). Anything else is a real test-environment failure and must not
# be skipped.
_SYMLINK_UNAVAILABLE_ERRNOS = {getattr(errno, name) for name in
                               ('EPERM', 'EOPNOTSUPP', 'ENOTSUP', 'ENOSYS')} - {None}
_SYMLINK_WINDOWS_ERRORS = (5, 1314)  # ERROR_ACCESS_DENIED, ERROR_PRIVILEGE_NOT_HELD


def _symlink_unavailable(exc):
    """True only for known unsupported-platform or Windows privilege failures."""
    if not isinstance(exc, OSError):
        return False
    if getattr(exc, 'winerror', None) in _SYMLINK_WINDOWS_ERRORS:
        return True
    return exc.errno in _SYMLINK_UNAVAILABLE_ERRNOS


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
        try:
            (self.root / 'outside.md').symlink_to(self.root.parent / 'outside.md')
        except OSError as exc:
            if _symlink_unavailable(exc):
                self.skipTest(f'symlink creation unavailable on this platform: {exc}')
            raise
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


class SymlinkUnavailableTests(unittest.TestCase):
    """Injected-error checks for the narrow symlink skip decision."""

    def test_windows_privilege_errors_are_skippable(self):
        for winerror in (5, 1314):
            with self.subTest(winerror=winerror):
                exc = OSError(errno.EACCES, 'symlink privilege not held')
                exc.winerror = winerror
                self.assertTrue(_symlink_unavailable(exc))

    def test_unsupported_filesystem_errnos_are_skippable(self):
        for code in _SYMLINK_UNAVAILABLE_ERRNOS:
            with self.subTest(errno=code):
                self.assertTrue(_symlink_unavailable(OSError(code, 'unsupported')))

    def test_unexpected_errors_are_not_skippable(self):
        for exc in (OSError(errno.ENOENT, 'missing path'),
                    OSError(errno.EACCES, 'access denied'),
                    OSError(errno.EIO, 'i/o error'),
                    ValueError('not an OSError')):
            with self.subTest(exc=repr(exc)):
                self.assertFalse(_symlink_unavailable(exc))


if __name__ == '__main__':
    unittest.main()
