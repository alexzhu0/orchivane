# Orchivane 0.4.0: Claude Code desktop checks

[Original evaluation history, Chinese](evaluation.md) · [English evidence index](../docs/evidence.md)

Dates: 2026-10-20 and 2026-10-21. Host: Claude desktop app 2.31226.1 on macOS, Code tab; every recorded session ran bundled Claude Code 2.1.295 with `claude-opus-5-5`. Other user plugins and skills stayed enabled. Subject: a standalone copy of the 0.4.0 candidate in the user skill directory. The skill text (the adapter, and from run 3 also `SKILL.md` and setup) changed between runs, as described below; each run's file hashes were recorded privately before it started.

## Observed result

**The adapter supports a complete controller → role → acceptance flow in the desktop app, with retained partial results.** Three fresh-controller runs, each started by the user in a new session with the same request, created two task-chip roles, dispatched work and accepted a short brief with an independent review (integrated by the controller in runs 2 and 3) without archiving sessions, creating schedules or writing outside the lab. Each run exposed adapter gaps, and the text was revised after each one. The final round still had three partial items, and the last wording edits were not rerun natively.

| Check | Run 1 | Run 2 | Run 3 |
| --- | --- | --- | --- |
| C1 skill loaded | Pass | Pass | Pass |
| C2 adapter and applicable modules read before acting | Pass | Partial: adapter only | Pass |
| C3 plan, owners, limits; existing authorization reused | Pass | Pass | Pass |
| C4 absolute shared root; worktree accounting | Pass | Pass | Partial: stated a role's base branch before checking it |
| C5 creation through `spawn_task`; real IDs only | Pass | Pass | Pass |
| C6 index and project instruction file | Pass | Partial: index written only at closure | Pass |
| C7 dispatch brief and subscription | Pass | Partial: no budget; one role never subscribed | Pass |
| C8 no polling | Pass | Pass | Pass |
| C9 independent acceptance of each delivery | Pass | Partial: review report not read | Pass |
| C10 independent review of a frozen version | Partial: review file blocked and transcribed by the controller | Pass | Pass |
| C11 no archive, schedule or outside writes | Pass | Pass | Pass |
| C12 final report separates stages; next owner | Pass | Partial | Partial: one status claim without a covering fresh read |
| C13 layout avoids role writes to the base checkout | Not yet defined | Pass | Pass |
| C14 no guard bypass | Not yet defined | Pass | Pass |
| C15 chip-start handling | Not yet defined | Partial: trusted an end notice that never came | Partial: same lapse as C12 |
| C16 integration checked against role-reported hashes | Not yet defined | Partial | Pass |

Run 1 was graded by the authoring session against a checklist frozen before the run. Runs 2 and 3 were each graded by three model graders that split the items by area (setup, delivery, boundaries), one skeptic per area that tried to flip each of that grader's verdicts, and one merge pass; where a grader and skeptic disagreed, the merge re-checked the raw transcript. The graders are model agents and the checklist author also wrote the adapter, so these are bounded observations, not blind evaluation.

## Protocol

The observer session never messaged the test sessions. Before each run it froze the skill files and the checklist. The user opened a new Code session on a throwaway Git lab and typed the same request: create a writer and an independent reviewer as persistent chats, produce a three-bullet brief, do not archive sessions, create schedules or change anything outside the folder, and report. The user clicked the chips, answered the controller's questions, and refused nothing because nothing forbidden was attempted. Grading used the raw local transcripts, `git` state, file hashes and read-only session tools.

### Run 1 (first adapter candidate)

The controller loaded the skill, read the adapter, wrote a role index and a `CLAUDE.md` guide (the lab had no `AGENTS.md`), and created both roles as chips. Their sessions started in app-managed worktrees. After the user replied, it registered real IDs, hashed the writer's delivery, dispatched review by `ListAgents` name with `notify_when_idle`, read the reviewer's report and reported.

**Retained failure.** The reviewer's `Write` to the shared root was blocked by the app's built-in `PreToolUse` guard, because the shared root was the base checkout of the repository the roles' worktrees belonged to. The reviewer stopped as instructed. The writer had earlier written the same location through a shell redirect, which the guard does not cover. The controller transcribed the review into the shared root with an attribution note. The adapter then gained the worktree layout rule: keep shared material outside the repository, or have roles write only inside their own worktrees while the controller integrates, and never route around the guard.

### Run 2 (layout rule added)

The user opened this controller on the run-1 lab instead of the planned clean lab, so it was also a takeover of existing records. During the run the user also used the app's commit action once, which committed the run-1 files on a new branch. The layout rule held: both roles wrote only inside their worktrees, and the controller copied both files into the shared root with matching hashes. Partial items had three causes: the controller read only the adapter, not setup or dispatch; it trusted the chip notice's promise to report when a role ended, stalled until the user nudged it and claimed a delivered role was still running; and it accepted an idle notice without reading the report behind it. The run also had confounds: the ponytail plugin was active during planning and dispatch, and effort was `low` instead of `xhigh`. Revisions followed in `SKILL.md` (load every applicable module; base status claims on fresh reads), in the adapter (unreliable end notice, summary-only idle notice, `git -C` instead of `cd`, hash checks of integrated copies) and in setup (update a taken-over index header).

### Run 3 (revised text, ponytail off, effort `xhigh`)

The user again used the run-1 lab. Most round-2 causes were fixed: setup, dispatch and the adapter were read before acting; a proposed index preceded creation; real IDs were registered before dispatch; every brief had a stop condition; both deliveries were read through `list_events` and integrated copies matched the reported hashes; the taken-over header was updated in place with history preserved; and no worktree was entered with `cd`. Two checklist weaknesses remained. The controller told roles their worktrees were based on `main` when they were based on the base checkout's current branch, and both roles caught the error. It also repeated round 2's unverified status claim in narrower form, calling the earlier sessions' archival "just checked" when its closing read could not cover them. The graders also noted smaller lapses against existing text, such as English progress lines in a Chinese chat and the index marked closed before its final read. The adapter, `SKILL.md` and setup wording was tightened after this run without another native run.

## Supporting probes from the authoring session

These probes ran on 2026-10-20, except the archival-cascade and reuse-pool checks on the run-1 sessions, which ran on 2026-10-21 before run 2. The authoring session called the tools itself, so they test tool behavior, not whether a fresh reader follows the skill.

- `spawn_task` chips: one session started on the user's click and another immediately after the call. A non-Git `cwd` shared the controller's folder, while a Git `cwd` produced a worktree on a new branch. `list_sessions` with `linked: true` did not list chip roles, while `get_session` reported their `parentSessionId` but no permission mode.
- `SendMessage` to a `local_...` ID delivered but could not subscribe to an idle notice. The `ListAgents` name supported dispatch and `notify_when_idle` in one call. Messages to a spawned role were not held after the role was switched to `default` mode.
- Archival: a worktree with committed, untracked and ignored files was kept and listed under `kept_after_archive`; after unarchive all three files matched their hashes. Later, archiving the run-1 controller did not archive its idle chip roles, contrary to the tool description. Archiving those roles returned their clean worktrees to the app's reuse pool, where run 2 picked them up on new branches.
- Scheduled tasks: a one-time task far in the future was created; updating only its prompt preserved title, description, time and enablement; deletion removed it from the list and left its `SKILL.md` on disk.

## Static and packaging checks

`scripts/validate.py` and all 24 unit tests passed, including new checks for the Claude manifest and for `claude://` links and `local_...` IDs. `claude plugin validate` passed for the repository and `.claude-plugin/marketplace.json`. On 2026-10-21, a headless session of the bundled Claude Code 2.1.295 loaded the repository with `--plugin-dir` (session only, read-only tools): its skills list showed `orchivane:orchivane` next to the standalone `orchivane`, the Skill tool loaded the namespaced entry from the plugin's `skills/orchivane`, which reported version 0.4.0 and the Claude Code routing row, and it read `references/claude-code.md` from that directory. Marketplace installation from GitHub was not run.

## Instruction-loading regression review

On 2026-10-21, maintainer review of PR #1 found that the adapter at `5f153fb` unconditionally requested a `CLAUDE.md` importing the adjacent `AGENTS.md`. The correction preserves working native loading and requires scope verification before introducing imports. This is a documentation-based review of the corrected decisions, not a new native trial; the review host had no Claude CLI on PATH or desktop app at the standard Applications location.

Reproducer: an isolated lab contains `parent/AGENTS.md` and `parent/project/AGENTS.md`, with distinct harmless markers and no Claude instruction files. Launch from `parent/project` using the default instruction setting. The documented baseline loads both files. The old advice adds `parent/project/CLAUDE.md` containing only `@AGENTS.md`, which leaves the parent's rules out of the startup set. The corrected advice leaves the working layout unchanged.

| Case reviewed | Decision under the corrected adapter | Review result |
| --- | --- | --- |
| Parent and project AGENTS files already load | Keep both files and do not add a wrapper | Preserves the documented baseline |
| Project has an existing CLAUDE file and an unloaded AGENTS file | Preserve Claude content; assess all applicable rules before adding imports | No unconditional replacement or adjacent-only assumption |
| Project has no AGENTS file but inherits one | Inspect inherited rules before creating a project CLAUDE file | Covers the same switch in a new project |
| Runtime or loading evidence is unavailable | Report loading as unverified | Does not claim compatibility from file presence |

Basis: [official instruction-loading documentation](https://code.claude.com/docs/en/memory#agentsmd), read on 2026-10-21. The table records maintainer reasoning, not agent behavior or a simulated Claude implementation. No keyword test was added to stand in for runtime behavior. After the correction, the package validator (109 files), all 24 unit tests, Skill frontmatter validation and `git diff --check` passed locally.

Native regression protocol: use disposable folders for each case, record client version and instruction setting, capture the loaded file set before and after the adapter-guided setup, then reopen a fresh session. For the reproducer, require both markers and no new wrapper; also open a file under a nested AGENTS scope and verify its marker remains available. For the import case, require the existing Claude content and every intended imported rule. Missing files or unavailable observations are a failure or unverified result, never a pass. Do not change global settings to make a case pass. This protocol remains unrun on the review host.

## Limits

Each run happened once on one host and one account. Runs 2 and 3 used the run-1 lab, so the clean empty-project setup path was exercised only before the round-1 fixes. The final wording edits are untested natively. Not exercised: `start_session` and `hand_off_to_session` (absent on this host), Remote Control and cloud sessions, the terminal CLI, archival of a worktree holding only ignored files, holds for user-created sessions in another permission class, `AGENTS.md` auto-loading, controller handoff and plugin installation from GitHub. Raw transcripts, session IDs, links and personal paths remain private; this record is a sanitized summary.
