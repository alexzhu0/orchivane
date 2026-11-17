# Orchivane in Grok Bot: Usage and Validation

**English** · [简体中文](grok-bot-guide.zh-CN.md) · [Field trial record](../tests/grok-bot-site-trial.md)

This is a community usage guide. It describes how one team used Orchivane in Grok Bot: one controller bot coordinating several long-lived bot teammates, with the user making every final decision. It is a usage pattern observed in one configuration, not a statement about how Grok Bot behaves in general. Where a step was not exercised in the trial, it says so.

"Observed" and "PASS" in this guide are the contributor's records, judged against the trial's own acceptance criteria. They are contributor-reported and have not been independently reviewed by the maintainers. They do not mean that upstream has certified Grok Bot compatibility, and they do not claim stable Grok Bot support.

Read it together with the skill's own modules: [setup](../skills/orchivane/references/setup.md), [dispatch](../skills/orchivane/references/dispatch.md), [handoff](../skills/orchivane/references/handoff.md) and [health check](../skills/orchivane/references/health-check.md). When this guide and the skill disagree, the skill and your own team rules win.

## 0. Loading and using Orchivane in Grok Bot (what the trial actually did)

- **Pinned version:** Orchivane 0.4.1 from `alexzhu0/orchivane`, commit `f1b45702`.
- **Loading method: manual reading.** No plugin was installed and no auto-discovery or auto-loading was used; neither was verified, so neither is claimed as supported. The team turned the skill into an internal team reference (a team-written summary with team-specific limits, such as no implicit invocation and reviewer sign-off for risky actions). **This is a modified copy.** A read-only copy of the original `SKILL.md` and all 7 references was kept alongside it; its md5 values match the commit above, and the skill text itself was not modified.
- **Modules used:** setup, dispatch, handoff and health-check. The controller read and cited the original dispatch, handoff and health-check modules when writing change records, the handoff plan and the health check report. Other roles received the location of the team reference in the "background" section of their dispatch briefs and read it as needed. **No receipt was recorded showing that each role read the original modules** (contributor-reported, not independently reviewed by maintainers).
- **Role registration:** write a collaboration entry file before work starts, listing roles, read/write scopes and readiness (see §1).
- **Dispatch and receipts:** the controller sends dispatch briefs with Grok Bot's built-in send-to-teammate message tool, and teammates reply with receipts through the same tool. The controller archives the message text. A "sent" result from the tool only means the message was delivered; it does not mean the task is done.
- **Where artifacts and receipts live:** in a project record folder in the shared cloud workspace, split into authorization, readiness, setup, dispatch, freeze, deliverables, acceptance, handoff and health-check subfolders. Receipts are also saved as files and logged in the evidence log.
- **When to stop:** every dispatch brief lists its stop conditions. The trial actually used "stop if an input md5 does not match" and "do not perform a risky action without a reviewer receipt". If a referenced source is missing or a receipt has not arrived, the task should stay "not done / pending"; the controller does not report it as done on the other role's behalf, and once the condition is fixed it sends a resume message under the same task ID. **"Stop on a missing source and resume after it is restored" was not tested on its own in the trial. A supplementary small test on 2026-10-24 tested one missing-input case: the executor bot stopped, wrote only a blocked receipt and made up no results; after the controller supplied the input, the task resumed and completed under the same task ID (this one exception type only, single run; see §6 of the trial record). Because step 5 failed on write scope, that supplementary test is judged FAIL overall against its pre-set threshold (see §6.8 of the trial record).**

## Evidence level and validation scope

| Capability | How it was used | Scenario and count | Result | Evidence | Known limits |
| --- | --- | --- | --- | --- | --- |
| Loading Orchivane | Manual reading of the team reference + read-only original copy (commit `f1b45702`) | 1 task, initial run + rerun | Controller records cite the original modules | Trial record §1 | No per-role load receipts; plugin install and auto-loading not verified |
| Structure, roles, readiness receipts | Collaboration entry file; roles reply through native messaging | Initial T1, once | Observed | Trial record §1, §3; excerpts in §1.4 | Only some readiness receipts survive verbatim |
| Authorization on paper | User quotes archived verbatim | Initial run + rerun | Observed | Trial record §2 | Single user |
| Dispatch, external developers, per-command approval | Dispatch briefs + reviewer clearance + per-command user approval | Initial run + rerun | Observed | Trial record §3, Appendix A | External developer tools are not required dependencies |
| Freezing inputs (md5) | Freeze list + `md5sum -c` | Initial run once, rerun once | Initial run FAIL, rerun PASS (by the trial's own criteria) | Trial record §2, §3 | Single task |
| Acceptance with four separate steps | Delivery → technical check → acceptance → user's final choice | Rerun, 2 rounds | Observed | Trial record §3, §4 | Adversarial collusion not tested |
| Reviewer-only role | Risky actions go to the reviewer first | Initial run + rerun | Observed | Trial record §3 | — |
| Simulated handoff | Temporary subagent reads the handoff package | Initial T4 once, rerun T4R once | The two results differ; see §9 | Trial record §3, §1.4 | Temporary-subagent simulation only; long-lived role takeover not verified |
| Read-only health check | H1–H11 read-only inspection | Initial T5 once, rerun T5R once | Observed | Trial record §3, §1.4 | No scheduled health checks |
| One-off scheduled check-back | — | 0 | Drafted, never created | Trial record §5 | Not verified |
| Small Grok-Bot-only case (supplementary test) | Controller + one executor role | 2026-10-24, one run, each of 5 steps once: loading and readiness, normal closed loop, repeat with a new input, stop on missing input, resume under the same task ID; 5 controller-to-executor messages, 0 follow-ups | **FAIL overall** (against the test's own pre-set threshold): step 5 failed on write scope. Recorded separately: all three summaries matched the sealed answers; the executor stopped on a missing input and resumed under the same task ID once it was supplied, meeting the pre-set criteria. The reviewer bot's judgment at the time ("post-run check PASS", "the write not counted as a failure") is kept in the trial record and superseded by the corrected conclusion in §6.8 | Trial record §6 (corrected conclusion in §6.8) | One executor bot only; only the missing-input exception tested, no-receipt case not tested; single run; write scope checked only within the monitored folder, and in the resume step the executor bot wrote one verification copy to the system temporary folder (deleted afterwards; this is the cause of the write-scope failure); one extra snapshot beyond the plan, and the message-count file was edited once after S5; the blocked receipt's wording differs from the plan's but means the same; the executor bot also sent progress messages to the user; not independently reviewed by maintainers |
| Native plugin install / auto-loading, real long-lived role takeover and archiving, recovery from interrupted runs, repeated dispatch, continued readability of old sources during upgrades | — | 0 | Not verified | — | Not verified |

## 1. Set the structure

Write one collaboration entry file before any work starts. Keep it short and factual:

- **Roles, not people.** List every long-lived bot by role, what it reads, what it writes, its current task and whether it has confirmed it is ready. In the trial the entry file's role table registered 5 long-lived roles: controller, content (requirements and acceptance criteria), design/layout, technical executor, and reviewer. The user sits above all of them. The rerun reused the requirements and layout frozen in the initial run, so the content and design/layout roles produced nothing new in the rerun. A compliance role reviewed the public drafts once before publication; it was not registered in the role table.
- **Only existing teammates.** The table lists bots that already exist. Creating, archiving or rebinding bots is out of scope unless the user asks for it.
- **One owner per deliverable.** Each file has exactly one writer. Other roles read.
- **One reporting channel.** Only the controller reports to the user. Other roles report to the controller.
- **External developers are suppliers, not roles.** In the trial two AI coding tools built the web pages. They received briefs and returned files; they were not listed as team members.
- **Readiness receipts.** Each role confirms it has read the entry file and the frozen inputs and that their md5 values match the freeze list. The controller marks a role ready only after its receipt arrives.

## 2. Record authorization

- Ask the user through a selection card or a direct question in chat. Archive the answer verbatim with its date, the channel and the exact question it answered.
- A relayed approval ("the user said it is fine") is not an approval. Treat it as a stop condition and ask the user directly.
- Write down the limits that come with the authorization: budget, revision rounds, what may be sent outside, what may be published. Unused budget does not authorize extra rounds.
- If the bot's own wording ends up in a record as if it were the user's intent, correct it (see §6). Quote the user; paraphrase only with a label.

## 3. Dispatch

A dispatch brief states: goal, inputs (with md5 prefixes), output location and file list, acceptance criteria reference, limits (rounds, budget, time), what is out of scope, how to report completion, and the stop conditions.

- **Sending to an external developer is an external send.** Each batch goes to the reviewer first with the file list, md5 values and the full instruction text. Only after the reviewer clears it does the controller send.
- **Commands on the user's computer** are approved by the user one at a time. Ask for each command separately; do not bundle.
- **Background runs do not reliably announce completion.** In the trial two developer runs went to the background, finished within about three and a half minutes, and nobody caught it for over an hour. Use the host's task-status or completion mechanism when available. Create a one-off scheduled check-back only when the user explicitly requests or authorizes it; an estimate that a task is about to finish is not, by itself, authorization to create one. Otherwise, record the pending run and check it at the next normal interaction; do not create a scheduled task by default.
- **No scheduled task was created in the trial.** The initial run only drafted a one-off reminder and never created it. The 13 routine tasks checked during handoff already belonged to the executor role and were used only as check objects; this trial did not create or rebind them, and Orchivane did not generate them.

## 4. Freeze inputs with md5

- Before dispatch, write a freeze list: every input file with its md5.
- Re-check the freeze list before and after each acceptance pass. A mismatch stops the pass.
- In public copies cite only the first 8 characters of an md5 ("md5 prefix"), never the full value.
- **Frozen requirements and acceptance criteria must never be modified mid-run via a change record (CHG).** In our initial run, modifying frozen requirements and acceptance criteria via CHGs after the freeze caused Stage T2 to fail. In the user-authorized rerun from the freeze point, all 23 frozen files were locked with zero modifications (`23/23 OK` via `md5sum -c` throughout, with zero material-modifying CHGs); internal wording conflicts or sandbox screenshot limitations were handled by ruling from existing asset guides or grading the non-blocker item as fail (`✗`) under the original rubric rather than editing frozen files. If a new baseline is ever needed, back up the old files and establish a separate freeze list for the new run rather than editing frozen files in the current run.

## 5. Change through change records (CHG)

Every adjustment to execution plans, dispatch scope, or runtime limits gets a numbered CHG file (note: frozen requirements and acceptance criteria remain locked within a run; in the rerun from freeze, both builders stayed strictly within the two-round cap and passed acceptance in Round 2). A useful template:

1. Goal and status (draft / reviewed / approved by the user).
2. Sources: the archived user quotes that justify the change.
3. Scope: exactly what changes, and only that.
4. What does not change.
5. Questions for the reviewer.
6. Budget and stop conditions.
7. Task table: who does what next.

**Exceptions are CHGs too.** When the user approves going past a limit (for example an extra revision round), write it as a CHG that cites the user's quote. Leave the original rule text unchanged and state that the exception does not set a precedent. In the trial two extra rounds were handled this way, and the second exception explicitly ruled out any further round.

## 6. Keep an evidence log

One file, one row per event:

| ID | Time | Who | What happened | Evidence (file, md5 prefix, quote) | Result |
| --- | --- | --- | --- | --- | --- |

- Never delete or rewrite a row. A correction is a new row that points to the old one. Corrections to an archived quote go into a separate errata note; the archive itself stays unchanged.
- Mark who observed each fact and where (the user's computer or the bot's cloud workspace).
- Keep "done", "technically checked", "accepted" and "delivered" as separate events. One is never evidence for another.

## 7. Acceptance

- The controller grades every criterion: pass ✓, fail ✗, cannot judge ?, not applicable —. Recount totals each round instead of carrying them forward.
- Put a short red-line group first. Failing any red-line item fails the version, whatever the other scores are.
- Say where each measurement was taken. In the trial, measurements in the bot's cloud workspace used fallback fonts and were treated as reference only; the user's computer was authoritative.
- Separate the developer's self-report from what the team verified. If the team fills in a value the developer could not report, label it as team-filled.
- Subjective items (look and feel) can be scored independently by two roles. If an item is carried over from a previous round without rescoring, say so.
- "All data checks pass" and "the intended effect was achieved" are different statements. Record both.
- Screenshot settings must match the page width being judged. Headless browsers can enforce a minimum window width wider than a phone viewport, which crops or pads the image. Check the image dimensions against the intended viewport before grading from it.

## 8. A reviewer that only reviews

- The reviewer reads, checks and scores; it does not produce deliverables or run tasks.
- Every risky action passes the reviewer first: external sends, publishing, edits to settings or skills, deletions.
- A simple score scale works: in the trial, 8 meant "minor fixes needed" and 9 meant "pass".
- A reviewer pass is not user approval. A reviewer addition that the user rejects is withdrawn and recorded as withdrawn.
- The reviewer is the right place to catch attribution errors, for example the bot's own wording recorded as the user's intent.

## 9. Handoff and health check

The initial run and the rerun each performed one **simulated handoff** and one **read-only health check** (following [handoff](../skills/orchivane/references/handoff.md) and [health check](../skills/orchivane/references/health-check.md)). The two handoffs had different results and are reported separately:

| | Initial T4 | Rerun T4R |
| --- | --- | --- |
| Key files verified | 8/8 | 9/9 |
| Verification questions | 7/7 | 7/7 |
| Handoff receipt | Receiver replied in text only, relayed by the executor role; no receipt file written by the receiver | Receiver wrote the receipt file itself |
| Pre-handoff directory snapshot | Not taken | Taken, and compared with a post-handoff snapshot |
| Verdict (by the trial's own criteria) | PASS with caveat (P-02) | PASS |

- **Simulated handoff (observed in rerun T4R):** the controller prepared handoff package v1, a key file list, verification questions and a sealed answer key, and took snapshots before dispatch. A freshly spawned temporary helper subagent with a clean context read the handoff files and frozen inputs read-only, ran `md5sum` on the key files itself (9/9), answered the questions (7/7), and wrote its handoff receipt directly to a file. The controller graded the receipt and saved handoff package v2 (`Accepted`). The two initial-run issues (no receipt written by the receiver, no pre-handoff snapshot) were corrected in T4R; the initial-run record is kept as it was.
- **What the T4R snapshot compared:** md5 values of the 259 files that already existed in the rerun folder before the handoff, taken before and after. **No unexpected change was found in the monitored existing files.** The files allowed to be added or changed (the receipt, handoff package v2, the post-handoff snapshot and the routine task exports) were written to a separate handoff folder and were not among those 259 files. A read-only export of the executor role's 13 routine tasks was also compared before and after, with no change.
- **Scope boundary:** this was a temporary-subagent simulated handoff: no conversation archiving, no routine rebinding, and no permanent owner switch. A long-lived role actually taking over and continuing the work was not verified.
- **Read-only health check (once in each run):** a snapshot was taken before the check, all referenced source file md5 values were recalculated live, and items H1–H11 were audited one by one (single owner per deliverable, entry/handoff consistency, 4-step acceptance timestamp ordering, zero edits to frozen inputs, `.bak`/`.diff` reversibility, routine task consistency, tool and spend boundaries, verbatim user authorization archives, no orphan tasks, cross-machine copy consistency, and honest reporting of tool defects). In rerun T5R, before/after snapshots of the 893 files in the trial record folder, **excluding the health check report and the snapshot files themselves**, showed no change in the monitored files. **Scope boundary: strictly read-only inspection (inspect and report only, never silently edit files), with no recurring scheduled health checks and no waking of idle roles.**
- **How scope was determined:** the commands used to take the two snapshots were not archived at the time; the comparison scope above was reconstructed from the snapshot files themselves.

## 10. Before publishing anything from the records

Raw records contain private details. Before quoting them in public, remove names, machine details, local paths, IDs, ports, full hashes, accounts, costs and locations, and replace role titles with generic roles. Public copies give dates only, not clock times. Then scan the text once more.
