"""Exercise the install checker against disposable skill directories, offline."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'verify_install.py'
REFERENCES = ('setup', 'adoption', 'dispatch', 'handoff',
              'health-check', 'codex', 'claude-code')

SKILL = ('---\nname: orchivane\ndescription: Coordinate project work across sessions.\n'
         'license: MIT\nmetadata:\n  version: "1.0.0"\n---\n# Orchivane\n\n'
         'Load only what is needed: [Setup](references/setup.md), '
         '[Adoption](references/adoption.md), [Dispatch](references/dispatch.md), '
         '[Handoff](references/handoff.md), [Health check](references/health-check.md), '
         '[Codex](references/codex.md), [Claude Code](references/claude-code.md).\n')


class VerifyInstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'skill'
        self.root.mkdir()
        self.write_skill(self.root)

    def write_skill(self, root, skill=SKILL):
        (root / 'agents').mkdir(parents=True, exist_ok=True)
        (root / 'references').mkdir(parents=True, exist_ok=True)
        (root / 'SKILL.md').write_text(skill, encoding='utf-8')
        (root / 'agents/openai.yaml').write_text('interface: {}\n', encoding='utf-8')
        for name in REFERENCES:
            (root / 'references' / f'{name}.md').write_text(f'# {name}\n', encoding='utf-8')

    def run_check(self, path=None, cwd=None):
        args = [sys.executable, str(SCRIPT)]
        if path is not None:
            args.append(str(path))
        return subprocess.run(args, cwd=cwd or self.temp.name,
                              capture_output=True, text=True)

    def assert_fails(self, clue, path=None, cwd=None):
        result = self.run_check(path, cwd)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn(clue, result.stdout)
        self.assertNotIn('Traceback', result.stderr)

    def test_complete_install_passes(self):
        result = self.run_check(self.root)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn('PASS:', result.stdout)

    def test_missing_reference_fails(self):
        (self.root / 'references' / 'health-check.md').unlink()
        self.assert_fails('references/health-check.md', self.root)

    def test_missing_entry_and_openai_file_fail(self):
        (self.root / 'SKILL.md').unlink()
        self.assert_fails('SKILL.md', self.root)
        self.write_skill(self.root)
        (self.root / 'agents' / 'openai.yaml').unlink()
        self.assert_fails('agents/openai.yaml', self.root)

    def test_unterminated_frontmatter_fails(self):
        self.write_skill(self.root, skill='---\nname: orchivane\ndescription: demo\n')
        self.assert_fails('frontmatter', self.root)

    def test_frontmatter_missing_metadata_fails(self):
        self.write_skill(self.root, skill=('---\nname: orchivane\n'
                                           'description: Coordinate a project.\n---\n# Demo\n'))
        self.assert_fails('metadata', self.root)

    def test_missing_link_target_fails(self):
        self.write_skill(self.root, skill=SKILL + '[Broken](references/broken.md)\n')
        self.assert_fails('references/broken.md', self.root)

    def test_escaping_link_fails(self):
        (self.root.parent / 'outside.md').write_text('outside')
        self.write_skill(self.root, skill=SKILL + '[Outside](../outside.md)\n')
        self.assert_fails('escapes', self.root)

    def test_private_path_fails(self):
        (self.root / 'references' / 'setup.md').write_text(
            '# Setup\n\nC:\\Users\\real-person\\private\n', encoding='utf-8')
        self.assert_fails('personal absolute path', self.root)

    def test_malformed_frontmatter_flow_sequence_fails(self):
        # Maintainer-reported false pass: `name: [` looks key-shaped but is
        # not a valid scalar, so every check must not pass.
        self.write_skill(self.root, skill=('---\nname: [\ndescription: demo\n'
                                           'metadata:\n  version: "0.4.1"\n---\n'))
        self.assert_fails('name', self.root)

    def test_invalid_frontmatter_scalar_shapes_fail(self):
        cases = {
            'flow-sequence name': ('---\nname: [demo]\ndescription: demo\n'
                                   'metadata:\n  version: "0.4.1"\n---\n', 'name'),
            'empty name': ('---\nname:\ndescription: demo\n'
                           'metadata:\n  version: "0.4.1"\n---\n', 'name'),
            'empty quoted description': ('---\nname: demo\ndescription: ""\n'
                                         'metadata:\n  version: "0.4.1"\n---\n', 'description'),
            'unclosed quoted version': ('---\nname: demo\ndescription: demo\n'
                                        'metadata:\n  version: "0.4.1\n---\n', 'version'),
            'multiline plain continuation': ('---\nname: demo\ndescription: demo\n'
                                             '  continued\nmetadata:\n  version: "0.4.1"\n---\n',
                                             'indented'),
            'indented keys outside metadata': ('---\nname: demo\ndescription: demo\n'
                                               'other:\n  field: value\n'
                                               'metadata:\n  version: "0.4.1"\n---\n',
                                               'unknown root key'),
        }
        for label, (skill, clue) in cases.items():
            with self.subTest(label=label):
                self.write_skill(self.root, skill=skill)
                self.assert_fails(clue, self.root)

    def test_version_must_belong_to_root_metadata_block(self):
        cases = {
            'metadata without version': ('---\nname: demo\ndescription: demo\n'
                                         'metadata:\n---\n', 'version'),
            'version under another key': ('---\nname: demo\ndescription: demo\n'
                                          'metadata:\nother:\n  version: "0.4.1"\n---\n',
                                          'version'),
            'version nested deeper in metadata': ('---\nname: demo\ndescription: demo\n'
                                                  'metadata:\n  nested:\n'
                                                  '    version: "0.4.1"\n---\n',
                                                  'version'),
            'top-level version line': ('---\nname: demo\ndescription: demo\n'
                                       'metadata:\nversion: "0.4.1"\n---\n', 'version'),
        }
        for label, (skill, clue) in cases.items():
            with self.subTest(label=label):
                self.write_skill(self.root, skill=skill)
                self.assert_fails(clue, self.root)

    def test_broken_quoted_scalars_fail_and_valid_escapes_pass(self):
        bad = {
            'embedded quote': ('---\nname: "or"chivane"\ndescription: demo\n'
                               'metadata:\n  version: "0.4.1"\n---\n', 'name'),
            'unclosed quote': ('---\nname: "or\ndescription: demo\n'
                               'metadata:\n  version: "0.4.1"\n---\n', 'name'),
            'broken version quote': ('---\nname: demo\ndescription: demo\n'
                                     'metadata:\n  version: "0.4."1"\n---\n', 'version'),
            'illegal escape backslash-q': ('---\nname: "a\\q"\ndescription: demo\n'
                                           'metadata:\n  version: "0.4.1"\n---\n', 'name'),
            'illegal hex escape backslash-xZZ': ('---\nname: "a\\xZZ"\ndescription: demo\n'
                                                 'metadata:\n  version: "0.4.1"\n---\n', 'name'),
        }
        for label, (skill, clue) in bad.items():
            with self.subTest(label=label):
                self.write_skill(self.root, skill=skill)
                self.assert_fails(clue, self.root)
        # a properly escaped quoted scalar still passes
        self.write_skill(self.root, skill=('---\nname: demo\n'
                                           'description: "Coordinate \\"work\\" across sessions."\n'
                                           'metadata:\n  version: "0.4.1"\n---\n'))
        self.assertEqual(self.run_check(self.root).returncode, 0)

    def test_frontmatter_subset_negative_matrix(self):
        cases = {
            'colon-space in plain description': ('---\nname: demo\n'
                                                 'description: Coordinate: work.\n'
                                                 'metadata:\n  version: "0.4.1"\n---\n',
                                                 'description'),
            'duplicate metadata blocks': ('---\nname: demo\ndescription: demo\n'
                                          'metadata:\n  version: "0.4.1"\n'
                                          'metadata: {}\n---\n', 'duplicate'),
            'duplicate description': ('---\nname: demo\ndescription: demo\n'
                                      'description:\nmetadata:\n  version: "0.4.1"\n---\n',
                                      'duplicate'),
            'duplicate version': ('---\nname: demo\ndescription: demo\n'
                                  'metadata:\n  version: "0.4.1"\n  version: "0.4.2"\n---\n',
                                  'duplicate'),
            'duplicate name': ('---\nname: demo\nname: other\ndescription: demo\n'
                               'metadata:\n  version: "0.4.1"\n---\n', 'duplicate'),
            'duplicate license': ('---\nname: demo\ndescription: demo\nlicense: MIT\n'
                                  'license: Apache-2.0\nmetadata:\n  version: "0.4.1"\n---\n',
                                  'duplicate'),
            'unknown root key': ('---\nname: demo\ndescription: demo\nfoo: bar\n'
                                 'metadata:\n  version: "0.4.1"\n---\n', 'unknown root key'),
            'unknown metadata key': ('---\nname: demo\ndescription: demo\n'
                                     'metadata:\n  other: x\n  version: "0.4.1"\n---\n',
                                     'unsupported key in metadata'),
            'key without space after colon': ('---\nname:demo\ndescription: demo\n'
                                              'metadata:\n  version: "0.4.1"\n---\n',
                                              'unsupported root line'),
            'tab-indented metadata block': ('---\nname: demo\ndescription: demo\n'
                                            'metadata:\n\tversion: "0.4.1"\n---\n',
                                            'tab indentation'),
            'mixed indentation': ('---\nname: demo\ndescription: demo\n'
                                  'metadata:\n  version: "0.4.1"\n   other: x\n---\n',
                                  'inconsistent indentation'),
            'trailing colon in plain': ('---\nname: demo\ndescription: ends:\n'
                                        'metadata:\n  version: "0.4.1"\n---\n', 'colon'),
            'colon-tab in plain': ('---\nname: demo\ndescription: a:\tb\n'
                                   'metadata:\n  version: "0.4.1"\n---\n', 'colon'),
            'control char in plain': ('---\nname: demo\ndescription: a\x07b\n'
                                      'metadata:\n  version: "0.4.1"\n---\n',
                                      'control character'),
            'control char in quotes': ('---\nname: demo\ndescription: "a\x07b"\n'
                                       'metadata:\n  version: "0.4.1"\n---\n',
                                       'control character'),
            'c1 control char': ('---\nname: demo\ndescription: a\x7fb\n'
                                'metadata:\n  version: "0.4.1"\n---\n',
                                'control character'),
            'unicode escape above range': ('---\nname: demo\n'
                                           'description: "\\U00110000"\n'
                                           'metadata:\n  version: "0.4.1"\n---\n',
                                           'description'),
            'unicode escape overflow': ('---\nname: demo\n'
                                        'description: "\\UFFFFFFFF"\n'
                                        'metadata:\n  version: "0.4.1"\n---\n',
                                        'description'),
            'leading-space tilde name': ('---\nname:  ~\ndescription: demo\n'
                                         'metadata:\n  version: "0.4.1"\n---\n', 'null'),
            'leading-space flow name': ('---\nname:  [x]\ndescription: demo\n'
                                        'metadata:\n  version: "0.4.1"\n---\n',
                                        'not a plain scalar'),
            'leading-space unclosed quote': ('---\nname:  "broken\ndescription: demo\n'
                                             'metadata:\n  version: "0.4.1"\n---\n',
                                             'malformed quoted'),
            'leading-tab tilde name': ('---\nname: \t~\ndescription: demo\n'
                                       'metadata:\n  version: "0.4.1"\n---\n', 'null'),
            'flow metadata map': ('---\nname: demo\ndescription: demo\n'
                                  'metadata: {version: "1"}\n---\n', 'bare'),
            'tilde null name': ('---\nname: ~\ndescription: demo\n'
                                'metadata:\n  version: "0.4.1"\n---\n', 'null'),
            'null description': ('---\nname: demo\ndescription: null\n'
                                 'metadata:\n  version: "0.4.1"\n---\n', 'null'),
            'NULL version': ('---\nname: demo\ndescription: demo\n'
                             'metadata:\n  version: NULL\n---\n', 'null'),
            'document end marker': ('---\nname: demo\ndescription: demo\n...\n'
                                    'metadata:\n  version: "0.4.1"\n---\n',
                                    'unsupported root line'),
            'free text line': ('---\nname: demo\ndescription: demo\nhello world\n'
                               'metadata:\n  version: "0.4.1"\n---\n',
                               'unsupported root line'),
            'text after closing quote': ('---\nname: demo\n'
                                         'description: "demo" extra\n'
                                         'metadata:\n  version: "0.4.1"\n---\n',
                                         'malformed quoted'),
        }
        for label, (skill, clue) in cases.items():
            with self.subTest(label=label):
                self.write_skill(self.root, skill=skill)
                self.assert_fails(clue, self.root)

    def test_frontmatter_subset_positive_matrix(self):
        bases = {
            'quoted colon-space description': ('---\nname: demo\n'
                                               'description: "Coordinate: work."\n'
                                               'metadata:\n  version: "0.4.1"\n---\n'),
            'trailing comment on plain': ('---\nname: demo\n'
                                          'description: demo # note\n'
                                          'metadata:\n  version: "0.4.1"\n---\n'),
            'trailing comment on quoted': ('---\nname: demo\ndescription: demo\n'
                                           'metadata:\n  version: "1.0.0" # keep\n---\n'),
            'comment line inside metadata block': ('---\nname: demo\ndescription: demo\n'
                                                   'metadata:\n  # the version of the skill\n'
                                                   '  version: "0.4.1"\n---\n'),
            'doubled single quote': ("---\nname: 'it''s fine'\ndescription: demo\n"
                                     'metadata:\n  version: "0.4.1"\n---\n'),
            'four-space indent and shuffled keys': ('---\nname: demo\n'
                                                    'metadata:\n    version: "0.4.1"\n'
                                                    'description: demo\nlicense: MIT\n---\n'),
            'unicode escape upper bound': ('---\nname: demo\n'
                                           'description: "\\U0010FFFF"\n'
                                           'metadata:\n  version: "0.4.1"\n---\n'),
            'apostrophe in plain description': ("---\nname: demo\n"
                                                "description: Track user's work # note: demo\n"
                                                'metadata:\n  version: "0.4.1"\n---\n'),
            'leading bom': None,
        }
        for label, skill in bases.items():
            with self.subTest(label=label):
                if label == 'leading bom':
                    (self.root / 'SKILL.md').write_bytes(
                        ('\ufeff' + bases['quoted colon-space description'])
                        .encode('utf-8'))
                else:
                    self.write_skill(self.root, skill=skill)
                self.assertEqual(self.run_check(self.root).returncode, 0)

    def test_private_link_in_openai_yaml_fails(self):
        # Synthetic disclosure probe: the maintained agent configuration must
        # be part of the privacy scan even though it is not Markdown. The
        # literal is split so the package-wide scan does not flag this file.
        (self.root / 'agents' / 'openai.yaml').write_text(
            'interface: {}\n# codex://' + 'threads/123-private\n', encoding='utf-8')
        self.assert_fails('private thread link', self.root)

    def test_unreadable_reference_reports_named_failure(self):
        (self.root / 'references' / 'setup.md').write_bytes(b'# Setup\n\xc3\x28\n')
        result = self.run_check(self.root)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn('setup.md: cannot be read as UTF-8', result.stdout)
        self.assertNotIn('Traceback', result.stderr)

    def test_package_root_and_default_cwd_resolution(self):
        nested = Path(self.temp.name) / 'skills' / 'orchivane'
        self.write_skill(nested)
        result = self.run_check(Path(self.temp.name))
        self.assertEqual(result.returncode, 0, result.stdout)
        result = self.run_check(cwd=str(self.root))
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_real_repo_passes_all_checks_and_references_complete(self):
        repo_root = Path(__file__).resolve().parents[1]
        spec = importlib.util.spec_from_file_location('verify_install_module', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        skill_dir = module.find_skill_dir(repo_root)
        for check in (module.required_files, module.frontmatter,
                      module.relative_links, module.private_leaks):
            self.assertEqual(check(skill_dir), [], check.__name__)
        actual = {path.stem for path in (skill_dir / 'references').glob('*.md')}
        self.assertTrue(actual)
        self.assertEqual(set(module.REQUIRED_REFERENCES), actual)


if __name__ == '__main__':
    unittest.main()
