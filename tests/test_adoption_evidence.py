"""Replay published file effects; does not exercise chat delivery or model behavior."""
import csv
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'tests/outputs/v0.4.1-adoption'


class AdoptionEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.artifacts = json.loads((EVIDENCE / 'artifacts.json').read_text())
        self.inputs = json.loads((EVIDENCE / 'inputs.json').read_text())

    def test_published_bytes_and_frozen_candidate(self):
        self.assertEqual(set(self.artifacts), {
            'baseline', 'candidate-controller', 'partial-mismatch',
            'worker-input', 'normal-worker'})
        for phase, artifact in self.artifacts.items():
            self.assertEqual(set(artifact['files']), set(artifact['sha256']))
            for name, content in artifact['files'].items():
                with self.subTest(phase=phase, path=name):
                    self.assertFalse(Path(name).is_absolute())
                    self.assertNotIn('..', Path(name).parts)
                    self.assertEqual(hashlib.sha256(content.encode()).hexdigest(),
                                     artifact['sha256'][name])
        # Historical evidence remains replayable after a later skill release.
        if json.loads((ROOT / 'plugin.json').read_text())['version'] != '0.4.1':
            return
        hashes = json.loads((EVIDENCE / 'skill-hashes.json').read_text())['0.4.1']
        source = ROOT / 'skills/orchivane'
        self.assertEqual(set(hashes), {str(p.relative_to(source))
                                      for p in source.rglob('*') if p.is_file()})
        for name, digest in hashes.items():
            self.assertEqual(hashlib.sha256((source / name).read_bytes()).hexdigest(),
                             digest, name)

    def test_historical_replay_does_not_pin_future_skill_versions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'plugin.json').write_text('{"version":"0.4.2"}\n')
            with patch(__name__ + '.ROOT', root):
                self.test_published_bytes_and_frozen_candidate()

    def test_controllers_preserve_work_and_simulated_runtime(self):
        for phase in ('baseline', 'candidate-controller', 'partial-mismatch'):
            files = self.artifacts[phase]['files']
            for name, content in self.inputs.items():
                if name not in {'AGENTS.md', 'docs/SESSION-MANAGEMENT.md'}:
                    with self.subTest(phase=phase, path=name):
                        self.assertEqual(files[name], content)
            self.assertNotIn('work/data/summary.json', files)
        submitted = json.loads(self.artifacts['partial-mismatch']['files'][
            'coordination/submitted-receipt.json'])
        hashes = json.loads((EVIDENCE / 'skill-hashes.json').read_text())
        self.assertEqual(submitted['entry_sha256'], hashes['0.4.0']['SKILL.md'])
        self.assertEqual(submitted['reported_version'], '0.4.1')
        self.assertEqual(submitted['modules'], [])
        self.assertIsNone(submitted['behavior_evidence'])

    def test_normal_task_effects_and_worker_write_boundary(self):
        before = self.artifacts['worker-input']['files']
        after = self.artifacts['normal-worker']['files']
        for name, content in before.items():
            self.assertEqual(after[name], content, name)
        additions = set(after) - set(before)
        self.assertIn('work/data/summary.json', additions)
        self.assertIn('work/data/receipt-N2.json', additions)
        self.assertTrue(all(name.startswith('work/data/') for name in additions))
        rows = list(csv.DictReader(io.StringIO(before['inputs/n2.csv'])))
        summary = json.loads(after['work/data/summary.json'])
        self.assertEqual(summary['row_count'], len(rows))
        self.assertEqual(summary['total_quantity'],
                         sum(int(row['quantity']) for row in rows))
        state = json.loads(after['coordination/runtime-state.json'])
        self.assertEqual(state['messages'], [])
        self.assertEqual(state['paused'], [])
        self.assertEqual(state['old_budget_remaining'], 0)
        self.assertEqual(state['network_calls'], 0)
        self.assertEqual(state['model_calls'], 0)

    def test_native_041_adoption_and_receipt_artifacts(self):
        evidence = ROOT / 'tests/outputs/v0.4.1-native-adoption'
        prompts = json.loads((evidence / 'prompts.json').read_text())
        self.assertEqual(set(prompts), {'N1', 'adoption', 'N2', 'acceptance'})
        for prompt in prompts.values():
            self.assertTrue(prompt['text'].strip())
            self.assertTrue(prompt['source'])
        artifacts = json.loads((evidence / 'artifacts.json').read_text())
        self.assertEqual(set(artifacts), {
            'before-adoption', 'after-adoption', 'after-n2', 'final'})
        for phase, artifact in artifacts.items():
            self.assertEqual(set(artifact['files']), set(artifact['sha256']))
            for name, content in artifact['files'].items():
                self.assertFalse(Path(name).is_absolute())
                self.assertNotIn('..', Path(name).parts)
                self.assertEqual(hashlib.sha256(content.encode()).hexdigest(),
                                 artifact['sha256'][name], (phase, name))
        before = artifacts['before-adoption']['files']
        adopted = artifacts['after-adoption']['files']
        for name, content in before.items():
            if name != 'docs/SESSION-MANAGEMENT.md':
                self.assertEqual(adopted[name], content, name)
        delivered = artifacts['after-n2']['files']
        for name, content in adopted.items():
            self.assertEqual(delivered[name], content, name)
        self.assertEqual(set(delivered) - set(adopted), {
            'work/data/n2-summary.json', 'work/data/n2-receipt.json'})
        final = artifacts['final']['files']
        for name, content in delivered.items():
            if name not in {'docs/SESSION-MANAGEMENT.md', 'docs/SESSION-HEALTH.md'}:
                self.assertEqual(final[name], content, name)
        for task in ('n1', 'n2'):
            rows = list(csv.DictReader(io.StringIO(final[f'inputs/{task}.csv'])))
            summary = json.loads(final[f'work/data/{task}-summary.json'])
            self.assertEqual(summary, {
                'row_count': len(rows),
                'total_quantity': sum(int(row['quantity']) for row in rows)})
        receipt = json.loads(final['coordination/N2-ACCEPTANCE.json'])
        self.assertEqual(receipt['loading_acceptance']['observed_entry_metadata_version'],
                         '0.4.1')


if __name__ == '__main__':
    unittest.main()
