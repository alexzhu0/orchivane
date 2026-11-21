"""Identical v1 task and independently verified injection milestone."""
import hashlib
from pathlib import Path
from decisions import PAGINATION_REQUIREMENTS
from safe_files import read_task_file
from oracle import evaluate, CORE_CHECK_CODE, CHECK_CODE

REQUIREMENTS = PAGINATION_REQUIREMENTS
CHANGED_REQUIREMENTS = frozenset({'dataset'})
READY_FILE = None

FILES={
'auth.py':'''def require_account(account):
    if not isinstance(account, str) or not account:
        raise ValueError("account required")
    return account
''',
'core.py':'''def list_orders(rows, account, size=2, cursor=None):
    raise NotImplementedError("Implement pagination")
''',
'api.py':'''from auth import require_account
from core import list_orders

def fetch_orders(rows, account, size=2, cursor=None):
    raise NotImplementedError("Implement API wrapper")
''',
'client.py':'''def collect_orders(fetch, size=2):
    raise NotImplementedError("Collect every page")
''',
 'test_orders.py':'# Add regression tests using unittest.\n'
}
INITIAL='''Implement core.py, api.py, client.py and test_orders.py in this directory. Work only here, with no network or external dependencies. auth.py already works: preserve it. Python 3.11, stdlib only. rows is a list of (integer_id, account) tuples; IDs are unique and immutable. Dataset requirement v1: rows are static throughout traversal. list_orders returns {"items": [...], "next_cursor": ...}, descending IDs, account-scoped, size is an integer 1..100 (not bool). None starts or ends traversal; v1 cursor is an integer offset. fetch_orders must use require_account and list_orders with the same signature. collect_orders(fetch,size=2) calls fetch(size=size,cursor=cursor), collects every page exactly once and stops on next_cursor=None. Add executable unittest regressions.
MANDATORY CHECKPOINT: implement and verify core.py FIRST in a separate tool call. Leave api.py, client.py, auth.py and test_orders.py byte-identical until that tool call has returned. Then continue the remaining implementation and testing, and finish with a brief summary. Avoid unbounded loops in checks; cap test iterations.'''
CHANGE='''Requirement changed to revision 2 (dataset): new orders can be inserted BETWEEN calls, with globally monotonically increasing unique immutable integer IDs. No updates or deletions. A traversal must return exactly all orders for its account that existed on the FIRST call, in descending ID order, with no duplicates, omissions or later inserts. Cursor representation may change but must survive JSON round-tripping. Preserve signatures and return keys, size validation, account isolation and auth.py. Update core, API, client and regression tests consistently. Execute the revision incrementally: your NEXT tool call should update and check core.py only. After that call returns, implement the API/client, then tests, in separate short tool calls. If a decision record is required, update it in a separate call after the code checks. Do not bundle all revised files and records into one large tool call or response. Keep explanations brief and execute each completed edit promptly. Complete the revised task and stop. Bound any test loops.'''
RECORD='''Additionally, before leaving the core-only checkpoint, write decisions.json in the SAME tool call as that checkpoint. Build it from YOUR actual v1 design decisions, not a canned graph. Schema: {"revision":1,"assumptions":[{"id":"unique ID","claim":"your assumption","requirement":"dataset or auth"}],"decisions":[{"id":"unique ID","depends_on":["assumption or decision IDs"],"artifacts":["relative file paths"]}]}. Include dependencies of planned API/client/tests and unchanged authorization behavior. Use at least one assumption for dataset and one for auth; no cycles. Only core.py and decisions.json may change before the checkpoint.'''


def create_fixture(work, files=FILES):
    work=Path(work);work.mkdir(parents=True,exist_ok=True)
    for name,content in files.items():(work/name).write_text(content)


def file_hashes(work, files=FILES):
    result={}
    for name in (*files,'decisions.json'):
        p=Path(work)/name
        data=read_task_file(p)
        result[name]=hashlib.sha256(data).hexdigest() if data is not None else None
    return result


def checkpoint_ready(work, initial_hashes):
    hashes=file_hashes(work)
    if any(hashes[n]!=initial_hashes[n] for n in FILES if n!='core.py'):return False
    return evaluate(work,'core')=={'static_core':True}
