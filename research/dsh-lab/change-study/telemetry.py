"""Selected SDK events only. Never persist model reasoning or request context."""
import json
import re
from pathlib import Path


def redact(value, secrets=()):
    if isinstance(value, dict):
        return {k: '[REDACTED]' if any(x in k.lower() for x in ('api_key','apikey','authorization','password','secret','access_token')) else redact(v,secrets) for k,v in value.items()}
    if isinstance(value, list):
        return [redact(v,secrets) for v in value]
    if isinstance(value,str):
        for secret in secrets:
            if secret:value=value.replace(secret,'[REDACTED]')
        value=re.sub(r'(?i)((?:api[_-]?key|password|secret|authorization|access_token)["\s]*[=:]\s*["\']?)[^\s"\',;}]+',r'\1[REDACTED]',value)
        return re.sub(r'\bsk-[A-Za-z0-9_-]+','[REDACTED]',value)
    return value


class Trace:
    def __init__(self, directory, secrets=()):
        self.directory=Path(directory)
        self.directory.mkdir(parents=True,exist_ok=True,mode=0o700)
        self.secrets=secrets
        self.pending={}
        self.calls=[]
        self.usage={}

    def write(self, entry):
        entry=redact(entry,self.secrets)
        path=self.directory/'trace.jsonl'
        with path.open('a') as f:
            f.write(json.dumps(entry,ensure_ascii=False)+'\n')
        path.chmod(0o600)
        return entry

    def observe(self, notification, now):
        p=notification.payload
        e=p.get('event',{})
        kind=e.get('type',notification.method)
        data=e.get('data',{})
        sid=p.get('sessionId','')
        entry={'seconds':now,'type':kind,'session_id':sid}
        if kind=='tool/call':
            args=data.get('arguments')
            if isinstance(args,str):
                try:args=json.loads(args)
                except ValueError:pass
            call={'session_id':sid,'call_id':data.get('callId'),'name':data.get('name'),'arguments':redact(args,self.secrets),'started':now}
            self.pending[(sid,call['call_id'])]=call
            self.calls.append(call)
            entry.update(call)
        elif kind=='tool/result':
            msg=data.get('message',{})
            cid=msg.get('toolCallId',msg.get('source',{}).get('callId'))
            call=self.pending.pop((sid,cid),None)
            entry.update(call_id=cid,is_error=bool(msg.get('isError')),orphan=call is None)
            # Redact BEFORE truncating so a cut key cannot leak a prefix.
            text='\n'.join(b.get('text','') for b in msg.get('content',[]) if b.get('type')=='text')
            entry['result_excerpt']=redact(text,self.secrets)[:2000]
            if call is not None:
                call.update(duration=now-call['started'],finished=now,is_error=entry['is_error'])
                entry['duration']=call['duration']
        elif kind=='assistant/message':
            usage=data.get('usage',{})
            entry['usage']={k:v for k,v in usage.items() if isinstance(v,(int,float))}
            for k,v in entry['usage'].items():self.usage[k]=self.usage.get(k,0)+v
        elif kind=='turn/end':
            entry['turn']=data.get('turn')
            entry['finish_reason']=data.get('reason',{}).get('kind')
        elif kind in ('turn/start','step/start','step/end'):
            entry['turn']=data.get('turn')
            entry['step']=data.get('step')
        elif kind=='user/message':
            # Keep delivery evidence without saving prompt or context text.
            entry['message_id']=data.get('id')
        elif kind=='agent/inbox/spliced':
            entry['message_ids']=[v.get('id') for v in data.get('inserted',[])]
        elif notification.method=='session.status':
            entry['status']=p.get('status')
        return self.write(entry)

    def summary(self, now):
        return redact({'tool_calls':self.calls,'pending':[{**v,'waiting_seconds':now-v['started']} for v in self.pending.values()],'usage':self.usage},self.secrets)
