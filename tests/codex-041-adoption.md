# Codex 0.4.1: installed-plugin adoption and receipts

[English README](../README.md) · [简体中文说明](../README.zh-CN.md) · [Evidence index](../docs/evidence.md)

Date: 2026-10-22. This follow-up uses the merged 0.4.1 plugin and native Codex chats, rather than the temporary-agent/simulated-state exercise in [the earlier report](adoption-upgrade.md). The maintainer authorized PR #2 review/merge, a local plugin upgrade and isolated new-chat validation; existing projects are outside the test scope.

## Review and installation

PR #2 was independently reviewed at `2693363`. One important maintenance defect was reproduced: the historical evidence test unconditionally pinned future source versions to 0.4.1. Commit `6d7d625` scoped current-source comparison to the recorded version and added a future-version regression, retaining unconditional artifact checks. The maintainer checked that narrow correction; all 29 offline tests and both PR CI runs passed. PR #2 then merged at `b613abdf58a7b182a9ed2e1a3532688db6fb9723`.

The operator used Codex CLI 0.157.1 to refresh only the existing Orchivane marketplace and run its normal plugin installation command. Installed/enabled state changed from 0.4.0 to 0.4.1, with one active Orchivane entry. All nine installed skill files matched the merged source; the other 27 installed-plugin records and the global configuration bytes were unchanged. No standalone skill copy or application restart was added.

**The native upgrade removed the old 0.4.0 cache.** Before the update, 138 old-package files had been independently copied and hash-checked outside discovery directories. The post-update old-path preservation check failed because the old directory had disappeared. The operator restored all 138 files at the original path and verified their hashes, while leaving the active registration on 0.4.1. This is a successful restoration, not continuous old-path availability. No existing project chat was messaged or restarted; whether any old chat attempted a read during that absence was not inspected. Therefore this run does not establish an uninterrupted upgrade for active projects.

## Frozen native protocol

Two projectless native chats, four total solver turns, one attempt per phase, with no model override or hard token/cost cap. The observed default was `gpt-6.1-sol` / `high` in both chats:

1. Data role performs ordinary N1 on a two-row CSV and writes its summary/receipt; no adoption campaign is requested.
2. A fresh controller adopts the existing project/role using the declared installed Orchivane skill, verifies the N1 delivery and reviews a labeled synthetic stale/partial source receipt. It saves an N2 addendum without messaging the idle data role.
3. The operator dispatches ordinary N2 to the same data chat. That role reads the agreed entry/modules, summarizes a three-row CSV and writes its own scoped receipt.
4. The operator requests controller acceptance in the same controller chat. It reads actual artifacts and native read evidence, then reconciles the sole current index and remaining gaps.

Initial prompts supply no installed entry path; discovery comes from the new chat's declared skill catalog. The controller may inspect only the registered test role's native history. Solvers cannot create/message/archive chats, alter scheduling/installation/configuration, call business providers or access other projects. The data role writes only its two assigned outputs per task; the controller owns coordination records. Inputs, accepted frozen material, configuration, registration and old receipts remain protected. A failed discovery, ownership or preservation check stops dependent phases; there are no repair turns.

The stale/partial receipt is explicitly synthetic: it reports 0.4.1 but references preserved 0.4.0 bytes with no module/task evidence. It is not represented as an actual claim by the native data role. N1 and N2 business results must be real, not simulated transitions.

## Native outcomes

**The bounded adoption, source/version verification and task-receipt paths passed. The uninterrupted-upgrade requirement is not fully established because the native updater removed the old cache before restoration.**

| Phase | Observed result |
| --- | --- |
| Ordinary N1 | Actual saved summary: two rows, total 5. Only the two assigned outputs added. The worker read other declared skills but did not read Orchivane or claim adoption |
| Controller adoption | Declared installed 0.4.1 entry and setup/adoption/dispatch/health-check/codex actually read; manifests, install revision and hashes checked. Real N1 independently accepted. Synthetic 0.4.1 label rejected because its entry is 0.4.0. Eleven original files unchanged; N2 brief saved without waking the idle worker |
| Ordinary N2 | Same data chat received its normal business task, read the installed entry plus setup/adoption/dispatch/codex, and added only its N2 summary and scoped receipt. Three rows, total 9; all 15 previous files unchanged. Controller acceptance remained pending |
| Controller acceptance | Same controller inspected actual artifacts and the worker's native N2 history, accepted business and read-action evidence separately, and updated its sole index/review records. Fifteen protected files unchanged; final state closed at 4/4 with no further execution allowance |

The operator independently recalculated both CSV results, checked before/after hashes and reviewed native commands and final records. Data-role N2 did not edit the central index. The final controller retained earlier pending states and marked their supersession rather than rewriting old receipts or the synthetic input. Both completed test chats remain idle; they were not archived.

Native history retrieval truncated two long outputs during controller acceptance. The report explicitly retains 4,312 trailing module-output characters not directly recovered in that review. Successful read commands, original output lengths, visible prefixes and matching current-source hashes support the read-action conclusion; this is not a complete audit of the retrieved module text or proof of understanding every rule. Reachability/hash checks on unused references are not counted as content loading or behavioral validation.

The four native `durationMs` values total 781.485 seconds. This is cumulative solver execution time, not full wall-clock time, human coordination time or a cost estimate. There were no repair turns or business-provider calls. Standard assistant inference still consumes account resources; no hard token cap or actual billing measurement was available.

## Evidence and replay

- [Frozen plan](outputs/v0.4.1-native-adoption/plan.json), [redacted input records](outputs/v0.4.1-native-adoption/prompts.json) and [phase results](outputs/v0.4.1-native-adoption/results.json). N1's input is the native `read_thread` preview; the other three are the operator's saved dispatch inputs, with provenance marked in each record.
- [Installation comparison](outputs/v0.4.1-native-adoption/installation.json): nine source hashes, target enablement and the old-cache deletion/restoration limitation. Full private plugin inventories and configuration contents are not published.
- [Project artifacts](outputs/v0.4.1-native-adoption/artifacts.json): input to adoption, post-adoption, post-N2 and final snapshots, including scoped receipts and the reconciled index. Hashes identify sanitized derivative bytes; they are not authenticated raw chat exports.
- [Visible native evidence](outputs/v0.4.1-native-adoption/trace-evidence.json): phase durations, observed model settings, visible messages and selected read/native-tool calls. Private paths and real chat/turn IDs are replaced with placeholders; original native receipts remain local.

The replay checks published hashes, protected-file preservation, the worker's exact two-file addition and both CSV calculations. It does not rerun model behavior, loading or installation:

```sh
.venv/bin/python -m unittest discover -s tests -p 'test_adoption_evidence.py' -v
```

With this native replay included, all 30 offline tests, the static package checks and skill-schema validation pass locally. The offline suite does not create chats or call models.

For a new native run, use a new isolated shared directory and fresh chats with explicit creation/dispatch authorization. Preserve old installed sources independently before package replacement and understand the host's cache cleanup first. Create the data role for N1, register its actual returned ID, then create the adopting controller. Keep the synthetic stale receipt separate from the genuine worker receipt. At the ordinary N2 boundary, use the saved controller brief; after delivery, have the controller verify and reconcile its own records. Record each native result separately and stop at the frozen limit. Never use the published placeholders to contact the original owner's chats.

## Limits

This is one explicitly requested workflow on one host, with other plugins available and detailed role/permission/task boundaries. It does not isolate a skill effect, measure coordination savings, establish implicit skill selection or test Claude Code. No real concurrent writer, interrupting delivery probe, archive, schedule, crash or production task was exercised. Restoring the old cache after the native updater removed it cannot prove that active projects experienced no interruption.

中文摘要：PR #2 经审查补修历史测试耦合后已合并，本机插件从0.4.0升级为0.4.1，九个技能文件与合并源码一致。两个新原生对话完成四轮，接入、旧版回执识别、普通任务实读与独立验收通过，最终索引收口为4/4。升级器曾清除旧缓存，138文件虽已完整恢复，仍不能承诺旧路径全程可用或现有项目绝对未受影响；未向现有项目发消息或重启对话。
