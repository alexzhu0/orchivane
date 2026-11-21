"""Strict macOS tool-process confinement, distinct from DSH's write-only fence.

The trusted controller/runtime never executes inside this policy. Every model
command and evaluator importing generated code must use it. There is no
unconfined fallback; a successful capability probe is required before a trial.
"""
import json
import os
import selectors
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from process_probe import probe_process_access


class IsolationUnavailable(RuntimeError):
    pass


def _quote(path):
    # JSON's quote/backslash escaping agrees with SBPL string literals. Reject
    # controls rather than relying on JSON-only unicode escape semantics.
    value=str(path)
    if any(ord(c)<32 for c in value):raise ValueError('control character in sandbox path')
    return json.dumps(value,ensure_ascii=False)


def _kill_group(process):
    try:os.killpg(process.pid,signal.SIGKILL)
    except (ProcessLookupError,PermissionError):pass
    if process.poll() is None:
        try:process.kill()
        except ProcessLookupError:pass


def _existing_aliases(path):
    """Keep each existing spelling, including the macOS writable-volume alias."""
    original=Path(path).absolute();resolved=original.resolve(strict=True)
    data=Path('/System/Volumes/Data');candidates={original,resolved}
    for candidate in tuple(candidates):
        candidates.add(Path('/')/candidate.relative_to(data) if candidate.is_relative_to(data)
                       else data/str(candidate).lstrip('/'))
    result=[]
    for candidate in sorted(candidates):
        try:
            # Probe every existing counterpart. Cross-volume inode/device
            # comparisons must not silently remove a dangerous alias test.
            if candidate.exists():result.append(candidate)
        except OSError:continue
    return result


class Sandbox:
    """Allow task writes/reads and system/Python reads; deny everything else."""
    def __init__(self, work):
        self.work=Path(work).resolve(strict=True)
        if not self.work.is_dir():raise ValueError('sandbox workspace must be a directory')
        if Path(__file__).resolve().is_relative_to(self.work):
            raise ValueError('sandbox workspace must not contain controller source')
        self.python=Path(getattr(sys,'_base_executable',sys.executable)).resolve(strict=True)
        self.python_root=Path(sys.base_prefix).resolve(strict=True)
        # Never broaden a badly detected interpreter into a home/system grant.
        if not self.python.is_relative_to(self.python_root) or self.python_root in (Path('/'),Path('/usr'),Path('/usr/local'),Path.home()):
            raise IsolationUnavailable('Python installation cannot be granted narrowly')
        self.home=self.work/'.home';self.temp=self.work/'.tmp'
        for directory in (self.home,self.temp):
            if directory.is_symlink():raise ValueError('sandbox private directory is a symlink')
            directory.mkdir(exist_ok=True,mode=0o700)
        self._state_lock=threading.Lock();self._run_lock=threading.Lock()
        self._cancelled=threading.Event();self._idle=threading.Event();self._idle.set()
        self._active=None
        self._cleanup_failed=False

    @property
    def profile(self):
        # /System itself also contains /System/Volumes/Data/Users, an alias of
        # user data. Never grant it wholesale. No broad sysctl-read grant:
        # KERN_PROCARGS2 can otherwise disclose another process's environment.
        read_roots={Path(p).resolve() for p in ('/System/Library','/usr/lib','/usr/share','/usr/bin','/usr/sbin','/bin','/sbin')}
        read_roots.add(self.python_root)
        # Only metadata on ancestors: realpath/dyld may walk these, but neither
        # directory contents nor source bytes become readable by this grant.
        ancestors=set(self.work.parents)|set(self.python_root.parents)
        return '\n'.join([
            '(version 1)',
            '(deny default)',
            # Apple's narrow loader bootstrap grants Cryptex/cache access and
            # opening / as an openat root. Do not import broad system.sb.
            '(import "dyld-support.sb")',
            '(deny network*)',
            # ctypes imports os.uname() on Darwin. Permit only its basic OS
            # identity queries; process argv/environment sysctls stay denied.
            '(allow sysctl-read (sysctl-name "kern.ostype" "kern.osrelease" "kern.version" "kern.hostname" "hw.machine"))',
            '(deny sysctl-read (sysctl-name "kern.procargs" "kern.procargs2"))',
            '(allow process-exec process-fork)',
            '(allow signal (target same-sandbox))',
            '(allow file-read-metadata '+ ' '.join('(literal '+_quote(p)+')' for p in sorted(ancestors))+')',
            '(allow file-read* '+ ' '.join('(subpath '+_quote(p)+')' for p in sorted(read_roots))+')',
            '(allow file-map-executable '+ ' '.join('(subpath '+_quote(p)+')' for p in sorted(read_roots))+')',
            '(allow file-read* file-write* (subpath '+_quote(self.work)+'))',
            '(allow file-read* file-write* (literal "/dev/null"))',
            '(allow file-read* (literal "/dev/random") (literal "/dev/urandom") (literal "/private/etc/localtime"))',
        ])

    def argv(self, command_argv):
        if sys.platform!='darwin':raise IsolationUnavailable('strict Seatbelt isolation requires macOS')
        if not Path('/usr/bin/sandbox-exec').is_file():raise IsolationUnavailable('sandbox-exec missing')
        if not command_argv or not all(isinstance(s,str) and '\0' not in s for s in command_argv):
            raise ValueError('nonempty string argv required')
        return ['/usr/bin/sandbox-exec','-p',self.profile,*command_argv]

    def environment(self):
        return {'PATH':str(self.python.parent)+':/usr/bin:/bin:/usr/sbin:/sbin',
                'HOME':str(self.home),'TMPDIR':str(self.temp),'LANG':'en_US.UTF-8',
                'LC_ALL':'en_US.UTF-8','PYTHONDONTWRITEBYTECODE':'1'}

    def run(self, command_argv, *, timeout=30, max_output=65536):
        if timeout<=0 or max_output<1:raise ValueError('positive execution limits required')
        argv=self.argv(command_argv)
        result={'returncode':None,'stdout':'','stderr':'','timed_out':False,'output_limited':False,'cancelled':False}
        # Serial execution plus sticky shutdown makes a queued command unable
        # to start after cancel_active() has begun waiting for cleanup.
        with self._run_lock:
            with self._state_lock:
                if self._cancelled.is_set():return {**result,'cancelled':True}
                self._idle.clear()
            try:return self._execute(argv,result,timeout,max_output)
            finally:
                with self._state_lock:self._active=None;self._idle.set()

    def _execute(self, argv, result, timeout, max_output):
        streams={'stdout':bytearray(),'stderr':bytearray()};total=0;process=None
        try:
            with self._state_lock:
                if self._cancelled.is_set():return {**result,'cancelled':True}
                process=subprocess.Popen(argv,cwd=self.work,env=self.environment(),stdin=subprocess.DEVNULL,
                                         stdout=subprocess.PIPE,stderr=subprocess.PIPE,close_fds=True,start_new_session=True)
                self._active=process
            deadline=time.monotonic()+timeout
            with selectors.DefaultSelector() as selector:
                for name in streams:selector.register(getattr(process,name),selectors.EVENT_READ,name)
                while selector.get_map():
                    if self._cancelled.is_set():result['cancelled']=True;break
                    remaining=deadline-time.monotonic()
                    if remaining<=0:
                        result['timed_out']=True;break
                    for key,_ in selector.select(min(remaining,.1)):
                        chunk=os.read(key.fileobj.fileno(),4096)
                        if not chunk:selector.unregister(key.fileobj);continue
                        available=max_output-total
                        streams[key.data].extend(chunk[:available]);total+=min(len(chunk),available)
                        if len(chunk)>available:result['output_limited']=True;break
                    if result['output_limited']:break
                if not result['timed_out'] and not result['output_limited'] and not result['cancelled']:
                    try:process.wait(timeout=max(.001,deadline-time.monotonic()))
                    except subprocess.TimeoutExpired:result['timed_out']=True
        except OSError as exc:
            raise IsolationUnavailable('sandbox process could not start: '+str(exc)) from exc
        finally:
            if process is not None:
                # Reap the owned group even when its direct shell has exited.
                # Descendants that deliberately create another session are not
                # claimed reaped, but retain the inherited kernel sandbox.
                _kill_group(process)
                try:process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    self._cleanup_failed=True
                    raise IsolationUnavailable('sandbox child not reaped')
                finally:
                    result['returncode']=process.returncode
                    for name in streams:getattr(process,name).close()
        result['cancelled']=result['cancelled'] or self._cancelled.is_set()
        for name,data in streams.items():result[name]=data.decode('utf-8',errors='replace')
        return result

    def cancel_active(self, timeout=2):
        """Permanently shut this executor down and wait for its run cleanup.

        Failure to join cleanup raises; the caller must not proceed to final
        evaluation while an executor thread may still mutate the workspace.
        """
        with self._state_lock:
            self._cancelled.set();process=self._active
        if process is not None:_kill_group(process)
        if not self._idle.wait(timeout) or self._cleanup_failed:
            raise IsolationUnavailable('sandbox cancellation did not finish; evaluation must not proceed')

    def run_shell(self, command, *, timeout=30, max_output=65536):
        if not isinstance(command,str):raise ValueError('command must be text')
        return self.run(['/bin/bash','--noprofile','--norc','-c',command],timeout=timeout,max_output=max_output)


def probe_details(outcome):
    code=outcome.get('returncode');signame=None
    if isinstance(code,int) and code<0:
        try:signame=signal.Signals(-code).name
        except ValueError:signame='UNKNOWN'
    return {'returncode':code,'signal':signame,
            **{k:bool(outcome.get(k)) for k in ('timed_out','output_limited','cancelled')},
            'stdout':outcome.get('stdout','')[:800],'stderr':outcome.get('stderr','')[:800]}


def isolation_preflight(work=None, forbidden_paths=()):
    """Real positive/negative probes. No key, model request, or silent fallback.

    ``work`` optionally selects the parent for disposable probe material.
    Existing forbidden paths are opened without reading their bytes; an open
    succeeding means isolation failed. The parent never reads those files.
    """
    probes={};outcomes={};result={'passed':False,'reason':None,'probes':probes,'probe_results':outcomes,'mechanism':'macOS Seatbelt deny-default per child'}
    try:
        with tempfile.TemporaryDirectory(prefix='orchivane-isolation-',dir=work) as directory:
            root=Path(directory);task=root/'task';task.mkdir()
            outside=root/'controller-marker';outside.write_text('private experiment sentinel')
            observation=root/'observations'/'future-marker';observation.parent.mkdir();observation.write_text('private future sentinel')
            other_arm=root/'other-arm'/'task-marker';other_arm.parent.mkdir();other_arm.write_text('private competing trial sentinel')
            (task/'outside-link').symlink_to(outside)
            box=Sandbox(task)
            positive=box.run([str(box.python),'-I','-B','-c',
                'from pathlib import Path; p=Path("allowed"); p.write_text("ok"); assert p.read_text()=="ok"; print("task-ok")'],timeout=5)
            probes['task_read_write']=positive['returncode']==0 and positive['stdout'].strip()=='task-ok'
            outcomes['task_read_write']=probe_details(positive)
            if not probes['task_read_write']:
                result['reason']='strict sandbox unavailable or required Python/task access denied'
                result['failed_probe']='task_read_write'
                result['detail']=positive['stderr'][:800] or 'Python probe stopped: '+json.dumps(outcomes['task_read_write'])
                return result
            denied_code='''import os,sys
for p in sys.argv[1:]:
    try: fd=os.open(p,os.O_RDONLY)
    except PermissionError: continue
    except OSError as e: raise SystemExit("not a verified policy denial: "+str(e.errno))
    else: os.close(fd); raise SystemExit("forbidden open succeeded")
print("read-denied")
'''
            forbidden=[outside,observation,other_arm,*forbidden_paths]
            # Do not resolve away the alternate spelling passed to the child.
            candidates=sorted({p for path in forbidden for p in _existing_aliases(path)})
            denied=box.run([str(box.python),'-I','-B','-c',denied_code,str(task/'outside-link'),*map(str,candidates)],timeout=5)
            probes['outside_and_symlink_read_denied']=denied['returncode']==0 and denied['stdout'].strip()=='read-denied'
            probes['observation_other_arm_and_available_aliases_denied']=probes['outside_and_symlink_read_denied']
            result['data_volume_aliases_checked']=sum(p.is_relative_to('/System/Volumes/Data') for p in candidates)
            writes=box.run([str(box.python),'-I','-B','-c',
                'import os,sys\ntry: fd=os.open(sys.argv[1],os.O_WRONLY)\nexcept PermissionError: print("write-denied")\nelse: os.close(fd); raise SystemExit(1)',str(outside)],timeout=5)
            probes['outside_write_denied']=writes['returncode']==0 and writes['stdout'].strip()=='write-denied'
            network=box.run([str(box.python),'-I','-B','-c',
                'import socket\ntry: s=socket.socket(); s.bind(("127.0.0.1",0))\nexcept PermissionError: print("network-denied")\nelse: s.close(); raise SystemExit(1)'],timeout=5)
            probes['network_denied']=network['returncode']==0 and network['stdout'].strip()=='network-denied'
            # A real listening socket distinguishes policy denial from a missing
            # endpoint. /tmp keeps AF_UNIX paths under macOS's short path limit.
            with tempfile.TemporaryDirectory(prefix='ov-',dir='/tmp') as socket_dir:
                endpoint=str(Path(socket_dir)/'s')
                with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as listener:
                    listener.bind(endpoint);listener.listen(1)
                    ipc=box.run([str(box.python),'-I','-B','-c',
                        'import socket,sys\ns=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)\ntry: s.connect(sys.argv[1])\nexcept PermissionError: print("ipc-denied")\nelse: s.close(); raise SystemExit(1)',endpoint],timeout=5)
            probes['controller_socket_connect_denied']=ipc['returncode']==0 and ipc['stdout'].strip()=='ipc-denied'
            process_probe=probe_process_access(box)
            probes['external_process_args_denied']=process_probe['passed']
            result['process_access_probe']=process_probe
            shell=box.run_shell('python -I -B -c \'print("shell-ok")\'',timeout=5)
            probes['shell_python_works']=shell['returncode']==0 and shell['stdout'].strip()=='shell-ok'
            for name,outcome in [('outside_and_symlink_read_denied',denied),
                                 ('observation_other_arm_and_available_aliases_denied',denied),
                                 ('outside_write_denied',writes),('network_denied',network),
                                 ('controller_socket_connect_denied',ipc),
                                 ('shell_python_works',shell)]:
                outcomes[name]=probe_details(outcome)
            result['passed']=all(probes.values())
            if not result['passed']:
                result['reason']='strict sandbox capability probes failed'
                result['failed_probes']=[name for name,passed in probes.items() if not passed]
    except (OSError,ValueError,IsolationUnavailable) as exc:
        result['reason']='strict sandbox unavailable: '+str(exc)
    return result
