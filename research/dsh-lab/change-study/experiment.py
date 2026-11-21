"""DSH mid-task requirement-change controller; offline tests do not measure agents."""
import argparse
import difflib
import hashlib
import json
import os
import random
import signal
import subprocess
import sys
import time
import uuid
from pathlib import Path

import scenario
from decisions import invalidate, validate_record
from oracle import evaluate, evaluate_agent_tests
from scenario import FILES, INITIAL, CHANGE, RECORD, checkpoint_ready, create_fixture, file_hashes
from telemetry import Trace, redact
from safe_files import read_task_file

ROOT=Path(__file__).resolve().parent
LAB=ROOT.parent
ARMS=('native','impact_prompt','dependency_record')


def read_record(work, revision, *, requirements=scenario.REQUIREMENTS):
    p=Path(work)/'decisions.json'
    data=read_task_file(p,65536)
    if data is None:
        raise ValueError('record missing, linked or too large')
    return validate_record(json.loads(data),revision,requirements=requirements)


def check_budget(elapsed, pending, tool_limit=45, total_limit=180):
    if elapsed>=total_limit:raise TimeoutError(f'total deadline {total_limit}s exceeded')
    if any(elapsed-call['started']>=tool_limit for call in pending):
        raise TimeoutError(f'pending tool deadline {tool_limit}s exceeded')


def arm_order(seed, repetition):
    order=list(ARMS);random.Random(seed).shuffle(order)
    offset=repetition%len(order)
    return order[offset:]+order[:offset]


class TrialInvalidated(ValueError):
    pass


class Controller:
    def __init__(self, work, output, arm, send_input, secrets=(), *, evaluator=evaluate, agent_evaluator=evaluate_agent_tests, case=scenario):
        if arm not in ARMS:raise ValueError('unknown arm')
        self.work=Path(work);self.output=Path(output)
        if self.output.resolve().is_relative_to(self.work.resolve()):raise ValueError('logs must be outside task cwd')
        self.arm=arm;self.send_input=send_input;self.case=case
        self.evaluate=evaluator;self.evaluate_agent_tests=agent_evaluator
        self.trace=Trace(output,secrets)
        self.initial_hashes=file_hashes(work,case.FILES)
        self.previous=self.contents()
        self.churn=0;self.changed_after=set();self.injected_at=None;self.received_at=None
        self.message_id=None;self.invalid_reason=None;self.invalidated=[]
        self.first_pass=None;self.checks=[];self.last_hashes=None

    def contents(self):
        result={}
        for n in (*self.case.FILES,'decisions.json'):
            p=self.work/n
            data=read_task_file(p)
            result[n]=data.decode(errors='replace') if data is not None else ''
        return result

    def snapshot(self, now):
        current=self.contents();hashes=file_hashes(self.work,self.case.FILES)
        changed=[n for n in current if current[n]!=self.previous[n]]
        if self.injected_at is not None:
            self.changed_after.update(changed)
            for n in changed:
                self.churn+=sum(line.startswith(('+ ','- ')) for line in difflib.ndiff(self.previous[n].splitlines(),current[n].splitlines()))
        self.previous=current
        self.trace.write({'type':'study.snapshot','seconds':now,'hashes':hashes,'changed':changed})
        return hashes

    def check_code(self, now, force=False):
        hashes=file_hashes(self.work,self.case.FILES)
        if not force and hashes==self.last_hashes:return
        started=time.monotonic();result=self.evaluate(self.work,'final');finished=now+(time.monotonic()-started)
        item={'seconds':finished,'checks':result}
        self.checks.append(item);self.last_hashes=hashes
        self.trace.write({'type':'study.check',**item})
        if self.received_at is not None and self.first_pass is None and all(v is True for v in result.values()):
            self.first_pass=finished

    def observe(self, notification, now):
        entry=self.trace.observe(notification,now)
        # Direct-path audit only; NOT a sandbox or exhaustive access detector.
        if entry['type']=='tool/call':
            args=json.dumps(entry.get('arguments'),ensure_ascii=False)
            if any(marker in args for marker in (str(self.output.resolve()), '../observations/', 'prompt.json', 'trace.jsonl')):
                self.invalid_reason='diagnostic_material_access'
                self.trace.write({'type':'study.invalidated','seconds':now,'reason':self.invalid_reason})
                raise TrialInvalidated(self.invalid_reason)
        if entry['type']=='agent/inbox/spliced' and self.message_id and self.message_id in entry.get('message_ids',[]):
            self.received_at=now
            self.trace.write({'type':'study.change_received','seconds':now,'message_id':self.message_id})
        if entry['type']!='tool/result':return
        self.after_tool(now)

    def checkpoint_reached(self, hashes, now):
        if self.case.READY_FILE is None:
            if any(hashes[name] != self.initial_hashes[name] for name in self.case.FILES if name != 'core.py'):
                self.invalid_reason = 'checkpoint_missed'
                return False
            return self.evaluate(self.work, 'core') == {'static_core': True}
        if read_task_file(self.work / self.case.READY_FILE, 64) != b'ready\n':
            return False

        checks = self.evaluate(self.work, 'core')
        agent_tests = self.evaluate_agent_tests(self.work)
        passed = (
            bool(checks) and all(value is True for value in checks.values())
            and agent_tests.get('passed') is True
            and all(hashes[name] is not None for name in self.case.FILES)
            and hashes['auth.py'] == self.initial_hashes['auth.py']
        )
        self.trace.write({'type': 'study.checkpoint', 'seconds': now, 'passed': passed,
                          'checks': checks, 'agent_tests': agent_tests, 'hashes': hashes})
        if not passed:
            self.invalid_reason = 'initial_checkpoint_failed'
        return passed

    def after_tool(self, now):
        """Trusted checkpoint; v3 calls this while the runtime tool awaits the host."""
        started=time.monotonic()
        hashes=self.snapshot(now)
        if self.injected_at is None and self.invalid_reason is None and self.checkpoint_reached(hashes, now):
            extra=''
            if self.arm=='impact_prompt':
                extra='\nFirst analyze which assumptions and prior decisions this change invalidates and which remain valid; use that analysis to guide the edits.'
            elif self.arm=='dependency_record':
                try:
                    requirements = self.case.REQUIREMENTS
                    record=read_record(self.work,1,requirements=requirements)
                    if {a['requirement'] for a in record['assumptions']}!=requirements:
                        raise ValueError('requirement coverage missing: '+', '.join(sorted(requirements)))
                    self.invalidated=invalidate(record,self.case.CHANGED_REQUIREMENTS,requirements=requirements)
                    (self.output/'initial-record.json').write_text(json.dumps(redact(record,self.trace.secrets),indent=2))
                    affected = ', '.join(sorted(self.case.CHANGED_REQUIREMENTS))
                    extra='\nYour recorded decisions potentially invalidated by this '+affected+' change: '+json.dumps(self.invalidated)+'. Reconsider their dependent artifacts. Validate preserved behavior too. Update decisions.json to revision=2 with the new assumptions and decisions after rechecking them.'
                except (ValueError,OSError) as exc:
                    self.invalid_reason='invalid_record: '+str(exc)
                    return
            self.injected_at=now+(time.monotonic()-started)
            self.trace.write({'type':'study.change_sending','seconds':self.injected_at,'invalidated':self.invalidated})
            self.message_id=self.send_input(self.case.CHANGE+extra)
            self.trace.write({'type':'study.change_sent','seconds':self.injected_at,'message_id':self.message_id})
        if self.received_at is not None:self.check_code(now+(time.monotonic()-started))

    def finish(self, status, now):
        self.snapshot(now);self.check_code(now,force=True)
        final=self.checks[-1]['checks'];record_ok=None
        if self.arm=='dependency_record':
            try:read_record(self.work,2,requirements=self.case.REQUIREMENTS);record_ok=True
            except (ValueError,OSError):record_ok=False
        result={'arm':self.arm,'status':status,'session_completed':status=='completed',
                'valid_trial':self.invalid_reason is None and self.message_id is not None and self.received_at is not None,
                'invalid_reason':self.invalid_reason or ('change_not_received' if self.received_at is None else None),
                'seconds':now,'injected_at':self.injected_at,'received_at':self.received_at,'message_id':self.message_id,
                'code_passed':all(v is True for v in final.values()),'checks':final,'check_history':self.checks,
                'first_pass_observed':self.first_pass,'invalidated_decisions':self.invalidated,
                'record_revalidated':record_ok,'record_validation_scope':'schema/revision only; semantic correctness not proven',
                'post_change_line_churn':self.churn,'post_change_changed_files':sorted(self.changed_after),
                'auth_unchanged':file_hashes(self.work,self.case.FILES)['auth.py']==self.initial_hashes['auth.py'],
                'trace':self.trace.summary(now),'initial_hashes':self.initial_hashes,
                'cost_note':'Usage includes graph generation/maintenance but only received events; incomplete runs are partial. Churn is not a measure of proven wasted work.'}
        result['agent_tests']=self.evaluate_agent_tests(self.work)
        result['source_readable']=all(file_hashes(self.work,self.case.FILES)[name] is not None for name in self.case.FILES)
        result['task_succeeded']=bool(result['valid_trial'] and result['session_completed'] and result['code_passed'] and result['source_readable'] and result['auth_unchanged'] and result['agent_tests']['passed'] and not self.trace.pending and (record_ok is not False))
        (self.output/'result.json').write_text(json.dumps(redact(result,self.trace.secrets),indent=2))
        return result


def runtime_preflight():
    if sys.platform=='darwin':
        try:
            p=subprocess.run(['/bin/ps','-p',str(os.getpid()),'-o','pid='],capture_output=True,text=True,timeout=5)
            if p.returncode: return {'passed':False,'reason':'DSH requires process inspection; /bin/ps is denied in this environment.'}
        except (OSError,subprocess.TimeoutExpired):return {'passed':False,'reason':'DSH process inspection unavailable.'}
    runtime=LAB/'npm-runtime/node_modules/@deepseek-ai/dsh/lib/bin.js'
    return {'passed':runtime.is_file(),'reason':None if runtime.is_file() else 'npm DSH runtime missing'}


def load_key():
    for line in (LAB/'.env').read_text().splitlines():
        if line.startswith('DEEPSEEK_API_KEY='):
            key=line.split('=',1)[1].strip().strip('\"\'')
            if key:return key
    raise ValueError('DEEPSEEK_API_KEY missing')


def run_arm(base, arm, key, max_tokens=8192):
    from deepseek_harness import DeepSeekHarness
    work=base/arm/'task';output=base/arm/'observations';create_fixture(work)
    start=time.monotonic();controller=None;h=None;status='error';error=None;sid=None;finish_reason=None
    old_handler=signal.getsignal(signal.SIGALRM)
    def watchdog(signum,frame):
        check_budget(time.monotonic()-start,[] if controller is None else controller.trace.pending.values())
    signal.signal(signal.SIGALRM,watchdog);signal.setitimer(signal.ITIMER_REAL,1,1)
    try:
        h=DeepSeekHarness(model='deepseek-v4-flash',profile='sdk-minimal',patches=(str(ROOT/'shell-history.patch.yml'),),dsh_bin=str(LAB/'npm-runtime/node_modules/@deepseek-ai/dsh/lib/bin.js'),dsh_home=str(LAB/'runtime-home'),cwd=str(work),api_key=key,max_tokens=max_tokens,request_timeout_seconds=15,shutdown_timeout_seconds=2)
        session=h.start_session();sid=session.id
        controller=Controller(work,output,arm,lambda text:h.client.session_prompt(session.id,[{'type':'text','text':text}]),secrets=(key,))
        prompt=INITIAL+(RECORD if arm=='dependency_record' else '')
        (output/'prompt.json').write_text(json.dumps({'initial_sha256':hashlib.sha256(prompt.encode()).hexdigest(),'changed_sha256':hashlib.sha256(CHANGE.encode()).hexdigest()},indent=2))
        result=session.run(prompt,on_notification=lambda n:controller.observe(n,time.monotonic()-start))
        finish_reason=result.finish_reason
        status='completed' if finish_reason=='completed' else 'incomplete'
    except TrialInvalidated as exc:status='invalid';error=str(exc)
    except TimeoutError as exc:status='timeout';error=str(exc)
    except Exception as exc:error=redact(str(exc),(key,))
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        signal.signal(signal.SIGALRM,old_handler)
        cleanup_started=time.monotonic();cleanup_error=None
        if h is not None:
            try:h.close()
            except Exception as exc:cleanup_error=redact(str(exc),(key,))
    cleanup_seconds=time.monotonic()-cleanup_started
    if controller is None:controller=Controller(work,output,arm,lambda _:None,secrets=(key,))
    result=controller.finish(status,time.monotonic()-start)
    result.update(session_id=sid,finish_reason=finish_reason,configured_max_tokens=max_tokens,error=error,cleanup_seconds=cleanup_seconds,cleanup_error=cleanup_error,cleanup_note='SDK closes owned runtime; descendant termination is not independently verified.')
    (output/'result.json').write_text(json.dumps(redact(result,(key,)),indent=2))
    return result


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--offline-check',action='store_true')
    p.add_argument('--repetitions',type=int,default=1)
    p.add_argument('--seed',type=int,default=7)
    p.add_argument('--arm',choices=ARMS)
    p.add_argument('--max-tokens',type=int,default=8192)
    args=p.parse_args(argv)
    if args.repetitions<1:p.error('--repetitions must be positive')
    if args.max_tokens<1:p.error('--max-tokens must be positive')
    if args.offline_check:
        return subprocess.call([sys.executable,'-m','unittest','discover','-s',str(ROOT/'tests'),'-v'],cwd=ROOT)
    preflight=runtime_preflight()
    if not preflight['passed']:
        (ROOT/'live-preflight.json').write_text(json.dumps(preflight,indent=2))
        print(json.dumps(preflight));return 2
    key=load_key()
    destination=ROOT/'runs'/(time.strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:6])
    destination.mkdir(parents=True,mode=0o700)
    summary={'kind':'live DSH experiment','model':'deepseek-v4-flash','runtime':'npm DSH 0.2.1-rc.3','seed':args.seed,'max_tokens':args.max_tokens,'protocol_revision':'2.2-pilot','blindness_enforced':False,'shell_history_patch_sha256':hashlib.sha256((ROOT/'shell-history.patch.yml').read_bytes()).hexdigest(),'trials':[]}
    for repetition in range(args.repetitions):
        for arm in arm_order(args.seed,repetition):
            if args.arm and args.arm!=arm:continue
            print(f'START {repetition+1} {arm}',flush=True)
            result=run_arm(destination/f'repeat-{repetition+1}',arm,key,max_tokens=args.max_tokens)
            summary['trials'].append(result)
            (destination/'summary.json').write_text(json.dumps(redact(summary,(key,)),indent=2))
            print(json.dumps({k:result[k] for k in ('arm','status','valid_trial','code_passed','task_succeeded','seconds')}),flush=True)
    print('RESULTS '+str(destination/'summary.json'))
    return 0 if all(t['task_succeeded'] for t in summary['trials']) else 1


if __name__=='__main__':raise SystemExit(main())
