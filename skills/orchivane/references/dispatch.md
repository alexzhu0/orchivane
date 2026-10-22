# Impact analysis, dispatch and acceptance

## Make the task reviewable first

Compare the request with current rules and original evidence. List affected artifacts, callers, tests, materials and release steps without forcing unnecessary stages onto a small task. For existing decisions, check original text, comments, subsequent corrections and receipts; distinguish quotations, research synthesis and engineering interpretation. Do not ask the user to repeat answers already available.

A change record should include:

```markdown
# Change ID: concrete goal
Status: draft / authorized / executing / awaiting acceptance / closed / blocked
User goal and authorization source: ...
Current evidence and input versions: ...
Scope, budget and stop conditions: ...

| Task | Sole owner / chat ID | Deliverable and permitted edits | Dependencies | Completion criteria |
| --- | --- | --- | --- | --- |

## Dispatch and actual acceptance of responsibility
Delivery result; recipient's understanding of task, inputs, boundaries and first step.
Do not mark an undelivered task as executing.
## Delivery and acceptance
Actual paths/document versions/commits; validation coverage; outcome; push; deployment;
remaining work and next owner.
## Correction coverage
Updated; unchanged with reason; unverifiable; historical supersession.
```

Execute specifically authorized tasks. Authorization for research or a plan alone does not cover implementation, external communication or publication. For expanded scope, confirm only genuinely new actions requiring authority, not the previously approved list.

## Dispatch brief

> You own [role/task ID]. Human authorization: [verifiable original request]. Goal: [deliverable]; shared entry: [accessible root]; necessary context: [change, skill version and input-version links]; permitted edits: [scope]; dependencies and frozen items: [details]; budget and stop conditions: [limits]. Check the actual directory and inputs first. Deliver artifacts, versions, validation, remaining issues and next steps here. List cross-role changes in this chat for the controller to read; this message grants no new authority to reply to other chats.

Provide enough context to start, but only necessary materials. Record dispatch, understanding, execution, completion and acceptance separately. Before a message that may interrupt active work, check status and whether it is a necessary correction to the current task; avoid duplicate wake-ups.

For a pending adoption/version check, include its source and receipt requirement in the next authorized normal-task brief, following [adoption.md](adoption.md). Keep the current task and budget intact; an upgrade-only message is not a reason to interrupt or wake a role.

Independent tasks may run in parallel. Shared writes, production-data renaming and frozen-input updates need ordering or isolated directories first. Use temporary subagents only when host and user/project rules allow them, for bounded analysis or verification. They do not automatically replace existing persistent roles or authorize new user-visible chats.

When freezing inputs, preserve the directory structure and dependencies needed by references, or specify and verify their resolution base. An unchanged file hash after relocation does not prove relative links still work. Verify versions, required references and readability at the actual recipient entry before dispatching dependent work. If packaging breaks a reference, the controller responsible for freezing fixes the package; do not ask an author to alter correct source text to conceal the packaging fault. Keep the failed snapshot and version the replacement separately.

## Controller acceptance

1. Check actual artifacts and applicable versions against completion criteria. Reuse validation only while its evidence remains applicable. Arrange authorized independent acceptance for high-impact changes; ordinary small edits do not require multiple review rounds.
2. Record implementation, technical validation, actual outcome, push and deployment separately. A build may pass while a trial fails; report that failure and follow the original stop condition rather than claiming product acceptance.
3. For a failed result, record the reason and next decision. Continue only if the original authorization includes repair iterations and the stop condition has not been reached. Unused budget does not authorize tuning, switching models or rerunning.
4. Check every affected current location and recheck existing constraints touched by a correction. A new exception path must not conflict with existing state, permission or record rules. Preserve original text and frozen versions with supersession labels. Report inaccessible external locations honestly instead of claiming synchronization.
5. State the next owner and prerequisites. Leave idle roles alone when there is no new task; idleness does not justify reminders or handoff.
