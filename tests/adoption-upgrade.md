# Existing-project adoption and deferred upgrades

[English README](../README.md) · [简体中文说明](../README.zh-CN.md) · [Evidence index](../docs/evidence.md)

Date: 2026-10-22. The subject is the frozen 0.4.1 candidate, compared with the unchanged 0.4.0 skill for one initial-adoption case. Four fresh-context temporary agents each completed one turn, observed as `gpt-6.1-sol` / `max` with no model override. These are real agent executions on isolated files, with simulated persistent-role states. They are not native desktop chat, installation or hot-reload tests.

## Frozen protocol

The example project prepares a stock summary. Its existing controller maintains coordination records; a data worker is finishing N1, a reviewer has no task, and a former worker is retained but stopped. The next ordinary data task, N2, summarizes three CSV rows into a row count and total. Original authorization, a zero business-provider/network budget, an in-progress checkpoint, a historical receipt and accepted frozen input must survive adoption.

Four solver turns are permitted, one per phase, with no repair turns:

1. The 0.4.0 controller handles the adoption request using its frozen snapshot.
2. A fresh 0.4.1 controller handles the same request and initial project files.
3. After the evaluator checks protected files, N1 ends in the fixture and a fresh data worker receives ordinary N2, using the same frozen candidate. This is a planned task boundary, not an upgrade-only wake-up.
4. A separate controller reviews a receipt claiming 0.4.1 while its actual entry belongs to 0.4.0, with no module/task evidence. It receives no new task for a specialist.

No solver may create, message, stop, schedule or archive native chats, install/update a plugin, change configuration or call business providers. They may read only their case and specified snapshots and write only their assigned case/role outputs. Simulated `runtime-state.json` is evidence, not an API for manufacturing delivery or acceptance. The evaluator freezes artifacts before each dependent phase and retains failures. A failed controller-preservation check stops the dependent worker phase.

The checks cover preservation of business/frozen files and runtime states; reuse of existing roles and single index ownership; separation of source availability, actual reads and task checks; deferred active/idle coverage; a normal task's actual result and role-owned receipt; and detection of stale/partial evidence. Artifact checks and manual read-trace review are separate. A baseline that already respects a boundary remains a passing baseline; one pair cannot establish improvement or reliability.

## Results

**The exercised paths passed. The old-version baseline also respected the important boundaries, so this is not evidence that 0.4.1 improves on 0.4.0.**

| Phase | Actual result |
| --- | --- |
| 0.4.0 adoption baseline | Seven protected files unchanged; entry/setup/dispatch/health-check actually read. N1 continued, other roles deferred, predecessor historical. It already distinguished a supplied snapshot from installed/latest state |
| 0.4.1 controller | Eight protected files unchanged, including AGENTS.md. Entry/setup/adoption/dispatch read; a normal-N2 addendum saved locally, explicitly unsent and unaccepted. Other roles remained pending |
| Mismatched/partial receipt | Actual entry was read and verified as 0.4.0 despite the submitted 0.4.1 label; absent module/task evidence kept worker coverage unverified. Eight protected fixture files plus the submitted receipt unchanged; no pause or upgrade dispatch |
| Normal N2 task | Three CSV rows, quantity total 9, independently recalculated and saved JSON parsed. Only `work/data/summary.json` and `work/data/receipt-N2.json` added; all 12 previous files unchanged. Entry/setup/adoption read; the receipt identifies source hashes, explicit-path loading, task scope, authority, limits and next owner |

The evaluator checked controller preservation before staging the N1→N2 fixture transition. This changed only the simulated worker's task and added an evaluator marker; it is not proof that a real N1 ran. The independent mismatch case overlapped controller work. There were no additional solver turns or repair dispatches. Actual tool calls were inspected alongside artifacts, rather than inferring reads from version labels or counting keywords.

After N2, the worker correctly left the sole controller index untouched and marked acceptance pending. The evaluator verified the actual output and receipt separately; the controller was not woken for a fifth turn to clear coverage. Its index remains an earlier inspection snapshot, with N2 acceptance and other roles' checks due at normal boundaries. The exercise does not claim all project roles upgraded or that the saved brief was delivered by a native host.

One wording defect is retained: the candidate controller describes “four references,” but its table and trace contain four source files—entry plus three modules. Evaluation uses the actual reads, not that count. An evaluator-only evidence collection command had a missing import, corrected without a solver retry or business effect. Intermediate package validation also found the new report link before this report existed; the completed package was checked again.

## What changed in the skill

The [adoption reference](../skills/orchivane/references/adoption.md) makes the existing-project path explicit: identify the actual source and target, separate installation from reads and task checks, preserve ownership/budgets/history, defer verification until normal work, and keep partial/mismatched evidence open. It adds a small receipt contract to existing task records. Entry routing, setup, dispatch, health-check and Codex guidance link this path; manifests and maintained entry metadata agree on 0.4.1. No runtime, hooks, automatic broadcasts or extra installation mechanism was added.

The candidate was frozen before its three turns; all nine skill files still match the published source hashes. The baseline used the unchanged eight-file 0.4.0 snapshot from the prior repository head. Documentation and evidence were completed afterwards without changing the tested candidate.

## Reproduction and limits

Published, sanitized derivatives:

- [Plan](outputs/v0.4.1-adoption/plan.json), [original input files](outputs/v0.4.1-adoption/inputs.json) and [reusable task briefs](outputs/v0.4.1-adoption/task-briefs.json). The briefs summarize evaluator dispatches; they are not authenticated verbatim native-message exports.
- [Artifacts and hashes](outputs/v0.4.1-adoption/artifacts.json): baseline, candidate controller, mismatch, staged worker input and completed worker. Placeholder paths replace private paths; hashes identify the published derivative bytes.
- [Source hashes](outputs/v0.4.1-adoption/skill-hashes.json), [results](outputs/v0.4.1-adoption/results.json) and [visible-message/read summary](outputs/v0.4.1-adoption/trace-summary.json). Selected read-call code is included; remaining tool code and host project context stay private. The read summary was reviewed against actual calls, not generated by a keyword grader.

For a new behavioral run, materialize the inputs in isolated cases, freeze complete skill directories, use the same bounded task briefs, inspect actual module reads and output artifacts, and check protected files before staging the normal-task transition. The malformed submitted receipt is retained in the mismatch artifact. Preserve every original result; new runs are new evidence.

Offline replay, with no agent/model calls or native chat operations:

```sh
.venv/bin/python -m unittest discover -s tests -p 'test_adoption_evidence.py' -v
```

The three tests verify published hashes, equality with the frozen candidate, preservation of controller inputs/runtime state, the worker's write boundary and the actual CSV result. They do not independently grade prose or reproduce model decisions. Package validation, all 28 offline unit tests and the skill-creator format check also passed; these are separate from the four behavioral turns.

The agents inherited host project instructions and the installed skill catalog even without parent conversational history. Those instructions already include deferred-loading guidance; this is not a clean skill ablation, and their private text is not published. The evaluator knew the scenarios and inspected outcomes; there was one example per phase, no statistical repetition and no equal-spend comparison.

This exercise does not test concurrent native writers, interrupting message delivery, live host queues, installed-cache upgrades, automatic discovery, Claude Code, real archival, long-running scheduling, human coordination time or comparative token/financial cost. Business-provider/network calls were prohibited; agent inference still consumes normal assistant resources, with no hard token cap. Temporary agents do not replace persistent chats. Explicit snapshot reads establish only that loading mode. Real host-level noninterruption still depends on using the host's actual capabilities as documented in the adoption module.

中文摘要：四个隔离场景完成了真实临时agent执行，接入、版本冲突识别、正常任务附带回执及受保护文件检查通过；旧版基线也正确遵守了主要边界。角色运行状态为模拟，不能据此证明桌面热加载、消息不打断、全员升级或协调成本降低。没有为补齐回执额外唤醒角色；N2仍将总控验收作为后续正常步骤。

## PR #2 review follow-up

Pre-merge review reproduced a maintenance defect in the offline replay test: comparing every future checkout with the frozen 0.4.1 skill hashes would reject a legitimate later release. The fix retains unconditional artifact/preservation checks and compares current source only when its manifest version is 0.4.1. A new temporary-root regression covers version 0.4.2 without modifying historical artifacts. All 29 offline tests and package checks passed after the correction. Independent review found no other blocking issue; its review covered the original head, and the maintainer verified this test-only correction separately. The tested skill bytes and four agent outcomes above are unchanged.
