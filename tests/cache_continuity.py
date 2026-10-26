"""Explicit native CLI lab. CI only replays its published evidence; no model calls."""
import argparse
from collections import Counter
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import threading
import time
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
BASE = 'f1b45702d76e921710213a9398adaa97419cd705'
MARKET = 'orchivane-continuity-lab'
URL = 'https://orchivane-cache-lab.invalid/marketplace.git'


def inventory(root):
    paths = list(root.rglob('*'))
    if not root.is_dir() or root.is_symlink() or any(p.is_symlink() for p in paths):
        raise ValueError('Source must be an independent directory without symlinks')
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(paths) if p.is_file()}


def verify_source(root, expected):
    if not expected or inventory(root) != expected:
        raise ValueError('Source inventory changed or is incomplete')
    for path in root.rglob('*.md'):
        # shortcut: this fixture uses ordinary inline Markdown links; extend for other syntax.
        for target in re.findall(r'\]\(([^\s)]+)\)', path.read_text()):
            url = urlsplit(target)
            if url.scheme == 'file':
                raise ValueError('File URI is not an independent retained reference')
            if url.scheme or url.netloc or not url.path:
                continue
            resolved = (path.parent / unquote(url.path)).resolve()
            if not resolved.is_relative_to(root.resolve()) or not resolved.is_file():
                raise ValueError('Local reference is missing or outside the retained tree')


def continue_task(project, retained, expected):
    """A deterministic post-update task, not a native role or loading receipt."""
    verify_source(retained, expected)
    source_version = re.search(r'version:\s*"([^"]+)"', (retained / 'SKILL.md').read_text()).group(1)
    work = project / 'work'
    work.mkdir()
    input_path = work / 'n2.csv'
    input_path.write_text('item,quantity\nfirst,2\nsecond,3\nthird,4\n')
    rows = list(csv.DictReader(input_path.read_text().splitlines()))
    summary = {'row_count': len(rows), 'total_quantity': sum(int(row['quantity']) for row in rows)}
    raw_quantities = [int(line.split(',')[1]) for line in input_path.read_text().splitlines()[1:]]
    assert summary == {'row_count': len(raw_quantities), 'total_quantity': sum(raw_quantities)}
    output = work / 'n2-summary.json'
    output.write_text(json.dumps(summary, indent=2) + '\n')
    receipt = {'kind': 'deterministic post-update continuation, not native chat acceptance',
               'source_entry': str(retained / 'SKILL.md'), 'source_version': source_version,
               'source_files_reopened_and_verified': expected,
               'input_staged': 'after native update', 'saved_output': json.loads(output.read_text()),
               'independent_raw_line_calculation_matches': True}
    (work / 'n2-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    verify_source(retained, expected)
    return receipt


def run_lab(lab):
    deadline = time.monotonic() + 180
    lab = lab.resolve()
    real_home = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))).resolve()
    if lab.exists() or lab.is_relative_to(real_home) or real_home.is_relative_to(lab):
        raise ValueError('Use a new lab directory outside the real Codex home')
    lab.mkdir(parents=True)
    child_home = lab / 'cli-home'
    child_home.mkdir()
    market = lab / 'marketplace'
    market.mkdir()
    env = os.environ.copy()
    env.update({'CODEX_HOME': str(child_home), 'GIT_CONFIG_GLOBAL': os.devnull,
                'GIT_CONFIG_SYSTEM': os.devnull, 'GIT_CONFIG_COUNT': '1',
                'GIT_CONFIG_KEY_0': f'url.{market.as_uri()}.insteadOf',
                'GIT_CONFIG_VALUE_0': URL})
    for key in ('OPENAI_API_KEY', 'ANTHROPIC_API_KEY'):
        env.pop(key, None)
    commands = []

    def run(args, cwd=lab):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError('Native experiment deadline reached')
        result = subprocess.run(args, cwd=cwd, env=env, capture_output=True,
                                text=True, timeout=min(45, remaining))
        commands.append({'argv': [str(x) for x in args], 'exit_code': result.returncode,
                         'stdout': result.stdout, 'stderr': result.stderr})
        (lab / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
        if result.returncode:
            raise RuntimeError(result.stderr or result.stdout)
        return result.stdout

    def global_state():
        paths = [real_home / 'config.toml']
        cache = real_home / 'plugins/cache/orchivane-local/orchivane'
        if cache.exists():
            paths.extend(p for p in cache.rglob('*') if p.is_file())
        return {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in paths if p.is_file()}

    before_global = global_state()
    (lab / 'global-before.json').write_text(json.dumps(before_global, indent=2) + '\n')
    skill_files = [p.relative_to(ROOT).as_posix() for p in (ROOT / 'skills/orchivane').rglob('*')
                   if p.is_file() and p.suffix != '.pyc']
    package_files = ['plugin.json', '.codex-plugin/plugin.json',
                     '.claude-plugin/plugin.json', *skill_files]
    for name in package_files:
        target = market / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(subprocess.run(['git', '-C', str(ROOT), 'show', f'{BASE}:{name}'],
                                         check=True, capture_output=True).stdout)
    catalog = market / '.agents/plugins/marketplace.json'
    catalog.parent.mkdir(parents=True)
    catalog.write_text(json.dumps({'name': MARKET, 'plugins': [{
        'name': 'orchivane', 'source': {'source': 'local', 'path': './'},
        'policy': {'installation': 'AVAILABLE', 'authentication': 'ON_INSTALL'}}]}) + '\n')
    run(['git', 'init', '--initial-branch=main'], cwd=market)

    def commit(message):
        run(['git', 'add', '.'], cwd=market)
        run(['git', '-c', 'user.name=Orchivane Fixture', '-c',
             'user.email=fixture@example.invalid', 'commit', '-m', message], cwd=market)

    commit('Frozen old package')
    cli_version = run(['codex', '--version']).strip()
    setup = json.loads(run(['codex', 'plugin', 'marketplace', 'add', URL, '--json']))
    assert Path(setup['installedRoot']).resolve().is_relative_to(child_home)
    plugin_id = f'orchivane@{MARKET}'
    run(['codex', 'plugin', 'add', plugin_id, '--json'])
    old = child_home / f'plugins/cache/{MARKET}/orchivane/0.4.1/skills/orchivane'
    expected = inventory(old)
    verify_source(old, expected)
    retained = lab / 'project/retained/0.4.1/orchivane'
    retained.parent.mkdir(parents=True)
    shutil.copytree(old, retained)
    verify_source(retained, expected)
    assert not retained.resolve().is_relative_to(child_home)
    # Fault injections run before the readers or installer start.
    entry = retained / 'SKILL.md'
    original_entry = entry.read_bytes()
    entry.write_bytes(original_entry + b'\ncorrupted copy\n')
    rejected_corruption = False
    try:
        verify_source(retained, expected)
    except ValueError:
        rejected_corruption = True
    entry.write_bytes(original_entry)
    link = retained / 'cache-alias'
    link.symlink_to(old, target_is_directory=True)
    rejected_symlink = False
    try:
        inventory(retained)
    except ValueError:
        rejected_symlink = True
    link.unlink()
    verify_source(retained, expected)
    assert rejected_corruption and rejected_symlink
    for name in package_files:
        (market / name).write_bytes((ROOT / name).read_bytes())
    commit('Candidate package')
    events = []
    phase = {'name': 'before'}
    stop = threading.Event()
    ready = {name: threading.Event() for name in ('cache', 'retained')}
    started = time.monotonic_ns()

    def reader(name, root):
        while not stop.is_set():
            event = {'worker': name, 'phase': phase['name'],
                     'elapsed_ns': time.monotonic_ns() - started, 'ok': True}
            try:
                for relative, digest in expected.items():
                    if hashlib.sha256((root / relative).read_bytes()).hexdigest() != digest:
                        raise ValueError('bytes changed')
                ready[name].set()
            except (OSError, ValueError) as exc:
                event.update(ok=False, error=type(exc).__name__, file=relative)
            events.append(event)
            stop.wait(0.005)

    threads = [threading.Thread(target=reader, args=(name, root), daemon=True)
               for name, root in [('cache', old), ('retained', retained)]]
    old_exists_after_refresh = None
    try:
        for thread in threads:
            thread.start()
        assert all(signal.wait(5) for signal in ready.values())
        time.sleep(0.25)
        phase['name'] = 'marketplace-refresh'
        run(['codex', 'plugin', 'marketplace', 'upgrade', MARKET, '--json'])
        old_exists_after_refresh = old.exists()
        phase['name'] = 'plugin-install'
        run(['codex', 'plugin', 'add', plugin_id, '--json'])
        phase['name'] = 'after'
        time.sleep(0.25)
    finally:
        stop.set()
        for thread in threads:
            if thread.ident is not None:
                thread.join(timeout=5)
        (lab / 'reader-events.json').write_text(json.dumps(events, indent=2) + '\n')
    verify_source(retained, expected)
    continuation = continue_task(lab / 'project', retained, expected)
    new_version = json.loads((ROOT / 'plugin.json').read_text())['version']
    new = child_home / f'plugins/cache/{MARKET}/orchivane/{new_version}/skills/orchivane'
    verify_source(new, inventory(ROOT / 'skills/orchivane'))
    listing = json.loads(run(['codex', 'plugin', 'list', '--json']))
    installed = [p for p in listing['installed'] if p['pluginId'] == plugin_id]
    assert len(installed) == 1 and installed[0]['version'] == new_version
    assert installed[0]['installed'] and installed[0]['enabled']
    after_global = global_state()
    (lab / 'global-after.json').write_text(json.dumps(after_global, indent=2) + '\n')
    assert before_global == after_global
    counts = {}
    for worker in ('cache', 'retained'):
        counts[worker] = {}
        for name in ('before', 'marketplace-refresh', 'plugin-install', 'after'):
            subset = [e for e in events if e['worker'] == worker and e['phase'] == name]
            counts[worker][name] = {'reads': len(subset), 'failures': sum(not e['ok'] for e in subset)}
    assert counts['retained']['before']['reads'] and counts['retained']['after']['reads']
    assert not any(c['failures'] for c in counts['retained'].values())
    assert not old.exists() and any(c['failures'] for c in counts['cache'].values())
    result = {'date': '2026-10-23', 'base_commit': BASE, 'cli': cli_version,
              'old_version': '0.4.1', 'new_version': new_version,
              'old_source_files': expected, 'new_source_files': inventory(new),
              'old_cache_exists_after_marketplace_refresh': old_exists_after_refresh,
              'old_cache_exists_after_install': old.exists(), 'read_counts': counts,
              'failure_kinds': dict(Counter(e['error'] for e in events if not e['ok'])),
              'retained_entry': str(retained / 'SKILL.md'),
              'rejected_corrupt_copy_before_update': rejected_corruption,
              'rejected_symlink_copy_before_update': rejected_symlink,
              'post_update_continuation': continuation,
              'real_config_and_existing_orchivane_cache_files_unchanged': len(before_global),
              'one_enabled_candidate_install_in_isolated_home': True,
              'native_chat_creations': 0, 'native_chat_messages': 0, 'model_calls': 0,
              'limits': ['Deterministic reader threads, not native chat loading or hot reload.',
                         'Native CLI update deliberately bypasses the proposed hold for the unsafe control reader.',
                         'No claim that the host preserves its original cache path or enforces Orchivane guidance.',
                         'One host/version, finite sampling, no crash or concurrent external updater.']}
    (lab / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lab', required=True, type=Path, help='New disposable directory')
    print(json.dumps(run_lab(parser.parse_args().lab), indent=2))
