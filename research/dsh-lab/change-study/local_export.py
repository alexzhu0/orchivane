"""Synthetic case: export must change while live browsing preserves its contract."""

from scenario import FILES as PAGINATION_FILES

REQUIREMENTS = frozenset({'live', 'export', 'auth'})
CHANGED_REQUIREMENTS = frozenset({'export'})
READY_FILE = '.v1-ready'

FILES = {
    'auth.py': PAGINATION_FILES['auth.py'],
    'core.py': PAGINATION_FILES['core.py'],
    'api.py': PAGINATION_FILES['api.py'],
    'export_api.py': '''from auth import require_account
from core import list_orders

def fetch_export_page(rows, account, size=2, cursor=None):
    raise NotImplementedError("Implement export API")
''',
    'client.py': '''def collect_export(fetch, size=2):
    raise NotImplementedError("Collect every export page")
''',
    'test_orders.py': PAGINATION_FILES['test_orders.py'],
}

INITIAL = '''Implement order browsing and batch export in this directory. Python 3.11, stdlib only. Preserve auth.py. Rows are (unique immutable integer ID, account) tuples.
1. core.list_orders(rows, account, size=2, cursor=None) returns {"items": [...], "next_cursor": ...}. Filter by account, sort descending by ID, and page with an integer offset into the rows passed to the current call. None starts or ends a traversal. Size is an integer 1..100, not bool. Do not mutate rows.
2. api.fetch_orders and export_api.fetch_export_page use the same signature, validate the account via require_account, and use the shared paginator in v1. The live list always reads current rows. In v1 the export dataset is static within a traversal.
3. client.collect_export(fetch, size=2) calls fetch(size=size, cursor=cursor) and combines pages into a list. Forward the returned cursor unchanged, request each page once, and stop at None.
4. Write and run executable unittest tests in test_orders.py covering both APIs and the export worker.
CHECKPOINT: finish and test all v1 behavior first. Then, in its own tool call, run exactly: printf 'ready\\n' > .v1-ready
Wait for that tool result. If you receive a revised requirement, continue within this turn. Work in short tool calls, keep explanations brief, and bound test loops.
'''

CHANGE = '''Requirement changed to revision 2 for batch export only. During an export traversal, new rows with globally increasing IDs can be inserted between calls, without updates or deletes. Each export must return exactly the rows for its account that existed on its FIRST call in descending order, with no duplicates or omissions. A later export started with cursor=None uses the rows available on that later first call. Interleaved exports must remain independent.
fetch_export_page must honor this contract, including across JSON round-trips of the cursor. collect_export must still collect every page with the same signature. The live list (api.fetch_orders and core.list_orders) must retain its integer offset cursor and read from current rows on each call. Preserve signatures, return keys, size validation, authorization, and auth.py.
Work in short tool calls. First implement the export paging change and check a small example, then verify the worker and add executable regressions for export and live behavior. If a decision record is required, update it in a separate call. Finish with a brief summary.
'''

RECORD = '''Before marking v1 ready, write decisions.json based on your actual v1 design. Use this schema: {"revision":1,"assumptions":[{"id":"unique ID","claim":"short premise","requirement":"live, export or auth"}],"decisions":[{"id":"unique ID","depends_on":["assumption or decision IDs"],"artifacts":["relative file paths"]}]}. Use one or more assumptions for each of live, export and auth. Record actual shared dependencies as well as the live and export paths and their tests. Each requirement value is a single label. No cycles. Keep claims brief.
'''

# Both phases test the preserved contract. The v1 checker string contains no
# v2 export tests or code so generated imports cannot inspect future semantics.
COMMON_CHECKS = r'''
import json
import sys

sys.path.insert(0, sys.argv[1])
from api import fetch_orders
from client import collect_export
from core import list_orders
from export_api import fetch_export_page

rows = [(10, 'a'), (9, 'b'), (8, 'a'), (6, 'a'), (5, 'b'), (4, 'a'), (2, 'a')]
expected = [row for row in rows if row[1] == 'a']
checks = {}

def require(condition):
    if not condition:
        raise AssertionError('contract mismatch')

def check(name, test):
    try:
        test()
        checks[name] = True
    except Exception as exc:
        checks[name] = type(exc).__name__ + ': ' + str(exc)[:200]

def offset_and_current_rows(fn):
    data = list(rows)
    first = fn(data, 'a', 2)
    require(first == {'items': expected[:2], 'next_cursor': 2})
    require(type(first['next_cursor']) is int)
    require(data == rows)
    data.append((11, 'a'))
    require(fn(data, 'a', 2) == {'items': [(11, 'a'), (10, 'a')], 'next_cursor': 2})
    require(fn(data, 'a', 2, 2) == {'items': [(8, 'a'), (6, 'a')], 'next_cursor': 4})
    require(data == rows + [(11, 'a')])

def account_and_size(fn):
    data = list(rows)
    require(fn(data, 'b', 100) == {'items': [(9, 'b'), (5, 'b')], 'next_cursor': None})
    require(fn(data, 'absent', 1) == {'items': [], 'next_cursor': None})
    require(len(fn(data, 'a', 1)['items']) == 1)
    for account in ('', None, 3):
        try:
            fn(data, account, 2)
        except ValueError:
            continue
        raise AssertionError('invalid account accepted')
    for size in (0, -1, True, 101, '2'):
        try:
            fn(data, 'a', size)
        except ValueError:
            continue
        raise AssertionError('invalid size accepted')
    require(data == rows)

check('live_core_current_offset', lambda: offset_and_current_rows(list_orders))
check('live_api_current_offset', lambda: offset_and_current_rows(fetch_orders))
check('live_api_account_and_size', lambda: account_and_size(fetch_orders))
check('export_account_and_size', lambda: account_and_size(fetch_export_page))
'''

CORE_CHECK_CODE = COMMON_CHECKS + r'''
def export_pages():
    require(fetch_export_page(rows, 'a', 2) == {'items': expected[:2], 'next_cursor': 2})
    require(fetch_export_page(rows, 'a', 2, 2) == {'items': expected[2:4], 'next_cursor': 4})
    require(fetch_export_page(rows, 'a', 2, 4) == {'items': expected[4:], 'next_cursor': None})

def worker():
    cursors = []
    def fetch(size=2, cursor=None):
        require(len(cursors) < 3 and size == 2)
        cursors.append(cursor)
        return fetch_export_page(rows, 'a', size, cursor)
    require(collect_export(fetch, 2) == expected)
    require(cursors == [None, 2, 4])

check('export_static_pages', export_pages)
check('export_static_worker', worker)
print(json.dumps(checks))
'''

CHECK_CODE = COMMON_CHECKS + r'''
def page(data, account, cursor):
    before = list(data)
    result = fetch_export_page(data, account, 2, cursor)
    require(data == before and set(result) == {'items', 'next_cursor'})
    require(isinstance(result['items'], list) and len(result['items']) <= 2)
    return result['items'], json.loads(json.dumps(result['next_cursor']))

def export_with_inserts():
    data = list(rows)
    cursor = None
    collected = []
    for index in range(10):
        items, cursor = page(data, 'a', cursor)
        collected.extend(items)
        if cursor is None:
            require(collected == expected)
            return
        data.extend([(20 + index * 2, 'a'), (21 + index * 2, 'b')])
    raise AssertionError('export traversal did not end')

def interleaved_exports():
    data = list(rows)
    first_items, first_cursor = page(data, 'a', None)
    data.append((11, 'a'))
    second_items, second_cursor = page(data, 'a', None)
    data.append((12, 'a'))
    require(first_items == expected[:2] and second_items == [(11, 'a'), (10, 'a')])
    require(first_cursor is not None and second_cursor is not None)
    require(page(data, 'a', first_cursor)[0] == expected[2:4])
    require(page(data, 'a', second_cursor)[0] == expected[1:3])

def export_worker_with_inserts():
    data = list(rows)
    cursors = []
    def fetch(size=2, cursor=None):
        require(len(cursors) < 3 and size == 2)
        require(not any(cursor == previous for previous in cursors))
        if cursors:
            require(cursor is not None)
            data.append((20 + len(cursors), 'a'))
        cursors.append(cursor)
        items, next_cursor = page(data, 'a', json.loads(json.dumps(cursor)))
        return {'items': items, 'next_cursor': next_cursor}
    require(collect_export(fetch, 2) == expected and len(cursors) == 3)

check('export_pages_survive_inserts', export_with_inserts)
check('export_interleaved_traversals', interleaved_exports)
check('export_worker_survives_inserts', export_worker_with_inserts)
print(json.dumps(checks))
'''
