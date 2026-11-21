"""Probe actual argv reads against a disposable, credential-free process only."""
import json
import subprocess
import uuid

PROBE_CODE=r'''
import ctypes,json,sys
libc=ctypes.CDLL(None,use_errno=True)
libc.sysctl.argtypes=[ctypes.POINTER(ctypes.c_int),ctypes.c_uint,ctypes.c_void_p,ctypes.POINTER(ctypes.c_size_t),ctypes.c_void_p,ctypes.c_size_t]
libc.sysctl.restype=ctypes.c_int
mib=(ctypes.c_int*3)(1,49,int(sys.argv[1]))
size=ctypes.c_size_t()
ctypes.set_errno(0)
sr=libc.sysctl(mib,3,None,ctypes.byref(size),None,0);se=ctypes.get_errno()
buffer=ctypes.create_string_buffer(1024*1024);length=ctypes.c_size_t(len(buffer))
ctypes.set_errno(0)
r=libc.sysctl(mib,3,buffer,ctypes.byref(length),None,0);e=ctypes.get_errno()
print(json.dumps({'size_returncode':sr,'size_errno':se,'size':size.value,
                 'read_returncode':r,'read_errno':e,
                 'marker_found':r==0 and sys.argv[2].encode() in buffer.raw[:length.value]}))
'''


def classify(control,confined):
    """A working positive control and denied actual read are both mandatory."""
    return (control.get('read_returncode')==0 and control.get('marker_found') is True
            and confined.get('read_returncode')==-1 and confined.get('read_errno') in (1,13)
            and confined.get('marker_found') is False)


def probe_process_access(box):
    marker='orchivane-dummy-'+uuid.uuid4().hex
    # No host environment, credential, controller argv or real runtime is read.
    dummy=subprocess.Popen([str(box.python),'-I','-B','-c','import sys; sys.stdin.buffer.read()',marker],
                           env={'PATH':'/usr/bin:/bin','ORCHIVANE_DUMMY':marker},stdin=subprocess.PIPE,
                           stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,close_fds=True)
    evidence={'passed':False,'target':'disposable credential-free process'}
    try:
        argv=[str(box.python),'-I','-B','-c',PROBE_CODE,str(dummy.pid),marker]
        control=subprocess.run(argv,env={'PATH':'/usr/bin:/bin'},stdin=subprocess.DEVNULL,
                               capture_output=True,text=True,timeout=5)
        if control.returncode:
            evidence.update(reason='positive control failed',stderr=control.stderr[:800]);return evidence
        evidence['control']=json.loads(control.stdout)
        if evidence['control'].get('read_returncode')!=0 or not evidence['control'].get('marker_found'):
            evidence['reason']='positive control could not read dummy marker';return evidence
        confined=box.run(argv,timeout=5)
        evidence['execution']={k:confined.get(k) for k in ('returncode','timed_out','cancelled','stderr')}
        if confined['returncode'] or confined.get('timed_out') or confined.get('cancelled'):
            evidence['reason']='confined probe did not complete';return evidence
        evidence['confined']=json.loads(confined['stdout'])
        evidence['passed']=classify(evidence['control'],evidence['confined']) and dummy.poll() is None
        if not evidence['passed']:evidence['reason']='actual read not denied or dummy exited; see returncode/errno'
        return evidence
    except (OSError,ValueError,subprocess.TimeoutExpired) as exc:
        evidence['reason']='process probe inconclusive: '+str(exc);return evidence
    finally:
        dummy.kill();dummy.communicate(timeout=2)
