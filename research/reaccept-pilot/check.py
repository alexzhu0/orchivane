"""Read-only replay of the RUN-001 A to B acceptance fixture."""
from pathlib import Path
import csv
import hashlib
import json
import re
import sys

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def references(doc, root):
    refs = re.findall(r"`(\.\./[^`]+)`", doc.read_text())
    return {ref: (doc.parent / ref).resolve().is_relative_to(root.resolve())
                 and (doc.parent / ref).is_file() for ref in refs}

def main(case):
    old = case / 'snapshots/design-v1'
    new = case / 'snapshots/run-v2'
    manifest = json.loads((case / 'receipts/run-v2-freeze.json').read_text())
    failed = False
    for name, expected in manifest['files'].items():
        target = (new / name).resolve()
        if not target.is_relative_to(new.resolve()) or not target.is_file() or digest(target) != expected:
            print('FAIL current receipt:', name)
            failed = True
            continue
        previous = old / target.name if name.startswith('design/') else case / name
        print('RECHECK' if digest(previous) != expected else 'SAME BYTES', name)
    if failed:
        return 1
    for label, doc, root in [('A', old/'pilot.md', old), ('B', new/'design/pilot.md', new)]:
        refs = references(doc, root)
        print(label, 'references:', refs)
        if label == 'B' and (len(refs) != 2 or not all(refs.values())):
            return 1
    def rows(path):
        with path.open(newline='') as f:
            return list(csv.reader(f))
    a, b = rows(old/'inventory.csv'), rows(new/'design/inventory.csv')
    if len(a) != len(b) or a[0] != b[0] or any(len(x)!=len(y) for x,y in zip(a,b)):
        print('RECHECK inventory structure')
        return 1
    changes = [(i, b[0][j]) for i,(x,y) in enumerate(zip(a,b)) for j,(v,w) in enumerate(zip(x,y)) if v!=w]
    print('CSV changed cells:', len(changes), 'columns:', sorted({col for _,col in changes}))
    print('Current snapshot verified. Business acceptance requires independent review.')
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main(Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).parent/'case'))
    except (OSError, ValueError, KeyError) as exc:
        sys.exit(str(exc))
