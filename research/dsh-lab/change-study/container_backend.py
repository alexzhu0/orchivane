"""Linux containers for generated commands; never fall back to host execution."""
import base64
import json
import os
import re
import selectors
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from pathlib import Path

DEFAULT_IMAGE='python:3.11-slim'

# Run inside the container: dormant kernel tunnel devices are permitted, but
# any UP non-loopback interface or non-loopback route fails acceptance.
NETWORK_PROBE_CODE='''network={'criterion':'no active non-loopback interfaces or routes'}
checks['private_network']=False
try:
    network['sysfs_interfaces']=sorted(p.name for p in Path('/sys/class/net').iterdir())
    network['socket_interfaces']=sorted(name for _,name in socket.if_nameindex())
    network['interface_flags']={name:int((Path('/sys/class/net')/name/'flags').read_text().strip(),16) for name in network['socket_interfaces']}
    network['active_non_loopback']=[name for name,flags in network['interface_flags'].items() if name!='lo' and flags & 1]
    network['ipv4_routes']=Path('/proc/net/route').read_text().splitlines()[1:]
    network['ipv6_routes']=Path('/proc/net/ipv6_route').read_text().splitlines()
    routes=[]
    for row in network['ipv4_routes']:
        fields=row.split()
        if len(fields)!=11:raise ValueError('invalid IPv4 route row')
        if fields[0]!='lo':routes.append(row)
    for row in network['ipv6_routes']:
        fields=row.split()
        if len(fields)!=10:raise ValueError('invalid IPv6 route row')
        if fields[-1]!='lo':routes.append(row)
    network['non_loopback_routes']=routes
    checks['private_network']='lo' in network['socket_interfaces'] and not network['active_non_loopback'] and not routes
except (OSError,ValueError) as exc:network['error']=str(exc)
checks['network_diagnostics']=network
'''


class ContainerUnavailable(RuntimeError):pass


def docker_control(args,timeout=10):
    binary=shutil.which('docker')
    if not binary:raise ContainerUnavailable('Docker CLI not found')
    # The CLI retains Docker connection configuration, never forwards it to tools.
    env={k:v for k,v in os.environ.items() if k in ('PATH','HOME','DOCKER_HOST','DOCKER_CONTEXT','DOCKER_CONFIG','DOCKER_TLS_VERIFY','DOCKER_CERT_PATH')}
    try:
        result=subprocess.run([binary,*args],env=env,stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=timeout)
    except (OSError,subprocess.TimeoutExpired) as exc:raise ContainerUnavailable(str(exc)) from exc
    if result.returncode:raise ContainerUnavailable(result.stderr.strip()[:1000] or f'Docker command failed ({result.returncode})')
    return result.stdout.strip()


class ContainerSandbox:
    python='/usr/local/bin/python3'
    task_path='/task'

    def __init__(self,work,*,image):
        self.work=Path(work).resolve(strict=True)
        if not self.work.is_dir() or Path(__file__).resolve().is_relative_to(self.work):
            raise ValueError('task directory must not include controller source')
        if any(c in str(self.work) for c in (',','\n','\r')):raise ValueError('unsupported mount path characters')
        if not re.fullmatch(r'sha256:[0-9a-f]{64}',image):raise ValueError('immutable local image ID required')
        self.image=image;self._stop=threading.Event();self._idle=threading.Event();self._idle.set()
        self._serial=threading.Lock();self._state=threading.Lock();self._cleanup_failed=False;self.executions=[]

    def control(self,args,timeout=10):return docker_control(args,timeout)

    def create_args(self,name,argv,read_only=False):
        if not argv or not all(isinstance(x,str) and '\0' not in x for x in argv):raise ValueError('invalid container argv')
        mount='type=bind,src='+str(self.work)+',dst=/task'+(',readonly' if read_only else '')
        return ['create','--name',name,'--label','orchivane.change-study=true','--pull=never',
                '--network=none','--ipc=private','--read-only','--cap-drop=ALL','--security-opt=no-new-privileges',
                '--pids-limit=64','--memory=512m','--memory-swap=512m','--cpus=1','--init',
                '--user',f'{os.getuid()}:{os.getgid()}','--workdir=/task','--mount',mount,
                '--tmpfs','/tmp:rw,nosuid,nodev,noexec,size=64m,mode=1777','--no-healthcheck','--log-driver=none',
                '--entrypoint=/usr/bin/env',self.image,'-i','PATH=/usr/local/bin:/usr/bin:/bin',
                'HOME=/tmp','TMPDIR=/tmp','LANG=C.UTF-8','PYTHONDONTWRITEBYTECODE=1',*argv]

    def remove_owned(self,name):
        # Exact unguessable per-call name; never prune unrelated containers.
        self.control(['rm','--force',name])
        remaining=self.control(['ps','--all','--quiet','--filter','name=^/'+name+'$'])
        if remaining:raise ContainerUnavailable('owned container remains after removal')

    def attach(self,name,timeout,max_output):
        result={'returncode':None,'stdout':'','stderr':'','timed_out':False,'output_limited':False,'cancelled':False}
        binary=shutil.which('docker')
        if not binary:raise ContainerUnavailable('Docker CLI not found')
        env={k:v for k,v in os.environ.items() if k in ('PATH','HOME','DOCKER_HOST','DOCKER_CONTEXT','DOCKER_CONFIG','DOCKER_TLS_VERIFY','DOCKER_CERT_PATH')}
        p=subprocess.Popen([binary,'start','--attach',name],env=env,stdin=subprocess.DEVNULL,
                           stdout=subprocess.PIPE,stderr=subprocess.PIPE,close_fds=True)
        buffers={'stdout':bytearray(),'stderr':bytearray()};total=0;deadline=time.monotonic()+timeout
        try:
            with selectors.DefaultSelector() as selector:
                for stream in buffers:selector.register(getattr(p,stream),selectors.EVENT_READ,stream)
                while selector.get_map():
                    if self._stop.is_set():result['cancelled']=True;break
                    if time.monotonic()>=deadline:result['timed_out']=True;break
                    for key,_ in selector.select(min(.1,max(0,deadline-time.monotonic()))):
                        chunk=os.read(key.fileobj.fileno(),4096)
                        if not chunk:selector.unregister(key.fileobj);continue
                        remaining=max_output-total;buffers[key.data].extend(chunk[:remaining]);total+=min(len(chunk),remaining)
                        if len(chunk)>remaining:result['output_limited']=True;break
                    if result['output_limited']:break
            if not any(result[k] for k in ('timed_out','cancelled','output_limited')):
                try:result['returncode']=p.wait(timeout=max(.001,deadline-time.monotonic()))
                except subprocess.TimeoutExpired:result['timed_out']=True
        finally:
            if p.poll() is None:p.kill()
            p.wait(timeout=2)
            for stream in buffers:getattr(p,stream).close()
        for stream,value in buffers.items():result[stream]=value.decode(errors='replace')
        return result

    def run(self,argv,*,timeout=30,max_output=65536,read_only=False):
        if timeout<=0 or max_output<1:raise ValueError('positive limits required')
        with self._serial:
            with self._state:
                if self._cleanup_failed:raise ContainerUnavailable('previous container cleanup unverified')
                if self._stop.is_set():return {'returncode':None,'stdout':'','stderr':'','timed_out':False,'cancelled':True,'output_limited':False}
                self._idle.clear()
            name='orchivane-'+uuid.uuid4().hex;started=time.monotonic();created=False;result=None
            try:
                self.control(self.create_args(name,argv,read_only));created=True
                created_at=time.monotonic()
                if self._stop.is_set():
                    result={'returncode':-9,'stdout':'','stderr':'','timed_out':False,'cancelled':True,'output_limited':False}
                else:result=self.attach(name,timeout,max_output)
                if any(result[k] for k in ('timed_out','cancelled','output_limited')):result['returncode']=-9
                else:
                    state=json.loads(self.control(['inspect','--format','{{json .State}}',name]))
                    if state['Running']:raise ContainerUnavailable('attached CLI exited while container still running')
                    result['returncode']=state['ExitCode'];result['oom_killed']=state.get('OOMKilled',False)
                result['container_create_seconds']=created_at-started
                return result
            finally:
                cleanup_started=time.monotonic()
                try:
                    self.remove_owned(name)
                    if not created:
                        # A timed-out create has ambiguous daemon state, even if
                        # a removal happened to succeed. Do not continue scoring.
                        self._cleanup_failed=True
                except Exception:
                    self._cleanup_failed=True
                    raise
                finally:
                    entry={'container':name,'seconds':time.monotonic()-started,
                           'cleanup_seconds':time.monotonic()-cleanup_started,'removed':not self._cleanup_failed}
                    if result is not None:entry.update({k:result.get(k) for k in ('container_create_seconds','returncode','timed_out','cancelled','output_limited')})
                    self.executions.append(entry);self._idle.set()

    def run_shell(self,command,*,timeout=30,max_output=65536):
        return self.run(['/bin/bash','--noprofile','--norc','-c',command],timeout=timeout,max_output=max_output)

    def cancel_active(self,timeout=30):
        with self._state:self._stop.set()
        if not self._idle.wait(timeout) or self._cleanup_failed:
            raise ContainerUnavailable('container cleanup unverified; evaluation must not proceed')


def container_preflight(image=DEFAULT_IMAGE):
    result={'passed':False,'stage':'daemon','mechanism':'Linux container PID/mount/network namespaces','probes':{}}
    try:
        server=json.loads(docker_control(['version','--format','{{json .Server}}']))
        if not server or server.get('Os')!='linux':raise ContainerUnavailable('Linux Docker daemon required')
        result['docker_version']=server.get('Version');result['stage']='image'
        image_info=json.loads(docker_control(['image','inspect',image]))[0]
        if image_info.get('Os')!='linux' or image_info.get('Config',{}).get('Volumes'):
            raise ContainerUnavailable('Linux image without implicit volumes required')
        result['image_id']=image_info['Id'];result['image_reference']=image
        result['stage']='container_probes'
        with tempfile.TemporaryDirectory(prefix='orchivane-container-') as d:
            root=Path(d);work=root/'task';work.mkdir();outside=root/'future-marker';outside.write_text('not mounted')
            (work/'outside-link').symlink_to(outside)
            marker='orchivane-host-'+uuid.uuid4().hex
            dummy=subprocess.Popen([sys.executable,'-I','-B','-c','import sys;sys.stdin.buffer.read()',marker],
                                   env={'PATH':'/usr/bin:/bin'},stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            box=ContainerSandbox(work,image=result['image_id'])
            try:
                code='''import base64,json,os,socket
from pathlib import Path
p=Path('/task/ok');p.write_text('ok');checks={'task_read_write':p.read_text()=='ok'}
checks['outside_unmounted']=not Path(OUTSIDE).exists() and not Path('/task/outside-link').exists()
checks['docker_socket_absent']=not Path('/var/run/docker.sock').exists() and not Path('/run/docker.sock').exists()
checks['no_api_environment']=not any('KEY' in k or 'TOKEN' in k for k in os.environ)
needle=base64.b64decode(MARKER)
seen=[]
for f in Path('/proc').glob('[0-9]*/cmdline'):
    try:seen.append(f.read_bytes())
    except (PermissionError,FileNotFoundError):pass
checks['host_process_invisible']=bool(seen) and not any(needle in x for x in seen)
NETWORK_PROBE
s=socket.socket();s.settimeout(.2)
try:s.connect(('192.0.2.1',80));checks['egress_denied']=False
except OSError:checks['egress_denied']=True
finally:s.close()
try:Path('/outside-write').write_text('bad');checks['root_read_only']=False
except OSError:checks['root_read_only']=True
print(json.dumps(checks))
'''.replace('OUTSIDE',repr(str(outside))).replace('MARKER',repr(base64.b64encode(marker.encode()).decode())).replace('NETWORK_PROBE',NETWORK_PROBE_CODE)
                probe=box.run([box.python,'-I','-B','-c',code],timeout=10)
                if probe['returncode']:raise ContainerUnavailable('container probe failed: '+probe['stderr'][:800])
                result['probes']=json.loads(probe['stdout'])
                result['network_diagnostics']=result['probes'].pop('network_diagnostics')
                result['probes']['host_task_bind_verified']=(work/'ok').is_file() and (work/'ok').read_text()=='ok'
                if dummy.poll() is not None:result['probes']['host_process_invisible']=False
                shell=box.run_shell('python3 -I -B -c \'print("shell-ok")\'',timeout=10)
                result['probes']['shell_python']=shell['returncode']==0 and shell['stdout'].strip()=='shell-ok'
                ro=box.run([box.python,'-I','-B','-c',"from pathlib import Path\ntry:Path('/task/forbidden').write_text('x')\nexcept OSError:print('readonly-ok')"],timeout=10,read_only=True)
                result['probes']['oracle_task_read_only']=ro['returncode']==0 and ro['stdout'].strip()=='readonly-ok'
                # A child escapes its process group, but remains in the container
                # PID namespace. Successful container removal must end its writes.
                timeout_code="import os,time\nif os.fork()==0:\n os.setsid()\n while True:\n  open('/task/heartbeat','a').write('x');time.sleep(.05)\ntime.sleep(60)"
                timed=box.run([box.python,'-I','-B','-c',timeout_code],timeout=2)
                heartbeat=work/'heartbeat';before=heartbeat.read_bytes() if heartbeat.exists() else b''
                time.sleep(.2);after=heartbeat.read_bytes() if heartbeat.exists() else b''
                result['probes']['timeout_stops_escaped_child']=timed['timed_out'] and bool(before) and before==after
                result['executions']=box.executions
                result['passed']=all(v is True for v in result['probes'].values())
                if not result['passed']:
                    result['failed_probes']=[name for name,value in result['probes'].items() if value is not True]
                    result['reason']='container acceptance probes failed'
                result['stage']='complete'
            finally:
                dummy.kill();dummy.communicate(timeout=2);box.cancel_active()
    except (OSError,ValueError,KeyError,IndexError,ContainerUnavailable,subprocess.TimeoutExpired) as exc:
        result['passed']=False;result['reason']=str(exc)
        if result['stage']=='image':result['setup_hint']='Run run-local.sh --prepare-image to pull the official Python image; no API key is used.'
    return result
