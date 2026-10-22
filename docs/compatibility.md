# Compatibility and current design basis

Checked against primary documentation on 2026-10-19; the Claude Code row on 2026-10-21. Version 0.4.0 adds a Claude Code adapter and manifests, with desktop runs recorded in [the Claude Code record](../tests/claude-code-desktop.md). Version 0.3.2 translates the skill and default presentation into English; the native installation and behavioral observations below remain tied to their original versions. A [2026-10-20 native 0.3.2 follow-up](../tests/bilingual-032.md) verified local upgrade and fresh-chat loading, with partial bilingual/handoff results and retained failures. A [2026-10-22 Codex 0.4.0 check](../tests/codex-040.md) verified two fresh chats and the bounded handoff path, retaining a source-record defect and evaluator correction. Availability is a capability question, not a brand-name guarantee.

| Surface | Supported claim | Limit |
| --- | --- | --- |
| Agent Skills-compatible reader | Standard SKILL.md, progressive references, no runtime dependency | The host must actually load the skill; no automatic tool entitlement |
| Codex desktop with native chat tools | Historical 0.2.0 creation → dispatch → artifact → review; a 0.4.0 follow-up verified fresh loading, read-only takeover, continuation and serial duplicate suppression | A documented run on one host is not every account/client version |
| Codex CLI / other skill clients | Instructions and records can be used | Native persistent-chat control must be verified separately; subagents are not a drop-in substitute |
| Claude Code desktop app (Code tab) | 0.4.0 adapter and `.claude-plugin/` manifests; three fresh-controller runs created task-chip roles, dispatched work and accepted a short brief with an independent review | Plugin installation from GitHub, `start_session`, controller handoff and a clean run of the final text are unverified; the terminal CLI lacks the desktop session tools; agent teams remain a conceptual comparison |
| Portable / Codex plugin package | CLI 0.157.1 installation passed; user observed desktop directory visibility; two fresh desktop chats read and used 0.3.1; later four fresh chats read installed 0.3.2, with partial behavioral results; two fresh chats read installed 0.4.0, with eight source hashes matched | UI-button installation, other hosts and repeatable implicit selection remain unverified |

The [Agent Skills specification](https://agentskills.io/specification) standardizes skill files and progressive loading; it does not standardize chat creation or archival. The core stays independent of a host, and the Codex reference documents native capabilities that must exist at execution time. Other clients can fall back to files and copyable task briefs without pretending a message was sent.

[OpenAI's plugin packaging guide](https://developers.openai.com/plugins/build/plugins) distinguishes portable manifests, compatibility manifests and local catalogs. The repository ships all three relevant files, no MCP server or hooks. The repo catalog points to its own root and makes the package available; it does not silently install or enable it.

[Claude Code's agent-team documentation](https://code.claude.com/docs/en/agent-teams) distinguishes teams and subagents and describes their coordination cost and lifecycle limits. That supports our distinction between durable user-visible roles and temporary helpers. It does not establish that Codex-native tools work in Claude Code. We do not copy tool names between runtimes or enable experimental features for the user. Version 0.4.0 therefore ships a separate adapter written from the desktop app's own tool descriptions and checked in native runs.

[Anthropic's multi-agent research account](https://www.anthropic.com/engineering/multi-agent-research-system) emphasizes delegation boundaries, complementary work and evaluation. Its results belong to its research system; this project claims no inherited quality or efficiency gain. [Context engineering guidance](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) motivates concise durable records and loading only relevant evidence, rather than copying complete chat histories.

## Observed installation behavior

The observations below concern the former Session Control 0.3.0 name. Orchivane 0.3.1 is the rename release; current checks are recorded in the evaluation document. Historical discovery results are not silently reassigned to the new name.

A full standalone copy in the documented user skill directory was discovered by Codex CLI 0.157.1 using app-server skills/list with forceReload=true, enabled=true, with no parsing errors. A symlink into this plugin repository appeared under a namespaced skill name in the CLI. Neither observation certifies the desktop skill catalog: three newly created desktop test chats did not list the skill, while an explicitly requested file read loaded version0.3.0 and all five references. Root cause remains unconfirmed. No desktop restart, plugin UI install or unrelated configuration changes were performed.

## Orchivane plugin installation follow-up

On 2026-10-19, `codex plugin marketplace add alexzhu0/orchivane` and `codex plugin add orchivane@orchivane-local` completed on CLI0.157.1. The plugin list reported installed=true and enabled=true for0.3.1. All seven skill files in the plugin cache matched the source; the standalone copy was preserved outside discovery directories. A fresh app-server scan returned exactly one `orchivane:orchivane` with pluginId `orchivane@orchivane-local`, enabled=true and a cache path.

Subsequent desktop checks on the same date established more: the user observed the directory entry; a fresh native chat discovered the declared skill, read its cached entry and setup module, and applied it to a fictional CSV-import request. Another fresh chat, whose request body did not name the skill, selected it and read setup and handoff modules. The controller inspected actual read commands and final responses. This establishes use on this host, not a guarantee of implicit selection: other plugins were active, both chats had Orchivane in their titles, and each scenario ran once. UI inspection was unavailable to the agent; visibility is explicitly user-reported. See [test record](../tests/desktop-plugin.md).

No desktop restart, UI-button installation, official-directory submission or new package behavior was required. The prior standalone failure remains historical evidence with an unknown cause; the verified plugin route is the recommended installation.

## What is deliberately outside the package

No background daemon, automatic role creation, centralized database, provider account access or new runtime protocol. Native tools already own those capabilities. Add an adapter only with a real target client, a minimal reproducible use case and an end-to-end result. Cross-host transfer, long-running scheduling, safe archival and interrupted-creation recovery each require separate real evidence before claiming support at the same level as the tested dispatch path.

## Isolated handoff and recovery follow-up

On 2026-10-20, a separate frozen 0.3.1 run exercised real old-owner delivery, fresh native successor acceptance, independent backup restoration and subsequent task execution. Missing inputs and conflicting ownership declarations blocked takeover; the latter was a labeled file injection, not a real concurrent writer. Identical serial dispatch reused evidence without another apply. Independent review supported those bounded checks but found two stale controller records; both passed closure recheck after one correction. See the [experiment and closure record](../tests/handoff-recovery.md). The fixture deliberately has no application-level deduplication. This is neither transactional exactly-once behavior nor crash, archive, lost-context or asynchronous transport recovery validation.

## Claude Code desktop follow-up

On 2026-10-20 and 2026-10-21, three fresh controllers in the Claude desktop app ran the skill end to end with task-chip roles; see the [record](../tests/claude-code-desktop.md). Host behavior that shaped the adapter: roles in app-managed worktrees are blocked by a built-in guard from `Write`/`Edit` on the base checkout while shell writes are not; worktrees branch from the base checkout's current branch; a chip's start notice arrives only with the controller's next turn and its end notice did not fire; archiving a controller did not archive its idle chip roles, despite the tool description; dirty worktrees were kept after archive and clean ones returned to a reuse pool. Each was observed in these runs or probes on one host, some only once, and may change between app versions.
