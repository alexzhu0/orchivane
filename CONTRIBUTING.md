# Contributing

Orchivane is a workflow skill for durable role-based chats. Changes should improve an observed coordination problem without requiring a new agent runtime.

## Validate locally

From the repository root, with Python 3.10 or later:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python scripts/validate.py
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v
```

On Windows use `.venv\Scripts\python.exe`. The development dependency parses YAML; running the skill itself needs no Python or packages. Static validation is read-only; fixture tests use temporary directories. Neither creates sessions or calls providers.

## Language conventions

`README.md` is the canonical English entry; `README.zh-CN.md` is the complete Chinese guide. Keep installation steps, capabilities and evidence claims in sync when editing either. `README.en.md` is a compatibility link, not a third maintained copy. The research and value guides also have `.zh-CN.md` counterparts.

Use English for code identifiers, comments, maintained skill instructions, plugin metadata and technical contributor documentation. Conversations should follow the user's preferred language. Preserve source-language quotations, historical reports and frozen fixtures; link an English summary instead of rewriting evidence. Translating a skill does not revalidate its prior behavior, so retain original experiment versions and disclose untested language behavior.

## Report a problem

Include the skill version, host/client and available tools, the minimal user request, expected and observed behavior, and which evidence was actually checked. Redact credentials, personal paths, private chat IDs, internal document links and transcripts. Do not publish raw session exports. For a security-sensitive issue, use the host repository's private vulnerability reporting if enabled; otherwise contact the maintainer through a private channel before sharing details publicly.

## Propose a change

Keep the main Skill short; place mode-specific instructions in the relevant reference. Preserve existing authorization, stop conditions and historical evidence. Record a reproducer before changing behavior and evaluate the changed path afterward. A baseline that already passes is a valid observation, not a failed test to relabel. Add small executable tests for new scripts; prose behavior requires actual agent outcomes, not keyword counts.

Change the portable manifest, the Codex and Claude compatibility manifests (`.codex-plugin/plugin.json`, `.claude-plugin/plugin.json`) and Skill metadata version together. Keep the README, examples and current evidence in sync. Historical test reports retain their original version and limitations. Update the CI action pins deliberately; do not add execution hooks or telemetry by default.

For adoption changes, exercise an existing project with active, idle and historical roles, then a normal task and a stale/partial receipt. Verify protected files and budgets, source/read/task evidence and deferred coverage separately. Keep simulated role-state exercises distinct from native messaging, installation and hot-reload claims; see [the bounded adoption protocol](tests/adoption-upgrade.md).

Native E2E runs require explicit human authorization to create and message real chats. Follow [the reproduction protocol](tests/native-e2e.md); do not launch native sessions automatically from CI. Passing static CI does not prove model behavior, cross-client compatibility or archival safety.

The [handoff/recovery protocol](tests/handoff-recovery.md) includes a bounded fixture for missing local inputs, ownership conflicts and duplicate dispatch. Count effects only in the actual runtime directory, not copied audit evidence. Verify that current role labels and next actions agree with delivered results before closing a run; retain failed snapshots and scope later hash comparisons to the relevant phase.

The [paired pilot](tests/paired/README.md) includes frozen inputs, prompts, final artifacts, resource metrics and offline replay tests. A zero-request baseline is a valid result. Keep human-time measurements separate from scripted coordination-request proxies, and equal budget ceilings separate from actual spend. New native trials require a new bounded plan; offline replay is not another behavioral trial.

Contributions are offered under this repository's [MIT license](LICENSE). Third-party source material retains its own license; add attribution when copying material, and prefer linking to upstream references.
