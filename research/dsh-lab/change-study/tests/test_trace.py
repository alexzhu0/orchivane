import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from telemetry import Trace

def note(kind, data, sid='s'):
    return SimpleNamespace(method='session.event', payload={'sessionId':sid,'event':{'type':kind,'data':data}})

class TraceTests(unittest.TestCase):
    def test_pairing_duration_and_redaction(self):
        with tempfile.TemporaryDirectory() as d:
            t=Trace(Path(d), secrets=('private-value',))
            t.observe(note('tool/call',{'callId':'c','name':'bash','arguments':'{"command":"echo private-value","API_KEY":"another-secret"}'}),1)
            t.observe(note('tool/result',{'message':{'toolCallId':'c','isError':True,'content':[{'type':'text','text':'private-value'}]}}),4)
            self.assertEqual(t.summary(5)['tool_calls'][0]['duration'],3)
            self.assertEqual(t.pending,{})
            stored=(Path(d)/'trace.jsonl').read_text()
            self.assertNotIn('private-value',stored)
            self.assertNotIn('another-secret',stored)
    def test_pending_and_session_scoping(self):
        with tempfile.TemporaryDirectory() as d:
            t=Trace(Path(d))
            t.observe(note('tool/call',{'callId':'same','name':'bash','arguments':'{}'}),2)
            t.observe(note('tool/result',{'message':{'toolCallId':'same','content':[]}},sid='other'),3)
            self.assertEqual(len(t.pending),1)
            self.assertEqual(t.summary(10)['pending'][0]['waiting_seconds'],8)
    def test_omits_reasoning(self):
        with tempfile.TemporaryDirectory() as d:
            t=Trace(Path(d));t.observe(note('assistant/message',{'message':{'reasoning':'DO_NOT_LOG'},'usage':{'outputTokens':5}}),1)
            self.assertNotIn('DO_NOT_LOG',(Path(d)/'trace.jsonl').read_text())
            self.assertEqual(t.summary(2)['usage']['outputTokens'],5)
    def test_preserves_turn_end_reason(self):
        with tempfile.TemporaryDirectory() as d:
            t=Trace(Path(d));t.observe(note('turn/end',{'turn':2,'reason':{'kind':'max-tokens'}}),59)
            last=json.loads((Path(d)/'trace.jsonl').read_text().splitlines()[-1])
            self.assertEqual(last['finish_reason'],'max-tokens')
