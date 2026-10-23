# Codex adapter: use capabilities actually available now

This is tool-selection guidance, not a new API or grant of authority. Follow the current environment's live tool descriptions. On other clients, use equivalent capabilities; if absent, provide copyable handoff packages and briefs without pretending execution occurred.

| Need | Preferred native capability |
| --- | --- |
| Inspect actual chats and necessary history | `list_threads`, `read_thread`; verify exact titles/IDs and actual pagination coverage |
| Find an existing target/project | `list_projects`; `create_thread` only for a user request to create a chat |
| Dispatch to an existing role | `send_message_to_thread`, with direct human authorization or verifiable original human authority |
| Collect results | Compact `wait_threads` status, then `read_thread` as needed; avoid repeated polling |
| Check worktree/archive dependencies | `list_artifacts` plus actual file checks; the current chat's list does not describe another chat's attachments |
| Archive and confirm | `set_thread_archived`, `list_archived_threads`, with pagination as needed |
| Configure scheduled work | `automation_update`; first read matching existing configuration and preserve fields the user did not ask to change |

Look up projects before creation when the tool requires it. Reuse the original project and execution environment by default; choose worktrees or a specified starting state only under the user's request and tool rules. A returned `clientThreadId` is not a ready `threadId`. Check readiness rather than passing a pending ID to messaging/wait tools. Inspect uncertain creation results before deciding to retry.

When no registered project is available, an authorized projectless chat may be used, but it has its own working directory. Give actual shared-material paths and separate write boundaries in its first prompt. On initial acceptance, verify the actual working directory, shared root and input versions. If shared materials are inaccessible, report that precise gap rather than editing an unrelated default directory or relying on unauthorized paths.

Creation, dispatch, substantive acceptance and final validation are different events. Save returned IDs and register each immediately; handle registration delays as described in setup. Store native receipts in a private project runtime directory. Public examples should use sanitized copies without real chat IDs, personal absolute paths or raw transcripts, explicitly distinguished from replayable original logs.

For existing-chat upgrades, use [adoption.md](adoption.md). A newer installed cache does not prove an old chat read it. Marketplace refresh can also replace configured plugin files; apply the same preservation gate before refresh as before installation. Keep an update deferred while affected readers still depend on cache paths or their coverage is unknown. Independent retained-source reads need their own normal-task receipts and are not new-plugin discovery. This adapter specifies no hot-reload API or noninterrupting message guarantee: check the live tool semantics, and keep a pending normal-task brief on disk when delivery could interrupt active work. Do not send a probe merely to establish loading.

`fork_thread` retains history and is not a clean successor. `handoff_thread` moves a chat's execution location; it does not perform this skill's responsibility handoff. Chat archival and worktree archival are separate operations. Do not add worktree cleanup to “finish” a chat handoff.

Read automation configuration to verify task association, not to execute its prompt. When rebinding a target, construct the complete update from freshly read fields and verify the target, status, cadence and prompt. Trust actual current tool results only. If configuration cannot be read, state the coverage gap.

The package provides no MCP service, background process or automatic wake-up hook. Installing a skill does not grant tools or background execution. Persistent roles are native user chats; temporary subagents assist within the current task. Keep their records and permissions distinct.
