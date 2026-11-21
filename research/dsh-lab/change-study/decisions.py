"""Validate agent-authored dependency records and propagate explicit changes."""
from pathlib import PurePosixPath

PAGINATION_REQUIREMENTS = frozenset({'dataset', 'auth'})


def validate_record(record, revision=1, *, requirements=PAGINATION_REQUIREMENTS):
    if not isinstance(record,dict) or record.get('revision')!=revision:
        raise ValueError('record revision missing or incorrect')
    assumptions=record.get('assumptions'); decisions=record.get('decisions')
    if not isinstance(assumptions,list) or not assumptions or not isinstance(decisions,list) or not decisions:
        raise ValueError('nonempty assumptions and decisions required')
    ids=set()
    for node in assumptions+decisions:
        if not isinstance(node,dict) or not isinstance(node.get('id'),str) or not node['id'] or node['id'] in ids:
            raise ValueError('unique nonempty IDs required')
        ids.add(node['id'])
    for a in assumptions:
        if (not isinstance(a.get('claim'),str) or not a['claim']
            or not isinstance(a.get('requirement'),str) or a['requirement'] not in requirements):
            raise ValueError('assumption needs a claim and a recognized requirement')
    graph={}
    for d in decisions:
        deps=d.get('depends_on'); files=d.get('artifacts')
        if not isinstance(deps,list) or not deps or any(not isinstance(x,str) or x not in ids for x in deps):
            raise ValueError('dependencies must reference existing nodes')
        if not isinstance(files,list) or not files:
            raise ValueError('artifacts required')
        for f in files:
            if not isinstance(f,str) or not f or '\\' in f or PurePosixPath(f).is_absolute() or '..' in PurePosixPath(f).parts:
                raise ValueError('artifact must be a safe relative path')
        graph[d['id']]=deps
    visiting=set();done=set()
    def visit(n):
        if n in visiting:raise ValueError('dependency cycle')
        if n in done:return
        visiting.add(n)
        for dep in graph.get(n,[]):visit(dep)
        visiting.remove(n);done.add(n)
    for n in graph:visit(n)
    return record


def invalidate(record, changed_keys, *, requirements=PAGINATION_REQUIREMENTS):
    validate_record(record, requirements=requirements)
    stale={a['id'] for a in record['assumptions'] if a['requirement'] in changed_keys}
    while True:
        more={d['id'] for d in record['decisions'] if any(x in stale for x in d['depends_on'])}
        if more<=stale:break
        stale|=more
    return sorted(d['id'] for d in record['decisions'] if d['id'] in stale)
