# Cache cleanup and retained old-source reads

[English README](../README.md) · [简体中文](../README.zh-CN.md) · [Evidence](../docs/evidence.md)

Date: 2026-10-23. Candidate skill: 0.4.2. Native installer: Codex CLI 0.157.1. Base source: `f1b45702d76e921710213a9398adaa97419cd705`.

**Conditional closure:** retaining and actually using an independent old source survived the tested cleanup. The original managed cache path did not survive. Orchivane cannot make a host-managed pathname permanent or silently redirect an already-running chat. If affected readers have not accepted independent sources at a normal boundary, defer both marketplace refresh and installation while their work continues.

## Why restoration was insufficient

The [0.4.1 native run](codex-041-adoption.md) backed up 138 old-package files, observed their deletion and restored them. That established recovery after a gap. It could not establish availability during the gap.

OpenAI's packaging documentation identifies installed plugin caches and says marketplace refresh can refresh configured plugins even when disabled. Our isolated observation additionally identifies deletion of this old cache during refresh; the documentation does not promise old-path retention. [Official packaging and refresh guidance](https://developers.openai.com/plugins/build/plugins#enable-or-disable-a-plugin-for-a-repo).

## Frozen scope and isolation

The maintainer authorized an isolated example and repository changes. The [plan](outputs/cache-continuity/plan.json) allowed one native upgrade, two installs, two deterministic readers, no model/provider calls or native-chat actions, and bounded command/run time. A disposable checkout holds the candidate; no real project or installed plugin is upgraded.

The native CLI receives a separate home **only in its child-process environment**. Its reserved `.invalid` Git marketplace address is rewritten to a local Git repository using child-only Git configuration. No real credentials or user configuration are copied. Paths returned by marketplace setup must resolve into the isolated home. The real `config.toml` and every existing file under the real Orchivane plugin cache are hashed before and after: 295 files matched. Private raw inventories stay local; the public [isolation record](outputs/cache-continuity/isolation.json) contains their comparison digests.

This is native installation with deterministic filesystem workers, **not** a new native-chat or agent-behavior trial. The unsafe cache-bound reader deliberately remains in the control arm while the lab bypasses the proposed hold. Production guidance would defer that update. No idle role was messaged; no current chat was restarted, archived or retargeted.

## Observed sequence and results

1. Install the frozen 0.4.1 package through the real CLI in the isolated home.
2. Copy its complete nine-file skill tree into the independent example project. Verify all hashes and local reference targets at the copied location. A modified entry and a cache-dependent symlink are separately rejected, then removed/restored before the experiment.
3. Start two reader threads. Every sweep reopens and hashes all nine source files. Both must complete a successful sweep before refresh. One reads the managed cache, the other the retained old source. No file descriptor or in-memory module text substitutes for reopening files.
4. Refresh the Git marketplace to the candidate 0.4.2, then run the normal install command. Record source existence after each command. Continue both readers afterwards.
5. Verify the retained 0.4.1 tree, new 0.4.2 tree, enabled candidate state and real-home preservation. Stage a small CSV after the update and use the retained source for a deterministic continuation; save and independently reparse its result/receipt.

| Phase | Managed cache sweeps / failures | Retained old-source sweeps / failures |
| --- | --- | --- |
| Before refresh | 36 / 0 | 35 / 0 |
| Marketplace refresh | 50 / 1 | 50 / 0 |
| Explicit install | 7 / 7 | 6 / 0 |
| After install | 35 / 35 | 34 / 0 |
| Total | 128 / 43 | 125 / 0 |

All observed cache failures were `FileNotFoundError`. The old cache was already absent immediately after marketplace refresh and remained absent after explicit installation. No restoration or symlink alias was used to conceal that failure. The retained reader completed 1,125 individual file opens across its 125 successful sweeps; the nine final hashes and relative references matched the pre-update source. The retained worker's observation window was 924.324 ms, with a maximum 9.065 ms gap between sweep starts. This is finite sampling, not a proof of every instant or indefinite availability.

The subsequent deterministic task read the retained **0.4.1** source, produced three rows/total 9, and saved an inspectable receipt. Its CSV was staged after the update; this is not a claim about preserving business inputs through that update or a native role's own acceptance. The isolated installed candidate was **0.4.2**. The real installed plugin remained **0.4.1** and its existing cache files stayed unchanged.

## Workflow correction

The maintained [adoption module](../skills/orchivane/references/adoption.md#preserve-old-reads-before-any-package-refresh) now requires:

- Preserve a complete self-contained old source outside managed caches, temporary worktrees and automatic discovery; verify content identity and reference resolution.
- Use the next ordinary task/checkpoint for actual source acceptance. The role's receipt must identify its retained entry and actual reads; copying files or editing the controller index cannot redirect a busy role.
- Keep refresh **and** installation deferred while an affected reader still needs the cache, a pin is unaccepted or shared-project coverage is unknown. Idle roles remain pending without upgrade-only wakeups.
- Verify retained sources after the authorized update and keep them until dependent work is complete and cleanup is authorized. Existing permissions, budgets and stop conditions remain intact.

This is an operational rule for a controller, not a package hook or host lock. It cannot stop another actor or an uncontrolled host updater. No daemon, global cache patch, special filesystem alias or automatic restart was added. Native-chat source acceptance remains unverified.

## Supplemental planning forward test

After the draft, two fresh temporary agents each received one explicit skill source (baseline 0.4.1 or candidate 0.4.2) and the same two synthetic case directories, with one turn each and no repair turn. They did not inherit the parent conversation or an intended verdict. Both were restricted to reading the supplied skill/cases and writing their own concrete plans; no real host or chat action was permitted. These are temporary agents, not user-owned native conversations. Standard assistant inference consumes account resources; it is separate from the zero-provider-call native CLI trial.

- **Project A:** an active role still names a cache path, an idle role has not accepted the copied source, and cross-project reader coverage is explicitly incomplete. Both agents saved a plan deferring refresh. The candidate also explicitly kept both the idle-role acceptance and unknown coverage as refresh blockers, with unsent normal-task briefs.
- **Project B:** supplied synthetic ordinary-task acceptance covers the only active reader's independent old source, its nine hashes match, and the registry covers this isolated host. Both agents said refresh prerequisites were satisfied in the modeled case while existing work continues from retained 0.4.1. Neither called that a completed installation or native role verification.

The saved [plans, inputs and limited reading receipts](outputs/cache-continuity/forward-test.json) were inspected. Source copies matched frozen hashes; reading claims come from the agents' receipts, not collected native tool histories. Project A's cache pathname is a declared synthetic state rather than a materialized running reader; actual source continuity was measured in the separate CLI trial. The planned deferral case now has this bounded planning check, not a real dispatch/interrupt probe. Both versions already made the two main decisions correctly, so this pair does not establish a model-behavior or coordination improvement. It was a post-draft forward check, not a claimed test-first causal experiment.

## Evidence and reproduction

[Plan](outputs/cache-continuity/plan.json), [actual command log](outputs/cache-continuity/commands.json), [individual reader events](outputs/cache-continuity/reader-events.json), [results/source hashes](outputs/cache-continuity/results.json), [project snapshot](outputs/cache-continuity/project-artifacts.json), [isolation comparison](outputs/cache-continuity/isolation.json) and the separate [planning forward test](outputs/cache-continuity/forward-test.json). Public paths are placeholders; hashes of published project text identify sanitized derivative bytes. Private originals remain local.

Offline checks never invoke Codex or models:

```sh
python3 -m unittest discover -s tests -p 'test_cache_continuity.py' -v
```

The complete local suite has 36 passing tests; package checks and skill-schema validation also pass. These checks include source loss, corruption, symlink/external-reference rejection and evidence replay, without re-running native installation or agents.

The optional [native fixture](cache_continuity.py) performs local installation and must be invoked deliberately with an absent disposable directory, a compatible Codex CLI on `PATH`, Git and Python 3.10+:

```sh
python3 -B tests/cache_continuity.py --lab /tmp/orchivane-cache-lab-new
```

The fixture needs the historical base commit locally; a shallow checkout may need that commit fetched first. It refuses an existing lab or a location overlapping the real Codex home and uses child-only installation/Git configuration. Preserve failed logs; do not point it at a production directory. The observed run executed one upgrade with two installs. The post-update task helper was added and executed separately afterwards. File-URI rejection was added and unit-tested; an aggregate deadline guard was also added without another installer run or timeout-path exercise. Tested skill bytes and original reader counts are unchanged.

## Limits

One host/CLI version, two deterministic threads and one short update. No native chat pin acceptance, implicit discovery, host-wide enforcement, crash, power-loss, external updater race, long-running service or Claude installer was tested. The example covers Orchivane's self-contained source files; external scripts, servers or other plugin dependencies need their own checks. Existing live projects were not migrated. Prior cache-gap, bilingual, handoff and efficiency limitations are unchanged.

中文摘要：隔离测试确认，单是刷新目录就会清理旧缓存；原路径失败43次，独立旧来源125次完整读取均成功，升级后仍用旧版完成3行合计9的确定性任务。真实配置及插件295文件未变。0.4.2新增“先独立保全、正常任务确认；覆盖不全则暂缓刷新和安装”的规则。不能保证宿主缓存原路径永久可用，也未验证原生对话改读或自动执行该规则；没有触达现有项目。

## Review follow-up: capability-limited symlink test (2026-10-26)

The cache-continuity symlink test now skips only when creation is unsupported (`ENOSYS` / `ENOTSUP`, or Windows error 50) or Windows lacks the required privilege (error 1314). Unexpected access denial, a missing parent and filesystem I/O errors still fail. On a capable host, the real symlink is created and the source inventory must still reject it.

A regression test injects all four supported skip cases and three unexpected errors. It failed on the unchanged test, then passed with the narrow guard. The seven cache-continuity tests and the complete 37-test suite pass locally, as do static package and whitespace checks. This follow-up uses fault injection on macOS, not native Windows validation. It changes no skill bytes, frozen evidence or installer behavior and does not rerun the native experiment. The earlier 36-test result remains the historical check for the original candidate.
