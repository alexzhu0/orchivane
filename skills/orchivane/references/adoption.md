# Adopt or upgrade an existing project

Keep the existing controller, roles, authorization, budgets, local edits and frozen inputs. Read the current project rules and index through [setup.md](setup.md); record only the coordination changes needed for adoption. A workflow upgrade neither creates a new product task nor resets a stop condition. Installing or enabling the plugin is a separate action, requiring its own authorization and the host's supported mechanism.

## Establish the source and target

The controller records the desired version and why, then verifies the actual available source: declared skill path, `SKILL.md` metadata version and required references. For a plugin, compare its manifest version with the entry metadata when accessible. A source checkout or release page alone does not prove that version is installed. Use file hashes or a revision when copies, local customizations or mixed versions would otherwise be ambiguous; do not compare version labels alone. Preserve customizations before proposing a replacement. Do not silently choose between multiple active copies.

Keep these observations separate:

| Observation | Evidence and limit |
| --- | --- |
| Available / installed | Actual host catalog or installation state and source/version, if accessible; visibility is not a read |
| Actually read | Entry and task-required module paths, versions or hashes, read time/turn and loading mode; reading a repository by explicit path is not automatic discovery |
| Checked for this task | Actual task artifacts/checks and their scope; a receipt or version label alone does not prove behavior |

“Latest” means the source/version actually checked, with its check time; distinguish latest locally available from a verified upstream release. If metadata disagrees, a reference is missing, or the source cannot be inspected, record the mismatch and last verified source. Keep the upgrade unverified; neither an old receipt nor a successful business task closes that gap. Do not edit metadata to manufacture agreement.

## Preserve old reads before any package refresh

Host-managed caches are replaceable installation locations, not durable version pins. A backup restored after deletion cannot establish continuous availability at the old path. Orchivane cannot prevent the host or another actor from cleaning that path.

When work must continue on an older version:

1. Before refreshing a marketplace or replacing a package, copy the complete self-contained skill/source tree to a project-owned location outside managed caches, temporary checkouts and automatic skill discovery. Keep the relative layout and local customizations. Record the original and retained entry, version and full file hashes; reopen the retained entry and required references at their actual new locations. A symlink or references back into the cache are not independent preservation. If dependencies extend beyond the copied tree, preserve their resolution base too or keep the refresh blocked.
2. At the role's next normal task or agreed checkpoint, have it actually read the retained entry and needed modules and record that source in its own task receipt. The controller verifies the receipt before marking that reader protected. Copying files, changing an index or retaining an old read receipt does not redirect an already-running role. Do not message, restart or interrupt it merely to obtain this acknowledgment.
3. Hold **both marketplace refresh and package replacement** while any affected reader still needs the managed path, has an unaccepted pin, or has unknown source coverage. A plugin may be shared across projects; absence from this project's index does not prove there are no other readers. Without covering evidence, defer the update and let existing work continue. An idle role remains pending its next task; either that task verifies its retained source first or the update stays deferred. Check any host-triggered refresh mechanism before promising a maintenance window.
4. Once all affected readers have accepted independent sources or finished their work, use the authorized host update mechanism. Verify retained source hashes and reference readability afterwards, separately from the new installation. Keep each old copy until its dependent work ends and its owner authorizes cleanup. Do not rewrite old receipts or count retained-source reads as discovery/loading of the new plugin.

For a source-only skill such as Orchivane, preserving its complete skill directory preserves its relative reference layout. A plugin with servers, scripts or external runtime dependencies needs a separate dependency check; copying its Markdown alone is insufficient. This workflow protects a verified independent source from cache cleanup. It does not guarantee the original cache pathname, automatic hot reload, host-wide enforcement or availability through crashes and unrelated deletion.

## Roll out without interrupting work

1. The controller records its own reads and applies the relevant modules at its next safe work boundary. Keep one index maintainer and reuse existing change/health records.
2. For an active role, attach a pending check to the next normal task brief or agreed checkpoint. Leave its current execution, frozen skill snapshot and inputs alone. Check host messaging semantics before sending: if delivery can interrupt and has no verified noninterrupting queue, save the brief for later instead of sending an upgrade message now.
3. An idle role with no business task stays **pending next normal task**. A stopped or archived predecessor stays historical; a reference-only role checks only when its actual work needs the workflow. Do not create replacements, restart chats or change schedules to clear a coverage table.
4. At the next normal task, the role reads the agreed entry and necessary modules, confirms ownership/limits, completes authorized work and saves its own receipt. The controller later reads that evidence and updates the single index. Specialists never race to update the controller's ledger.

A version gap alone need not stop compatible, already-authorized work under the last verified rules. If ownership, authorization, budgets or a changed requirement conflict, pause only the affected action and route the conflict to the controller. Adoption does not grant new peer-messaging rights. Report a queued brief separately from substantive acceptance and from completed verification, using [dispatch.md](dispatch.md).

## Minimal receipt and coverage

Add these fields to an existing task receipt; do not introduce a parallel database or require every task to repeat unchanged evidence:

```text
Role / actual chat ID; normal task ID; read time or turn:
Target source/version; observed source/version; loading mode:
Actually read: entry + task-required modules, real paths and hashes/revision if needed:
Source retention when needed: original/retained entry, complete inventory/hash check,
normal-boundary acceptance evidence; readers still blocking refresh; post-update check:
Role ownership, original authorization, remaining budget and stop boundary:
Actual task artifacts/checks; what those checks do and do not establish:
Status: pending normal task / read only / checked for this task / unverified:
Gap and next owner/checkpoint; prior receipt being reused or superseded:
```

The controller's coverage row needs only role, target, last verified receipt/version, current status and next normal checkpoint. Partial reads cover only those modules. A specialist's claim without inspectable read/task evidence remains reported, not independently verified. Reuse a prior receipt with its original scope/time if source bytes, relevant modules and task boundaries still apply; read newly needed modules when the task changes. Recheck after an actual source change, not on every turn. Preserve old receipts and mark supersession rather than rewriting history.

Close only the verified roles and task scope; list deferred, historical and unverified entries explicitly. A passing controller check never establishes that all old chats hot-reloaded. Use [health-check.md](health-check.md) for gaps that need follow-up and [handoff.md](handoff.md) if a genuine responsibility handoff is also requested. No blanket restart, broadcast or repeated polling is part of adoption.
