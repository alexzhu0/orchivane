import tempfile
import unittest
from pathlib import Path
from scenario import create_fixture, checkpoint_ready, file_hashes
from oracle import evaluate

OFFSET='''def list_orders(rows, account, size=2, cursor=None):
    if not isinstance(size,int) or isinstance(size,bool) or not 1<=size<=100: raise ValueError()
    r=sorted([r for r in rows if r[1]==account],reverse=True); n=cursor or 0
    return {"items":r[n:n+size],"next_cursor":n+size if n+size<len(r) else None}
'''
CURSOR='''def list_orders(rows, account, size=2, cursor=None):
    if not isinstance(size,int) or isinstance(size,bool) or not 1<=size<=100: raise ValueError()
    r=sorted([r for r in rows if r[1]==account and (cursor is None or r[0]<cursor)],reverse=True)
    return {"items":r[:size],"next_cursor":r[size-1][0] if len(r)>size else None}
'''
API='''from core import list_orders
from auth import require_account
def fetch_orders(rows,account,size=2,cursor=None):
    require_account(account)
    return list_orders(rows,account,size,cursor)
'''
CLIENT='''def collect_orders(fetch,size=2):
    items=[]; cursor=None
    while True:
        r=fetch(size=size,cursor=cursor); items.extend(r['items']); cursor=r['next_cursor']
        if cursor is None: return items
'''

class ScenarioTests(unittest.TestCase):
    def test_checkpoint_requires_unchanged_other_files(self):
        with tempfile.TemporaryDirectory() as d:
            w=Path(d);create_fixture(w);baseline=file_hashes(w)
            self.assertFalse(checkpoint_ready(w,baseline))
            (w/'core.py').write_text(OFFSET)
            self.assertTrue(checkpoint_ready(w,baseline))
            (w/'client.py').write_text(CLIENT)
            self.assertFalse(checkpoint_ready(w,baseline))
    def test_oracle_rejects_offset_and_accepts_snapshot(self):
        with tempfile.TemporaryDirectory() as d:
            w=Path(d);create_fixture(w)
            (w/'api.py').write_text(API);(w/'client.py').write_text(CLIENT)
            (w/'core.py').write_text(OFFSET)
            self.assertIsNot(evaluate(w,'final')['core_snapshot'],True)
            (w/'core.py').write_text(CURSOR)
            results=evaluate(w,'final')
            self.assertTrue(all(v is True for v in results.values()),results)
    def test_client_infinite_loop_is_bounded(self):
        with tempfile.TemporaryDirectory() as d:
            w=Path(d);create_fixture(w)
            (w/'core.py').write_text(CURSOR);(w/'api.py').write_text(API)
            (w/'client.py').write_text('def collect_orders(fetch,size=2):\n    while True: pass\n')
            self.assertIn('oracle_error',evaluate(w,'final'))
    def test_auth_regression_detected(self):
        with tempfile.TemporaryDirectory() as d:
            w=Path(d);create_fixture(w)
            (w/'core.py').write_text(CURSOR);(w/'api.py').write_text(API.replace('    require_account(account)','    pass'))
            (w/'client.py').write_text(CLIENT)
            self.assertIsNot(evaluate(w,'final')['auth'],True)

class AgentTests(unittest.TestCase):
    def test_empty_test_suite_not_accepted(self):
        from oracle import evaluate_agent_tests
        with tempfile.TemporaryDirectory() as d:
            w=Path(d);create_fixture(w)
            self.assertFalse(evaluate_agent_tests(w)['passed'])
            (w/'test_orders.py').write_text('import unittest\nclass T(unittest.TestCase):\n    def test_failure(self): self.assertEqual(1,2)\n')
            self.assertFalse(evaluate_agent_tests(w)['passed'])
            (w/'test_orders.py').write_text('import unittest\nclass T(unittest.TestCase):\n    def test_pass(self): self.assertEqual(1,1)\n')
            self.assertTrue(evaluate_agent_tests(w)['passed'])
    def test_oracle_timeout_stops_descendants(self):
        import time
        import sys
        with tempfile.TemporaryDirectory() as d:
            w=Path(d);create_fixture(w)
            child="import time; from pathlib import Path; time.sleep(5); Path('leaked.txt').write_text('survived')"
            (w/'core.py').write_text('import subprocess,sys\nsubprocess.Popen([sys.executable,"-c",'+repr(child)+'])\nwhile True: pass\n')
            self.assertIn('oracle_error',evaluate(w,'core'))
            time.sleep(2.5)
            self.assertFalse((w/'leaked.txt').exists(),'oracle child survived timeout')
    def test_direct_core_validation_not_masked_by_api(self):
        with tempfile.TemporaryDirectory() as d:
            w=Path(d);create_fixture(w)
            (w/'core.py').write_text(CURSOR.replace('    if not isinstance(size,int) or isinstance(size,bool) or not 1<=size<=100: raise ValueError()\n',''))
            (w/'api.py').write_text(API.replace('    require_account(account)','    if not isinstance(size,int) or isinstance(size,bool) or not 1<=size<=100: raise ValueError()\n    require_account(account)'))
            (w/'client.py').write_text(CLIENT)
            result=evaluate(w,'final')
            self.assertFalse(all(v is True for v in result.values()),result)
