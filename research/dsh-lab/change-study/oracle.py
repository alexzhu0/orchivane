"""Independent, bounded checks. Executed outside the DSH session."""
import json
import os
import signal
import subprocess
import sys
from pathlib import Path

# Generated code shares this Python process. Before injection, it must never
# receive the final-phase source via argv, frames, globals or code constants.
CORE_CHECK_CODE=r'''
import json,sys
sys.path.insert(0,sys.argv[1])
from core import list_orders
try:
    rows=[(i,'a' if i%3 else 'b') for i in range(1,18)]
    assert list_orders(rows,'a',2)=={'items':[(17,'a'),(16,'a')],'next_cursor':2}
    assert list_orders(rows,'a',2,2)['items']==[(14,'a'),(13,'a')]
    result={'static_core':True}
except Exception as e:
    result={'static_core':type(e).__name__+': '+str(e)[:200]}
print(json.dumps(result))
'''

CHECK_CODE=r'''
import copy,json,sys
sys.path.insert(0,sys.argv[1])
from core import list_orders
checks={}
def require(x):
    if not x:raise AssertionError('contract mismatch')
def check(name,fn):
    try:fn();checks[name]=True
    except Exception as e:checks[name]=type(e).__name__+': '+str(e)[:200]
rows=[(i,'a' if i%3 else 'b') for i in range(1,18)]
if sys.argv[2]=='core':
    def static():
        r=list_orders(rows,'a',2)
        require(r=={'items':[(17,'a'),(16,'a')],'next_cursor':2})
        require(list_orders(rows,'a',2,2)['items']==[(14,'a'),(13,'a')])
    check('static_core',static)
else:
    from api import fetch_orders
    from client import collect_orders
    def traverse(fn):
        data=copy.deepcopy(rows);expected=sorted([r for r in rows if r[1]=='a'],reverse=True)
        seen=[];cursor=None
        for step in range(30):
            old=copy.deepcopy(data);r=fn(data,'a',2,cursor)
            require(data==old and len(r['items'])<=2)
            seen.extend(r['items']);cursor=json.loads(json.dumps(r['next_cursor']))
            if cursor is None:
                require(seen==expected);return
            data.extend([(100+step*2,'a'),(101+step*2,'b')])
        raise AssertionError('traversal did not end')
    check('core_snapshot',lambda:traverse(list_orders))
    check('api_snapshot',lambda:traverse(fetch_orders))
    def client():
        data=copy.deepcopy(rows);calls=0
        def fetch(size=2,cursor=None):
            nonlocal calls
            calls+=1
            if calls>30:raise AssertionError('client did not stop at end')
            if calls>1:data.append((100+calls,'a'))
            return fetch_orders(data,'a',size,cursor)
        require(collect_orders(fetch,2)==sorted([r for r in rows if r[1]=='a'],reverse=True))
    check('client_snapshot',client)
    def auth():
        for account in ['',None,17]:
            try:fetch_orders(rows,account)
            except ValueError:continue
            raise AssertionError('missing account accepted')
    check('auth',auth)
    def validation(fn):
        for size, expected_length in [(1,1),(100,12)]:
            require(len(fn(rows,'a',size)['items'])==expected_length)
        for size in [0,-1,101,True,'2',1.5]:
            try:fn(rows,'a',size)
            except ValueError:continue
            raise AssertionError('invalid size accepted')
    check('validation',lambda:validation(fetch_orders))
    check('core_validation',lambda:validation(list_orders))
    check('empty',lambda:require(fetch_orders([],'a')=={'items':[],'next_cursor':None}))
    def immutable():
        data=copy.deepcopy(rows);fetch_orders(data,'a');require(data==rows)
    check('input_immutable',immutable)
    check('account_filter',lambda:require(fetch_orders([(2,'b')],'a')['items']==[]))
print(json.dumps(checks))
'''


AGENT_TEST_CODE=r"""
import io,json,sys,unittest
sys.path.insert(0,sys.argv[1])
suite=unittest.defaultTestLoader.discover(sys.argv[1],pattern='test_orders.py')
r=unittest.TextTestRunner(stream=io.StringIO()).run(suite)
print(json.dumps({'passed':r.wasSuccessful() and r.testsRun>len(r.skipped),'tests_run':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'skipped':len(r.skipped)}))
"""


def run_check(work, code, phase='final'):
    env={k:v for k,v in os.environ.items() if k in ('PATH','TMPDIR','LANG','SYSTEMROOT')}
    p=None
    try:
        p=subprocess.Popen([sys.executable,'-I','-B','-c',code,str(Path(work).resolve()),phase],cwd=work,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
        stdout,_=p.communicate(timeout=3)
        if p.returncode:return {'oracle_error':'check process failed'}
        result=json.loads(stdout.splitlines()[-1])
        return result if isinstance(result,dict) and result else {'oracle_error':'empty checks'}
    except subprocess.TimeoutExpired:
        return {'oracle_error':'check process exceeded 3 seconds'}
    except (OSError,ValueError,IndexError):
        return {'oracle_error':'check process returned invalid output'}
    finally:
        if p is not None:
            # The evaluator owns this new process group. Reap descendants even if
            # the direct checker exited; an escaped process is not claimed covered.
            try:os.killpg(p.pid,signal.SIGKILL)
            except (ProcessLookupError,PermissionError):pass
            if p.poll() is None:
                try:p.kill()
                except ProcessLookupError:pass
            try:p.communicate(timeout=1)
            except subprocess.TimeoutExpired:
                p.stdout.close();p.stderr.close()


def evaluate(work, phase):
    if phase not in ('core','final'):raise ValueError('unknown phase')
    return run_check(work,CORE_CHECK_CODE if phase=='core' else CHECK_CODE,phase)


def evaluate_agent_tests(work):
    result=run_check(work,AGENT_TEST_CODE)
    if 'oracle_error' in result:result['passed']=False
    return result
