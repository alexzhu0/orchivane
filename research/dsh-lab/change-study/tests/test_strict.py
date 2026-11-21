import json
import tempfile
import unittest
from pathlib import Path
from strict_experiment import StrictController, Bridge, isolated_evaluators
from scenario import create_fixture
from test_trace import note
from test_scenario import OFFSET


class FakeSandbox:
    python='/controlled/python'
    def run(self, argv, **kwargs):
        self.argv=argv
        return {'returncode':0,'stdout':'{"static_core":true}\n','stderr':'','timed_out':False}
    def run_shell(self, command, **kwargs):
        return {'returncode':0,'stdout':'ok','stderr':'','timed_out':False}
    def cancel_active(self):pass


class StrictTests(unittest.TestCase):
    def make_controller(self, root):
        work=Path(root)/'task';create_fixture(work)
        self.sandbox=FakeSandbox()
        return StrictController(work,Path(root)/'observations','native',self.sandbox,clock=lambda:1.)

    def test_oracle_executes_only_through_isolated_runner(self):
        box=FakeSandbox();evaluate,_=isolated_evaluators(box)
        self.assertEqual(evaluate('/task','core'),{'static_core':True})
        self.assertEqual(box.argv[:3],['/controlled/python','-I','-B'])

    def test_prechange_evaluator_does_not_carry_future_requirements(self):
        box=FakeSandbox();evaluate,_=isolated_evaluators(box)
        evaluate('/task','core')
        self.assertNotIn('snapshot',box.argv[4])
        self.assertNotIn('data.extend',box.argv[4])
        self.assertNotIn('collect_orders',box.argv[4])
        evaluate('/task','final')
        self.assertIn('core_snapshot',box.argv[4])

    def test_post_consumption_request_waits_for_sdk_notification(self):
        import threading,time
        with tempfile.TemporaryDirectory() as root:
            c=self.make_controller(root)
            c.dispatch({'op':'ready','session_id':'s','tools':['study_bash']})
            (c.work/'core.py').write_text(OFFSET)
            req={'op':'execute','session_id':'s','call_id':'a','command':'true','turn':1,'step':1}
            c.dispatch(req)
            c.dispatch({'op':'steered','session_id':'s','call_id':'a','message_id':'m','turn':1,'step':1})
            def delayed_sdk():
                time.sleep(.05)
                c.observe(note('step/start',{'turn':1,'step':2}),2)
                c.observe(note('user/message',{'id':'m'}),2.1)
            thread=threading.Thread(target=delayed_sdk);thread.start()
            try:
                result=c.dispatch({**req,'call_id':'b','step':2})
                self.assertEqual(result['stdout'],'ok')
                self.assertTrue(c.same_turn_consumed)
            finally:thread.join(timeout=1)

    def test_tool_inventory_fail_closed(self):
        with tempfile.TemporaryDirectory() as root:
            c=self.make_controller(root)
            with self.assertRaisesRegex(ValueError,'tool_inventory'):
                c.dispatch({'op':'ready','session_id':'s','tools':['study_bash','read_file']})
            self.assertEqual(c.invalid_reason,'tool_inventory')

    def test_next_step_current_turn_consumption_required(self):
        with tempfile.TemporaryDirectory() as root:
            c=self.make_controller(root)
            c.dispatch({'op':'ready','session_id':'s','tools':['study_bash']})
            (c.work/'core.py').write_text(OFFSET)
            response=c.dispatch({'op':'execute','session_id':'s','call_id':'a','command':'true','turn':1,'step':1})
            self.assertIn('Requirement changed',response['steering']['text'])
            self.assertIsNone(c.received_at)
            c.dispatch({'op':'steered','session_id':'s','call_id':'a','message_id':'m','turn':1,'step':1})
            c.observe(note('step/start',{'turn':1,'step':2}),2)
            c.observe(note('user/message',{'id':'m','content':[{'type':'text','text':'private'}]}),2.1)
            self.assertTrue(c.same_turn_consumed)
            self.assertEqual(c.consumed_turn,1)
            self.assertNotIn('private',(c.output/'trace.jsonl').read_text())

    def test_followup_turn_and_extra_tool_fail_closed(self):
        for fault in ('turn','extra_tool'):
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as root:
                c=self.make_controller(root)
                c.dispatch({'op':'ready','session_id':'s','tools':['study_bash']})
                (c.work/'core.py').write_text(OFFSET)
                req={'op':'execute','session_id':'s','call_id':'a','command':'true','turn':1,'step':1}
                c.dispatch(req)
                c.dispatch({'op':'steered','session_id':'s','call_id':'a','message_id':'m','turn':1,'step':1})
                if fault=='turn':
                    c.observe(note('step/start',{'turn':2,'step':1}),2)
                    c.observe(note('user/message',{'id':'m'}),2.1)
                    self.assertEqual(c.invalid_reason,'steering_consumed_outside_next_step')
                else:
                    with self.assertRaisesRegex(ValueError,'tool_before_steering_consumed'):
                        c.dispatch({**req,'call_id':'b'})
                self.assertFalse(c.same_turn_consumed)

    def test_bridge_authentication_rejects_before_dispatch(self):
        with tempfile.TemporaryDirectory() as root:
            c=self.make_controller(root)
            bridge=Bridge(c)
            response=bridge.handle_request({'token':'wrong','op':'ready','tools':['study_bash']})
            self.assertFalse(response['ok'])
            self.assertFalse(c.runtime_ready)

    def test_failed_preflight_and_preflight_only_never_load_key(self):
        import contextlib,io
        from unittest.mock import patch
        from strict_experiment import main
        for passed in (False,True):
            with tempfile.TemporaryDirectory() as root,patch('strict_experiment.ROOT',Path(root)),patch('strict_experiment.preflight',return_value={'passed':passed}),patch('strict_experiment.load_key') as key,contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(['--preflight-only']),0 if passed else 2)
                key.assert_not_called()

    def test_bridge_shutdown_cancels_and_joins_before_return(self):
        import threading
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as root:
            c=self.make_controller(root);cancelled=threading.Event();finished=threading.Event()
            def work():
                cancelled.wait(2);finished.set()
            worker=threading.Thread(target=work);worker.start()
            c.box.cancel_active=lambda:cancelled.set()
            b=Bridge(c)
            b.server=SimpleNamespace(shutdown=lambda:None,server_close=lambda:worker.join(2))
            b.thread=SimpleNamespace(join=lambda **kw:None)
            b.__exit__(None,None,None)
            self.assertTrue(c.stopping.is_set())
            self.assertTrue(finished.is_set())
            self.assertFalse(worker.is_alive())

    def test_generated_core_cannot_introspect_future_checker(self):
        from oracle import evaluate
        with tempfile.TemporaryDirectory() as root:
            w=Path(root);create_fixture(w)
            probe='import sys\nfrom pathlib import Path\nPath("checker.txt").write_text(repr(sys.orig_argv)+repr(sys._getframe().f_back.f_code.co_consts))\n'
            (w/'core.py').write_text(probe+OFFSET)
            self.assertEqual(evaluate(w,'core'),{'static_core':True})
            exposed=(w/'checker.txt').read_text()
            self.assertNotIn('snapshot',exposed)
            self.assertNotIn('data.extend',exposed)

    def test_failed_cancellation_skips_final_generated_code(self):
        import sys
        from types import SimpleNamespace
        from unittest.mock import patch,Mock
        from strict_experiment import run_arm
        box=FakeSandbox();box.run=Mock(side_effect=AssertionError('unsafe final oracle'))
        class Harness:
            def __init__(self,**kw):pass
            def start_session(self):return SimpleNamespace(id='s',run=lambda *a,**kw:SimpleNamespace(finish_reason='completed'))
            def close(self):pass
        class FailedBridge:
            def __init__(self,c):self.quiesced=False;self.path='/unused';self.token='test-token'
            def __enter__(self):return self
            def __exit__(self,*args):raise RuntimeError('cleanup still active')
        with tempfile.TemporaryDirectory() as root,patch.dict(sys.modules,{'deepseek_harness':SimpleNamespace(DeepSeekHarness=Harness)}),patch('strict_experiment.Sandbox',return_value=box),patch('strict_experiment.Bridge',FailedBridge):
            result=run_arm(Path(root),'native','fake-key')
            self.assertEqual(result['status'],'error')
            self.assertEqual(result['invalid_reason'],'cleanup_unverified')
            self.assertFalse(result['task_succeeded'])
            box.run.assert_not_called()

    def test_bridge_server_cleanup_survives_cancellation_failure(self):
        from types import SimpleNamespace
        from unittest.mock import Mock
        c=SimpleNamespace(stop=Mock(side_effect=RuntimeError('still active')))
        b=Bridge(c);b.server=SimpleNamespace(shutdown=Mock(),server_close=Mock())
        b.thread=SimpleNamespace(join=Mock())
        with self.assertRaises(RuntimeError):b.__exit__(None,None,None)
        b.server.shutdown.assert_called_once()
        b.server.server_close.assert_called_once()
        self.assertFalse(b.quiesced)
