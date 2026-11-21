import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from container_backend import ContainerSandbox, ContainerUnavailable, container_preflight

IMAGE='sha256:'+'a'*64


class ContainerTests(unittest.TestCase):
    def network_probe(self, flags, ipv4='', ipv6='', socket_error=False):
        import container_backend, socket
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for name,value in flags.items():
                p=root/'sys/class/net'/name;p.mkdir(parents=True)
                (p/'flags').write_text(hex(value))
            (root/'sys/class/net/bonding_masters').write_text('')
            p=root/'proc/net';p.mkdir(parents=True)
            (p/'route').write_text('Iface Destination Gateway Flags RefCnt Use Metric Mask MTU Window IRTT\n'+ipv4)
            (p/'ipv6_route').write_text(ipv6)
            scope={'checks':{},'Path':lambda p:root/str(p).lstrip('/'),'socket':socket}
            with patch.object(socket,'if_nameindex',side_effect=OSError('denied') if socket_error else None,return_value=list(enumerate(flags,1))):
                exec(container_backend.NETWORK_PROBE_CODE,scope)
            return scope['checks']

    def test_down_tunnels_and_sysfs_control_file_are_not_active_network(self):
        result=self.network_probe({'lo':9,'gre0':128,'tunl0':128})
        self.assertTrue(result['private_network'])
        self.assertEqual(result['network_diagnostics']['active_non_loopback'],[])

    def test_up_interface_rejected_regardless_of_tunnel_name(self):
        self.assertFalse(self.network_probe({'lo':9,'gre0':129})['private_network'])

    def test_nonloopback_ipv4_route_rejected_even_with_interface_down(self):
        self.assertFalse(self.network_probe({'lo':9,'gre0':128},ipv4='gre0 00000000 00000000 0001 0 0 0 00000000 0 0 0\n')['private_network'])

    def test_nonloopback_ipv6_route_rejected(self):
        row='0'*32+' 00 '+'0'*32+' 00 '+'0'*32+' 00000000 00000000 00000000 00000001 gre0\n'
        self.assertFalse(self.network_probe({'lo':9,'gre0':128},ipv6=row)['private_network'])

    def test_interface_inspection_error_fails_closed(self):
        result=self.network_probe({'lo':9},socket_error=True)
        self.assertFalse(result['private_network'])
        self.assertIn('denied',result['network_diagnostics']['error'])

    def test_only_task_is_mounted_and_image_is_immutable(self):
        with tempfile.TemporaryDirectory() as d:
            box=ContainerSandbox(d,image=IMAGE)
            args=box.create_args('orchivane-test',['/bin/bash','-c','true'])
            self.assertEqual(args.count('--mount'),1)
            self.assertIn('type=bind,src='+str(Path(d).resolve())+',dst=/task',args)
            for flag in ['--read-only','--network=none','--ipc=private','--cap-drop=ALL','--security-opt=no-new-privileges','--pull=never']:
                self.assertIn(flag,args)
            self.assertNotIn('--privileged',args);self.assertNotIn('--pid=host',args)
            self.assertIn(IMAGE,args)
            ro=box.create_args('orchivane-test',['/usr/local/bin/python3'],read_only=True)
            self.assertIn('type=bind,src='+str(Path(d).resolve())+',dst=/task,readonly',ro)
            with self.assertRaises(ValueError):ContainerSandbox(d,image='python:latest')

    def test_cancellation_prevents_new_container(self):
        with tempfile.TemporaryDirectory() as d:
            box=ContainerSandbox(d,image=IMAGE);box.cancel_active()
            with patch.object(box,'control') as control:
                self.assertTrue(box.run(['/bin/true'])['cancelled'])
                control.assert_not_called()

    def test_cleanup_must_confirm_absence(self):
        with tempfile.TemporaryDirectory() as d:
            box=ContainerSandbox(d,image=IMAGE)
            with patch.object(box,'control',side_effect=['removed','still-present']):
                with self.assertRaises(ContainerUnavailable):box.remove_owned('orchivane-test')

    def test_unavailable_daemon_stops_before_image_or_execution(self):
        with patch('container_backend.docker_control',side_effect=ContainerUnavailable('daemon denied')) as control:
            result=container_preflight()
            self.assertFalse(result['passed']);self.assertEqual(result['stage'],'daemon')
            self.assertEqual(control.call_count,1)

    def test_nonzero_command_and_timeout_both_remove_container(self):
        for timeout in (False,True):
            with self.subTest(timeout=timeout),tempfile.TemporaryDirectory() as d:
                box=ContainerSandbox(d,image=IMAGE)
                def control(args,**kwargs):
                    if args[0]=='create':return 'container-id'
                    if args[0]=='inspect':return json.dumps({'Running':False,'ExitCode':7,'OOMKilled':False})
                    self.fail(args)
                outcome={'returncode':0,'stdout':'hello','stderr':'','timed_out':timeout,'output_limited':False,'cancelled':False}
                with patch.object(box,'control',side_effect=control),patch.object(box,'attach',return_value=outcome),patch.object(box,'remove_owned') as remove:
                    result=box.run(['/bin/false'])
                    self.assertEqual(result['returncode'],-9 if timeout else 7)
                    remove.assert_called_once()

    def test_cleanup_error_blocks_later_checks(self):
        with tempfile.TemporaryDirectory() as d:
            box=ContainerSandbox(d,image=IMAGE)
            with patch.object(box,'control',return_value='id'),patch.object(box,'attach',side_effect=RuntimeError('attach failed')),patch.object(box,'remove_owned',side_effect=ContainerUnavailable('remove failed')):
                with self.assertRaises(ContainerUnavailable):box.run(['/bin/true'])
            with self.assertRaises(ContainerUnavailable):box.cancel_active()

    def test_cancel_waits_for_active_container_removal(self):
        import threading
        started=threading.Event();removed=threading.Event();results=[]
        with tempfile.TemporaryDirectory() as d:
            box=ContainerSandbox(d,image=IMAGE)
            def attach(*args):
                started.set();box._stop.wait(2)
                return {'returncode':-9,'stdout':'','stderr':'','timed_out':False,'cancelled':True,'output_limited':False}
            with patch.object(box,'control',return_value='id'),patch.object(box,'attach',side_effect=attach),patch.object(box,'remove_owned',side_effect=lambda _:removed.set()):
                thread=threading.Thread(target=lambda:results.append(box.run(['/bin/true'])));thread.start()
                self.assertTrue(started.wait(1));box.cancel_active();thread.join(1)
                self.assertTrue(removed.is_set());self.assertFalse(thread.is_alive())
                self.assertTrue(results[0]['cancelled'])

    def test_oracle_path_and_readonly_mount_are_forwarded(self):
        from strict_experiment import isolated_evaluators
        with tempfile.TemporaryDirectory() as d:
            box=ContainerSandbox(d,image=IMAGE)
            with patch.object(box,'run',return_value={'returncode':0,'timed_out':False,'stdout':'{"static_core":true}'}) as run:
                evaluate,_=isolated_evaluators(box)
                self.assertEqual(evaluate(d,'core'),{'static_core':True})
                self.assertEqual(run.call_args.args[0][-2],'/task')
                self.assertTrue(run.call_args.kwargs['read_only'])

    def test_image_preparation_failure_does_not_load_key(self):
        import contextlib,io
        from strict_experiment import main
        with patch('strict_experiment.docker_control',side_effect=ContainerUnavailable('denied')),patch('strict_experiment.load_key') as key,contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(['--prepare-image']),2);key.assert_not_called()
