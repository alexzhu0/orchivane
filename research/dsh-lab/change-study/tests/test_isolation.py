import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from isolation import Sandbox, IsolationUnavailable, isolation_preflight


class IsolationTests(unittest.TestCase):
    def test_uname_sysctls_allowed_without_process_argument_access(self):
        import re
        with tempfile.TemporaryDirectory() as d:
            profile=Sandbox(Path(d)).profile
            rules=re.findall(r'\(allow sysctl-read\s+\(sysctl-name ([^)]*)\)\)',profile)
            self.assertEqual(len(rules),1)
            self.assertEqual(set(re.findall(r'"([^"]+)"',rules[0])),
                             {'kern.ostype','kern.osrelease','kern.version','kern.hostname','hw.machine'})
            self.assertNotIn('(allow sysctl-read)',profile)
            self.assertIn('(deny sysctl-read (sysctl-name "kern.procargs" "kern.procargs2"))',profile)

    def test_native_loader_bootstrap_is_narrow_and_explicit(self):
        with tempfile.TemporaryDirectory() as d:
            profile=Sandbox(Path(d)).profile
            self.assertIn('(import "dyld-support.sb")',profile)
            self.assertIn('(allow file-map-executable ',profile)
            self.assertNotIn('(import "system.sb")',profile)
            self.assertNotIn('(subpath "/System")',profile)
            self.assertNotIn('(allow sysctl-read)',profile)

    def test_silent_loader_abort_has_exit_signal_and_probe_details(self):
        outcome={'returncode':-6,'stdout':'','stderr':'','timed_out':False,'output_limited':False,'cancelled':False}
        with patch.object(Sandbox,'run',return_value=outcome):
            result=isolation_preflight()
            self.assertFalse(result['passed'])
            self.assertEqual(result['failed_probe'],'task_read_write')
            self.assertEqual(result['probe_results']['task_read_write']['signal'],'SIGABRT')
            self.assertEqual(result['probe_results']['task_read_write']['returncode'],-6)
            self.assertTrue(result['detail'])

    def test_profile_defaults_deny_and_only_grants_task_and_runtime(self):
        with tempfile.TemporaryDirectory() as d:
            work=Path(d)/'task';work.mkdir()
            box=Sandbox(work)
            profile=box.profile
            self.assertIn('(deny default)',profile)
            self.assertNotIn('(allow default)',profile)
            self.assertIn('(deny network*)',profile)
            self.assertIn('(subpath "'+str(work.resolve())+'")',profile)
            self.assertNotIn('(subpath "/Users")',profile)
            self.assertNotIn('(subpath "/usr/local")',profile)
            self.assertNotIn('(subpath "/System")',profile)
            self.assertIn('(subpath "/System/Library")',profile)
            self.assertNotIn('(allow sysctl-read)',profile)
            self.assertNotIn('(subpath "'+str(Path(d).resolve())+'")',profile)
            self.assertNotIn('(allow mach-lookup)',profile)

    def test_child_environment_and_stdin_do_not_inherit_controller_authority(self):
        with tempfile.TemporaryDirectory() as d,patch.dict(os.environ,{'DEEPSEEK_API_KEY':'sentinel-secret','PYTHONPATH':'/forbidden','BASH_ENV':'/forbidden'}):
            box=Sandbox(Path(d))
            env=box.environment()
            self.assertNotIn('DEEPSEEK_API_KEY',env)
            self.assertNotIn('PYTHONPATH',env)
            self.assertNotIn('BASH_ENV',env)
            self.assertEqual(Path(env['HOME']).parent,Path(d).resolve())
            self.assertEqual(Path(env['TMPDIR']).parent,Path(d).resolve())
            argv=box.argv(['/bin/bash','--noprofile','--norc','-c','true'])
            self.assertEqual(argv[:2],['/usr/bin/sandbox-exec','-p'])
            self.assertEqual(argv[-1],'true')

    def test_wrong_platform_fails_closed_before_spawn(self):
        with tempfile.TemporaryDirectory() as d,patch('isolation.sys.platform','linux'),patch('isolation.subprocess.Popen') as spawn:
            with self.assertRaises(IsolationUnavailable):Sandbox(Path(d)).run(['/usr/bin/true'])
            spawn.assert_not_called()

    def test_profile_quotes_paths_without_policy_injection(self):
        with tempfile.TemporaryDirectory() as d:
            work=Path(d)/'quote" slash\\ x';work.mkdir()
            profile=Sandbox(work).profile
            self.assertIn('quote\\" slash\\\\ x',profile)
            self.assertEqual(profile.count('(version 1)'),1)

    def test_workspace_must_not_contain_controller_source(self):
        with self.assertRaisesRegex(ValueError,'controller'):
            Sandbox(Path(__file__).resolve().parents[1])

    def test_failed_sandbox_probe_never_claims_enforcement(self):
        failed={'returncode':1,'stdout':'','stderr':'sandbox-exec: sandbox_apply: Operation not permitted','timed_out':False,'output_limited':False}
        with patch.object(Sandbox,'run',return_value=failed):
            result=isolation_preflight()
            self.assertFalse(result['passed'])
            self.assertIn('unavailable',result['reason'])
            self.assertFalse(result['probes'].get('task_read_write',False))

    def test_shell_uses_noninteractive_bash_and_explicit_argv(self):
        with tempfile.TemporaryDirectory() as d,patch.object(Sandbox,'run',return_value={'returncode':0}) as run:
            Sandbox(Path(d)).run_shell('printf "!r"',timeout=2)
            self.assertEqual(run.call_args.args[0],['/bin/bash','--noprofile','--norc','-c','printf "!r"'])
            self.assertEqual(run.call_args.kwargs['timeout'],2)

    def test_shutdown_cancellation_kills_owned_process_and_joins_run(self):
        # Only fake process/selector objects: this does not bypass Seatbelt.
        from unittest.mock import MagicMock
        spawned=threading.Event();killed=threading.Event();outcomes=[]
        process=MagicMock();process.pid=12345;process.returncode=None
        process.poll.side_effect=lambda:process.returncode
        def kill(*args):
            process.returncode=-9;killed.set()
        def wait(timeout=None):
            if not killed.wait(timeout):raise subprocess.TimeoutExpired('fake',timeout)
            return process.returncode
        process.wait.side_effect=wait
        def start(*args,**kwargs):spawned.set();return process
        selector=MagicMock();selector.__enter__.return_value=selector
        selector.get_map.return_value={'stdout':object()}
        selector.select.side_effect=lambda timeout:(time.sleep(min(timeout,.01)) or [])
        with tempfile.TemporaryDirectory() as d,patch('isolation.subprocess.Popen',side_effect=start) as spawn,patch('isolation.selectors.DefaultSelector',return_value=selector),patch('isolation._kill_group',side_effect=kill):
            box=Sandbox(Path(d));thread=threading.Thread(target=lambda:outcomes.append(box.run(['/usr/bin/true'],timeout=5)))
            thread.start()
            try:
                self.assertTrue(spawned.wait(1))
                box.cancel_active();thread.join(1)
            finally:
                kill();thread.join(6)
            self.assertFalse(thread.is_alive())
            self.assertTrue(killed.is_set())
            self.assertTrue(outcomes[0]['cancelled'])
            self.assertEqual(outcomes[0]['returncode'],-9)
            # Shutdown is sticky: another queued call may not spawn afterwards.
            result=box.run(['/usr/bin/true'])
            self.assertTrue(result['cancelled'])
            self.assertEqual(spawn.call_count,1)

    def test_cancellation_timeout_does_not_claim_cleanup_finished(self):
        with tempfile.TemporaryDirectory() as d:
            box=Sandbox(Path(d));box._idle.clear()
            with self.assertRaisesRegex(IsolationUnavailable,'evaluation must not proceed'):
                box.cancel_active(timeout=.001)

    def test_unreaped_direct_child_prevents_final_evaluation(self):
        from unittest.mock import MagicMock
        process=MagicMock();process.returncode=None
        process.wait.side_effect=subprocess.TimeoutExpired('dummy',1)
        selector=MagicMock();selector.__enter__.return_value=selector;selector.get_map.return_value={}
        with tempfile.TemporaryDirectory() as d,patch('isolation.subprocess.Popen',return_value=process),patch('isolation.selectors.DefaultSelector',return_value=selector),patch('isolation._kill_group'):
            box=Sandbox(Path(d))
            with self.assertRaisesRegex(IsolationUnavailable,'not reaped'):box.run(['/usr/bin/true'])
            with self.assertRaisesRegex(IsolationUnavailable,'evaluation must not proceed'):box.cancel_active()

    def test_preflight_checks_observation_other_arm_and_data_volume_aliases(self):
        observed=[]
        def fake_run(self,argv,**kwargs):
            observed.extend(argv)
            code=argv[4] if len(argv)>4 and argv[3]=='-c' else ''
            token=next((x for x in ('task-ok','read-denied','write-denied','network-denied','ipc-denied','process-denied','shell-ok') if x in code),'')
            return {'returncode':0,'stdout':token,'stderr':'','timed_out':False,'output_limited':False,'cancelled':False}
        def aliases(path):
            p=Path(path).absolute()
            return [p,Path('/System/Volumes/Data')/str(p).lstrip('/')]
        with patch.object(Sandbox,'run',fake_run),patch('isolation._existing_aliases',side_effect=aliases),patch('isolation.socket.socket'),patch('isolation.probe_process_access',return_value={'passed':True}):
            result=isolation_preflight()
        self.assertTrue(result['passed'],result)
        self.assertTrue(any('/observations/' in x for x in observed))
        self.assertTrue(any('/other-arm/' in x for x in observed))
        self.assertTrue(any(x.startswith('/System/Volumes/Data/') and 'controller-marker' in x for x in observed))


if __name__=='__main__':unittest.main()
