# Grok Bot Field Trial Report: Coordinating a Multi-Agent Team with Orchivane (Initial Run & Rerun from Freeze)

This document records a real-world field trial of `orchivane` running on a **Grok Bot** multi-agent team, covering both **Part 1: Initial Run (T1–T5)** and **Part 2: User-Authorized Rerun from the Freeze Point (T2R–T5R)**.

> **Status:** This is a contributor-reported field trial report and has not been independently reviewed by the maintainers. Every `PASS` / `FAIL` in this document is a judgment against this trial's own acceptance criteria. It does not mean that upstream has certified Grok Bot compatibility, and it does not claim stable Grok Bot support. Supplementary validation done on 2026-10-24 is reported separately in §6 and is not written back as historical receipts.

Before submission, all personal names, local file paths, machine IDs, session IDs, wall-clock timestamps, full file hashes (only the first 8 characters are kept), personal business identifiers, and internal role nicknames were sanitized. The submitter signature is kept as **大冰**.

---

## 1. Environment & Team Setup

### 1.1 Environment table

| Item | Record |
|---|---|
| Orchivane version and source | 0.4.1, repository `alexzhu0/orchivane`, commit `f1b45702` |
| Modified copy used? | **Yes.** Roles referred to a team-written internal reference (a summary with team-specific limits, such as no implicit invocation and reviewer sign-off for risky actions). A read-only copy of the original `SKILL.md` and all 7 references was kept alongside it; its md5 values match the commit above |
| Loading / reading method | Manual reading. No plugin was installed; auto-discovery and auto-loading were not used (both not verified) |
| Modules read | The controller read and cited the original dispatch, handoff and health-check modules when writing change records, the handoff plan and the health check report. Other roles received the location of the team reference in the "background" section of their dispatch briefs and read it as needed. **Whether each role read the original modules was not recorded at the time** (contributor-reported, not independently reviewed by maintainers) |
| Grok Bot service setup | Shared cloud workspace + one registered local computer (every local command needed explicit in-person user approval); dispatch and receipts used Grok Bot's built-in send-to-teammate message tool |
| Grok Bot version | No version number provided (not shown by the service) |
| Test date | 2026-10-23 (initial run and rerun on the same day) |
| External builders | Two local AI coding tools built the website; they are not required dependencies for using Orchivane. Versions, spend and other details are in Appendix A |

### 1.2 Team topology

- **5 registered long-lived roles** (role table in the collaboration entry file):
  - **Controller:** Clarifies requirements, prepares dispatch packages, performs independent acceptance checks in the cloud browser, and maintains collaboration records.
  - **Content:** Writes the requirements and acceptance criteria.
  - **Design/layout:** Writes the layout requirements and prepares the cover background images.
  - **Technical executor:** Invokes the external builders, runs commands on the local computer (with per-command user approval), and performs read-only technical inspections.
  - **Reviewer:** Performs independent reviews before and after key milestones (setup, freeze, dispatch, change requests, acceptance, handoff, health check, and public PR drafts); reviews only and does not do the work.
- The rerun reused the requirements and layout frozen in the initial run, so **the content and design/layout roles produced nothing new in the rerun**.
- **Compliance:** A compliance role reviewed the public drafts once for privacy and sensitive data before submission. It was not registered in the role table.
- **The user** sits above all roles and makes every final decision.
- **External Builders A and B:** two local AI coding tools, listed separately as suppliers, not team roles (see Appendix A).

### 1.3 Task

Build a responsive, offline-capable single-page magazine-style directory website with category filtering and typographic cover cards from a curated table of 13 public articles (7 fields each) and 8 local cover background images, testing both external builders against the exact same frozen inputs and 77-item acceptance checklist, followed by a simulated handoff and a read-only health check.

### 1.4 Sanitized excerpts from the original records

The excerpts below come from the records made at the time. Only role names, paths, file names and internal terms were replaced, and hashes and clock times were removed; nothing else was changed. The originals are in Chinese; the English is a translation. Full conversations, private folders and business material are not published.

**Readiness receipt (initial T1, message from the design/layout role to the controller, items 1 and 3):**

> 1. Role: sole owner of the layout spec. The layout spec is section 8 of the requirements file, "Layout requirements (added by [design/layout role])"; the other sections are not mine.
>
> 3. Where I may write: only section 8 of the requirements file, and only after T-01 is accepted, with a backup first; read-only after the freeze. The background image pack was made by me, but it counts as frozen material this time, so I will not change it.

This receipt was sent with Grok Bot's built-in send-to-teammate message tool, which returned "sent". It is the original message found afterwards in the sender's conversation history, not a later resubmission.

**Handoff receipt (rerun T4R, file written directly by the temporary helper subagent, excerpt):**

> **Comparison result: the measured md5 values of all 9/9 key files match the handoff package and the key file list exactly (zero deviation).**
>
> This run strictly followed the red lines: it read only the 3 handoff package entry files, the 9 key files, and the 7 related source files explicitly cited by the handoff package (19 files in total); it **never read** any answer key, grading or verification-result file in the handoff folder or any initial-run handoff file, and kept every file it read strictly read-only.

Note: "zero deviation" and "never read" are the receiving party's own claims (self-reported); see the scope notes under the table in §3.

**Health check output (rerun T5R health check report, excerpt):**

> Snapshot `diff -u` result: 0 bytes (apart from the health check's own output files, the other 893 files under the trial record folder had 100% zero changes).

Note: this is the report's original wording. The accurate reading is "no change was found in the 893 monitored files before and after the health check"; see the scope notes under the table in §3.

**Repository check output (contributor's local copy, 2026-10-23):**

```text
OK: static package checks passed (138 files scanned).
Ran 30 tests in 2.043s
OK
```

Note: this only covers the repository's existing static checks and unit tests. It does not verify Grok Bot native behavior.

---

## 2. Why Both an Initial Run and a Rerun from Freeze?

1. **What Went Wrong in the Initial Run (T1–T5):**
   - T1 (Team Setup) passed cleanly. However, after freezing the 23 input files in T2, the team encountered two issues in the original frozen files during T3: (a) an internal width discrepancy for Cover #05 in `requirements.md` (`900` in the table vs `960` in prose), and (b) item `G3` in `acceptance.md` requiring builders to self-capture two PNG screenshots inside their delivery folder (which failed due to missing browser tools in Builder A and a headless Chrome sandbox crash with exit code 134 in Builder B).
   - Instead of keeping the frozen files immutable, the initial run issued `CHG-002` and `CHG-003` to modify the already-frozen `acceptance.md` and `requirements.md`, and overwrote two early log files without prior `.bak` backups.
   - Consequently, **Initial T2 was graded FAIL**, and Initial T5 (`HEALTH-001`) logged three findings: `P-01` (Major), `P-02` (Moderate), and `P-03` (Minor).
2. **User-Authorized Rerun from Freeze (T2R–T5R):**
   - After reviewing the initial findings, the user authorized a rerun from the T2 freeze point under the strict principle of **keeping the original test plan and frozen materials completely untouched**.
   - All 23 original frozen files were locked read-only (`23/23 OK` via `md5sum -c` throughout the rerun, with **0 edits and 0 material-modifying CHGs**). The Cover #05 width conflict was resolved by ruling `900` from the asset guide without editing `requirements.md`, and `G3` was graded strictly as **FAIL (`✗`)** (a non-blocker item) for both builders without editing `acceptance.md`.

---

## 3. End-to-End Comparison: Initial Run vs. Rerun from Freeze

`PASS` / `FAIL` in this table are judged against this trial's own acceptance criteria.

| Stage | Initial Run (T1–T5) Outcome | Rerun from Freeze (T2R–T5R) Outcome |
|---|---|---|
| **T1 Team Setup** | **PASS**: Roles, single-owner assignment, entry file, budget cap, and local computer approval rules established. | **Carried over as PASS**; entry file upgraded to v4 in R-R21 with full `.bak` backup, `.diff`, and `patch --dry-run` verification. |
| **T2 / T2R Freeze & Dispatch** | **FAIL**: Frozen `acceptance.md` and `requirements.md` were modified post-freeze via `CHG-002` and `CHG-003`. | **PASS**: All 23 frozen files verified **23/23 OK** (`0` modifications, `0` material CHGs); dispatch packages reviewed by the controller and reviewer before user-approved execution. |
| **T3 / T3R Dual-Builder Iterations & Acceptance** | **Conditional (compromised by post-freeze rubric edit)**: Builder A stopped after 2 rounds; Builder B ran 3 rounds (extended to v5) and scored 71 pass / 0 fail / 5 subjective pending / 1 N/A under the modified rubric. | **PASS (strictly within the 2-revision cap and original 77-item frozen rubric)**:<br>• **Round 1 (v1)**: Builder A v1 scored 61 pass / 7 fail (4 Group-A blockers) / 8 undetermined / 1 N/A; Builder B v1 scored 63 pass / 5 fail (1 Group-A blocker) / 8 undetermined / 1 N/A.<br>• **Round 2 (v2, 1st revision)**: Both Builder A v2 and Builder B v2 achieved **16/16 Group-A blockers PASS**, and identical overall scores of **67 PASS / 1 FAIL (only G3) / 8 Undetermined (3 external link checks + 5 subjective visual items) / 1 N/A**.<br>• **User Final Selection (Step ④)**: Following the strict 4-step sequence (① Builder delivery → ② technical executor read-only tech check → ③ controller acceptance & side-by-side comparison → ④ User final selection), completed in order, the user selected **Builder B v2** as the final adopted version, with Builder A v2 archived for reference. |
| **T4 / T4R Simulated Handoff (`HO-001` / `HO-001R`)** | **PASS with caveat (`P-02`)**: Helper answered 7/7 questions and checked 8/8 files, but the receiver did not write the receipt file itself (it was relayed by the technical executor), and no pre-handoff directory snapshot was taken. | **PASS (both initial-run caveats corrected in the rerun)**: the controller wrote `HO-001R_v1` and took a pre-handoff snapshot; a fresh helper subagent independently verified **9/9 key file hashes**, answered **7/7 verification questions**, and **wrote the receipt file itself**; before/after comparison of 259 existing files and the 13-item routine task list **found no change** (scope below the table); closed as `HO-001R_v2` (`Accepted`). This was a temporary-subagent simulated handoff. |
| **T5 / T5R Read-Only Health Check (`HEALTH-001` / `HEALTH-001R`)** | **PASS**: Audited H1–H11 read-only and logged `P-01`, `P-02`, and `P-03`; no files were changed during the check. | **PASS**: Audited H1–H11 read-only, checked that `P-01`–`P-03` were corrected in the rerun, and before/after snapshots of 893 files **found no change** (scope below the table). |

**Snapshot comparison scope:**

- **T4R, 259 files:** all files that already existed in the rerun folder before the handoff, compared by md5 before and after. No unexpected change was found in the monitored existing files. The files allowed to be added or changed (the receipt, handoff package v2, the post-handoff snapshot and the routine task exports) were written to a separate handoff folder and were not among those 259 files. The 13 routine tasks already belonged to the technical executor and were used only as check objects; this trial did not create or rebind them.
- **T5R, 893 files:** the whole trial record folder at the time of the check (including the handoff and rerun folders), excluding the health check report and the snapshot files themselves. After the check, two files (the evidence log and the checksum list) were updated as normal, so the result means "no change before and after the check", not "unchanged to this day".
- The commands used to take the two snapshots were not archived at the time; the scope above was reconstructed from the snapshot files themselves.

---

## 4. Observations from this initial run and rerun

1. **Frozen inputs:** In this initial run, the acceptance criteria and requirements were changed through change records after the freeze, and the run was graded FAIL. The rerun locked the md5 values of the 23 frozen files, issued no material-changing change records, and kept `G3` as `✗` under the original rubric. This is an observation from this single-team, single-task initial run and rerun, not a general causal conclusion established by a controlled experiment.
2. **Four separate steps:** This rerun recorded four separate steps: delivery, technical check, acceptance and the user's final choice; adversarial collusion was not tested. In round 2 of the rerun, the two versions tied on the objectively judged items; the controller provided a side-by-side comparison, and the user chose Builder B v2.
3. **Handoff:** The temporary subagent passed 9 file checks and 7 verification questions, which supports the readability of the handoff package in this simulation; a long-lived role taking over and continuing the work has not been verified. The two items missing in the initial run (a receipt written by the receiver and a pre-handoff snapshot) were added in the rerun.
4. **Backups and diff records:** This trial used backups and diff records (`.bak` first, a `.diff`, and `patch --dry-run` verification), and no overwrite of the same kind was observed within the checked scope; this is not a guarantee for future runs.

---

## 5. Limitations, Evidence Gaps and Items Not Yet Verified

### 5.1 Limitations & Boundaries Disclosed (6 Items)

1. **Single-Team Sample Size:** Results come from one user and one multi-agent setup across two runs (initial + rerun) and should not be over-generalized.
2. **Initial Run Post-Freeze Rubric Edit (Corrected in Rerun):** The initial run's T2 failure is disclosed transparently alongside the rerun (frozen materials: 23/23 md5 unchanged, no material-changing change records).
3. **Non-Blocker Item `G3` Remains `✗` Under Original Rubric:** Neither external builder could capture screenshots in its environment (details in Appendix A); `G3` is honestly graded `✗` rather than patched out of the rubric, and acceptance screenshots were taken independently in the cloud workspace.
4. **8 Items Left as Undetermined (`?`) by Rule:** 3 external link items (`B11`, `C9`, `D8`) were not clicked per safety rules, and 5 subjective visual items (`F6–F10`) were left for the user's final selection.
5. **Simulated Handoff to a Temporary Subagent:** T4R verified the readability of the handoff package in this simulation (9/9 file checks, 7/7 questions, receipt written by the receiver) via a fresh subagent context, without permanently switching role ownership, archiving conversations, rebinding routine tasks or creating live scheduled jobs; the one-off check-back was only drafted, never created.
6. **No Second Cross-Machine Re-Audit During T4R/T5R:** After verifying hashes upon copying v2 deliverables from the local computer, T4R and T5R operated strictly inside the cloud workspace without touching the user's local machine again.

### 5.2 Evidence gaps (not recorded at the time, or not publishable)

- Whether each role read the original Orchivane modules: no receipt; not recorded at the time.
- Grok Bot version: not provided by the service.
- The technical executor's initial readiness receipt was not found verbatim; the reviewer's readiness receipt survives only as a summary, not the original.
- The initial run's evidence log has a gap of about 1 hour 45 minutes.
- No pre-handoff snapshot was taken in initial T4.
- The commands used for the two snapshots were not archived.
- One module checksum cited in the rerun health check report matches no copy; it is a recording error and is not cited here.
- Full conversations, private folders and business material are not published; only the sanitized excerpts above are. All conclusions above are contributor-reported and have not been independently reviewed by maintainers.

### 5.3 Not yet verified

The following were not verified in this trial and are left for future work: native plugin install / auto-loading; real long-lived role takeover and archiving; recovery from interrupted runs; repeated dispatch; continued readability of old sources during upgrades.

---

## 6. Supplementary validation (2026-10-24)

> This section reports a small test run separately on 2026-10-24. It does not change the 2026-10-23 historical record above. As elsewhere, `PASS` here is judged only against this test's own pre-set criteria and does not mean that upstream has certified Grok Bot compatibility. Post-run check by the reviewer bot: PASS.

### 6.1 Purpose

Following point 3 of the maintainer's second comment, a small Grok-Bot-only scenario was used to check three things: whether an executor bot can manually read Orchivane at a pinned version and confirm readiness with a receipt; whether the "dispatch → artifact → receipt → controller check" loop works again with a different input; and whether, on a missing input, the executor stops without making up results and then resumes under the same task ID once the input is supplied.

### 6.2 Configuration

| Item | Record |
|---|---|
| Orchivane | 0.4.1, `alexzhu0/orchivane` commit `f1b45702`; the executor bot read `SKILL.md`, `references/setup.md` and `references/dispatch.md` from the read-only original copy (manual reading, no plugin installed) |
| Roles | One controller bot (the only dispatcher) + one executor bot, both existing Grok Bot teammates on the team; no new bot was created |
| Dispatch | Grok Bot's built-in send-to-teammate message tool; each dispatch message was archived before sending, and the executor bot's replies were archived verbatim |
| Write scope | Test root `<TEST_ROOT>`; the executor bot could write only to `03_产出/` (outputs) and `04_回执/` (receipts); writing anywhere else counted as a failure |
| Inputs | Three fictional CSV files (below); the correct answers were computed and sealed by the controller in advance and not shown to the executor bot |
| Evidence | md5 snapshots of `<TEST_ROOT>` before and after each step (the snapshot commands were archived); new files listed against a timestamp marker; per-step check notes, a results table and a message count |
| Not involved | Local computer, external builder tools, business material, scheduled tasks, paid services; cost 0 |
| Grok Bot version | No version number provided |

Fictional inputs (two columns each: task name, estimated minutes; shown here in English, the files are in Chinese):

- `T-01_清单.csv`: tidy the bookshelf 20 / water the plants 10 / write a shopping list 15
- `T-02_清单.csv`: wash the dishes 15 / fold the laundry 25 / take out the trash 5
- `T-03_清单.csv`: wipe the table 10 / feed the cat 5 / pick up a parcel 20 (deliberately absent at the start)

Each task: count the data rows, sum the minutes, find the longest item, and write the result to `统计.md` (summary).

### 6.3 Steps and results

| Step | What | Result |
|---|---|---|
| 0 | Preparation: place the T-01 and T-02 inputs, seal the answers, take the initial snapshot, confirm that T-03 is absent | PASS |
| 1 | Loading and readiness (`ORV-L0`): in its own conversation, the executor bot read the three original files above, computed their md5 values itself, and wrote a receipt with the version, source commit, file md5 values, its duties, writable folders and stop conditions | PASS: version 0.4.1, commit `f1b45702`; the three md5 values `a445042a` / `3ec6967c` / `2b9342df` match the archived copy; duties and stop boundaries complete |
| 2 | Normal closed loop (`ORV-T01`, input T-01) | PASS: 3 rows / 45 minutes / longest "tidy the bookshelf" 20, matching the sealed answer; the receipt gives the task ID and the input and artifact md5 values; marked "done" only after the controller's check |
| 3 | Repeat with a new input (`ORV-T02`, input T-02) | PASS: 3 rows / 45 minutes / longest "fold the laundry" 25, matching the T-02 answer (not T-01's); the md5 values of the T-01 artifact and receipt were unchanged |
| 4 | Controlled exception: missing input (`ORV-T03`). The dispatch pointed to T-03, which did not exist yet, and did not mention that the file was missing | PASS: the executor bot stopped and wrote only a "blocked (missing input)" receipt; it created no artifact, made up no numbers and did not report completion; the T-01 and T-02 files were unchanged; the controller marked the task "pending" |
| 5 | Resume (`ORV-T03`, same task ID): the controller placed the T-03 input and sent a resume message | PASS: exactly one artifact, 3 rows / 35 minutes / longest "pick up a parcel" 20, matching the answer; the receipt keeps the blocked section first and appends a "completed after resume" section, and the controller's byte-level check found the md5 of the first section equal to that of the original blocked receipt; marked "done" only after the check |

According to the snapshot diffs, within the monitored folder `<TEST_ROOT>`, every file the executor bot added or changed in steps 1–5 was inside `03_产出/` or `04_回执/`. For what happened outside the monitored folder, see §6.5 item 1.

### 6.4 Message count

The controller bot sent 5 messages to the executor bot (one for each of steps 1–5) and 0 follow-ups, against a pre-set limit of 8 including follow-ups. The executor bot replied once per step, and the replies were archived verbatim. The request asking the reviewer bot for the post-run check is not part of the tested dispatch traffic and is not counted.

### 6.5 Deviations from the plan and other disclosures

1. **One temporary write outside the monitored folder:** in step 5, to check that the blocked section had not been altered, the executor bot copied the receipt to the system temporary folder outside the test folder, compared it there, and deleted the copy afterwards. The snapshots cover only `<TEST_ROOT>` and could not see this, so the receipt's statement that it "only wrote `03_产出/ORV-T03/` and the appended section of this receipt" is not fully accurate. Read literally, this was a write outside the allowed scope; judging by its purpose (verification only, no test or business folder touched, copy deleted), the reviewer bot did not count it as a failure. For this reason, every write-scope conclusion in this section is limited to "within the monitored folder".
2. **One extra snapshot:** the plan scheduled six snapshots, S0–S5. One more was taken after step 1 (loading), and the step 2 diff was taken against it (the diff against S0 is also listed separately).
3. **How T-03 was placed:** the T-03 input was copied in with a copy that keeps the original modification time (`cp -p`), so `find -newer` against the timestamp marker did not list it. A separate placement record (file name and md5) was archived. New files are determined from the snapshot diffs, not from `find -newer`.
4. **A change after S5:** S5 is the state at the end of step 5, not the final state of the test folder. Afterwards, the controller's message-count file was edited once more to record the message sent to the reviewer bot.
5. **Wording of the blocked receipt:** the receipt's own words were "受阻（缺输入）" ("blocked (missing input)"). This differs from the plan's wording "not done / pending: input missing", but the meaning is the same. "Pending" is the status the controller gave the task in its own records; it is not a quote from the receipt.

### 6.6 Limits

- Only one controller bot and one executor bot; multiple executor bots were not tested.
- Only one exception type, a missing input, was tested; "no receipt received" was not tested.
- A single run, each step once. Step 3 is a new task with a new input, not the same task dispatched twice; "repeated dispatch" and "recovery from interrupted runs" in §5.3 remain not verified.
- Write scope was checked only within the monitored folder; writes outside it are not visible to the snapshots (see §6.5 item 1).
- Contributor-reported; not independently reviewed by the maintainers.

### 6.7 One more observation

During the test, besides replying to the controller, the executor bot also sent progress messages directly to the user. The dispatch did not forbid this, and it does not affect the results above. Future dispatches should state that the executor role reports only to the controller.

Conclusion: repeatable in this configuration and these scenarios. This does not claim stable Grok Bot support and is not a compatibility certification.

---

## Appendix A: External builders (case background)

Two external AI coding tools built the website in this trial; they are not required dependencies for using Orchivane. The details below are case background only.

- **External Builder A:** Local Hermes Agent CLI (`v0.22.2` with a lightweight cost-effective model via pay-per-use API).
- **External Builder B:** Local Codex CLI (`v0.163.0-alpha.10.2`, covered by subscription).
- **Budget & Actual Spend:** User-approved total paid API cap of **100 CNY** (single-run stop line at **40 CNY**). External Builder A spent `~$0.054` USD across 2 rounds in the initial run (`$0.028146` + `$0.025603`) and `~$0.065` USD across 2 rounds in the rerun (`$0.040387` + `$0.024158`), totaling **`$0.118294` USD (`~¥0.86` CNY, under 1% of the 100 CNY budget cap)** across all 4 rounds. External Builder B used subscription quota (`196,316` tokens in the initial run; `81,668` tokens in the rerun [`47,296` + `34,372`]). Spend figures are the tools' own records.
- **Screenshot capability:** Builder A had no browser tool enabled; Builder B's headless browser crashed in its sandbox (exit code 134). That is why `G3` is `✗` for both versions.
- **Initial run:** Builder A stopped after 2 rounds because of per-round time and the layout gap (about `$0.054` spent); Builder B ran 3 rounds and was extended to v5.
- **Rerun final selection:** the user selected Builder B v2 (Codex) as the final adopted version, with Builder A v2 archived for reference.

---

*Submitted by: 大冰*
