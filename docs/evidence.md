# Evidence index

[English README](../README.md) · [简体中文说明](../README.zh-CN.md) · [Original evaluation history, Chinese](../tests/evaluation.md)

This English index summarizes existing experiments. Original records and frozen fixtures remain in their source language; translating a summary is not rerunning an experiment. Dates and skill versions identify the actual subjects of each run.

## Version 0.4.2: old-source retention before refresh

On 2026-10-23, an [isolated native CLI experiment](../tests/cache-continuity.md) used a disposable CLI home and local Git transport to install 0.4.1, refresh to the candidate 0.4.2 and reinstall. Marketplace refresh itself removed the old cache. A cache-bound deterministic reader observed 43 failures in 128 sweeps; an independent old-source reader completed 125 sweeps over all nine files without failure. Retained hashes/references stayed valid; a post-update deterministic CSV task used 0.4.1 and produced three rows/total 9. Corrupt and symlink-dependent copies were rejected before the update. The real configuration and existing Orchivane cache, 295 files, were unchanged.

The workflow now holds marketplace refresh as well as installation until affected readers have accepted independent sources at normal task boundaries or finished their work. Unknown/shared-project coverage keeps the update deferred. Two separate one-turn temporary agents then planned the same unsafe/ready cases: both baseline 0.4.1 and candidate 0.4.2 deferred the unsafe case and permitted refresh under the synthetic ready case. No causal behavior improvement is established. This is a controller procedure, not a host lock. No native chats were created, messaged or retargeted; native receipt compliance, hot reload, crashes and another client's installer remain untested. Original cache path availability still fails. Earlier restoration evidence and its gap remain historical.

## Version 0.4.1: adoption and deferred version checks

The [adoption module](../skills/orchivane/references/adoption.md) adds an explicit existing-project path, source/read/task evidence, scoped receipts and role verification at normal work boundaries. On 2026-10-22, [four isolated temporary-agent turns](../tests/adoption-upgrade.md) exercised a 0.4.0 baseline, 0.4.1 controller adoption, a normal data task and rejection of a mismatched/partial receipt. Protected files and simulated runtime states were preserved; the worker produced three rows/total 9 and only its two authorized outputs. Candidate source hashes, sanitized artifacts and offline replay are published.

The baseline already handled the main boundaries correctly. Host project instructions also supplied deferred-loading guidance, so the run does not isolate a skill effect or prove improvement. Explicit frozen-source reads are not installed-plugin upgrade, automatic discovery, persistent-chat interruption or hot-reload evidence; idle roles and later controller acceptance remain deferred. Historical native tests below retain their actual versions.

### Native installed-plugin follow-up, 2026-10-22

After independent PR #2 review and a test-maintenance correction, the PR merged at `b613abd`. The local plugin actually upgraded from 0.4.0 to 0.4.1, with nine source files matched and 27 other plugin records/global configuration unchanged. Two fresh native chats completed four turns: real N1 delivery, controller adoption without waking the idle role, ordinary N2 with its own installed-source/module receipt, then controller acceptance and index closure at 4/4. The synthetic stale/partial receipt remained separate; N1 was 2/5 and N2 3/9. [Full native record and evidence](../tests/codex-041-adoption.md).

The native updater deleted the old cache; 138 files were restored at the original path from a preverified backup. Continuous availability during that gap was not established, and no existing-project no-impact claim is made. Acceptance also retains 4,312 module-output characters not directly recovered by the native history tool, supported by read-action/length/hash evidence. These are bounded native loading/receipt results, not uninterrupted upgrade, implicit selection, other-client or efficiency evidence.

## Version 0.4.0: Claude Code adapter

Version 0.4.0 adds `.claude-plugin/` manifests and a [Claude Code adapter](../skills/orchivane/references/claude-code.md) that maps the workflow onto the Claude desktop app's session tools. `SKILL.md` now reads `CLAUDE.md` alongside `AGENTS.md`, loads the adapter alongside the other modules in Claude Code, requires every applicable module and bases claims about another chat's status on a covering fresh read; setup updates a taken-over index header, and the guide it appends now says "Orchivane modules" instead of "`$orchivane` modules". Apart from loading the adapter, these changes also apply to Codex. They had not been rerun there at the initial PR review; the bounded follow-up below adds Codex evidence.

Dates: 2026-10-20 to 2026-10-21. In three fresh-controller runs in the desktop app, the user typed the same request and the controller created a writer and a reviewer through task chips, dispatched by `ListAgents` name with idle notices, accepted a brief against hashes (integrated by the controller in runs 2 and 3), with no archives, schedules or writes outside the lab. In run 1 the app's worktree guard blocked the reviewer from writing to the base checkout, which the writer had reached through the shell; the layout rule added afterwards held in runs 2 and 3. Run 3 passed 13 of 16 items, with three partial. Runs 2 and 3 used the run-1 lab, run 2 was confounded by an active plugin during planning and low effort, and the final wording edits were not rerun. A session-only `--plugin-dir` load discovered and invoked the plugin skill; installation from GitHub was not observed. [Full record](../tests/claude-code-desktop.md).

The 2026-10-21 [instruction-loading regression review](../tests/claude-code-desktop.md#instruction-loading-regression-review) corrected an unconditional CLAUDE wrapper recommendation that could omit inherited AGENTS rules. Four setup cases were reviewed against documented behavior; native loading remains unverified.

### Codex 0.4.0 follow-up, 2026-10-22

The local plugin was already installed/enabled at the merged revision, with all eight skill files matching. Two fresh native chats completed four turns: actual installed-entry/module reads, A1, read-only takeover with 41 project files unchanged, evaluator ownership switch, A2, and identical repeated dispatch with no extra apply. The final index and handoff both closed at 4/4 used. One source-index relative path was wrong; the evaluator corrected current guidance while retaining the failed source snapshot, and successor records preserved that correction. This supports the tested functional paths, not complete nonregression or a causal benefit. See the [English report](../tests/codex-040.md), [Chinese report](../tests/codex-040.zh-CN.md) and their replayable artifacts. No skill or manifest changed; the earlier Claude and bilingual limitations remain.

## Version 0.3.2: English-first distribution

Version 0.3.2 changes the maintained skill instructions, plugin presentation and default documentation to English, adds a complete Chinese README with language switching, and provides bilingual research/value guides. Code identifiers and comments remain English. Responses follow the user's preferred language.

The change preserves the intended authorization, ownership, budget, frozen-input and handoff rules. Static validation and existing offline tests check packaging, links, recorded evidence and fixtures. They do not prove behavioral equivalence between translated prompts. A subsequent [native 0.3.2 check](../tests/bilingual-032.md) upgraded the local plugin and verified seven installed file hashes. Four fresh chats actually read the installed entry; both planning languages passed. English-to-Chinese takeover, A2 and duplicate suppression passed functional checks. Chinese-to-English acceptance stopped on a host capacity error. The completed chain retained a stale current budget/next step under conflicting read-only instructions; controller closure was recorded separately without regrading. Eight turns were dispatched (seven completed, one failed). These are bounded partial observations, not a clean bilingual nonregression result.

## Paired pilot

Date: 2026-10-20. Skill: 0.3.1, source `a86ba04`. Three small synthetic tasks, one pair per task, eight native chats and twelve aggregate turns. Both arms used `gpt-6.1-sol` with high effort and the same initial business inputs. Each task/arm had a ceiling of four turns, including any collaborators. No specialists were created; the handoff case used a fresh successor in each arm.

| Measure | Single chat | Orchivane |
| --- | --- | --- |
| Tasks completed | 3 of 3 | 3 of 3 |
| Extra coordination requests | 0 | 0 |
| Actual aggregate turns | 6 | 6 |
| Cumulative active duration | 216.163 s | 293.142 s |
| Reported total tokens | 1,120,054 | 1,536,528 |
| Real human minutes / monetary cost | Not measured / unavailable | Not measured / unavailable |

Tasks covered a small normalization change, staged changes across stock-summary code/CLI/docs/contract, and file-based handoff with a repeated request. Final functional checks passed in both arms: 4, 9 and 5 checks respectively. Each handoff arm applied A1 and A2 once; duplicate dispatch left the actual input, program, configuration, output and audit unchanged.

**No coordination reduction was observed.** Both baselines reached zero extra requests. The tasks were short and well specified, cross-file changes did not create cross-role pressure, and no sustained specialist collaboration occurred. Other plugins remained enabled; treatment prompts differed; the observer knew the arms. Turn ceilings were equal, actual token use was not. Cached tokens comprise much of the total and cannot be treated as an equal-rate bill. There were no independent repeats or human-time calibration.

Both arms retained intermediate failing tests before implementation, and the Orchivane preparation trace includes one failed read of absent index files. Measurement-driver errors are disclosed in the original report; no post-grading solver repair was added.

Reproducible materials: [frozen English protocol](../tests/paired/protocol.md), [plan](../tests/paired/plan.json), [metrics](../tests/paired/metrics.json), [results](../tests/paired/results.jsonl), [inputs](../tests/paired/inputs.json), [final artifacts](../tests/paired/artifacts.json), [grader](../tests/paired/grade.py), [full report and reproduction, Chinese](../tests/paired/README.md). The record audit found all six planned rows without missing, duplicate or version-conflicting records; it is not release approval or proof of labeling quality.

## Desktop installation

Date: 2026-10-19. Skill: 0.3.1. CLI 0.157.1 installed and enabled `orchivane@orchivane-local`. Seven cached skill files matched the source. The user observed Orchivane in the desktop directory. Two fresh native desktop chats actually read the cached entry and relevant modules and used them to recommend a collaboration structure.

One request body did not name the skill, but both chat titles included Orchivane and other plugins were enabled. Each case ran once; this is not an implicit-trigger rate or a clean ablation. No restart was needed for these checks. UI visibility is user-reported, while file reads and responses were inspected through tools.

The earlier Session Control 0.3.0 standalone copy was discovered in the CLI but absent from three fresh desktop chats. Its root cause remains unknown. The later successful plugin route does not retroactively repair that path. [Original observations and reproduction, Chinese](../tests/desktop-plugin.md); [English compatibility notes](compatibility.md).

## Handoff and recovery

Date: 2026-10-20. Skill: frozen 0.3.1 from `33fb0c4`. Three native chats represented the old owner, fresh successor and independent reviewer, with eight dispatched turns in total.

The isolated CSV fixture exercised missing ignored inputs, restoration from an independent backup, preservation of uncommitted configuration, injected ownership conflict, historical-versus-current evidence and identical serial duplicate dispatch. A1 produced two rows totaling 5; A2 produced three rows totaling 9, each with one actual execution receipt. The successor passed read-only acceptance before taking ownership and executing A2; the duplicate request did not apply again.

Initial independent review supported the six bounded behaviors but failed overall closure because the controller's pending handoff item and role label were stale. One correction to current records and a targeted independent recheck closed those issues; failed snapshots remained intact. Two read-only measurement assertions initially mixed copied or historical evidence into the wrong scope and were corrected without another business apply.

The ownership conflict was a labeled file injection, not a real concurrent writer. No native archival, unknown creation result, crash window, asynchronous transport recovery or retry after context loss was tested. The fixture has no built-in deduplication, so this is not transactional exactly-once execution. [Full protocol and closure report, Chinese](../tests/handoff-recovery.md); [fixture](../tests/fixtures/recovery/report.py).

## Native project example

Date: 2026-10-19. Three fresh native chats performed research, design and independent acceptance for a fictional tool-lending pilot. Execution used frozen Skill 0.2.0; version 0.3.0 incorporated fixes identified by the run and was not given a full native rerun.

Research covered three institutions and five primary pages. Initial acceptance was 17/20; after the sole allowed revision it was 19/20, with a remaining state-transition conflict. **Final acceptance failed**, and the stop condition prevented another repair. The process also exposed a controller-created frozen-package reference failure. Public artifacts are sanitized; private IDs and raw native receipts remain private.

[Full case, Chinese](../examples/tool-library/README.md), [native reproduction protocol, Chinese](../tests/native-e2e.md). This case establishes an inspectable native workflow and failure, not quality or efficiency superiority over one chat.

## Earlier text scenarios

Versions 0.1.0 and 0.2.0 included baseline and skill-guided text exercises. The no-skill baseline already respected several important permission, budget and preservation boundaries. The exercises produced real local records but did not operate native chats. Their evaluators knew the scenarios; these were neither blind controlled trials nor performance estimates. [Original history, Chinese](../tests/evaluation.md).

## What remains unverified

Real human coordination savings, representative long-running specialist work, language-specific behavioral equivalence, cross-client installation, archival survival, real concurrent writers, crash recovery and long-term scheduling need separate evidence. In Claude Code, plugin installation from GitHub, a clean empty-project run of the final text and controller handoff also remain unverified. Static CI, a well-formed manifest or a successful bounded run cannot establish these properties.
