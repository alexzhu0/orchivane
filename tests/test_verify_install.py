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
        }
        for label, (skill, clue) in cases.items():
            with self.subTest(label=label):
                self.write_skill(self.root, skill=skill)
                self.assert_fails(clue, self.root)

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
