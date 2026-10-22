# Orchivane 0.4.1

**English** · [简体中文](README.zh-CN.md) · [MIT](LICENSE) · [Contributing](CONTRIBUTING.md)

**One intent. Many minds. Work carried forward.** Orchivane combines orchestration with the image of a direction vane: specialist roles working toward one shared goal.

## Who keeps the project moving across AI conversations?

You open separate AI conversations for research, implementation and testing. Each can handle a task, while the coordination still lands on you:

- **Moving context between windows.** Copying conclusions and explaining the same constraints and decisions again.
- **Reconciling conflicting work.** Two chats edit the same file, or one implements an outdated interface.
- **Starting over at handoff.** A fresh chat has a summary but cannot tell which decisions are current, where local changes live or who owns unfinished work.
- **Deciding what “done” means.** Implementation, tests, acceptance, push and deployment get collapsed into one claim.
- **Remaining the project coordinator.** You decide who acts next, what context they need and which result to trust.

Orchivane gives that work a single controller entry point. The controller clarifies the goal, chooses a useful collaboration structure, assigns one owner per deliverable and verifies results against explicit inputs and acceptance conditions. Specialists deliver artifacts and evidence. Handoffs carry decisions, limits and next steps forward. Small tasks can stay in one conversation.

For example, ask the controller to add login to an existing product. It first checks the current identity design and interfaces, decides how implementation and independent review should be divided, then reports implementation, verification, push and deployment separately. You guide the goal and important tradeoffs without repeating the whole request in every role's chat. This is the intended workflow; tested capabilities and limits are documented below.

**Coordination savings are not yet established.** In the [paired pilot](docs/evidence.md#paired-pilot), both workflows completed three tasks with zero extra coordination requests under the same tasks, model and turn ceilings. Orchivane used more cumulative active time and reported tokens. Real human time and sustained specialist collaboration were not measured.

Version 0.4.1 adds [existing-project adoption and upgrades](skills/orchivane/references/adoption.md): source/version verification, task-scoped read receipts and deferred role checks at normal work boundaries. Installation, actual loading and checked behavior are tracked separately; active and idle roles are not woken just to refresh a version.

Version 0.4.0 adds Claude Code support: plugin manifests and a [Claude Code adapter](skills/orchivane/references/claude-code.md) for the Claude desktop app's Code tab. In [three native desktop runs](tests/claude-code-desktop.md), fresh controllers created two persistent roles, dispatched work and accepted a short brief with an independent review. The final run passed 13 of 16 checks with three partial, and the text was revised afterwards without a rerun; plugin installation from GitHub has not been observed.

A [2026-10-22 Codex 0.4.0 follow-up](tests/codex-040.md) verified the already-installed plugin against eight source hashes and exercised fresh-chat loading, read-only takeover, continuation and duplicate dispatch in two chats/four turns. The functional paths passed; one source-record path defect was corrected by the evaluator and retained in evidence. This is bounded compatibility evidence, not a blanket nonregression claim.

Version 0.3.2 makes skill instructions, plugin presentation and default documentation English-first, with a complete Chinese README. You can continue using Chinese in conversations. A [native 0.3.2 follow-up](tests/bilingual-032.md) verified upgrade and loading in four fresh chats, bilingual planning, and English-to-Chinese handoff execution. The reverse handoff was interrupted by host capacity; final record consistency also needed controller closure. This is partial evidence, not proof of translation equivalence.

## Start from an idea

Start with an idea, research and clarify the work, choose a collaboration structure, then dispatch and accept concrete deliverables. No existing sessions or repository are required. Existing projects reuse their roles and records. The workflow can support software, research, content and operations projects.

The package contains one independently installable skill and lightweight plugin manifests. A short entry loads setup, dispatch, health-check, handoff, Codex and Claude Code references as needed. There is no background service, runtime dependency or automatic wake-up hook.

## Use it

In a conversation where the skill is available:

```text
Use $orchivane. I have a new project idea and no other sessions.
Research it with me, clarify the important constraints, and recommend
an appropriate collaboration structure and a concrete starting plan.
```

In Claude Code, write “Use orchivane” or run `/orchivane:orchivane` (plugin) or `/orchivane` (standalone copy); `$orchivane` is Codex syntax.

Common requests:

- **Design a workflow:** “Use $orchivane. I want to build … Research the constraints and recommend whether to split the work across chats.”
- **Inspect an existing project:** “Use $orchivane to check current roles and TODOs. Do not dispatch new tasks.”
- **Dispatch authorized work:** “Use $orchivane to assign the tasks I approved to the corresponding chats and read their deliveries.”
- **Prepare a handoff:** “Use $orchivane to prepare a handoff package for the current controller. Do not create or archive chats yet.”
- **Execute a handoff:** “Use $orchivane to create and verify a successor from this package, transfer related automation, then archive the old chat only after preservation and acceptance checks, including a post-archive check.”
- **Run one health check:** “Use $orchivane to inspect this project's collaboration. Report new issues, important gaps and next steps.”

The workflow is: understand the goal → research and discuss → recommend a structure → propose concrete tasks → execute within authorization. Split by durable context, dependencies and independent acceptance needs. Role names and counts depend on the project. Reuse existing authorization; ask together only for genuinely new actions that need it. Persistent roles and temporary subagents have different lifecycles.

## Install and migrate

### Codex plugin — recommended

Add the GitHub source and install the plugin, using the same plugin mechanism as other Codex plugins. No repository clone is required:

```sh
codex plugin marketplace add alexzhu0/orchivane
codex plugin add orchivane@orchivane-local
codex plugin list --marketplace orchivane-local --json
```

These commands were exercised on Codex CLI 0.157.1 for version 0.3.1: installed and enabled, with the cached skill discovered as `orchivane:orchivane`. On 2026-10-19, the user observed the desktop directory entry and two fresh desktop chats actually read and used the cached skill without restarting the app. One request body did not name the skill. See the [English evidence summary](docs/evidence.md#desktop-installation) and [original test record, Chinese](tests/desktop-plugin.md). UI visibility was user-reported; tool traces verified enablement and reads.

Say “Use Orchivane” or select `orchivane:orchivane` in the client. `$orchivane` in examples refers to the same workflow. The package is distributed through its public GitHub source; it has not been submitted to the official curated directory. Commands depend on your installed CLI; see [OpenAI's packaging guidance](https://developers.openai.com/plugins/build/plugins).

If a standalone copy already exists, preserve the full directory and local changes outside skill discovery directories. Once the plugin works, keep one active source to avoid duplicate discovery.

**No background process needs starting.** `installed=true` and `enabled=true` confirm installation and enablement. Verify actual loading in a fresh chat:

```text
Check whether Orchivane appears in the available skills for this conversation.
If it does, read its declared entry, report the version, and use it to suggest
whether an unclear new project needs multiple persistent roles.
If it does not, report that it was not discovered; do not search for a file
as a workaround. Read only: do not create chats or dispatch tasks.
```

Discovery, reading and following the workflow are separate checks. Natural-language selection depends on the host, model and other skills; explicitly name the skill when you want it selected.

### Existing projects and upgrades

Ask the existing controller:

```text
Use $orchivane to adopt or upgrade this project's collaboration workflow.
Verify the actual available source/version and your own module reads.
Keep existing roles and work in progress. Check each role at its next
normal task and retain a scoped receipt; leave idle roles pending.
Do not interrupt work, broadcast upgrade messages or restart chats.
```

The controller reuses the project rules and role index, records a verified target and integrates any needed guidance without replacing local rules. Each role records the entry/modules actually read, version or content identity, task/turn, ownership and limits, and the artifacts/checks it completed. The controller accepts those receipts individually. Partial reads, old versions and unavailable sources stay explicit gaps; an installed plugin does not make all existing chats upgraded.

This workflow is separate from installing a package. Use the host's supported update mechanism when installation changes are authorized, preserve customizations and keep one active source. Explicit-path loading is recorded as such. See the [adoption reference](skills/orchivane/references/adoption.md) for receipt fields and boundaries, and the [isolated exercise](tests/adoption-upgrade.md) for observed behavior and limits.

### Claude Code plugin

In Claude Code, add the GitHub source and install the plugin:

```text
/plugin marketplace add alexzhu0/orchivane
/plugin install orchivane@orchivane
```

From a shell, `claude plugin marketplace add alexzhu0/orchivane` and `claude plugin install orchivane@orchivane` do the same. The manifests pass `claude plugin validate`, and a session-only `--plugin-dir` load discovered and invoked `orchivane:orchivane`; installation from this GitHub source has not been observed yet. For a standalone copy, place the complete `skills/orchivane` directory at `~/.claude/skills/orchivane` or in a project's `.claude/skills/`, and keep one active source. Creating, messaging and archiving persistent chats needs the session tools of the Claude desktop app's Code tab; see the [Claude Code adapter](skills/orchivane/references/claude-code.md) and the [desktop record](tests/claude-code-desktop.md).

### Standalone skill

```sh
git clone https://github.com/alexzhu0/orchivane.git
cd orchivane
mkdir -p "$HOME/.agents/skills"
test ! -e "$HOME/.agents/skills/orchivane" && test ! -L "$HOME/.agents/skills/orchivane" && cp -R skills/orchivane "$HOME/.agents/skills/orchivane"
```

This macOS/Linux example refuses to overwrite an existing file, directory or symlink. Copy the complete [`skills/orchivane`](skills/orchivane/SKILL.md) directory, including `references/` and `agents/`. On Windows, copy it into the user's `.agents/skills/` directory. Older clients using `~/.codex/skills/` need their own discovery check. Preserve local customizations when updating and choose one installation source. See [Codex skill documentation](https://learn.chatgpt.com/docs/build-skills).

Version 0.3.1 renamed Session Control to Orchivane. If you installed `session-control`, preserve it and any local modifications outside discovery directories before installing the new name. Historical tests retain their original name and version.

The former 0.3.0 standalone copy was discovered by the CLI but absent from three fresh desktop chats. Its root cause remains unknown. The later 0.3.1 plugin route passed discovery and use; this does not retroactively fix or retest standalone installation. See [compatibility notes](docs/compatibility.md).

If automatic discovery is unavailable, explicitly ask the assistant to read the installed `orchivane/SKILL.md` at its real full path and follow it. Record that as explicit loading, not successful automatic discovery.

The repository includes `.agents/plugins/marketplace.json`, a portable root `plugin.json`, `.codex-plugin/plugin.json`, and `.claude-plugin/plugin.json` with `.claude-plugin/marketplace.json` for Claude Code. Existing personal `session-handoff` or `session-health-check` skills can remain installed; Orchivane includes its own complete modules and does not modify or depend on those older skills.

## Documentation and evidence

| Topic | Entry |
| --- | --- |
| Core workflow and routing | [SKILL.md](skills/orchivane/SKILL.md) |
| Research, setup, takeover and context recovery | [Setup](skills/orchivane/references/setup.md) |
| Existing-project adoption, deferred upgrades and version receipts | [Adoption](skills/orchivane/references/adoption.md) |
| Task briefs, dispatch and acceptance | [Dispatch](skills/orchivane/references/dispatch.md) |
| Preservation, successor acceptance and archival checks | [Handoff](skills/orchivane/references/handoff.md) |
| Incremental collaboration checks | [Health checks](skills/orchivane/references/health-check.md) |
| Native tools and fallbacks | [Codex adapter](skills/orchivane/references/codex.md) · [Claude Code adapter](skills/orchivane/references/claude-code.md) |
| Ponytail, Superpowers and related work | [Research](docs/research.md) · [中文](docs/research.zh-CN.md) |
| Value, tradeoffs and next priorities | [Value assessment](docs/value-assessment.md) · [中文](docs/value-assessment.zh-CN.md) |
| Results, versions and limitations | [English evidence index](docs/evidence.md) · [Original records, 中文](tests/evaluation.md) |
| Platform support and boundaries | [Compatibility](docs/compatibility.md) |
| Local checks and language conventions | [Contributing](CONTRIBUTING.md) |

## Boundaries

The skill defines a workflow; the host supplies chat creation, reading, messaging and automation tools. Without those tools, it can prepare files and task briefs but cannot control other chats. An inspection or design request does not authorize new chats, messaging, product fixes or archival. Schedules require a user request.

The native example finished at 19/20 and **failed acceptance**. The paired pilot found no coordination-request reduction. Bounded handoff tests do not prove crash recovery, concurrent safety or archival reliability. See [evidence](docs/evidence.md) for versions and failures; static checks are not behavioral tests or cross-client certification.

Code identifiers, comments, plugin metadata and maintained skill instructions use English. The README and selected design guides provide Chinese counterparts. Respond in the user's preferred language. Original Chinese transcripts, fixtures and frozen reports remain in their source language so evidence is not rewritten; the bounded [bilingual check](tests/bilingual-032.md) retains incomplete and failed observations alongside passes.
