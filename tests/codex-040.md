# Orchivane 0.4.0: native Codex loading and handoff

[简体中文](codex-040.zh-CN.md) · [Evidence index](../docs/evidence.md)

Date: 2026-10-22 (Asia/Shanghai). Subject: installed plugin 0.4.0 from `d59ad6431709f00006517ffe18c0507ea8a75578`. Two fresh native Codex chats completed four bounded turns using the configured default, observed as `gpt-6.1-sol` / `high`. No model override or hard token cap was used.

## Result

**The tested Codex loading, read-only takeover, continuation and serial duplicate-dispatch paths passed. One source-record defect was retained and corrected by the evaluator. This is bounded evidence, not proof of complete nonregression.**

The plugin was already installed and enabled at the requested version before the run. Its installation receipt pointed to the merged commit, and all eight installed skill files matched source bytes. No reinstall, restart or unrelated plugin change was needed; this run did not observe the upgrade transition.

| Check | Observed result |
| --- | --- |
| Fresh-chat loading | Both chats actually read the installed 0.4.0 entry, setup, handoff and Codex modules; the execution turn also read dispatch. Neither used the Claude adapter |
| A1 preparation | Exactly one apply, two rows totaling 5; all five existing S3 checks passed |
| Read-only successor acceptance | All 41 project files, including Git files, unchanged; 21 preservation manifest entries checked and readable |
| Ownership and continuation | Evaluator checked acceptance before switching sole ownership and replacing input with R2; A2 applied once, three rows totaling 9; five S3 checks passed |
| Identical repeated dispatch | Same prompt bytes; no business-script call; ledger remains A1 then A2 and all eight non-coordination project files retain their hashes |
| Final current records | Both index and H040 show 4/4 used, no further execution, and evaluator as next acceptance/publication owner; only these two records changed during the duplicate turn |

The four native turn durations sum to 616.395 seconds. This is cumulative solver time, not wall time or human coordination time. No old-version control arm was rerun, and no token or efficiency comparison was made.

## Retained defect and correction

The source index used `../preservation` from `project/docs`, while the working relative path was `../../preservation`. Its absolute preservation entry was correct, all copies were present and readable, and this did not block takeover. The successor's read-only receipt did not flag the path defect. The evaluator preserved the source snapshot, corrected current guidance during the ownership switch, and recorded the intervention; subsequent successor records carried the correction forward. This does not retroactively make the original source record correct.

The earlier 0.3.2 pilot had conflicting instructions about whether the successor could update final records. This run froze a clear boundary: initial acceptance is wholly read-only; the evaluator owns the switch; execution and duplicate closure may update only the permitted business outputs and/or coordination records. Final consistency passed under that clarified protocol, which is not evidence that a skill change fixed the earlier failure. No skill or manifest was changed during this run.

An evaluator-only history request initially exceeded the tool's 20,000-character output limit and was corrected. It had no business effect and consumed no solver turn.

## Reproduction and published evidence

The [plan](outputs/v0.4.0-codex/plan.json) was frozen before creation: two chats, four turns, no retries, dependent phases stop on failure. The [sanitized prompts](outputs/v0.4.0-codex/prompts.json) record the actual task instructions. Explicitly naming Orchivane tests discovery and use on request, not implicit selection. The initial source prompt supplied no installation path or expected version; the source put its discovered path in the handoff package, which the successor could read.

Use an isolated Git lab and the unchanged [recovery script](fixtures/recovery/report.py). Commit an initial configuration, then leave `label=keep-local-change` uncommitted and place input under ignored `.runtime/`. The source executes A1, prepares the package and independent copies, then stops. A clean successor checks actual files without running the script or writing anything. The evaluator verifies unchanged hashes, switches ownership and replaces the input; the successor receives A2 and then exactly the same request again. Every request consumes one of four turns. No fifth turn, schedule, archive, peer messaging or network operation is authorized to the solvers.

- [Results](outputs/v0.4.0-codex/results.json): phase durations, actual module reads, checks and retained limits.
- [Installation hashes](outputs/v0.4.0-codex/installation.json): eight files and the already-installed state.
- [Business artifacts](outputs/v0.4.0-codex/artifacts.json): A1/A2 text and hashes, plus before/after duplicate hashes.
- [Sanitized coordination records](outputs/v0.4.0-codex/records.json): source, A2 and final solver records, including superseded history.

For offline replay, materialize each artifact's `files` in a temporary directory, verify its `sha256`, and run `python tests/paired/grade.py S3 <directory> --phase 1` for A1 or `--phase 2` for A2. Check the JSON `passed` field. The added unit test automates both replays and the published duplicate hash comparison; it does not reproduce native chat behavior. Original tool receipts, chat IDs, absolute personal paths and local preservation material remain private. Published records are sanitized derivatives, not authenticated raw exports.

## Repository verification

Static package/link/privacy checks passed (117 files scanned), all 25 unit tests passed including the new artifact replay, and `git diff --check` passed. A final comparison still matched all eight installed skill files to source. READMEs in both languages, compatibility, evidence and evaluation entries were synchronized. Skill code, manifests and frozen historical experiments were unchanged.

## Limits and next owner

One Chinese-language chain ran on one account with other plugins enabled; traces include Superpowers and Ponytail reads. Detailed prompts supplied budgets and phase boundaries. This neither isolates the skill's causal effect nor establishes reliability, implicit activation, English behavior, lower human cost or all Codex capabilities. No Claude runtime, real archival, concurrent writers, scheduling, crash or transport recovery was tested. Independent copies cover A1 materials and were checked for readability and equality; they are not a full Git backup, an A2 snapshot or proof of survival after archival.

The evaluator accepted the final functional results and recorded closure separately from solver output. The next owner is the maintainer for any new scoped validation; no further solver work is authorized by this run. Both test chats remain available and were not archived. Historical 0.3.2 and Claude evidence remains unchanged.
