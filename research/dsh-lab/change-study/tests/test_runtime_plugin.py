"""Behavioral checks against the installed DSH loop; the provider and IPC are fake."""
import json
from pathlib import Path
import shutil
import subprocess
import unittest


class RuntimeSteeringTests(unittest.TestCase):
    def probe(self, *args):
        node = shutil.which('node')
        if node is None:
            self.skipTest('Node runtime unavailable')
        script = Path(__file__).with_name('runtime_steering_probe.mjs')
        result = subprocess.run([node, str(script), *args], capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        data = json.loads(result.stdout)
        self.assertTrue(data['actual_dsh_agent_loop'])
        self.assertEqual(data['turns'], 1)
        return data

    def test_change_enters_next_model_request_in_same_turn(self):
        self.assertTrue(self.probe()['changed_message_in_next_request'])

    def test_same_batch_followon_is_not_executed(self):
        self.assertTrue(self.probe('--multiple')['same_batch_followon_blocked'])

    def test_tool_execution_resumes_after_change_consumption(self):
        self.assertTrue(self.probe('--continue')['tool_after_consumption_runs'])
