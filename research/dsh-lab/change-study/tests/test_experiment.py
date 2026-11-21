import json
import tempfile
import unittest
from pathlib import Path
from experiment import Controller, check_budget, arm_order, runtime_preflight
from scenario import create_fixture
from test_trace import note
from test_scenario import OFFSET, CURSOR, API, CLIENT
from test_decisions import record

class ControllerTests(unittest.TestCase):
    def test_inject_once_receipt_and_first_pass(self):
        with tempfile.TemporaryDirectory() as d:
            w=Path(d)/'task';create_fixture(w);sent=[]
            c=Controller(w,Path(d)/'output','native',lambda text: sent.append(text) or 'm2')
            (w/'core.py').write_text(OFFSET)
            c.observe(note('tool/result',{'message':{'toolCallId':'a','content':[]}}),1)
            c.observe(note('tool/result',{'message':{'toolCallId':'b','content':[]}}),2)
            self.assertEqual(len(sent),1)
            self.assertIsNone(c.received_at)
            c.observe(note('agent/inbox/spliced',{'inserted':[{'id':'m2'}]}),3)
            (w/'core.py').write_text(CURSOR);(w/'api.py').write_text(API);(w/'client.py').write_text(CLIENT)
            c.observe(note('tool/result',{'message':{'toolCallId':'c','content':[]}}),4)
            result=c.finish('completed',5)
            self.assertTrue(result['valid_trial'])
            self.assertIsNotNone(result['first_pass_observed'])
            self.assertTrue(result['code_passed'])
            self.assertFalse((w/'trace.jsonl').exists())
    def test_automatic_graph_invalidated_and_revision_required(self):
        with tempfile.TemporaryDirectory() as d:
            w=Path(d)/'task';create_fixture(w);sent=[]
            c=Controller(w,Path(d)/'out','dependency_record',lambda text: sent.append(text) or 'm')
            (w/'core.py').write_text(OFFSET);(w/'decisions.json').write_text(json.dumps(record()))
            c.observe(note('tool/result',{'message':{'content':[]}}),1)
            self.assertEqual(c.invalidated,['client','offset'])
            self.assertIn('revision=2',sent[0])
            c.observe(note('agent/inbox/spliced',{'inserted':[{'id':'m'}]}),2)
            result=c.finish('timeout',10)
            self.assertFalse(result['session_completed'])
            self.assertFalse(result['record_revalidated'])
    def test_bad_graph_stops_trial_without_injection(self):
        with tempfile.TemporaryDirectory() as d:
            w=Path(d)/'task';create_fixture(w)
            c=Controller(w,Path(d)/'out','dependency_record',lambda text:self.fail('must not inject'))
            (w/'core.py').write_text(OFFSET);(w/'decisions.json').write_text('{}')
            c.observe(note('tool/result',{'message':{'content':[]}}),1)
            self.assertIn('invalid_record',c.invalid_reason)
            self.assertFalse(c.finish('completed',2)['valid_trial'])
    def test_missed_checkpoint_and_missing_receipt_invalid(self):
        with tempfile.TemporaryDirectory() as d:
            w=Path(d)/'task';create_fixture(w)
            c=Controller(w,Path(d)/'out','native',lambda text:'m')
            (w/'api.py').write_text(API)
            c.observe(note('tool/result',{'message':{'content':[]}}),1)
            self.assertEqual(c.invalid_reason,'checkpoint_missed')
            self.assertFalse(c.finish('completed',2)['valid_trial'])
    def test_tool_budget_distinct_from_total_budget(self):
        with self.assertRaisesRegex(TimeoutError,'tool'):check_budget(46,[{'started':0}],tool_limit=45,total_limit=180)
        with self.assertRaisesRegex(TimeoutError,'total'):check_budget(181,[],tool_limit=45,total_limit=180)
        check_budget(44,[{'started':0}],tool_limit=45,total_limit=180)
    def test_counterbalanced_orders(self):
        orders=[arm_order(7,i) for i in range(3)]
        self.assertEqual(len({tuple(x) for x in orders}),3)
        self.assertEqual({x[0] for x in orders},{'native','impact_prompt','dependency_record'})

class CompletionTests(unittest.TestCase):
    def test_completed_code_requires_tests_auth_and_record(self):
        agent_test='import unittest\nclass T(unittest.TestCase):\n    def test_empty(self):\n        from api import fetch_orders\n        self.assertEqual(fetch_orders([],"a")["items"],[])\n'
        for fault in ['none','tests','auth','record','pending','receipt']:
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as d:
                w=Path(d)/'task';create_fixture(w)
                c=Controller(w,Path(d)/'out','dependency_record',lambda text:'m')
                (w/'core.py').write_text(OFFSET);(w/'decisions.json').write_text(json.dumps(record()))
                c.observe(note('tool/result',{'message':{'content':[]}}),1)
                if fault!='receipt':c.observe(note('agent/inbox/spliced',{'inserted':[{'id':'m'}]}),2)
                (w/'core.py').write_text(CURSOR);(w/'api.py').write_text(API);(w/'client.py').write_text(CLIENT)
                if fault!='tests':(w/'test_orders.py').write_text(agent_test)
                if fault=='auth':(w/'auth.py').write_text((w/'auth.py').read_text()+'\n# unnecessary modification\n')
                if fault!='record':
                    g=record();g['revision']=2;(w/'decisions.json').write_text(json.dumps(g))
                if fault=='pending':c.observe(note('tool/call',{'callId':'never-returned','name':'bash','arguments':'{}'}),3)
                result=c.finish('completed',4)
                self.assertEqual(result['task_succeeded'],fault=='none',result)

class RuntimeMetricsTests(unittest.TestCase):
    def test_cleanup_timing_excludes_final_oracle(self):
        import sys,time
        from types import SimpleNamespace
        from unittest.mock import patch
        from experiment import run_arm
        class Harness:
            def __init__(self,**kwargs):pass
            def start_session(self):
                return SimpleNamespace(id='fake',run=lambda *a,**kw:SimpleNamespace(finish_reason='completed'))
            def close(self):pass
        original=Controller.finish
        def slow_finish(self,*a,**kw):
            time.sleep(.2)
            return original(self,*a,**kw)
        with tempfile.TemporaryDirectory() as d,patch.dict(sys.modules,{'deepseek_harness':SimpleNamespace(DeepSeekHarness=Harness)}),patch.object(Controller,'finish',slow_finish):
            result=run_arm(Path(d),'native','test-secret')
            self.assertLess(result['cleanup_seconds'],.15)
    def test_adapter_timeout_preserves_pending_usage_and_redacts_error(self):
        import sys
        from types import SimpleNamespace
        from unittest.mock import patch
        from experiment import run_arm
        class Harness:
            def __init__(self,**kwargs):pass
            def start_session(self):
                def run(prompt,on_notification):
                    on_notification(note('assistant/message',{'usage':{'outputTokens':3}}))
                    on_notification(note('tool/call',{'callId':'stuck','name':'bash','arguments':'{"command":"echo test-secret"}'}))
                    raise TimeoutError('blocked test-secret')
                return SimpleNamespace(id='fake',run=run)
            def close(self):pass
        with tempfile.TemporaryDirectory() as d,patch.dict(sys.modules,{'deepseek_harness':SimpleNamespace(DeepSeekHarness=Harness)}):
            result=run_arm(Path(d),'native','test-secret')
            stored=(Path(d)/'native/observations/result.json').read_text()
            self.assertEqual(result['status'],'timeout')
            self.assertFalse(result['task_succeeded'])
            self.assertEqual(result['trace']['pending'][0]['call_id'],'stuck')
            self.assertEqual(result['trace']['usage']['outputTokens'],3)
            self.assertNotIn('test-secret',stored)
    def test_max_tokens_and_finish_reason_are_recorded(self):
        import sys
        from types import SimpleNamespace
        from unittest.mock import patch
        from experiment import run_arm
        configured={}
        class Harness:
            def __init__(self,**kwargs):configured.update(kwargs)
            def start_session(self):
                return SimpleNamespace(id='fake',run=lambda *a,**kw:SimpleNamespace(finish_reason='max-tokens'))
            def close(self):pass
        with tempfile.TemporaryDirectory() as d,patch.dict(sys.modules,{'deepseek_harness':SimpleNamespace(DeepSeekHarness=Harness)}):
            result=run_arm(Path(d),'native','test-secret',max_tokens=8192)
            self.assertEqual(configured['max_tokens'],8192)
            self.assertEqual(result['configured_max_tokens'],8192)
            self.assertEqual(result['finish_reason'],'max-tokens')
            self.assertEqual(result['status'],'incomplete')
    def test_runtime_receives_uniform_shell_history_patch(self):
        import sys
        from types import SimpleNamespace
        from unittest.mock import patch
        from experiment import run_arm, ROOT
        configured={}
        class Harness:
            def __init__(self,**kwargs):configured.update(kwargs)
            def start_session(self):return SimpleNamespace(id='fake',run=lambda *a,**kw:SimpleNamespace(finish_reason='completed'))
            def close(self):pass
        with tempfile.TemporaryDirectory() as d,patch.dict(sys.modules,{'deepseek_harness':SimpleNamespace(DeepSeekHarness=Harness)}):
            run_arm(Path(d),'native','test-secret')
            self.assertEqual(configured.get('patches'),(str(ROOT/'shell-history.patch.yml'),))
    def test_future_requirement_not_written_before_session(self):
        import sys
        from types import SimpleNamespace
        from unittest.mock import patch
        from experiment import run_arm
        observed=[]
        class Harness:
            def __init__(self,**kwargs):self.work=Path(kwargs['cwd'])
            def start_session(self):
                def run(*a,**kw):
                    observed.append((self.work.parent/'observations/prompt.json').read_text())
                    return SimpleNamespace(finish_reason='completed')
                return SimpleNamespace(id='fake',run=run)
            def close(self):pass
        with tempfile.TemporaryDirectory() as d,patch.dict(sys.modules,{'deepseek_harness':SimpleNamespace(DeepSeekHarness=Harness)}):
            run_arm(Path(d),'native','test-secret')
            self.assertNotIn('new orders can be inserted BETWEEN calls',observed[0])
    def test_diagnostic_path_access_invalidates_trial(self):
        with tempfile.TemporaryDirectory() as d:
            w=Path(d)/'task';create_fixture(w)
            c=Controller(w,Path(d)/'observations','native',lambda text:'m')
            with self.assertRaises(ValueError):
                c.observe(note('tool/call',{'callId':'read-log','name':'bash','arguments':'{"command":"cat ../observations/prompt.json"}'}),1)
            self.assertEqual(c.invalid_reason,'diagnostic_material_access')
            self.assertFalse(c.finish('invalid',2)['valid_trial'])
