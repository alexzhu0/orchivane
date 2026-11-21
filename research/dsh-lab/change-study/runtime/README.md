# DSH host bridge

`study-plugin.mjs` is a Cordis host plugin for the installed DSH 0.2.1-rc.3. Configuration is `{socketPath, token}`. Load it through a profile patch and remove stock tool plugins from that composition. It additionally restricts each agent's visible tool schema to `study_bash` and registers a deny guard for other tools.

The trusted host sends one NDJSON request per Unix socket connection. Every request includes `token`; replies must contain `ok: true`, or `{ok: false, error: "..."}`. Requests and replies are limited to 1 MiB. Connections have a 15-second deadline. Shell exchanges have a 45-second total deadline; control exchanges have a 15-second total deadline. Agent cancellation closes the connection.

| Request | Fields beyond `op` and `token` | Successful reply |
| --- | --- | --- |
| `ready` | `session_id`, `tools: ["study_bash"]` | `{ok:true}` |
| `execute` | `session_id`, `call_id`, `turn`, `step`, `command` | `{ok:true, stdout, stderr, exit_code, steering?:{text}}` |
| `steered` | `session_id`, `call_id`, `turn`, `step`, `message_id` | `{ok:true}` |
| `invalid` | `session_id`, `call_id`, `turn`, `step`, `reason` | `{ok:true}` |

The controller must run `command` only inside the required filesystem/process/network isolation. The plugin itself provides no OS sandbox. Its socket path, token, runtime files, and controller materials must remain inaccessible to tool child processes.

When `execute` returns steering, the host-only text stays in a WeakMap rather than entering the tool output. The awaited native `tools/post-execute` waterfall calls `Agent.steer(createUserMessage(...))` and waits for the controller's `steered` acknowledgement. DSH's current turn then admits the message at its next model step. This is step-boundary steering, not interruption of an already running model request or shell command.

The message's `agent/inbox/spliced` insertion is enqueue evidence only. Actual model admission is the later durable `user/message` event: its `data.id` equals `message_id`. The runtime logs a `step/start` before committing that message. The controller must verify the change was admitted in the same turn at a later step. If the model submitted another tool in the old step's batch, the plugin reports `invalid` with `tool_before_steering_consumed` and rejects that call before shell execution; this trial must be excluded.

The installed official SDK implementation at `@deepseek-ai/dsh-sdk-jsonrpc-server/lib/index.js` calls `agent.followup()` in `prompt()` (lines 153–164). The official `@deepseek-ai/dsh-agent/lib/types/runtime-types.d.ts` documents `steer()` as next-step input (lines 193–201); the loop claims next-step work between model calls in `@deepseek-ai/dsh-agent-loop/lib/index.js` (lines 950–1021). No SDK protocol methods or runtime files are patched.

`tests/runtime_steering_probe.mjs` uses the actual installed DSH AgentLoop, ToolRuntime, session store and message admission machinery, with a fake model and in-memory controller transport. It proves same-turn request visibility, wait-for-ack ordering, restricted tool inventory, rejection of another tool in the same batch, and resumption after consumption. It does not establish a real API run, Unix socket connectivity, or filesystem isolation. The ChatGPT execution sandbox rejects Unix socket `listen` with `EPERM`; those parts require a normal-terminal preflight/run.
