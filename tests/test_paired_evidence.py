"""Offline evidence replay; does not run models or measure human coordination."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).parent / 'paired'
spec = importlib.util.spec_from_file_location('paired_grader', ROOT / 'grade.py')
grader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(grader)


class PairedEvidenceTests(unittest.TestCase):
    def materialize(self, files):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        for name, content in files.items():
            target = root / name
            self.assertTrue(target.resolve().is_relative_to(root.resolve()))
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content.encode('utf-8'))
        return root

    def test_frozen_inputs_and_grader(self):
        inputs = json.loads((ROOT / 'inputs.json').read_text(encoding='utf-8'))
        hashes = json.loads((ROOT / 'initial-hashes.json').read_text(encoding='utf-8'))
        for task, files in inputs.items():
            self.assertEqual(set(files), set(hashes[task]))
            for name, content in files.items():
                self.assertEqual(hashlib.sha256(content.encode()).hexdigest(),
                                 hashes[task][name])
        manifest = json.loads((ROOT / 'frozen-manifest.json').read_text(encoding='utf-8'))
        for original, digest in manifest.items():
            name = original.removeprefix('grader/')
            self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(),
                             digest, original)

    def test_six_published_deliveries_and_complete_result_keys(self):
        artifacts = json.loads((ROOT / 'artifacts.json').read_text(encoding='utf-8'))
        hashes = json.loads((ROOT / 'artifact-hashes.json').read_text(encoding='utf-8'))
        plan = json.loads((ROOT / 'plan.json').read_text(encoding='utf-8'))
        results = [json.loads(line) for line in
                   (ROOT / 'results.jsonl').read_text(encoding='utf-8').splitlines()]
        expected = {(arm, task['task_id'], trial)
                    for arm in plan['variants'] for task in plan['tasks']
                    for trial in task['trial_ids']}
        actual = [(r['variant'], r['task_id'], r['trial_id']) for r in results]
        self.assertEqual(len(actual), len(set(actual)))
        self.assertEqual(set(actual), expected)
        self.assertEqual(set(artifacts), {f'{task}-{arm}' for arm, task, _ in expected})
        for row in results:
            key = f"{row['task_id']}-{row['variant']}"
            with self.subTest(trial=key):
                files = artifacts[key]
                self.assertEqual(set(files), set(hashes[key]))
                for name, content in files.items():
                    self.assertEqual(hashlib.sha256(content.encode()).hexdigest(),
                                     hashes[key][name])
                outcome = grader.grade(row['task_id'], self.materialize(files))
                self.assertTrue(outcome['passed'], outcome)
                self.assertEqual(row['versions'], plan['versions'])
                self.assertIs(row['passed'], True)

    def test_grader_rejects_known_bad_normalization_contract_and_duplicate(self):
        inputs = json.loads((ROOT / 'inputs.json').read_text(encoding='utf-8'))
        artifacts = json.loads((ROOT / 'artifacts.json').read_text(encoding='utf-8'))
        cases = {
            'S1': inputs['S1'],
            'S2': dict(artifacts['S2-single'], **{'contract.json': '{}\n'}),
            'S3': dict(artifacts['S3-single']),
        }
        ledger = cases['S3']['.runtime/executions.jsonl']
        cases['S3']['.runtime/executions.jsonl'] += ledger.splitlines()[-1] + '\n'
        for task, files in cases.items():
            with self.subTest(task=task):
                outcome = grader.grade(task, self.materialize(files))
                self.assertFalse(outcome['passed'], outcome)

    def test_codex_040_handoff_artifact_replay(self):
        evidence = ROOT.parent / 'outputs' / 'v0.4.0-codex'
        artifacts = json.loads((evidence / 'artifacts.json').read_text(encoding='utf-8'))
        for phase, name in ((1, 'A1'), (2, 'A2')):
            with self.subTest(phase=phase):
                artifact = artifacts[name]
                self.assertEqual(set(artifact['files']), set(artifact['sha256']))
                for path, content in artifact['files'].items():
                    self.assertEqual(hashlib.sha256(content.encode()).hexdigest(),
                                     artifact['sha256'][path])
                outcome = grader.grade('S3', self.materialize(artifact['files']), phase)
                self.assertTrue(outcome['passed'], outcome)
        self.assertEqual(artifacts['duplicate_before_sha256'],
                         artifacts['duplicate_after_sha256'])
        for path, digest in artifacts['A2']['sha256'].items():
            self.assertEqual(digest, artifacts['duplicate_after_sha256'][path])


if __name__ == '__main__':
    unittest.main()
