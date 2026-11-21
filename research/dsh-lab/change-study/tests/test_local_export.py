import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import local_export
from experiment import Controller
from oracle import evaluate_agent_tests, run_check
from scenario import create_fixture
from strict_experiment import main
from test_scenario import API, CLIENT, OFFSET


EXPORT_SNAPSHOT = '''from auth import require_account
from core import list_orders

def fetch_export_page(rows, account, size=2, cursor=None):
    require_account(account)
    eligible = rows if cursor is None else [r for r in rows if r[0] < cursor['before']]
    page = list_orders(eligible, account, size)
    if page['next_cursor'] is not None:
        page['next_cursor'] = {'before': page['items'][-1][0]}
    return page
'''

AGENT_TEST = '''import unittest
from api import fetch_orders

class Smoke(unittest.TestCase):
    def test_live_latest(self):
        self.assertEqual(fetch_orders([(1,'a'), (2,'a')], 'a', 1)['items'], [(2,'a')])
'''


def install_v1(work):
    for name, source in {
        'core.py': OFFSET,
        'api.py': API,
        'export_api.py': API.replace('fetch_orders', 'fetch_export_page'),
        'client.py': CLIENT.replace('collect_orders', 'collect_export'),
        'test_orders.py': AGENT_TEST,
    }.items():
        (work / name).write_text(source)


class LocalExportTests(unittest.TestCase):
    def test_checker_distinguishes_omission_from_live_regression(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            create_fixture(work, local_export.FILES)
            install_v1(work)
            before = run_check(work, local_export.CORE_CHECK_CODE)
            self.assertEqual(len(before), 6)
            self.assertTrue(all(value is True for value in before.values()), before)

            omitted = run_check(work, local_export.CHECK_CODE)
            self.assertIs(omitted['live_api_current_offset'], True)
            self.assertIsNot(omitted['export_pages_survive_inserts'], True)
            self.assertIsNot(omitted['export_worker_survives_inserts'], True)

            (work / 'export_api.py').write_text(EXPORT_SNAPSHOT)
            correct = run_check(work, local_export.CHECK_CODE)
            self.assertEqual(len(correct), 7)
            self.assertTrue(all(value is True for value in correct.values()), correct)

            (work / 'api.py').write_text('from export_api import fetch_export_page as fetch_orders\n')
            regressed = run_check(work, local_export.CHECK_CODE)
            self.assertIs(regressed['export_pages_survive_inserts'], True)
            self.assertIsNot(regressed['live_api_current_offset'], True)

    def test_marker_does_not_advance_an_incomplete_v1(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            work = root / 'task'
            create_fixture(work, local_export.FILES)
            messages = []
            controller = Controller(work, root / 'observations', 'native', messages.append,
                                    case=local_export, agent_evaluator=evaluate_agent_tests,
                                    evaluator=lambda work, phase: run_check(work, local_export.CORE_CHECK_CODE))
            install_v1(work)
            (work / 'export_api.py').write_text(local_export.FILES['export_api.py'])
            (work / local_export.READY_FILE).write_text('ready\n')
            controller.after_tool(1)
            self.assertEqual(controller.invalid_reason, 'initial_checkpoint_failed')
            self.assertEqual(messages, [])

    def test_verified_checkpoint_steers_only_export_dependencies(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            work = root / 'task'
            create_fixture(work, local_export.FILES)
            messages = []
            controller = Controller(work, root / 'observations', 'dependency_record', messages.append,
                                    case=local_export, agent_evaluator=evaluate_agent_tests,
                                    evaluator=lambda work, phase: run_check(work, local_export.CORE_CHECK_CODE))
            install_v1(work)
            record = {
                'revision': 1,
                'assumptions': [
                    {'id': 'current', 'claim': 'Read current rows', 'requirement': 'live'},
                    {'id': 'static', 'claim': 'Exports traverse static rows', 'requirement': 'export'},
                    {'id': 'account', 'claim': 'Account required', 'requirement': 'auth'},
                ],
                'decisions': [
                    {'id': 'live-list', 'depends_on': ['current', 'account'], 'artifacts': ['api.py']},
                    {'id': 'export-page', 'depends_on': ['static', 'account'], 'artifacts': ['export_api.py']},
                    {'id': 'worker', 'depends_on': ['export-page'], 'artifacts': ['client.py']},
                ],
            }
            (work / 'decisions.json').write_text(json.dumps(record))
            controller.after_tool(1)
            self.assertEqual(messages, [])
            (work / local_export.READY_FILE).write_text('ready\n')
            controller.after_tool(2)
            self.assertIsNone(controller.invalid_reason)
            self.assertEqual(controller.invalidated, ['export-page', 'worker'])
            self.assertEqual(len(messages), 1)
            self.assertTrue(messages[0].startswith(local_export.CHANGE))
            self.assertNotIn('"live-list"', messages[0])

    def test_cli_selects_exactly_one_pair_for_local_export(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def run_arm(path, arm, key, max_tokens, *, image_id, case):
                self.assertIs(case, local_export)
                self.assertEqual(max_tokens, 8192)
                return dict(arm=arm, status='completed', valid_trial=True,
                            same_turn_consumed=True, task_succeeded=True, seconds=1)

            with (patch('strict_experiment.ROOT', root),
                  patch('strict_experiment.preflight', return_value={'passed': True, 'image_id': 'test-image'}),
                  patch('strict_experiment.load_key', return_value='test-key'),
                  patch('strict_experiment.run_arm', side_effect=run_arm),
                  contextlib.redirect_stdout(io.StringIO())):
                self.assertEqual(main(['--scenario', 'local-export']), 0)
            summary_path, = (root / 'runs').glob('*/summary.json')
            summary = json.loads(summary_path.read_text())
            self.assertEqual(summary['scenario'], 'local-export')
            self.assertEqual(summary['protocol_revision'], '4.2')
            self.assertCountEqual([r['arm'] for r in summary['trials']], ['native', 'dependency_record'])
