import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock,patch
from process_probe import classify,probe_process_access


class ProcessProbeTests(unittest.TestCase):
    def test_size_success_does_not_imply_actual_read_success(self):
        control={'read_returncode':0,'marker_found':True}
        denied={'size_returncode':0,'size':262144,'read_returncode':-1,'read_errno':1,'marker_found':False}
        self.assertTrue(classify(control,denied))
        for changes in ({'read_returncode':0},{'read_errno':22},{'marker_found':True}):
            self.assertFalse(classify(control,{**denied,**changes}))
        self.assertFalse(classify({'read_returncode':-1},denied))

    def test_only_disposable_process_is_targeted_and_environment_is_scrubbed(self):
        dummy=Mock(pid=1234);dummy.poll.return_value=None
        control=SimpleNamespace(returncode=0,stdout=json.dumps({'read_returncode':0,'marker_found':True}))
        box=SimpleNamespace(python='/explicit/python',run=Mock(return_value={'returncode':0,'stdout':json.dumps({'read_returncode':-1,'read_errno':13,'marker_found':False})}))
        with patch('process_probe.subprocess.Popen',return_value=dummy) as spawn,patch('process_probe.subprocess.run',return_value=control) as run:
            self.assertTrue(probe_process_access(box)['passed'])
            self.assertEqual(set(spawn.call_args.kwargs['env']),{'PATH','ORCHIVANE_DUMMY'})
            self.assertEqual(run.call_args.args[0][-2],'1234')
            self.assertEqual(box.run.call_args.args[0][-2],'1234')
            dummy.kill.assert_called_once();dummy.communicate.assert_called_once()

    def test_failed_control_never_counts_as_isolation(self):
        dummy=Mock(pid=1234)
        control=SimpleNamespace(returncode=0,stdout=json.dumps({'read_returncode':-1,'read_errno':1,'marker_found':False}))
        box=SimpleNamespace(python='/explicit/python',run=Mock())
        with patch('process_probe.subprocess.Popen',return_value=dummy),patch('process_probe.subprocess.run',return_value=control):
            self.assertFalse(probe_process_access(box)['passed'])
            box.run.assert_not_called()
