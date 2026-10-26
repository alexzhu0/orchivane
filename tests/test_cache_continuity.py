"""Source-preservation checks and offline replay; never launches the native CLI."""
from collections import Counter
import errno
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('cache_continuity', ROOT / 'tests/cache_continuity.py')
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)


class CacheContinuityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'cache'
        (self.source / 'references').mkdir(parents=True)
        (self.source / 'SKILL.md').write_text('[Read](references/task.md)\n')
        (self.source / 'references/task.md').write_text('Frozen task rules\n')

    def test_full_copy_survives_original_cache_deletion(self):
        expected = fixture.inventory(self.source)
        retained = self.root / 'project/retained'
        shutil.copytree(self.source, retained)
        shutil.rmtree(self.source)
        fixture.verify_source(retained, expected)
        self.assertEqual((retained / 'references/task.md').read_text(), 'Frozen task rules\n')

    def test_rejects_modified_or_incomplete_copies(self):
        expected = fixture.inventory(self.source)
        (self.source / 'SKILL.md').write_text('Wrong source')
        with self.assertRaises(ValueError):
            fixture.verify_source(self.source, expected)
        (self.source / 'references/task.md').unlink()
        with self.assertRaises(ValueError):
            fixture.verify_source(self.source, expected)

    def test_rejects_symlink_dependent_copy(self):
        try:
            (self.source / 'alias').symlink_to(self.source / 'references', target_is_directory=True)
        except OSError as exc:
            if (getattr(exc, 'winerror', None) not in (50, 1314)
                    and exc.errno not in (errno.ENOSYS, errno.ENOTSUP)):
                raise
            self.skipTest(f'Symlink creation unavailable: {exc}')
        with self.assertRaises(ValueError):
            fixture.inventory(self.source)

    def test_symlink_creation_skips_only_capability_errors(self):
        privilege = PermissionError(errno.EACCES, 'Symlink privilege not held')
        privilege.winerror = 1314
        unsupported = OSError(errno.EINVAL, 'Windows symlinks not supported')
        unsupported.winerror = 50
        cases = [
            (privilege, unittest.SkipTest),
            (unsupported, unittest.SkipTest),
            (OSError(errno.ENOSYS, 'Symlinks not implemented'), unittest.SkipTest),
            (OSError(errno.ENOTSUP, 'Symlinks not supported'), unittest.SkipTest),
            (PermissionError(errno.EACCES, 'Unexpected access denial'), PermissionError),
            (FileNotFoundError(errno.ENOENT, 'Missing parent'), FileNotFoundError),
            (OSError(errno.EIO, 'Filesystem I/O failure'), OSError),
        ]
        for error, expected in cases:
            with self.subTest(errno=error.errno, winerror=getattr(error, 'winerror', None)):
                with patch.object(Path, 'symlink_to', side_effect=error):
                    with self.assertRaises(expected):
                        self.test_rejects_symlink_dependent_copy()

    def test_rejects_missing_external_or_file_uri_reference(self):
        (self.root / 'outside.md').write_text('Outside dependency')
        for target in ['missing.md', '../outside.md', '../%6futside.md', (self.root / 'outside.md').as_uri()]:
            with self.subTest(target=target):
                (self.source / 'SKILL.md').write_text(f'[Read]({target})\n')
                with self.assertRaises(ValueError):
                    fixture.verify_source(self.source, fixture.inventory(self.source))

    def test_native_evidence_replay(self):
        evidence = ROOT / 'tests/outputs/cache-continuity'
        result = json.loads((evidence / 'results.json').read_text())
        events = json.loads((evidence / 'reader-events.json').read_text())
        for worker, phases in result['read_counts'].items():
            for phase, counts in phases.items():
                selected = [e for e in events if e['worker'] == worker and e['phase'] == phase]
                self.assertEqual(counts, {'reads': len(selected), 'failures': sum(not e['ok'] for e in selected)})
        self.assertEqual(dict(Counter(e['error'] for e in events if not e['ok'])), result['failure_kinds'])
        self.assertFalse(result['old_cache_exists_after_marketplace_refresh'])
        self.assertFalse(result['old_cache_exists_after_install'])
        self.assertTrue(any(not e['ok'] for e in events if e['worker'] == 'cache'))
        self.assertTrue(all(e['ok'] for e in events if e['worker'] == 'retained'))
        for phase in ('before', 'marketplace-refresh', 'plugin-install', 'after'):
            self.assertGreater(result['read_counts']['retained'][phase]['reads'], 0)
        artifacts = json.loads((evidence / 'project-artifacts.json').read_text())
        for name, content in artifacts['files'].items():
            self.assertFalse(Path(name).is_absolute())
            self.assertNotIn('..', Path(name).parts)
            self.assertEqual(hashlib.sha256(content.encode()).hexdigest(), artifacts['sha256'][name])
        self.assertEqual(json.loads(artifacts['files']['work/n2-summary.json']), {'row_count': 3, 'total_quantity': 9})
        for name, digest in result['old_source_files'].items():
            self.assertEqual(artifacts['sha256']['retained/0.4.1/orchivane/' + name], digest)
        self.assertEqual(result['post_update_continuation']['source_version'], '0.4.1')
        if json.loads((ROOT / 'plugin.json').read_text())['version'] == result['new_version']:
            self.assertEqual(fixture.inventory(ROOT / 'skills/orchivane'), result['new_source_files'])
        isolation = json.loads((evidence / 'isolation.json').read_text())
        self.assertEqual(isolation['global_before_sha256'], isolation['global_after_sha256'])

    def test_forward_planning_evidence(self):
        evidence = ROOT / 'tests/outputs/cache-continuity'
        data = json.loads((evidence / 'forward-test.json').read_text())
        self.assertEqual(data['plan']['agent_turns'], 2)
        expected = {'project-a': False, 'project-b': True}
        self.assertEqual({p['project']: p['refresh_can_proceed_now']
                          for p in data['baseline']['projects']}, expected)
        for action in ('marketplace_refresh_permitted', 'package_replacement_permitted'):
            self.assertEqual({p['project']: p['refresh_now'][action]
                              for p in data['candidate']['projects']}, expected)
        self.assertEqual(data['baseline']['reading_receipt']['observed_operating_source_version'], '0.4.1')
        self.assertEqual(data['candidate']['reading_receipt']['observed_entry_version'], '0.4.2')
        for project, complete in [('project-a', False), ('project-b', True)]:
            roles = json.loads(data['inputs'][project + '/roles.json'])
            self.assertEqual(roles['role_registry_covers_all_projects_using_this_isolated_host'], complete)
        blocked = next(p for p in data['candidate']['projects'] if p['project'] == 'project-a')
        self.assertTrue(all(not brief['sent'] for brief in blocked['pending_unsent_briefs']))


if __name__ == '__main__':
    unittest.main()
