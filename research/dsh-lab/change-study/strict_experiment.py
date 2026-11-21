"""Protocol 4: Linux container tools, native DSH steering, no unsafe fallback."""
import argparse
import hashlib
import hmac
import json
import os
import signal
import socketserver
import sys
import tempfile
import threading
import time
import uuid
from pathlib import Path

import local_export
import scenario
from experiment import Controller, ARMS, ROOT, LAB, TrialInvalidated, arm_order, load_key, check_budget
from container_backend import ContainerSandbox as Sandbox, ContainerUnavailable, container_preflight, docker_control, DEFAULT_IMAGE
from oracle import AGENT_TEST_CODE
from scenario import create_fixture
from telemetry import redact


def isolated_evaluators(box, case=scenario):
    def run(work, code, phase):
        task_path=getattr(box,'task_path',str(Path(work).resolve()))
        options={'read_only':True} if hasattr(box,'task_path') else {}
        try:result=box.run([str(box.python),'-I','-B','-c',code,task_path,phase],timeout=3,**options)
        except ContainerUnavailable as exc:return {'oracle_error':'container check unavailable: '+str(exc)[:300]}
        if result['timed_out'] or result.get('cancelled'):return {'oracle_error':'isolated check stopped'}
        if result['returncode'] or result.get('output_limited'):return {'oracle_error':'isolated check failed'}
        try:
            parsed=json.loads(result['stdout'].splitlines()[-1])
            if not isinstance(parsed,dict) or not parsed:raise ValueError()
            return parsed
        except (ValueError,IndexError):return {'oracle_error':'invalid isolated check output'}
    def evaluate(work, phase):
        if phase not in ('core','final'):raise ValueError('unknown phase')
        return run(work,case.CORE_CHECK_CODE if phase=='core' else case.CHECK_CODE,phase)
    def agent_tests(work):
        result=run(work,AGENT_TEST_CODE,'final')
        if 'oracle_error' in result:result['passed']=False
        return result
    return evaluate,agent_tests


class StrictController(Controller):
    def __init__(self,work,output,arm,box,*,clock,secrets=(),case=scenario):
        self.lock=threading.RLock();self.condition=threading.Condition(self.lock)
        self.stopping=threading.Event();self.box=box;self.clock=clock
        self.runtime_ready=False;self.session_id=None;self.steering_text=None
        self.injection_turn=None;self.injection_step=None;self.injection_call=None
        self.current_turn=None;self.current_step=None
        self.consumed_turn=None;self.consumed_step=None;self.same_turn_consumed=False
        evaluator,agent_evaluator=isolated_evaluators(box,case)
        super().__init__(work,output,arm,self.queue_change,secrets,evaluator=evaluator,agent_evaluator=agent_evaluator,case=case)

    def queue_change(self,text):
        self.steering_text=text
        # The runtime supplies the actual native message id in the steered ack.
        return None

    def invalidate(self,reason):
        self.invalid_reason=reason
        self.trace.write({'type':'study.invalidated','seconds':self.clock(),'reason':reason})
        raise TrialInvalidated(reason)

    def dispatch(self,request):
        op=request.get('op')
        with self.lock:
            if self.stopping.is_set():raise TrialInvalidated('trial_stopped')
            if self.invalid_reason:raise TrialInvalidated(self.invalid_reason)
            if op=='ready':
                if self.runtime_ready or request.get('tools')!=['study_bash']:self.invalidate('tool_inventory')
                self.session_id=request.get('session_id')
                if not isinstance(self.session_id,str) or not self.session_id:self.invalidate('missing_session')
                self.runtime_ready=True
                self.trace.write({'type':'study.runtime_ready','seconds':self.clock(),'tools':['study_bash']})
                return {}
            if not self.runtime_ready or request.get('session_id')!=self.session_id:self.invalidate('unrecognized_session')
            if op=='invalid':self.invalidate(str(request.get('reason','runtime_invalid')))
            if op=='steered':
                if (self.injected_at is None or self.message_id is not None or
                    request.get('call_id')!=self.injection_call or request.get('turn')!=self.injection_turn or
                    request.get('step')!=self.injection_step or not isinstance(request.get('message_id'),str)):
                    self.invalidate('unexpected_steering_ack')
                self.message_id=request['message_id']
                self.trace.write({'type':'study.steered','seconds':self.clock(),'message_id':self.message_id,
                                  'turn':self.injection_turn,'step':self.injection_step})
                return {}
            if op!='execute':self.invalidate('unknown_bridge_operation')
            if not isinstance(request.get('command'),str) or len(request['command'])>131072:self.invalidate('invalid_command')
            if not all(type(request.get(k)) is int for k in ('turn','step')):self.invalidate('missing_step_metadata')
            if self.injected_at is not None and not self.same_turn_consumed:
                if request['turn']!=self.injection_turn or request['step']<=self.injection_step:
                    self.invalidate('tool_before_steering_consumed')
                # Native consumption is synchronous; SDK delivery is asynchronous.
                # Release the lock while the main SDK thread drains the evidence.
                self.condition.wait_for(lambda:self.same_turn_consumed or self.invalid_reason or self.stopping.is_set(),timeout=2)
                if self.invalid_reason:raise TrialInvalidated(self.invalid_reason)
                if not self.same_turn_consumed:self.invalidate('steering_consumption_not_observed')
        # No controller lock while executing: SDK notification ingestion remains live.
        result=self.box.run_shell(request['command'],timeout=30,max_output=65536)
        with self.lock:
            if self.stopping.is_set() or result.get('cancelled'):raise TrialInvalidated('trial_stopped')
            if result['timed_out']:self.invalidate('tool_deadline')
            if result.get('output_limited'):self.invalidate('tool_output_limit')
            was_injected=self.injected_at is not None
            self.after_tool(self.clock())
            if self.invalid_reason:raise TrialInvalidated(self.invalid_reason)
            response={'stdout':result['stdout'],'stderr':result['stderr'],'exit_code':result['returncode']}
            if not was_injected and self.injected_at is not None:
                self.injection_turn=request['turn'];self.injection_step=request['step'];self.injection_call=request['call_id']
                response['steering']={'text':self.steering_text}
            return response

    def observe(self,notification,now):
        with self.lock:
            entry=self.trace.observe(notification,now)
            if entry['type']=='step/start':
                self.current_turn=entry['turn'];self.current_step=entry['step']
            if entry['type']=='user/message' and self.message_id and entry.get('message_id')==self.message_id:
                self.received_at=now;self.consumed_turn=self.current_turn;self.consumed_step=self.current_step
                self.same_turn_consumed=(self.consumed_turn==self.injection_turn and self.consumed_step==self.injection_step+1)
                if not self.same_turn_consumed:self.invalid_reason='steering_consumed_outside_next_step'
                self.trace.write({'type':'study.change_consumed','seconds':now,'message_id':self.message_id,
                                  'turn':self.consumed_turn,'step':self.consumed_step,'same_turn':self.same_turn_consumed})
            self.condition.notify_all()

    def stop(self):
        self.stopping.set()
        self.box.cancel_active()
        with self.condition:self.condition.notify_all()

    def finish(self,status,now):
        with self.lock:
            if not self.runtime_ready:self.invalid_reason=self.invalid_reason or 'runtime_not_ready'
            if not self.same_turn_consumed:self.invalid_reason=self.invalid_reason or 'same_turn_consumption_unverified'
            result=super().finish(status,now)
            result.update(runtime_ready=self.runtime_ready,same_turn_consumed=self.same_turn_consumed,
                          injection_turn=self.injection_turn,injection_step=self.injection_step,
                          consumed_turn=self.consumed_turn,consumed_step=self.consumed_step,
                          delivery='DSH Agent.steer at completed tool boundary')
            return result


class Bridge:
    """Private bounded NDJSON IPC; no model command can open this socket."""
    def __init__(self,controller):
        self.controller=controller;self.token=uuid.uuid4().hex;self.directory=None;self.server=None
        self.request_lock=threading.Lock();self.quiesced=False

    def handle_request(self,request):
        if not isinstance(request,dict) or not isinstance(request.get('token'),str) or not hmac.compare_digest(request['token'],self.token):
            return {'ok':False,'error':'unauthorized bridge request'}
        try:
            with self.request_lock:return {'ok':True,**self.controller.dispatch(request)}
        except Exception as exc:
            # Protocol/runtime errors invalidate; never silently retry a partial trial.
            self.controller.invalid_reason=self.controller.invalid_reason or 'bridge_error'
            return {'ok':False,'error':redact(str(exc),self.controller.trace.secrets)}

    def __enter__(self):
        self.directory=tempfile.TemporaryDirectory(prefix='dsh-bridge-',dir='/tmp')
        self.path=str(Path(self.directory.name)/'control.sock')
        owner=self
        class Handler(socketserver.StreamRequestHandler):
            def handle(self):
                self.request.settimeout(1)
                try:
                    raw=self.rfile.readline(262145)
                    if len(raw)>262144 or not raw.endswith(b'\n'):raise ValueError('invalid bridge frame')
                    reply=owner.handle_request(json.loads(raw))
                    self.wfile.write((json.dumps(reply)+'\n').encode())
                except (ValueError,OSError):return
        class Server(socketserver.ThreadingUnixStreamServer):
            daemon_threads=False
            block_on_close=True
        try:
            self.server=Server(self.path,Handler);os.chmod(self.path,0o600)
            self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
            return self
        except BaseException:
            self.directory.cleanup();raise

    def __exit__(self,*args):
        try:
            if self.controller:self.controller.stop()
        finally:
            try:
                if self.server:self.server.shutdown();self.server.server_close();self.thread.join(timeout=2)
            finally:
                if self.directory:self.directory.cleanup()
        self.quiesced=True


def write_patch(path,bridge):
    # JSON is a YAML subset. Disable every stock model-visible tool and terminal.
    disabled=('tool-fs','tool-working-directory','persistent-bash','persistent-pwsh','terminal-bash','terminal-pwsh')
    patch=[{'id':name,'disabled':True} for name in disabled]
    patch.append({'id':'agent-loop','config':{'agents':[],'maxParallelToolCalls':1}})
    patch.append({'insert':[{'id':'orchivane-study','name':str(ROOT/'runtime/study-plugin.mjs'),
                            'config':{'socketPath':bridge.path,'token':bridge.token}}]})
    path.write_text(json.dumps(patch,indent=2));path.chmod(0o600)


def preflight():
    result=container_preflight()
    if not result['passed']:return result
    try:
        with Bridge(None):pass
        result['probes']['controller_ipc']=True
    except OSError as exc:
        result.update(passed=False,reason='private controller IPC unavailable: '+str(exc))
    runtime=LAB/'npm-runtime/node_modules/@deepseek-ai/dsh/lib/bin.js'
    if not runtime.is_file():result.update(passed=False,reason='installed DSH npm runtime missing')
    return result


def run_arm(base,arm,key,max_tokens=8192,image_id=None,*,case=scenario):
    from deepseek_harness import DeepSeekHarness
    work=base/arm/'task';output=base/arm/'observations';create_fixture(work,case.FILES)
    start=time.monotonic();clock=lambda:time.monotonic()-start
    box=Sandbox(work,image=image_id);controller=StrictController(work,output,arm,box,clock=clock,secrets=(key,),case=case)
    status='error';error=None;h=None;finish_reason=None;sid=None;cleanup_error=None;cleanup_started=None;bridge=None
    old_handler=signal.getsignal(signal.SIGALRM)
    def watchdog(*_):check_budget(clock(),list(controller.trace.pending.values()))
    signal.signal(signal.SIGALRM,watchdog);signal.setitimer(signal.ITIMER_REAL,1,1)
    try:
        with Bridge(controller) as bridge:
            try:
                patch=output/'runtime.patch.json';write_patch(patch,bridge)
                h=DeepSeekHarness(model='deepseek-v4-flash',profile='sdk-minimal',patches=(str(patch),),
                    dsh_bin=str(LAB/'npm-runtime/node_modules/@deepseek-ai/dsh/lib/bin.js'),
                    dsh_home=str(output/'runtime-home'),cwd=str(work.resolve()),api_key=key,
                    max_tokens=max_tokens,request_timeout_seconds=15,shutdown_timeout_seconds=2)
                session=h.start_session();sid=session.id
                prompt=case.INITIAL+(case.RECORD if arm=='dependency_record' else '')
                (output/'prompt.json').write_text(json.dumps({'initial_sha256':hashlib.sha256(prompt.encode()).hexdigest(),
                                                             'changed_sha256':hashlib.sha256(case.CHANGE.encode()).hexdigest()}))
                def observe(n):
                    controller.observe(n,clock())
                    if controller.invalid_reason:raise TrialInvalidated(controller.invalid_reason)
                result=session.run(prompt,on_notification=observe)
                finish_reason=result.finish_reason;status='completed' if finish_reason=='completed' else 'incomplete'
            finally:
                # Disarm before bridge cancellation/join; repeated SIGALRM must
                # never interrupt teardown while task writers still exist.
                signal.setitimer(signal.ITIMER_REAL,0)
                cleanup_started=time.monotonic()
    except TrialInvalidated as exc:status='invalid';error=str(exc)
    except TimeoutError as exc:status='timeout';error=str(exc)
    except Exception as exc:status='error';error=redact(str(exc),(key,))
    finally:
        signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,old_handler)
        if cleanup_started is None:cleanup_started=time.monotonic()
        if h is not None:
            try:h.close()
            except Exception as exc:cleanup_error=redact(str(exc),(key,))
    cleanup_seconds=time.monotonic()-cleanup_started
    # The bridge executor is permanently stopped before final checks. A fresh
    # instance grants the same policy, with no active command writers attached.
    quiesced=bridge is not None and bridge.quiesced
    final_box=None
    if quiesced:
        final_box=Sandbox(work,image=image_id)
        controller.evaluate,controller.evaluate_agent_tests=isolated_evaluators(final_box,case)
    else:
        controller.invalid_reason='cleanup_unverified';status='error'
        controller.evaluate=lambda *_:{'oracle_error':'final checks skipped: cleanup unverified'}
        controller.evaluate_agent_tests=lambda *_:{'passed':False,'oracle_error':'final checks skipped: cleanup unverified'}
    result=controller.finish(status,clock())
    result.update(session_id=sid,finish_reason=finish_reason,configured_max_tokens=max_tokens,error=error,
                  cleanup_seconds=cleanup_seconds,cleanup_error=cleanup_error,bridge_quiesced=quiesced,
                  container_executions=getattr(box,'executions',[])+getattr(final_box,'executions',[]),
                  image_id=image_id,
                  cleanup_note='Every owned container is force-removed and absence checked, including its PID namespace; cleanup failure prevents subsequent evaluation.')
    (output/'result.json').write_text(json.dumps(redact(result,(key,)),indent=2))
    return result


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--offline-check',action='store_true');p.add_argument('--preflight-only',action='store_true')
    p.add_argument('--prepare-image',action='store_true',help='Pull Python image and run acceptance checks only; never call the model')
    p.add_argument('--repetitions',type=int,default=1);p.add_argument('--seed',type=int,default=7)
    p.add_argument('--arm',choices=ARMS);p.add_argument('--max-tokens',type=int,default=8192)
    p.add_argument('--scenario',choices=('pagination','local-export'),default='pagination',
                   help='local-export runs native and dependency_record by default')
    args=p.parse_args(argv)
    case, revision = (local_export, '4.2') if args.scenario == 'local-export' else (scenario, '4.1')
    arms = ('native', 'dependency_record') if case is local_export else ARMS
    if args.arm:
        arms = (args.arm,)
    if args.repetitions<1 or args.max_tokens<1:p.error('repetitions and max-tokens must be positive')
    if args.offline_check:
        return __import__('subprocess').call([sys.executable,'-m','unittest','discover','-s',str(ROOT/'tests'),'-v'],cwd=ROOT)
    if args.prepare_image:
        try:
            docker_control(['version','--format','{{json .Server}}'])
            print('Preparing '+DEFAULT_IMAGE+' (no model calls)',flush=True)
            docker_control(['pull',DEFAULT_IMAGE],timeout=300)
        except ContainerUnavailable as exc:
            print(json.dumps({'passed':False,'stage':'image_preparation','reason':str(exc)}));return 2
    preflight_name = ('container-preflight-local-export.json' if case is local_export
                      else 'container-preflight.json')
    capability=preflight();(ROOT/preflight_name).write_text(json.dumps(capability,indent=2))
    if not capability['passed'] or args.preflight_only or args.prepare_image:
        print(json.dumps(capability,ensure_ascii=False));return 0 if capability['passed'] else 2
    # No credentials are loaded and no model is called before all probes pass.
    key=load_key();destination=ROOT/'runs'/(time.strftime('%Y%m%d-%H%M%S')+'-v'+revision+'-'+uuid.uuid4().hex[:6])
    destination.mkdir(parents=True,mode=0o700)
    summary={'kind':'live DSH experiment','protocol_revision':revision,'scenario':args.scenario,'model':'deepseek-v4-flash',
             'runtime':'npm DSH 0.2.1-rc.3','seed':args.seed,'max_tokens':args.max_tokens,
             'blindness_enforced':True,'isolation_preflight':capability,
             'planned_arms':list(arms),'planned_repetitions':args.repetitions,'trials':[]}
    (destination/'summary.json').write_text(json.dumps(redact(summary,(key,)),indent=2))
    for repetition in range(args.repetitions):
        for arm in arm_order(args.seed,repetition):
            if arm not in arms:continue
            print(f'START {repetition+1} {arm}',flush=True)
            result=run_arm(destination/f'repeat-{repetition+1}',arm,key,args.max_tokens,image_id=capability['image_id'],case=case)
            summary['trials'].append(result)
            (destination/'summary.json').write_text(json.dumps(redact(summary,(key,)),indent=2))
            print(json.dumps({k:result[k] for k in ('arm','status','valid_trial','same_turn_consumed','task_succeeded','seconds')}),flush=True)
    print('RESULTS '+str(destination/'summary.json'))
    return 0 if all(t['task_succeeded'] for t in summary['trials']) else 1


if __name__=='__main__':raise SystemExit(main())
